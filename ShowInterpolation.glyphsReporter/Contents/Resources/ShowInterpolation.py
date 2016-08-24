#!/usr/bin/env python
# encoding: utf-8

import objc
from Foundation import NSBundle, NSClassFromString, NSObject, NSLog, NSColor
import sys, os, re

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp

ServiceProvider = NSClassFromString("GSServiceProvider").alloc().init()
GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class ShowInterpolation ( NSObject, GlyphsReporterProtocol ):
	
	def init( self ):
		"""
		Put any initializations you want to make here.
		"""
		try:
			#Bundle = NSBundle.bundleForClass_( NSClassFromString( self.className() ));
			
			
			return self
		except Exception as e:
			self.logToConsole( "init: %s" % str(e) )
	
	def interfaceVersion( self ):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )
	
	def title( self ):
		"""
		This is the name as it appears in the menu in combination with 'Show'.
		E.g. 'return "Nodes"' will make the menu item read "Show Nodes".
		"""
		try:
			return "Interpolations"
		except Exception as e:
			self.logToConsole( "title: %s" % str(e) )
	
	def keyEquivalent( self ):
		"""
		The key for the keyboard shortcut. Set modifier keys in modifierMask() further below.
		Pretty tricky to find a shortcut that is not taken yet, so be careful.
		If you are not sure, use 'return None'. Users can set their own shortcuts in System Prefs.
		"""
		try:
			return None
		except Exception as e:
			self.logToConsole( "keyEquivalent: %s" % str(e) )
	
	def modifierMask( self ):
		"""
		Use any combination of these to determine the modifier keys for your default shortcut:
			return NSShiftKeyMask | NSControlKeyMask | NSCommandKeyMask | NSAlternateKeyMask
		Or:
			return 0
		... if you do not want to set a shortcut.
		"""
		try:
			return 0
		except Exception as e:
			self.logToConsole( "modifierMask: %s" % str(e) )
	
	def glyphInterpolation( self, thisGlyph, thisInstance ):
		"""
		Yields a layer.
		"""
		try:
			# try:
			# 	# Glyphs 1.x syntax:
			# 	thisInterpolation = thisInstance.instanceInterpolations()
			# except:
			# 	# Glyphs 2.x syntax:
			# 	thisInterpolation = thisInstance.instanceInterpolations
			interpolatedFont = thisInstance.pyobjc_instanceMethods.interpolatedFont()
			print "interpolatedFont", interpolatedFont
			interGlyphs = interpolatedFont.glyphForName_(thisGlyph.name)
			interpolatedLayer = interGlyphs.layerForKey_(interpolatedFont.fontMasterID())
			thisFont = thisGlyph.parent
			if not thisInstance.customParameters["Grid Spacing"] and not ( thisFont.gridMain() / thisFont.gridSubDivision() ):
				interpolatedLayer.roundCoordinates()
			if len( interpolatedLayer.paths ) != 0:
				return interpolatedLayer
			else:
				return None
		except Exception as e:
			import traceback
			print traceback.format_exc()
			return None
	
	def colorForParameterValue( self, parameterString ):
		"""
		Turns '0.3;0.4;0.9' into RGB values and returns an NSColor object.
		"""
		try:
			# default color:
			RGBA = [ 0.4, 0.0, 0.3, 0.15 ]
			
			# if set, take user input as color:
			if parameterString is not None:
				parameterValues = parameterString.split(";")
				for i in range(len( parameterValues )):
					thisValueString = parameterValues[i]
					try:
						thisValue = abs(float( thisValueString ))
						if thisValue > 1.0:
							thisValue %= 1.0
						RGBA[i] = thisValue
					except Exception as e:
						pass
						# self.logToConsole( "Could not convert '%s' (from '%s') to a float. Keeping default." % (thisValueString, parameterString) )
			
			# return the color:
			thisColor = NSColor.colorWithCalibratedRed_green_blue_alpha_( RGBA[0], RGBA[1], RGBA[2], RGBA[3] )
			return thisColor
		except Exception as e:
			self.logToConsole( "colorForParameterValue: %s" % str(e) )
	
	def drawForegroundForLayer_( self, Layer ):
		try:
			pass
		except Exception as e:
			self.logToConsole( str(e) )
	
	def drawBackgroundForLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed BEHIND the paths.
		"""
		try:
			if False: #change to False if you want to activate
				pass
			else:
				Glyph = Layer.parent
				Font = Glyph.parent
				Instances = [ i for i in Font.instances if i.active ]
			
				if len( Instances ) > 0:
					# display all instances that have a custom parameter:
					displayedInterpolationCount = 0
					for thisInstance in Instances:
						showInterpolationValue = thisInstance.customParameters["ShowInterpolation"]
						if showInterpolationValue is not None:
							interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
							displayedInterpolationCount += 1
							if interpolatedLayer is not None:
								self.colorForParameterValue( showInterpolationValue ).set()
								self.bezierPathComp(interpolatedLayer).fill()
					
					# if no custom parameter is set, display them all:
					if displayedInterpolationCount == 0:
						self.colorForParameterValue( None ).set()
						for thisInstance in Instances:
							interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
							if interpolatedLayer is not None:
								self.bezierPathComp(interpolatedLayer).fill()
		except Exception as e:
			self.logToConsole( "drawBackgroundForLayer_: %s" % str(e) )

	def bezierPathComp( self, thisPath ):
		"""Compatibility method for bezierPath before v2.3."""
		try:
			return thisPath.bezierPath() # until v2.2
		except Exception as e:
			return thisPath.bezierPath # v2.3+
	
	def drawBackgroundForInactiveLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed behind the paths, but for inactive masters.
		"""
		try:
			pass
		except Exception as e:
			self.logToConsole( str(e) )
	
	def needsExtraMainOutlineDrawingForInactiveLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed in the Preview at the bottom.
		Remove the method or return True if you want to leave the Preview untouched.
		Return True to leave the Preview as it is and draw on top of it.
		Return False to disable the Preview and draw your own.
		In that case, don't forget to add Bezier methods like in drawForegroundForLayer_(),
		otherwise users will get an empty Preview.
		"""
		return True
					
	def getScale( self ):
		"""
		self.getScale() returns the current scale factor of the Edit View UI.
		Divide any scalable size by this value in order to keep the same apparent pixel size.
		"""
		try:
			return self.controller.graphicView().scale()
		except:
			self.logToConsole( "Scale defaulting to 1.0" )
			return 1.0
	
	def setController_( self, Controller ):
		"""
		Use self.controller as object for the current view controller.
		"""
		try:
			self.controller = Controller
		except Exception as e:
			self.logToConsole( "Could not set controller" )
	
	def logToConsole( self, message ):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "Show %s plugin:\n%s" % ( self.title(), message )
		print myLog
		NSLog( myLog )
