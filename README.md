# Spatial Analysis Toolbox

Spatial Analysis Toolbox is a plugin for QGIS. It contains some processing algorithms that are used for spatial analysis, such as (Local) Moran's I, GWR, various spatial indices.
___

## Requirements

Spatial Analysis Toolbox depends on Pandas and Geopandas, PSySAL.
In order to use the plugin you will need to install Pandas and Geopandas.


Generally, you can install these dependencies by:

### Windows
1. Open OSGeo Shell (py3_env to activate python environment, if needed)

2. [Get fiona whl file (based on your system and python version)](https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona). 
    
    Then `pip install user/Path_To_whl_file/`

3. Finally, run `pip install pandas pyproj shapely geopandas libpysal esda mgwr`

### Linux and Mac

1. pip install pandas pyproj fiona geopandas libpysal esda mgwr

-  Keep in mind that you have to install these packages in QGIS python environment

You can also check the official instructions:

[Pandas Installing Documentation](https://pandas.pydata.org/docs/getting_started/install.html)

[Geopandas Installing Documentation](https://geopandas.org/en/stable/getting_started/install.html)
