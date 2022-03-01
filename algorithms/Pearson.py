"""
***************************************************************************
    Pearson.py
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
                      QgsProcessingParameterNumber,
                      QgsMessageLog,
                      Qgis)
import processing
import os, tempfile
import numpy as np
import geopandas as gpd
import pandas as pd


class Pearson(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    FIELDS = 'FIELDS'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input Layer', defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.FIELDS, 'Independent Variable', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT, allowMultiple=True))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Parameters to layers/numbers
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        fields = self.parameterAsFields(parameters, self.FIELDS, context)
        layer = layerSource
        
        fldCount = len(fields)
        
        # No correlation can be calculated for less that 2 fields
        if fldCount < 2:
            return {'Error': 'Cannot calculate correlation for less that 2 fields'}
        
        # Vector layer to GeoDataFrame
        tempDir = tempfile.gettempdir()
        temp = os.path.join(tempDir, 'temp.shp')  # Path
        processing.run("sat:clonelayer", {'INPUT':layer ,'OUTPUT':temp})
        data = gpd.read_file(temp)

        # Create a list with all columns arrays
        fieldList = []
        for fld in fields:
            fieldList.append(data[fld].to_numpy())

        corr = np.corrcoef(fieldList)
        corr = np.round(corr, decimals = 3)
        
        QgsMessageLog.logMessage('===== Pearson Correlation =====', "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Layer: '+ str(layerSource.sourceName()), "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Fields: '+ ' '.join(fields), "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Correlation: '+ '\n'+np.array2string(corr), "Spatial Analysis Toolbox", level=Qgis.Info)

        return {'1_Fields': ' '.join(fields),
                '2_Correlation': '\n'+np.array2string(corr),
                '3_Results': 'Check Log Messages for results'}

    def name(self):
        return 'pearson'

    def displayName(self):
        return 'Pearson Correlation'

    def shortHelpString(self):
        return ("Pearson correlation.")
    
    def createInstance(self):
        return Pearson()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))