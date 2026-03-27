// ShowInterpolationsPlugin.h
// ShowInterpolations
//
// Displays all active font instances overlaid with transparency
// in the Glyphs.app Edit view. Based on the ShowStyles reporter plugin.
//
// Copyright 2014-2024 Rainer Erich Scheichelbauer (@mekkablue).
// Licensed under the Apache License, Version 2.0.

#import <Cocoa/Cocoa.h>
#import <GlyphsCore/GlyphsReporterPlugin.h>
#import <GlyphsCore/GSFont.h>
#import <GlyphsCore/GSFontMaster.h>
#import <GlyphsCore/GSInstance.h>
#import <GlyphsCore/GSGlyph.h>
#import <GlyphsCore/GSLayer.h>
#import <GlyphsCore/GSPath.h>
#import <GlyphsCore/GSNode.h>
#import <GlyphsCore/GSAnchor.h>
#import <GlyphsCore/GSTab.h>
#import <GlyphsCore/Glyphs.h>

NS_ASSUME_NONNULL_BEGIN

/// Unicode star used as a node name to mark the alignment anchor point.
extern NSString * const GSIAlignMarker;

@interface ShowInterpolationsPlugin : GlyphsReporterPlugin

// MARK: - Drawing

/// Main drawing entry point called by Glyphs for every edit-view redraw.
/// Iterates active instances, interpolates each one, and fills the resulting
/// bezier paths behind the current layer's outlines.
- (void)drawBackgroundForLayer:(GSLayer *)layer;

// MARK: - Helpers

/// Returns an interpolated GSLayer for @p glyph in @p instance, or nil on
/// failure. Rounds to grid when gridLength == 1.
- (nullable GSLayer *)glyphInterpolation:(GSGlyph *)glyph
                                instance:(GSInstance *)instance;

/// Parses a semicolon-separated "R;G;B" or "R;G;B;A" string and returns the
/// corresponding NSColor. Falls back to @p fallback (same format), then to
/// the built-in default fuchsia (0.4, 0.0, 0.3, 0.15) if both are nil.
- (NSColor *)colorForParameterValue:(nullable NSString *)instanceValue
                           fallback:(nullable NSString *)fontValue;

/// Translates @p bezierPath horizontally by @p offset (no-op when |offset| ≤ 1).
- (void)alignBezierPath:(NSBezierPath *)bezierPath offset:(CGFloat)offset;

/// Returns a filled circle path of diameter @p markerWidth centred on @p point.
- (NSBezierPath *)roundDotForPoint:(NSPoint)point markerWidth:(CGFloat)markerWidth;

// MARK: - Context-menu actions

/// Toggles the "center interpolations" preference and forces a redraw.
- (void)toggleCentering:(nullable id)sender;

/// Marks the currently selected node with the alignment star on all masters.
- (void)alignAtNode:(nullable id)sender;

/// Removes all alignment stars from the current layer (and matching nodes on
/// other masters).
- (void)doNotAlignAtNode:(nullable id)sender;

@end

NS_ASSUME_NONNULL_END
