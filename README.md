# spatialanalysistoolbox

<p>
Spatial Analysis Toolbox is a plugin for QGIS. It contains some processing algorithms that are used for spatial analysis, such as (Local) Moran's I, GWR, various spatial indices.
</p>


<h3>REQUIREMENTS</h3>
<p>
Spatial Analysis Toolbox depends on Pandas and Geopandas, PSySAL.
In order to use the plugin you will need to install Pandas and Geopandas.
</p>
Generally, you can install these dependencies by:

<h4>Windows</h4>
1. Open OSGeo Shell (py3_env to activate python environment, if needed)<br>
2. Get fiona whl file (based on your system and python version) https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona <br>Then pip install *Path To whl file*<br>
3. pip install pandas pyproj shapely geopandas libpysal esda mgwr

<h4>Linux/Mac</h4>
1. pip install pandas pyproj fiona geopandas libpysal esda mgwr
<br> Keep in mind that you have to install these packages in QGIS python environment

You can also check the official instructions:<br>
https://pandas.pydata.org/docs/getting_started/install.html <br>
https://geopandas.org/en/stable/getting_started/install.html <br>
