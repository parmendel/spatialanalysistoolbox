"""
***************************************************************************
    MoransI.py
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
                       QgsProcessingParameterEnum,
                       QgsMessageLog,
                       Qgis)
import libpysal
from esda.moran import Moran
import os, tempfile
import processing

class MoransI(QgsProcessingAlgorithm):
    LAYER = 'LAYER'
    VARIABLE = 'VARIABLE'
    METHOD = 'METHOD'
    PARAM = 'PARAM'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.LAYER, 'Layer', types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.VARIABLE, 'Variable X', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.LAYER))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD, 'Method', options = ['Queen contiguity', 'Rook contiguity', 'K Nearest Neighbors', 'Distance Band'], defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.PARAM, type = QgsProcessingParameterNumber.Integer,description='K Neighbors / Distance threshold (only for KNN / Distance Band methods)', defaultValue = 1, minValue = 1))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Parameters to layers/numbers
        layerSource = self.parameterAsVectorLayer(parameters, self.LAYER, context)
        variable = self.parameterAsString(parameters, self.VARIABLE, context)
        method = self.parameterAsInt(parameters, self.METHOD, context)       # Queen = 0, Rook = 1, KNN = 2, Distance = 3
        knn_dist = self.parameterAsDouble(parameters, self.PARAM, context)
        
        layer = layerSource
        
        # List with variables
        y = []
        for ftr in layer.getFeatures():
            y.append(ftr[variable])

        # Create a temp layer
        temp = os.path.join(tempfile.gettempdir(), 'temp.shp')  # Path
        if layer.geometryType() == 0 and (method == 0 or method == 1):
            return {'Error':'This method is not available with point layers'}
        elif layer.geometryType() == 2 and (method == 2 or method == 3):
            processing.run("native:centroids", {'INPUT':layer,
                                                'ALL_PARTS':False,
                                                'OUTPUT':temp})['OUTPUT']
        else:
            processing.run("sat:clonelayer", {'INPUT':layer,
                                                 'OUTPUT':temp})['OUTPUT']

        # Create spatial weights
        if method == 0:
            w = libpysal.weights.contiguity.Queen.from_shapefile(temp)
        elif method == 1:
            w = libpysal.weights.contiguity.Rook.from_shapefile(temp)
        elif method == 2:
            w = libpysal.weights.distance.KNN.from_shapefile(temp, k=knn_dist)
        elif method ==3:
            w = libpysal.weights.distance.DistanceBand.from_shapefile(temp, threshold=knn_dist)
        
        # Calculate Moran's I
        MoransI = Moran(y, w)
        MI = MoransI.I
        EI = MoransI.EI
        Zscore = MoransI.z_norm
        Pvalue = MoransI.p_norm

        # Results
        results = {}
        results['1_Layer: '] = 'Layer: '+str(layerSource.sourceName())
        results['2_Variable: '] = str(variable)
        if method == 0: results['3_Method'] = 'Queen contiguity'
        elif method ==1: results['3_Method'] = 'Rook contiguity'
        elif method == 2: results['3_Method'] = 'K Nearest Neighbors, KNN = '+str(knn_dist)
        elif method == 3: results['3_Method'] = 'Distance Band, Fixed Distance = '+str(knn_dist)
        results['4_Morans-I'] = round(MI,5)
        results['5_Expected Value'] = round(EI,5)
        results['6_Z-score'] = round(Zscore,5)
        results['7_P-value'] = Pvalue
        results['8_Details: '] = 'Check message log for more info'
    
        # Report in Log Messages
        QgsMessageLog.logMessage('===== Morans I =====', "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Layer: '+str(layerSource.sourceName()), "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Variable: '+str(variable), "Spatial Analysis Toolbox", level=Qgis.Info)
        if method == 0: QgsMessageLog.logMessage('Method: Queen contiguity', "Spatial Analysis Toolbox", level=Qgis.Info)
        elif method == 1: QgsMessageLog.logMessage('Method: Rook contiguity', "Spatial Analysis Toolbox", level=Qgis.Info)
        elif method == 2: QgsMessageLog.logMessage('Method: K Nearest Neighbors, KNN = '+str(knn_dist), "Spatial Analysis Toolbox", level=Qgis.Info)
        elif method == 3: QgsMessageLog.logMessage('Distance Band, Fixed Distance = '+str(knn_dist), "Spatial Analysis Toolbox", level=Qgis.Info)
        QgsMessageLog.logMessage('Morans I = '+str(MI), "Spatial Analysis Toolbox" , level=Qgis.Info)
        QgsMessageLog.logMessage('Z-score = '+str(Zscore), "Spatial Analysis Toolbox" , level=Qgis.Info)
        
        return results

    def name(self):
        return 'moransi'

    def displayName(self):
        return 'Moran\'s I'
        
    def shortHelpString(self):
        return ("Moran's I is a spatial autocorrelation index. \n"
        		"There are three available methods:\n"
        		"- Queen contiguity in which areas with common edges or corners are considered neighbors (works only for polygon layers).\n"
        		"- K Nearest Neighbors (works with point/polygon* layers).\n"
       			"- Distance Band, in which areas or points within a fixed distance are considered neighbors (works with point/polygon* layers).\n"
      			"*In KNN and Distance Band, Morans I for polygon layers is calculated based on their centroids.")
    
    def createInstance(self):
        return MoransI()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))