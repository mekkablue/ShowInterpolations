// ShowInterpolationsPlugin.m
// ShowInterpolations
//
// Displays all active font instances overlaid with transparency
// in the Glyphs.app Edit view. Based on the ShowStyles reporter plugin.
//
// Copyright 2014-2024 Rainer Erich Scheichelbauer (@mekkablue).
// Licensed under the Apache License, Version 2.0.

#import "ShowInterpolationsPlugin.h"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

NSString * const GSIAlignMarker = @"\u2605"; // ★

static NSString * const kDefaultsKeyPrefix   = @"com.mekkablue.ShowInterpolations.";
static NSString * const kDefaultsCentering   = @"com.mekkablue.ShowInterpolations.centering";
static NSString * const kDefaultsAnchors     = @"com.mekkablue.ShowInterpolations.anchors";
static NSString * const kDefaultsShowDisabled = @"com.mekkablue.ShowInterpolations.showDisabledStyles";
static NSString * const kCustomParam         = @"ShowInterpolations";

// ---------------------------------------------------------------------------
// Private interface
// ---------------------------------------------------------------------------

@interface ShowInterpolationsPlugin ()

/// Removes all alignment-star node names from @p layer's paths.
- (void)resetNodeAlignment:(GSLayer *)layer;

/// Sets @p nodeName on @p node and (unless @p otherMaster is YES) mirrors the
/// change to matching nodes on every other master.
- (void)setNodeName:(GSNode *)node
               name:(NSString *)nodeName
        otherMaster:(BOOL)otherMaster;

@end

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

@implementation ShowInterpolationsPlugin

// MARK: - Plugin lifecycle

- (NSUInteger)interfaceVersion {
    // Minimum Glyphs interface version required.
    return 1;
}

- (NSString *)title {
    // Localised menu name shown in View > Show … .
    return [Glyphs localize:@{
        @"en" : @"Interpolations",
        @"de" : @"Interpolationen",
        @"es" : @"interpolaciones",
        @"fr" : @"interpolations",
        @"pt" : @"interpolações",
        @"zh" : @"💗插值",
    }];
}

- (NSString *)keyboardShortcut {
    // Ctrl + Cmd + Opt + S  (mirrors the ShowStyles shortcut)
    return @"s";
}

- (NSEventModifierFlags)keyboardShortcutModifier {
    return NSEventModifierFlagControl | NSEventModifierFlagCommand | NSEventModifierFlagOption;
}

- (void)awakeFromNib {
    // Register user-defaults so boolForKey returns a sensible initial value.
    NSDictionary *defaults = @{
        kDefaultsCentering   : @NO,
        kDefaultsAnchors     : @NO,
        kDefaultsShowDisabled : @NO,
    };
    [[NSUserDefaults standardUserDefaults] registerDefaults:defaults];
}

// MARK: - Drawing

