"""
***************************************************************************
    CloneLayer.py
    ---------------------
    Author               : Parmenion Delialis
    Date                 : March 2022
    Contact              : parmeniondelialis@gmail.com
***************************************************************************
"""

from qgis.core import (QgsProcessing,
                                 QgsProcessingAlgorithm,
                                 QgsProcessingParameterVectorLayer,
                                 QgsProcessingParameterNumber,
                                 QgsProcessingParameterFeatureSink,
                                 QgsFeatureSink,
                                 Qgis)
import processing

class CloneLayer(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input', types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Clone Layer', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Parameters to layers/numbers
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        
        # Output
        #layer.dataProvider().deleteAttributes([layer.fields().indexOf('moransID')])
        source = layerSource
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        
        return {"OUTPUT":dest_id}


    def name(self):
        return 'clonelayer'

    def displayName(self):
        return 'Clone Layer'

    def group(self):
        return 'Tools'

    def groupId(self):
        return 'tools'
        
    def shortHelpString(self):
        return ("Create an identical layer in memory.")
    
    def createInstance(self):
        return CloneLayer()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))