# spatialanalysistoolbox

<p>
Spatial Analysis Toolbox is a plugin for QGIS. It contains some processing algorithms that are used for spatial analysis, such as (Local) Moran's I, GWR, various spatial indices.
</p>


<h3>REQUIREMENTS</h3>
<p>
Spatial Analysis Toolbox depends on Pandas and Geopandas. Also, PySAL is required but the packages required are provided with the plugin.
In order to use the plugin you will need to install Pandas and Geopandas.
</p>
Normally, you can install these dependencies by:

<br><h4>Windows</h4>
1. Open OSGeo Shell
2. Get fiona whl file from the link below (based on your system and python version)
https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona
<br>Then pip install *Path To whl file*
3. pip install pandas pyproj shapely geopandas

<br><h4>Linux/Mac</h4>
1. pip install pandas pyproj fiona geopandas
<br> Keep in mind that you have to install these packages in QGIS python environment

You can also check the official instructions:<br>
https://pandas.pydata.org/docs/getting_started/install.html <br>
https://geopandas.org/en/stable/getting_started/install.html <br>
