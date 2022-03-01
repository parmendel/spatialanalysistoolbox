"""
***************************************************************************
    LocationQuotient.py
    ---------------------
    Author               : Parmenion Delialis
    Date                 : March 2022
    Contact              : parmeniondelialis@gmail.com
***************************************************************************
"""

import processing
from qgis.core import (QgsProcessing,
                                QgsProcessingAlgorithm,
                                QgsProcessingParameterVectorLayer,
                                QgsProcessingParameterField,
                                QgsProcessingParameterFeatureSink,
                                QgsProcessingParameterString,
                                QgsFeatureSink,
                                QgsField,
                                QgsProcessingUtils,
                                Qgis,
                                QgsSymbol,
                                QgsStyle,
                                QgsGraduatedSymbolRenderer)
from PyQt5.QtCore import QVariant
import os

class LocationQuotient(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    VARIABLEX = 'VARIABLEX'
    VARIABLEY = 'VARIABLEY'
    LQFIELD = 'LQFIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Layer', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.VARIABLEX, 'Variable X', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterField(self.VARIABLEY, 'Variable Y', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterString(self.LQFIELD, 'Name for LQ Field ', defaultValue = 'LQ'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Location Quotient', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Convert parameters
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        variableX = self.parameterAsString(parameters, self.VARIABLEX, context)
        variableY = self.parameterAsString(parameters, self.VARIABLEY, context)
        lqField = self.parameterAsString(parameters, self.LQFIELD, context)
        self.field = lqField
        dest_id = None
        
        # Clone layer
        layer = processing.run("sat:clonelayer", {'INPUT':layer, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        # Creating new field for LQ
        flds = layer.fields()
        pr = layer.dataProvider()
        
        # Checking if LQField exists
        if lqField not in flds.names():
            pr.addAttributes([QgsField(lqField, QVariant.Double, len=10, prec=5)])
            layer.updateFields()
            flds = layer.fields()
        else:
            return{'Error:':'LQ Field name already exists'}

        # Getting field index from name
        idx1 = flds.indexOf(variableX)
        idx2 = flds.indexOf(variableY)
        LQFieldIdx = flds.indexOf(lqField)
        # Calculating bottom part of fraction (Xi/Yi)
        X = 0   #Sum of xi
        Y = 0   #Sum of yi
        for ftr in layer.getFeatures():
            X += ftr[idx1]
            Y += ftr[idx2]
        XoverY = X/Y
        
        # Calculating LQ
        for ftr in layer.getFeatures():
            xovery = ftr[idx1] / ftr[idx2]
            LQ = xovery / XoverY
            toAdd = {LQFieldIdx:LQ}
            pr.changeAttributeValues({ftr.id():toAdd})
        layer.updateFields()

        source = layer
        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {self.OUTPUT: self.dest_id}

    def postProcessAlgorithm(self, context, feedback):
        # Styling
        layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        symbol = QgsSymbol.defaultSymbol(layer.geometryType() )
        if symbol is None:
            if geometryType == QGis.Point:
                symbol = QgsMarkerSymbol()
            elif geometryType == QGis.Line:
                symbol =  QgsLineSymbol()
            elif geometryType == QGis.Polygon:
                symbol = QgsFillSymbol()
        
        defStyle = QgsStyle().defaultStyle()
        colorRamp = defStyle.colorRamp('PiYG')
        renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, 
                                                                                            self.field,
                                                                                            5, 
                                                                                            1,
                                                                                            symbol,
                                                                                            colorRamp)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

        return {self.OUTPUT: self.dest_id}

    def name(self):
        return 'locationquotient'

    def displayName(self):
        return 'Location Quotient (LQ)'
        
    def shortHelpString(self):
        return (
"LQ compares the percentage of two variables in a region with the percentage of the same variables in a larger geographic unit (e.g. the whole country). \n"
"Location Quoetient formula: LQ = (xi/yi) / (Xi/Yi) where xi, yi are the variables and Xi, Yi is the summary of xi,yi in the wider area. \n"
"LQ Algorithm requires a vector layer (any geometry) and two fields as x, y variables. It calculates the LQ  and the value in the attribute table for each feature.")
    def createInstance(self):
        return LocationQuotient()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))