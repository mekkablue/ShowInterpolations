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
import math
ALIGN = u"★"

class ShowInterpolation(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Interpolations',
			'de': u'Interpolationen',
			'es': u'interpolaciones',
			'fr': u'interpolations'
		})
		
		# default centering setting:
		if Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] is None:
			Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] = False
	
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
	
	def recenterLayer(self, Layer, newCenterX):
		centerX = Layer.bounds.origin.x + Layer.bounds.size.width/2
		if centerX != newCenterX:
			shift = self.transform( float(newCenterX-centerX) )
			Layer.transform_checkForSelection_doComponents_(shift,False,False)
		return Layer
	
	def background(self, Layer):
		Glyph = Layer.parent
		Font = Glyph.parent
		Instances = [ i for i in Font.instances if i.active ]
		
		# values for centering:
		shouldCenter = Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]
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
		
		# EITHER display all instances that have a custom parameter,
		# OR, if no custom parameter is set, display them all:
		for thisInstance in Instances:
			showInterpolationValue = thisInstance.customParameters["ShowInterpolation"]
			if (not displayOnlyParameteredInstances) or (showInterpolationValue is not None):
				interpolatedLayer = self.glyphInterpolation( Glyph, thisInstance )
				if interpolatedLayer is not None:
					if not xAlign is None:
						interpolatedPoint = interpolatedLayer.paths[pathIndex].nodes[nodeIndex]
						xInterpolated = interpolatedPoint.x
						shift = self.transform( shiftX = (xAlign-xInterpolated) )
						interpolatedLayer.transform_checkForSelection_doComponents_(shift,False,False)
					elif shouldCenter:
						interpolatedLayer = self.recenterLayer(interpolatedLayer, centerX)
					self.colorForParameterValue( showInterpolationValue ).set()
					interpolatedLayer.bezierPath.fill()
	
	def glyphInterpolation( self, thisGlyph, thisInstance ):
		"""
		Yields a layer.
		"""
		try:
			# calculate interpolation:
			interpolatedFont = thisInstance.interpolatedFont
			interpolatedLayer = interpolatedFont.glyphs[thisGlyph.name].layers[0]
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
							'fr': u'Aligner les interpolations au point selectionné'
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
							'fr': u'Ne pas aligner les interpolations au point selectionné'
						}), 'action': self.doNotAlignAtNode
					},
				)
		
		if not Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Center Interpolations',
						'de': u'Interpolationen zentrieren',
						'es': u'Centrar las interpolaciones',
						'fr': u'Centrer les interpolations'
					}), 'action': self.toggleCentering
				},
			)
		else:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Do Not Center Interpolations',
						'de': u'Interpolationen nicht zentrieren',
						'es': u'No centrar las interpolaciones',
						'fr': u'Ne pas centrer les interpolations'
					}), 'action': self.toggleCentering
				},
			)

		# Return list of context menu items
		return contextMenus

	def toggleCentering(self):
		Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"] = not Glyphs.defaults["com.mekkablue.ShowInterpolation.centering"]
		# Glyphs.update() # causes crash in v919, therefore currently disabled
	
	def resetNodeAlignment(self, thisLayer):
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.name == ALIGN:
					thisNode.name = None
	
	def pathAndNodeIndexOfNode(self, requestedNode):
		"""
		Returns path and node indexes of the requested node.
		"""
		thisLayer = requestedNode.parent.parent
		
		# not found:
		return None, None
	
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
	
	def alignAtNode(self):
		thisLayer = Glyphs.font.selectedLayers[0]
		thisSelection = thisLayer.selection
		selectedNode = thisSelection[0]
		
		self.resetNodeAlignment(Glyphs.font.selectedLayers[0])
		self.setNodeName(selectedNode,ALIGN)
	
	def doNotAlignAtNode(self):
		self.resetNodeAlignment(Glyphs.font.selectedLayers[0])
		# self.setNodeName(None)
		
