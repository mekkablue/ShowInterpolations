// ShowInterpolationsPlugin.m
// ShowInterpolations
//
// Displays all active font instances overlaid with transparency
// in the Glyphs.app Edit view. Based on the ShowStyles reporter plugin.
//
// Copyright 2014-2024 Rainer Erich Scheichelbauer (@mekkablue).
// Licensed under the Apache License, Version 2.0.

#import "ShowInterpolationsPlugin.h"
#import <GlyphsCore/GSGlyphViewControllerProtocol.h>
#import <GlyphsCore/GSInterpolationFontProxy.h>

// ---------------------------------------------------------------------------
// Glyphs.app main-class helpers — accessed via NSClassFromString to avoid
// a direct _OBJC_CLASS_$_Glyphs symbol reference, which the modern macOS
// dyld no longer exports from the main executable into the flat namespace.
// ---------------------------------------------------------------------------
static NSString *GlyphsLocalize(NSDictionary<NSString *, NSString *> *dict) {
    Class cls = NSClassFromString(@"Glyphs");
    if (cls && [cls respondsToSelector:@selector(localize:)]) {
        return [cls performSelector:@selector(localize:) withObject:dict];
    }
    return dict[@"en"] ?: dict.allValues.firstObject ?: @"";
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

static NSString * const kDefaultsShowDisabled = @"com.mekkablue.ShowInterpolations.showDisabledStyles";
static NSString * const kCustomParam          = @"ShowInterpolations";

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

@implementation ShowInterpolationsPlugin

// MARK: - Plugin lifecycle

- (NSUInteger)interfaceVersion {
    // Minimum Glyphs interface version required.
    return 1;
}

- (void)loadPlugin {
    NSLog(@"[ShowInterpolations] loadPlugin called");
    // Register user-defaults so boolForKey returns a sensible initial value.
    NSDictionary *defaults = @{
        kDefaultsShowDisabled : @NO,
    };
    [[NSUserDefaults standardUserDefaults] registerDefaults:defaults];
}

- (NSString *)title {
    // Localised menu name shown in View > Show … .
    NSString *t = GlyphsLocalize(@{
        @"en" : @"Interpolations",
        @"de" : @"Interpolationen",
        @"es" : @"interpolaciones",
        @"fr" : @"interpolations",
        @"pt" : @"interpolações",
        @"zh" : @"💗插值",
    });
    NSLog(@"[ShowInterpolations] title = %@", t);
    return t;
}

- (NSString *)keyEquivalent {
    // Ctrl + Cmd + Opt + S  (mirrors the ShowStyles shortcut)
    return @"s";
}

- (NSEventModifierFlags)modifierMask {
    return NSEventModifierFlagControl | NSEventModifierFlagCommand | NSEventModifierFlagOption;
}

// MARK: - Drawing

- (void)drawBackgroundForLayer:(GSLayer *)layer options:(NSDictionary *)options {
    @try {
        if (!layer) return;

        GSGlyph *glyph = layer.parent;
        if (!glyph) return;

        GSFont *font = (GSFont *)glyph.parent;
        if (!font) return;

        // ---- Visual hierarchy weights ---------------------------------
        // When the user has selected a specific instance in the tab bar,
        // that instance is drawn at full-ish alpha and the rest are dimmed.
        // When nothing is selected (selectedIndex < 0) everything is full.
        CGFloat alphaFactor         = 0.33;
        CGFloat alphaFactorSelected = 1.2;
        NSInteger selectedIndex     = [(NSViewController<GSGlyphEditViewControllerProtocol> *)self.controller selectedInstance];
        if (selectedIndex < 0) {
            alphaFactor = 1.0;
        }

        // ---- User preferences -----------------------------------------
        BOOL showDisabledStyles = [[NSUserDefaults standardUserDefaults] boolForKey:kDefaultsShowDisabled];

        // ---- Build instance list --------------------------------------
        NSMutableArray<NSArray *> *instances = [NSMutableArray array];
        NSArray<GSInstance *> *allInstances  = font.instances;
        for (NSUInteger i = 0; i < allInstances.count; i++) {
            GSInstance *inst = allInstances[i];
            if (inst.visible || showDisabledStyles) {
                [instances addObject:@[@(i), inst]];
            }
        }
        if (instances.count == 0) return;

        // ---- Check whether any instance carries the custom parameter --
        // If at least one does, only parametered instances are shown.
        BOOL showOnlyParametered = NO;
        for (NSArray *pair in instances) {
            GSInstance *inst = pair[1];
            if ([inst customValueForKey:kCustomParam] != nil) {
                showOnlyParametered = YES;
                break;
            }
        }

        // ---- Font-wide color override ---------------------------------
        NSString *globalColorValue = [font customValueForKey:kCustomParam];

        // ---- Draw each instance ---------------------------------------
        for (NSArray *pair in instances) {
            NSInteger index  = [pair[0] integerValue];
            GSInstance *inst = pair[1];

            NSString *instanceColorValue = [inst customValueForKey:kCustomParam];
            if (showOnlyParametered && instanceColorValue == nil) continue;

            GSLayer *interpolatedLayer = [self glyphInterpolation:glyph instance:inst];
            if (!interpolatedLayer) continue;

            // Compute per-instance alpha.
            NSColor *color = [self colorForParameterValue:instanceColorValue fallback:globalColorValue];
            CGFloat alpha;
            if (index == selectedIndex) {
                alpha = MIN(1.0, MAX(0.1, color.alphaComponent * alphaFactorSelected));
            } else {
                alpha = MIN(0.9, MAX(0.05, color.alphaComponent * alphaFactor));
            }
            [[color colorWithAlphaComponent:alpha] set];

            // Draw the filled outline.
            [interpolatedLayer.bezierPath fill];
        }
    }
    @catch (NSException *e) {
        NSLog(@"[ShowInterpolations] drawBackgroundForLayer: exception: %@", e);
    }
}

// MARK: - Helpers

- (nullable GSLayer *)glyphInterpolation:(GSGlyph *)glyph instance:(GSInstance *)instance {
    @try {
        GSFont *interpolatedFont = [instance interpolatedFont];
        if (!interpolatedFont) return nil;

        GSGlyph *interpolatedGlyph = [interpolatedFont glyphForName:glyph.name];
        if (!interpolatedGlyph) return nil;

        GSLayer *interpolatedLayer = interpolatedGlyph.layers.allValues.firstObject;
        if (!interpolatedLayer) return nil;

        // Only return a layer that actually has outline data.
        if ([(id)interpolatedLayer.paths count] == 0) return nil;

        // Round coordinates to grid when the font uses integer grid spacing.
        if ([(id)interpolatedFont gridLength] == 1.0) {
            [interpolatedLayer roundCoordinates];
        }

        return interpolatedLayer;
    }
    @catch (NSException *e) {
        NSLog(@"[ShowInterpolations] glyphInterpolation:instance: exception: %@", e);
        return nil;
    }
}

- (NSColor *)colorForParameterValue:(nullable NSString *)instanceValue
                           fallback:(nullable NSString *)fontValue {
    // Default: fuchsia-ish  R=0.4  G=0.0  B=0.3  A=0.15
    CGFloat r = 0.4, g = 0.0, b = 0.3, a = 0.15;

    // Parse font-wide value first, then instance value (instance wins).
    for (NSString *paramStr in @[(fontValue ?: @""), (instanceValue ?: @"")]) {
        if (paramStr.length == 0) continue;
        NSArray<NSString *> *parts = [paramStr componentsSeparatedByString:@";"];
        CGFloat *channels[4] = { &r, &g, &b, &a };
        for (NSUInteger i = 0; i < MIN(parts.count, 4); i++) {
            double val = [parts[i] doubleValue];
            if (val < 0.0) val = -val;           // abs()
            if (val > 1.0) val = fmod(val, 1.0); // wrap to [0,1]
            *channels[i] = (CGFloat)val;
        }
    }

    return [NSColor colorWithCalibratedRed:r green:g blue:b alpha:a];
}

@end
