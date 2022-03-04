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
                      QgsProcessingParameterEnum,
                      Qgis)
import processing
import os, tempfile
import numpy as np
import geopandas as gpd
import pandas as pd

class CorrelationMatrix(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    FIELDS = 'FIELDS'
    METHOD = 'METHOD'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input Layer', defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.FIELDS, 'Independent Variable', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT, allowMultiple=True))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD, 'Method', options = ['Pearson', 'Kendall', 'Spearman'], defaultValue=0))


    def processAlgorithm(self, parameters, context, model_feedback):
        # Parameters to layers/numbers
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        fields = self.parameterAsFields(parameters, self.FIELDS, context)
        method = self.parameterAsInt(parameters, self.METHOD, context)
        layer = layerSource
        
        results = {}

        # No correlation can be calculated for less that 2 fields
        if len(fields) < 2:
            return {'Error': 'Cannot calculate correlation for less that 2 fields'}
        
        # Vector layer to GeoDataFrame
        tempDir = tempfile.gettempdir()
        temp = os.path.join(tempDir, 'temp.shp')  # Path
        processing.run("sat:clonelayer", {'INPUT':layer ,'OUTPUT':temp})
        data = gpd.read_file(temp)
        
        # Keep fields needed
        attr = data[fields]
        
        if method == 0: m = 'pearson'
        elif method == 1: m = 'kendall'
        elif method == 2: m = 'spearman'
 
        # Correlation Matrix
        corr = attr.corr(method=m)
        
        # Results to return
        results['1_Fields'] = ' '.join(fields)
        results['2_Correlation'] = corr.to_string()
        results['4_Results'] = 'Check Log Messages for results' 
        
        # Plot (seaborn package needed)
        try:
            import seaborn as sn
            import matplotlib.pyplot as plt
            import random, string
            ax = plt.axes()
            sn.set(rc={'figure.figsize':(11.7,8.27)})
            sn.heatmap(corr,
                            annot=True, 
                            cmap = sn.diverging_palette(230, 20, as_cmap=True),
                            vmin = -1.0, 
                            vmax = 1.0,
                            ax = ax)
            ax.set_title('Correlation Matrix')
            randExt = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
            tempPlot = os.path.join(tempfile.gettempdir(), 'CorrelationMatrix_{}.png'.format(randExt))  # Path
            plt.savefig(tempPlot)
            plt.clf()
            results['3_Plot'] = tempPlot
        except:
            results['3_Plot'] = 'Install seaborn python package for plots (Normally: pip install seaborn)'
       
        QgsMessageLog.logMessage('===== Pearson Correlation =====', "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Layer: '+ str(layerSource.sourceName()), "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Fields: '+ results['1_Fields'], "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Correlation: ' + results['2_Correlation'], "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Plot: ' + results['3_Plot'], "Spatial Analysis Toolbox", level=Qgis.Info)
        
        return results

    def name(self):
        return 'correlation'

    def displayName(self):
        return 'Correlation Matrix'
    
    def shortHelpString(self):
        return ("Correlation matrix supports Pearson, Kendal and Spearman correlation. \n Also, the algorithm saves a plotted correlation heatmap (seaborn python package required)")
    
    def createInstance(self):
        return CorrelationMatrix()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))