"""
***************************************************************************
    GWR.py
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
                          QgsProcessingParameterEnum,
                          QgsProcessingParameterFeatureSink,
                          QgsFeatureSink,
                          QgsVectorLayer,
                          Qgis)
import geopandas as gpd
import pandas as pd
import numpy as np
#from mgwr.gwr import GWR
#from mgwr.sel_bw import Sel_BW
from .mgwr.gwr import GWR
from .mgwr.sel_bw import Sel_BW
import os, tempfile
import processing

class GWR_(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    DEP = 'DEP'
    INDEP = 'INDEP'
    KERNEL = 'KERNEL'
    FIXED = 'FIXED'
    BW = 'BW'
    CONSTANT = 'CONSTANT'
    OUTPUT = 'OUTPUT'
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT, 'Input layer', types=[QgsProcessing.TypeVectorPolygon, QgsProcessing.TypeVectorPoint],  defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.INDEP, 'Independent Variable', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT, allowMultiple=True))
        self.addParameter(QgsProcessingParameterField(self.DEP, 'Dependent Variable', type=QgsProcessingParameterField.Numeric, parentLayerParameterName=self.INPUT, allowMultiple=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterEnum(self.KERNEL, 'Kernel Method', options = ['Gaussian', 'Bisquare', 'Exponential'], defaultValue=0))
        self.addParameter(QgsProcessingParameterEnum(self.FIXED, 'Kernel Type', options = ['Adaptive - NN', 'Distance based'], defaultValue=0))
        self.addParameter(QgsProcessingParameterNumber(self.BW, type = QgsProcessingParameterNumber.Integer,description='Bandwidth (0 for auto selection)', defaultValue = 0, minValue = 0))
        self.addParameter(QgsProcessingParameterEnum(self.CONSTANT, 'Calculate constant', options = ['True', 'False'], defaultValue=0))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, 'GWR', createByDefault=True, supportsAppend=False, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        layerSource = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        yField = self.parameterAsFields(parameters, self.DEP, context)[0]
        xFields = self.parameterAsFields(parameters, self.INDEP, context)
        kernel = self.parameterAsInt(parameters, self.KERNEL, context)
        fixed = self.parameterAsInt(parameters, self.FIXED, context)
        bw =  self.parameterAsInt(parameters, self.BW, context)
        constant = self.parameterAsInt(parameters, self.CONSTANT, context)
        
        if yField in xFields:
            return {'Error':'A variable cannot be both Dependent and Independent'}
        
        tempDir = tempfile.gettempdir()
        temp = os.path.join(tempDir, 'temp.shp')  # Path

        layer = processing.run("sat:clonelayer", {'INPUT':layerSource ,'OUTPUT':temp})['OUTPUT']
        data = gpd.read_file(layer)
        
        # List with coords
        coords = []
        for i in range(data.shape[0]):
            coords.append([data.at[i,'geometry'].x,
                           data.at[i,'geometry'].y])

        # Arrays with x variables
        arrays = []
        cols = []      # Column names
        t_stats = []
        for i, fld in enumerate(xFields):
            df = data[fld]
            arr = df.to_numpy().reshape((-1,1))
            arrays.append(arr)
            cols.append('X{}_{}'.format(str(i+1),str(fld)))
            t_stats.append('X{}_t-test'.format(str(i+1)))
        X = np.hstack(arrays)

        # Arrays with y variable
        y = data[yField].to_numpy().reshape((-1,1))

        # GWR
        # Parameters
        # Kernel Method
        if kernel == 0: kernel = 'gaussian'
        elif kernel == 1: kernel = 'bisquare'
        elif kernel == 2: kernel = 'exponential'

        # Kernel Type
        if fixed == 0: fixed = False
        elif fixed == 1: fixed = True

        # Kernel Bandwidth
        if bw == 0:     # This is auto kernel bandwidth
            bw = Sel_BW(coords, y, X, kernel=kernel, fixed=fixed)
            bw = bw.search('golden_section', 'AICc')
        
        # Calculate constant
        if constant == 0: 
            constant = True
            cols.insert(0, 'X0_Const')
            t_stats.insert(0,'X0_t-test')
        elif constant == 1: 
            constant = False

        # Model
        model = GWR(coords, y, X, bw = bw, fixed=fixed, kernel=kernel, constant=constant)
        res = model.fit()
        residuals = res.resid_response
        coeff = res.params
        predicted = res.predy
        localr2 = res.localR2
        tvalues = res.tvalues

        
        R2 = round(res.R2,4)
        summary = res.summary()
        
        # Join to gdf
        gwr = data.join(pd.DataFrame(coeff, columns = cols))  # This is a geodataframe
        gwr = gwr.join(pd.DataFrame(predicted, columns = ['predY']))
        gwr = gwr.join(pd.DataFrame(localr2, columns = ['localR2']))
        gwr = gwr.join(pd.DataFrame(residuals, columns = ['residuals']))
        gwr = gwr.join(pd.DataFrame(tvalues, columns = t_stats))

        outPath = os.path.join(tempfile.gettempdir(), 'temp_gwr.shp')
        gwr.to_file(outPath)
        
        # Geodataframe -> GeoJSON -> QgsVectorLayer
        vectorLayer = QgsVectorLayer(outPath,"mygeojson","ogr")
        vectorLayer.setCrs(layerSource.crs())

        # Output & Load to QGIS
        source = vectorLayer
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT , context , source.fields() , source.wkbType() ,source.sourceCrs())
        features = source.getFeatures()
        for current, feature in enumerate(features):
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
        return {'OUTPUT':dest_id, 'R2':R2}


    def name(self):
        return 'gwr_'

    def displayName(self):
        return 'Geographically Weighted Regression'
        
    def shortHelpString(self):
        return ("Geographically Weighted Regression (GWR)")

    def createInstance(self):
        return GWR_()
    
    def icon(self):
        from qgis.PyQt.QtGui import QIcon
        import os
        pluginPath = os.path.dirname(__file__)
        return QIcon(os.path.join(pluginPath,'styles','icon.png'))
