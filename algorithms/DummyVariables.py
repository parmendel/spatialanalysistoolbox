"""
***************************************************************************
    DummyVariables.py
    ---------------------
    Author               : Parmenion Delialis
    Date                 : March 2022
    Contact              : parmeniondelialis@gmail.com
***************************************************************************
"""

from qgis.core import    (QgsProcessing,
                          QgsProcessingAlgorithm,
                          QgsProcessingParameterVectorLayer,
                          QgsProcessingParameterField,
                          QgsProcessingParameterString,
                          QgsFeatureSink,
                          QgsProcessingParameterFeatureSink,
                          QgsVectorLayer,
                          Qgis)

import processing
import os, tempfile, random, string
import geopandas as gpd
import pandas as pd

class DummyVariables(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    VARIABLE = 'VARIABLE'
    PREFIX = 'PREFIX'
    OUTPUT = 'OUTPUT'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.VARIABLE, 'Categorical Variable', parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterString(self.PREFIX, 'Dummy fields prefix', optional=True, defaultValue='Cat'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Dummy Variables', createByDefault=True, supportsAppend=False, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        field = self.parameterAsString(parameters, self.VARIABLE, context)
        prefix = self.parameterAsString(parameters, self.PREFIX, context)
        dest_id = None
        
        layer = layerSource

        # Get temp path
        randExt = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
        temp = os.path.join(tempfile.gettempdir(), 'temp_{}.shp'.format(randExt))  # Path
        
        # Create a temp layer
        temp = os.path.join(tempfile.gettempdir(), 'temp.shp')  # Path

        # Read shp as geodataframe
        processing.run("script:clonelayer", {'INPUT':layer, 'OUTPUT':temp})['OUTPUT']
        data = gpd.read_file(temp)
        
        
        column = data[field]    # This is the original field
        data = pd.get_dummies(data=data, prefix=prefix, columns=[field])
        data = df = pd.concat([data, column], axis=1)   # pd.get_dummies deletes the original field, so this way it is joined back

        # Output
        outPath = os.path.join(tempfile.gettempdir(), 'temp_dummies_{}.shp'.format(randExt))
        data.to_file(outPath)
        vectorLayer = QgsVectorLayer(outPath,"DummyVariables","ogr")
        vectorLayer.setCrs(layer.crs())

        # Output & Load to QGIS
        source = vectorLayer
        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {self.OUTPUT: self.dest_id}

    def name(self):
        return 'dummy'

    def displayName(self):
        return 'Dummy Variables'

    def group(self):
        return 'Tools'

    def groupId(self):
        return 'tools'
        
    def shortHelpString(self):
        return ("Creates dummy variables from a categorical variable. \n This tool will create N new binary fields, where N is the unique number of categories in the given field.")

    def createInstance(self):
        return DummyVariables()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))