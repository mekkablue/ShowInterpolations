# Show Interpolations

This is a plugin for the [Glyphs font editor](http://glyphsapp.com/) by Georg Seifert.
It calculates all active instances for the given glyph and draws them behind your paths.
By default, it draws all active instances on top of each other using a transparent fuchsia/lavender color:

![All instances are shown live.](ShowInterpolations.png "Show Interpolations Screenshot")

After installation, it will add the menu item *View > Show Interpolations* (de: *Interpolationen zeigen,* fr: *Montrer Interpolations,* es: *Mostrar Interpolaciones,* zh: 💗插值).
You can set a keyboard shortcut in System Preferences.

### Installation

Please install the plugin via the built-in Plugin Manager, available via *Window > Plugin Manager*. If this is not possible for some reason or another, follow these steps:

1. Download the complete ZIP file and unpack it, or clone the repository.
2. Double click the `.glyphsReporter` file. Confirm the dialog that appears in Glyphs.
3. Restart Glyphs

### Usage Instructions

1. Open a glyph in Edit View.
2. Use *View > Show Interpolations* to toggle the preview of the instances.

To center the interpolations under the frontmost layer, Ctrl- or right-click anywhere in the canvas to invoke the context menu, and choose *Center Interpolations* (de: *Interpolationen zentrieren,* fr: *Centrer interpolations,* es: *Centrar interpolaciones,* zh: 以中心对齐). 

![Toggle the centering of interpolations via the context menu](ShowInterpolationsContextMenu.png "Show Interpolations Context Menu")

Alternatively, you can also align at a certain node. To do that, select a node, bring up the context menu, and choose 
*Align Interpolations at Selected Node* (de: *Interpolationen an ausgewähltem Punkt ausrichten,* es: *Alinear las interpolaciones a nodo seleccionado,* fr: *Aligner les interpolations au point selectionné,* zh: 以所选点为基点对齐).
The node in question will then be marked with a star. To cancel point alignment, select the starred node, and choose  *Do not Align Interpolations at Selected Node* (de: *Interpolationen nicht an ausgewähltem Punkt ausrichten,* es: *No alinear las interpolaciones a nodo seleccionado,* fr: *Ne pas aligner les interpolations au point selectionné,* zh: 不以所选点为基点对齐) from the context menu.


### Custom Parameter

To only view specific interpolations, add this custom parameter to the instance(s) you want to preview in *File > Font Info > Exports:*

    Property: ShowStyles
    Value: -
    Value: .1;.8;.2
    Value: 1;0.5;0;0.1

The Value defines the color of the instance. You can either leave the value blank to use the default color. Or, you can set semicolon-separated RGB values between 0 and 1. If you supply a fourth value, it will be interpreted as alpha (opacity: 1.0 = opaque, 0.0 = invisible).

If you want to change the color *globally,* add the parameter in *File > Font Info > Font > Custom Parameters.* 

**Legacy note:** In Glyphs 2, the parameter is called `ShowInterpolation`.


### Extra Settings

If you want the plug-in to also display inactive instances, run this in Macro Window:

```
Glyphs.defaults["com.mekkablue.ShowInterpolation.showDisabledInstances"]=True
```

### Requirements

The plugin needs Glyphs 2.4 or higher, running on OS X 10.9.5 or later.

### License

Copyright 2014-2018 Rainer Erich Scheichelbauer (@mekkablue).
Based on sample code by Georg Seifert (@schriftgestalt) and Jan Gerner (@yanone).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

See the License file included in this repository for further details.