- (void)drawBackgroundForLayer:(GSLayer *)layer {
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
        NSInteger selectedIndex     = [font.currentTab selectedInstance];
        if (selectedIndex < 0) {
            alphaFactor = 1.0;
        }

        // ---- User preferences -----------------------------------------
        NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
        BOOL drawCentered       = [ud boolForKey:kDefaultsCentering];
        BOOL drawAnchors        = [ud boolForKey:kDefaultsAnchors];
        BOOL showDisabledStyles = [ud boolForKey:kDefaultsShowDisabled];

        // ---- Build instance list --------------------------------------
        NSMutableArray<NSArray *> *instances = [NSMutableArray array];
        NSArray<GSInstance *> *allInstances  = font.instances;
        for (NSUInteger i = 0; i < allInstances.count; i++) {
            GSInstance *inst = allInstances[i];
            if (inst.active || showDisabledStyles) {
                [instances addObject:@[@(i), inst]];
            }
        }
        if (instances.count == 0) return;

        // ---- Center-X of the current layer ----------------------------
        CGFloat centerX = NSMidX(layer.bounds);

        // ---- Find alignment-star node in the current layer ------------
        NSInteger pathIndex = -1, nodeIndex = -1;
        CGFloat xAlign = 0.0;
        BOOL hasAlignNode = NO;

        for (NSUInteger pi = 0; pi < layer.shapes.count; pi++) {
            id shape = layer.shapes[pi];
            if (![shape isKindOfClass:[GSPath class]]) continue;
            GSPath *path = (GSPath *)shape;
            for (NSUInteger ni = 0; ni < path.nodes.count; ni++) {
                GSNode *node = path.nodes[ni];
                if ([node.name isEqualToString:GSIAlignMarker]) {
                    pathIndex   = (NSInteger)pi;
                    nodeIndex   = (NSInteger)ni;
                    xAlign      = node.position.x;
                    hasAlignNode = YES;
                    break;
                }
            }
            if (hasAlignNode) break;
        }

        // ---- Check whether any instance carries the custom parameter --
        // If at least one does, only parametered instances are shown.
        BOOL showOnlyParametered = NO;
        for (NSArray *pair in instances) {
            GSInstance *inst       = pair[1];
            id paramValue          = inst.customParameters[kCustomParam];
            if (paramValue != nil) {
                showOnlyParametered = YES;
                break;
            }
        }

        // ---- Font-wide color override ---------------------------------
        NSString *globalColorValue = font.customParameters[kCustomParam];

        // ---- Draw each instance ---------------------------------------
        for (NSArray *pair in instances) {
            NSInteger index    = [pair[0] integerValue];
            GSInstance *inst   = pair[1];

            NSString *instanceColorValue = inst.customParameters[kCustomParam];
            if (showOnlyParametered && instanceColorValue == nil) continue;

            GSLayer *interpolatedLayer = [self glyphInterpolation:glyph instance:inst];
            if (!interpolatedLayer) continue;

            // Compute horizontal offset for centering / node-alignment.
            CGFloat offset = 0.0;
            if (hasAlignNode
                    && pathIndex >= 0 && pathIndex < (NSInteger)interpolatedLayer.shapes.count) {
                id interpShape = interpolatedLayer.shapes[(NSUInteger)pathIndex];
                if ([interpShape isKindOfClass:[GSPath class]]) {
                    GSPath *interpPath = (GSPath *)interpShape;
                    if (nodeIndex >= 0 && nodeIndex < (NSInteger)interpPath.nodes.count) {
                        GSNode *interpNode = interpPath.nodes[(NSUInteger)nodeIndex];
                        offset = xAlign - interpNode.position.x;
                    }
                }
            } else if (drawCentered) {
                CGFloat newCenterX = NSMidX(interpolatedLayer.bounds);
                offset = centerX - newCenterX;
            }

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
            NSBezierPath *bezierPath = interpolatedLayer.completeBezierPath;
            [self alignBezierPath:bezierPath offset:offset];
            [bezierPath fill];

            // Optionally draw anchors.
            if (drawAnchors) {
                [[NSColor colorWithCalibratedRed:0.3 green:0.1 blue:0.1 alpha:0.5] set];
                CGFloat scale = [self getScale];
                for (GSAnchor *anchor in interpolatedLayer.anchors) {
                    CGFloat dotSize = (scale > 0.0) ? (5.0 / scale) : 5.0;
                    NSBezierPath *dot = [self roundDotForPoint:anchor.position markerWidth:dotSize];
                    [dot fill];
                }
            }
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

        GSLayer *interpolatedLayer = interpolatedGlyph.layers.firstObject;
        if (!interpolatedLayer) return nil;

        // Only return a layer that actually has outline data.
        if (interpolatedLayer.paths.count == 0) return nil;

        // Round coordinates to grid when the font uses integer grid spacing.
        if (interpolatedFont.gridLength == 1.0) {
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

- (void)alignBezierPath:(NSBezierPath *)bezierPath offset:(CGFloat)offset {
    if (fabs(offset) <= 1.0) return;
    NSAffineTransform *t = [NSAffineTransform transform];
    [t translateXBy:offset yBy:0.0];
    [bezierPath transformUsingAffineTransform:t];
}

- (NSBezierPath *)roundDotForPoint:(NSPoint)point markerWidth:(CGFloat)markerWidth {
    NSRect rect = NSMakeRect(
        point.x - markerWidth * 0.5,
        point.y - markerWidth * 0.5,
        markerWidth,
        markerWidth);
    return [NSBezierPath bezierPathWithOvalInRect:rect];
}

// MARK: - Context menus

- (NSArray *)conditionalContextMenus {
    NSMutableArray *menus = [NSMutableArray array];
    NSUserDefaults *ud    = [NSUserDefaults standardUserDefaults];

    GSLayer *layer = [Glyphs font].selectedLayers.firstObject;
    NSArray *selection = layer.selection;

    if (selection.count == 1 && [selection.firstObject isKindOfClass:[GSNode class]]) {
        GSNode *node = (GSNode *)selection.firstObject;
        if (![node.name isEqualToString:GSIAlignMarker]) {
            // Offer to set the alignment node.
            [menus addObject:@{
                @"name" : [Glyphs localize:@{
                    @"en" : @"Align interpolations at selected node",
                    @"de" : @"Interpolationen an ausgewähltem Punkt ausrichten",
                    @"es" : @"Alinear las interpolaciones al nodo seleccionado",
                    @"fr" : @"Aligner les interpolations au point sélectionné",
                    @"pt" : @"Alinhar interpolações no nó selecionado",
                    @"zh" : @"以所选点为基点对齐",
                }],
                @"action" : NSStringFromSelector(@selector(alignAtNode:)),
            }];
        } else {
            // Offer to remove the alignment node.
            [menus addObject:@{
                @"name" : [Glyphs localize:@{
                    @"en" : @"Do not align interpolations at selected node",
                    @"de" : @"Interpolationen nicht an ausgewähltem Punkt ausrichten",
                    @"es" : @"No alinear las interpolaciones al nodo seleccionado",
                    @"fr" : @"Ne pas aligner les interpolations au point sélectionné",
                    @"pt" : @"Não alinhar interpolações no nó selecionado",
                    @"zh" : @"不以所选点为基点对齐",
                }],
                @"action" : NSStringFromSelector(@selector(doNotAlignAtNode:)),
            }];
        }
    }

    // Center-toggle item (carries a checkmark state).
    [menus addObject:@{
        @"name" : [Glyphs localize:@{
            @"en" : @"Center interpolations",
            @"de" : @"Interpolationen zentrieren",
            @"es" : @"Centrar las interpolaciones",
            @"fr" : @"Centrer les interpolations",
            @"pt" : @"Centralizar as interpolações",
            @"zh" : @"以中心对齐",
        }],
        @"action" : NSStringFromSelector(@selector(toggleCentering:)),
        @"state"  : @([ud boolForKey:kDefaultsCentering]),
    }];

    return [menus copy];
}

// MARK: - Context-menu actions

- (void)toggleCentering:(nullable id)sender {
    NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
    [ud setBool:![ud boolForKey:kDefaultsCentering] forKey:kDefaultsCentering];
    [[Glyphs font].currentTab forceRedraw];
}

- (void)alignAtNode:(nullable id)sender {
    GSLayer *layer       = [Glyphs font].selectedLayers.firstObject;
    GSNode  *selectedNode = (GSNode *)layer.selection.firstObject;
    [self resetNodeAlignment:layer];
    [self setNodeName:selectedNode name:GSIAlignMarker otherMaster:NO];
}

- (void)doNotAlignAtNode:(nullable id)sender {
    GSLayer *layer = [Glyphs font].selectedLayers.firstObject;
    [self resetNodeAlignment:layer];
}

// MARK: - Private node helpers

- (void)resetNodeAlignment:(GSLayer *)layer {
    for (GSPath *path in layer.paths) {
        for (GSNode *node in path.nodes) {
            if ([node.name isEqualToString:GSIAlignMarker]) {
                node.name = nil;
            }
        }
    }
}

- (void)setNodeName:(GSNode *)node
               name:(NSString *)nodeName
        otherMaster:(BOOL)otherMaster {
    @try {
        // The node's parent is the path; the path's parent is the layer.
        GSPath  *path  = (GSPath *)node.parent;
        GSLayer *layer = (GSLayer *)path.parent;

        // Clear existing alignment markers in this layer.
        [self resetNodeAlignment:layer];

        // Mark this node.
        node.name = nodeName;

        if (otherMaster) return; // Prevent infinite recursion.

        // Find this node's index so we can mirror it to other masters.
        NSInteger foundPathIndex = -1, foundNodeIndex = -1;
        for (NSUInteger pi = 0; pi < layer.shapes.count; pi++) {
            id shape = layer.shapes[pi];
            if (![shape isKindOfClass:[GSPath class]]) continue;
            GSPath *p = (GSPath *)shape;
            for (NSUInteger ni = 0; ni < p.nodes.count; ni++) {
                if (p.nodes[ni] == node) {
                    foundPathIndex = (NSInteger)pi;
                    foundNodeIndex = (NSInteger)ni;
                    break;
                }
            }
            if (foundPathIndex >= 0) break;
        }
        if (foundPathIndex < 0 || foundNodeIndex < 0) return;

        // Apply to every other master's corresponding layer.
        GSGlyph *glyph = (GSGlyph *)layer.parent;
        GSFont  *font  = (GSFont *)glyph.parent;
        for (GSFontMaster *master in font.masters) {
            if (master == font.selectedFontMaster) continue;
            GSLayer *masterLayer = glyph.layers[master.id];
            if (!masterLayer
                    || foundPathIndex >= (NSInteger)masterLayer.shapes.count) continue;
            id shape = masterLayer.shapes[(NSUInteger)foundPathIndex];
            if (![shape isKindOfClass:[GSPath class]]) continue;
            GSPath *masterPath = (GSPath *)shape;
            if (foundNodeIndex >= (NSInteger)masterPath.nodes.count) continue;
            GSNode *masterNode = masterPath.nodes[(NSUInteger)foundNodeIndex];
            [self setNodeName:masterNode name:nodeName otherMaster:YES];
        }
    }
    @catch (NSException *e) {
        NSLog(@"[ShowInterpolations] setNodeName:name:otherMaster: exception: %@", e);
    }
}

@end
