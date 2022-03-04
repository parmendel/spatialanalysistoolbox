"""
***************************************************************************
    LocalMoransI.py
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
                          QgsProcessingParameterBoolean,
                          QgsProcessingParameterNumber,
                          QgsFeatureSink,
                          QgsProcessingParameterFeatureSink,
                          QgsProcessingParameterEnum,
                          QgsVectorLayer,
                          Qgis,
                          QgsProcessingUtils)
import processing
import os, tempfile, random, string
import geopandas as gpd
import pandas as pd
import libpysal
from esda.moran import Moran_Local

class LocalMoransI(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    VARIABLE = 'VARIABLE'
    METHOD = 'METHOD'
    KNN_DIST = 'KNN_DIST'
    OUTPUT = 'OUTPUT'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.VARIABLE, 'Variable X', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT))
        self.addParameter(QgsProcessingParameterEnum(self.METHOD, 'Method', options = ['Queen contiguity', 'Rook contiguity', 'K Nearest Neighbors', 'Distance Band'], defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.KNN_DIST, type = QgsProcessingParameterNumber.Integer,description='K Neighbors / Distance threshold (only for KNN / Distance Band methods)', defaultValue = 1, minValue = 1))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'Local Morans I', createByDefault=True, supportsAppend=False, defaultValue=None))


    def processAlgorithm(self, parameters, context, model_feedback):
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        field = self.parameterAsString(parameters, self.VARIABLE, context)
        method = self.parameterAsInt(parameters, self.METHOD, context)       # Queen = 0, Rook = 1, KNN = 2, Distance = 3
        knn_dist = self.parameterAsDouble(parameters, self.KNN_DIST, context)
        dest_id = None
        #print(os.path.abspath(__file__))
        
        layer = layerSource
        if layer.geometryType() == 0 and (method == 0 or method == 1): 
            return  {'Error':'This method is not available with point layers'}

        # Get temp path
        randExt = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        temp = os.path.join(tempfile.gettempdir(), 'temp_{}.shp'.format(randExt))  # Path
        
        # Create a temp layer
        temp = os.path.join(tempfile.gettempdir(), 'temp.shp')  # Path

        # Read shp as geodataframe
        processing.run("sat:clonelayer", {'INPUT':layer, 'OUTPUT':temp})['OUTPUT']
        data = gpd.read_file(temp)
        
        # If polygon & KNN or distance band then get Centroid
        if layer.geometryType() == 2 and (method == 2 or method == 3): 
            polygonColumn = data['geometry']
            data['geometry'] = data.centroid

        # Create spatial weights
        if method == 0:
            w = libpysal.weights.contiguity.Queen.from_shapefile(temp)
        elif method == 1:
            w = libpysal.weights.contiguity.Rook.from_shapefile(temp)
        elif method == 2:
            w = libpysal.weights.distance.KNN.from_shapefile(temp, k=knn_dist)
        elif method ==3:
            w = libpysal.weights.distance.DistanceBand.from_shapefile(temp, threshold=knn_dist)
            
        # y variable
        y = data[field]

        # Initialize Local Moran's I
        localMoran = Moran_Local(y, w)

        # Local Morans results
        LMI = localMoran.Is              # Index
        LMQ = localMoran.q              # Category 1 HH, 2 LH, 3 LL, 4 HL
        LMP = localMoran.p_z_sim    # P value

        # If Local morans was calculated with centroids, change dataframe back to polygons
        if layer.geometryType() == 2 and (method == 2 or method == 3): 
            data['geometry'] = polygonColumn

        # Join results
        data = data.join(pd.DataFrame(LMI, columns=['LMI']))
        data = data.join(pd.DataFrame(LMP, columns=['LMP']))
        data = data.join(pd.DataFrame(LMQ, columns=['LMQ']))

        # Output
        outPath = os.path.join(tempfile.gettempdir(), 'temp_lmi_{}.shp'.format(randExt))
        data.to_file(outPath)
        vectorLayer = QgsVectorLayer(outPath,"Local Morans I","ogr")
        vectorLayer.setCrs(layer.crs())

        # Output & Load to QGIS
        source = vectorLayer
        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {self.OUTPUT: self.dest_id}

    def postProcessAlgorithm(self, context, feedback):
        os.chdir(os.path.dirname(__file__))
        currentPath = os.getcwd()       
        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)

        if processed_layer.geometryType() == 0:
            processed_layer.loadNamedStyle(currentPath + '/styles/LocalMoransPoints.qml')
        elif  processed_layer.geometryType() == 2:
            processed_layer.loadNamedStyle(currentPath + '/styles/LocalMoransPolygons.qml')
        
        return {self.OUTPUT: self.dest_id}

    def name(self):
        return 'LocalMoransI'

    def displayName(self):
        return 'Local Moran\'s I'
        
    def shortHelpString(self):
        return ("Local Moran's I. \n"
        		"There are three available methods:\n"
        		"- Queen contiguity in which areas with common edges or corners are considered neighbors (works only for polygon layers).\n"
        		"- K Nearest Neighbors (works with point/polygon* layers).\n"
       			"- Distance Band, in which areas or points within a fixed distance are considered neighbors (works with point/polygon* layers).\n"
      			"*In KNN and Distance Band, Morans I for polygon layers is calculated based on their centroids.")

    def createInstance(self):
        return LocalMoransI()

    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))