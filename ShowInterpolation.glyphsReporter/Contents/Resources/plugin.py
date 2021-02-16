# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################


from GlyphsApp.plugins import *
from GlyphsApp import GSNode
import math

ALIGN = u"★"

class ShowInterpolation(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Interpolations',
			'de': u'Interpolationen',
			'es': u'interpolaciones',
			'fr': u'interpolations',
			'zh': u'💗插值',
		})
		
		# default centering setting:
		Glyphs.registerDefault("com.mekkablue.ShowInterpolation.centering", 0)
		Glyphs.registerDefault("com.mekkablue.ShowInterpolation.anchors", 0)

	@objc.python_method
	def transform(self, shiftX=0.0, shiftY=0.0, rotate=0.0, skew=0.0, scale=1.0):
		"""
		Returns an NSAffineTransform object for transforming layers.
		Apply an NSAffineTransform t object like this:
			Layer.transform_checkForSelection_doComponents_(t,False,True)
		Access its transformation matrix like this:
			tMatrix = t.transformStruct() # returns the 6-float tuple
		Apply the matrix tuple like this:
			Layer.applyTransform(tMatrix)
			Component.applyTransform(tMatrix)
			Path.applyTransform(tMatrix)
		Chain multiple NSAffineTransform objects t1, t2 like this:
			t1.appendTransform_(t2)
		"""
		myTransform = NSAffineTransform.transform()
		if rotate:
			myTransform.rotateByDegrees_(rotate)
		if scale != 1.0:
			myTransform.scaleBy_(scale)
		if not (shiftX == 0.0 and shiftY == 0.0):
			myTransform.translateXBy_yBy_(shiftX,shiftY)
		if skew:
			skewStruct = NSAffineTransformStruct()
			skewStruct.m11 = 1.0
			skewStruct.m22 = 1.0
			skewStruct.m21 = math.tan(math.radians(skew))
			skewTransform = NSAffineTransform.transform()
			skewTransform.setTransformStruct_(skewStruct)
			myTransform.appendTransform_(skewTransform)
		return myTransform

	@objc.python_method
	def recenterLayer(self, Layer, newCenterX):
		centerX = Layer.bounds.origin.x + Layer.bounds.size.width/2

		# update if the previous and current center are off sync
		# only act if the new difference is at least 1 unit to avoid 
		# rounding jitter
		if abs(centerX - newCenterX) > 1.0:
			shift = self.transform( float(newCenterX-centerX) )
			Layer.transform_checkForSelection_doComponents_(shift,False,False)
		return Layer

	@objc.python_method
	def background(self, Layer):
		if Layer:
			Glyph = Layer.parent
			if Glyph:
				Font = Glyph.parent
				if Font:
					Instances = [ i for i in Font.instances if i.active or Glyphs.defaults["com.mekkablue.ShowInterpolation.showDisabledInstances"] ]
		
					# values for centering:
					centerX = Layer.bounds.origin.x + Layer.bounds.size.width/2

					# values for aligning on a node:
					pathIndex, nodeIndex, xAlign = None, None, None
					for thisPathIndex, thisPath in enumerate(Layer.paths):
						for thisNodeIndex, thisNode in enumerate(thisPath.nodes):
							if thisNode.name == ALIGN:
								pathIndex, nodeIndex = thisPathIndex, thisNodeIndex
								xAlign = thisNode.x
		
					# Determine whether to display only instances with parameter:
					displayOnlyParameteredInstances = False
					for thisInstance in Instances:
						if thisInstance.customParameters["ShowInterpolation"]:
							displayOnlyParameteredInstances = True
					
					# check for value set in Font Info > Font > Custom Parameters:
					globalInterpolationValue = Font.customParameters["ShowInterpolation"]

					# EITHER display all instances that have a custom parameter,
					# OR, if no custom parameter is set, display them all:
					for thisInstance in Instances:
						showInterpolationValue = thisInstance.customParameters["ShowInterpolation"]
						if (not displayOnlyParameteredInstances) or (showInterpolationValue is not None):
							interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
							if interpolatedLayer is not None:
								
								# draw interpolated paths+components:
								if not xAlign is None:
									interpolatedPoint = interpolatedLayer.paths[pathIndex].nodes[nodeIndex]
									xInterpolated = interpolatedPoint.x
									shift = self.transform( shiftX = (xAlign-xInterpolated) )
									interpolatedLayer.transform_checkForSelection_doComponents_(shift,False,False)
								elif Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]:
									interpolatedLayer = self.recenterLayer(interpolatedLayer, centerX)
									
								# set color:
								self.colorForParameterValue( showInterpolationValue, globalInterpolationValue ).set()
								interpolatedLayer.bezierPath.fill()
								
								# draw anchors:
								if Glyphs.defaults["com.mekkablue.ShowInterpolation.anchors"]:
									NSColor.colorWithRed_green_blue_alpha_(0.3, 0.1, 0.1, 0.5).set()
									for thisAnchor in interpolatedLayer.anchors:
										self.roundDotForPoint( thisAnchor.position, 5.0/self.getScale() ).fill()

	@objc.python_method
	def roundDotForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with the radius markerWidth around thisPoint.
		"""
		myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
		return NSBezierPath.bezierPathWithOvalInRect_(myRect)

	@objc.python_method	
	def glyphInterpolation( self, thisGlyph, thisInstance ):
		"""
		Yields a layer.
		"""
		try:
			# calculate interpolation:
			# interpolatedFont = thisInstance.interpolatedFont # too slow still
			interpolatedFont = thisInstance.pyobjc_instanceMethods.interpolatedFont()
			interpolatedLayer = interpolatedFont.glyphForName_(thisGlyph.name).layers[0]
			
			if interpolatedLayer.components:
				interpolatedLayer.decomposeComponents()
			
			# round to grid if necessary:
			if interpolatedLayer.paths:
				if interpolatedFont.gridLength == 1.0:
					interpolatedLayer.roundCoordinates()
				return interpolatedLayer
			else:
				return None
			
		except:
			import traceback
			print traceback.format_exc()
			return None

	@objc.python_method
	def colorForParameterValue( self, instanceParameterString, fallbackParameterString ):
		"""
		Turns '0.3;0.4;0.9' into RGB values and returns an NSColor object.
		"""
		try:
			# default color:
			RGBA = [ 0.4, 0.0, 0.3, 0.15 ]
			
			# first overwrite with font-wide color,
			# then again with instance color:
			for parameterString in (fallbackParameterString, instanceParameterString):
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

	@objc.python_method
	def conditionalContextMenus(self):
		contextMenus = []
		
		thisLayer = Glyphs.font.selectedLayers[0]
		thisSelection = thisLayer.selection
		if len(thisSelection) == 1 and type(thisSelection[0]) == GSNode:
			thisNode = thisSelection[0]
			if thisNode.name != ALIGN:
				contextMenus.append(
					{
						'name': Glyphs.localize({
							'en': u'Align Interpolations at Selected Node',
							'de': u'Interpolationen an ausgewähltem Punkt ausrichten',
							'es': u'Alinear las interpolaciones a nodo seleccionado',
							'fr': u'Aligner les interpolations au point selectionné',
							'zh': u'以所选点为基点对齐',
						}), 'action': self.alignAtNode
					},
				)
			else:
				contextMenus.append(
					{
						'name': Glyphs.localize({
							'en': u'Do not Align Interpolations at Selected Node',
							'de': u'Interpolationen nicht an ausgewähltem Punkt ausrichten',
							'es': u'No alinear las interpolaciones a nodo seleccionado',
							'fr': u'Ne pas aligner les interpolations au point selectionné',
							'zh': u'不以所选点为基点对齐',
						}), 'action': self.doNotAlignAtNode
					},
				)
		
		contextMenus.append(
			{
				'name': Glyphs.localize({
					'en': u'Center Interpolations',
					'de': u'Interpolationen zentrieren',
					'es': u'Centrar las interpolaciones',
					'fr': u'Centrer les interpolations',
					'zh': u'以中心对齐',
				}),
				'action': self.toggleCentering,
				'state': Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"],
			},
		)

		# Return list of context menu items
		return contextMenus

	@objc.python_method	
	def toggleCentering(self):
		Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] = not Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]
		# Glyphs.update() # causes crash in v919, therefore currently disabled

	@objc.python_method
	def resetNodeAlignment(self, thisLayer):
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.name == ALIGN:
					thisNode.name = None

	@objc.python_method	
	def setNodeName(self, selectedNode, newNote, otherMaster=False):
		try:
			# reset alignment:
			thisLayer = selectedNode.parent.parent
			self.resetNodeAlignment(thisLayer)
			
			# set alignment:
			selectedNode.name = newNote

			# set alignment node in other masters too:
			if not otherMaster:
				
				# iterate through all nodes ...
				pathIndex, nodeIndex = None, None
				for thisPathIndex, thisPath in enumerate(thisLayer.paths):
					for thisNodeIndex, thisNode in enumerate(thisPath.nodes):
						# ... find selected node and record its indexes:
						if thisNode is selectedNode:
							pathIndex, nodeIndex = thisPathIndex, thisNodeIndex
				
				# go through other masters and set node with recorded indexes:
				thisGlyph = thisLayer.parent
				thisFont = thisGlyph.parent
				masters = [m for m in thisFont.masters if m != thisFont.selectedFontMaster]
				for thisMaster in masters:
					id = thisMaster.id
					masterNode = thisGlyph.layers[id].paths[pathIndex].nodes[nodeIndex]
					self.setNodeName( masterNode, newNote, otherMaster=True)
		except Exception as e:
			import traceback
			print traceback.format_exc()

	@objc.python_method
	def alignAtNode(self):
		thisLayer = Glyphs.font.selectedLayers[0]
		thisSelection = thisLayer.selection
		selectedNode = thisSelection[0]
		
		self.resetNodeAlignment(Glyphs.font.selectedLayers[0])
		self.setNodeName(selectedNode,ALIGN)

	@objc.python_method
	def doNotAlignAtNode(self):
		self.resetNodeAlignment(Glyphs.font.selectedLayers[0])
		# self.setNodeName(None)
		
