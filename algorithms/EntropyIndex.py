"""
***************************************************************************
    EntropyIndex.py
    ---------------------
    Author               : Parmenion Delialis
    Date                 : March 2022
    Contact              : parmeniondelialis@gmail.com
***************************************************************************
"""

from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsFeatureSink,
                       QgsField,
                       Qgis)
from PyQt5.QtCore import QVariant
import processing
import numpy as np

class EntropyIndex(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    FIELD1 = 'FIELD1'
    FIELD2 = 'FIELD2'
    ENTROPYFIELD = 'ENTROPYFIELD'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input Layer', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.FIELD1, 'First field in data series', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterField(self.FIELD2, 'Last field in data series', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterString(self.ENTROPYFIELD, 'Name for Entropy Field ', defaultValue = 'Entropy'))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Entropy Layer', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Convert parameters
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        field1 = self.parameterAsString(parameters, self.FIELD1, context)
        field2 = self.parameterAsString(parameters, self.FIELD2, context)
        entropyField = self.parameterAsString(parameters, self.ENTROPYFIELD, context)
        
        layer = processing.run("sat:clonelayer", {'INPUT':layerSource, 'OUTPUT':'TEMPORARY_OUTPUT'})['OUTPUT']
        
        flds = layer.fields()
        index1 = flds.indexOf(field1)
        index2 = flds.indexOf(field2)
        fieldCount = abs((index2 - index1)+1)
        ftrCount = layer.featureCount()
        
        # Passing fields to table
        dataList = []
        totalRow = []
        for i, ftr in enumerate(layer.getFeatures()):
            dataList.append([])
            for j in range(index1, index2+1):
                dataList[i].append(ftr[j])
        data = np.array(dataList)
        totalRow = np.sum(data, axis = 1)
        
        layer.dataProvider().addAttributes([QgsField(entropyField, QVariant.Double, len=10, prec=8)])
        layer.updateFields()
        flds = layer.fields()
        pr = layer.dataProvider()
        entropyFieldIndex = flds.indexOf(entropyField)
        
        # Calculating Entropy
        for i, ftr in  enumerate(layer.getFeatures()):
            row = data[i]
            sum = 0
            for j in range(0, fieldCount):
                perc = data[i][j] / totalRow[i]
                percLn = perc*np.log(perc)
                sum += percLn
            entropyIndex = float(-sum / np.log(fieldCount))
            toAdd = {entropyFieldIndex:entropyIndex}
            pr.changeAttributeValues({ftr.id():toAdd})
        layer.updateFields()
        
        # Output
        source = layer
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {'OUTPUT':dest_id}
        
    def name(self):
        return 'entropyindex'

    def displayName(self):
        return 'Entropy Index'
        
    def shortHelpString(self):
        return (
                    "Calculates Entropy Diversity Index in dataseries. \n"
                    "Requires the first and last field of dataseries.")

    def createInstance(self):
        return EntropyIndex()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))