## hydromatcher_plugin

#### Runtime Requirements
- Python Version: 3.7
- QGIS: >= 3.4
- PostgreSQL local installation incl PostGIS (needed for merging the shapes)

This plugin needs the following python libs at runtime, which are usually not contained in a standard python runtime. These must therefore be installed in the pyhton runtime using `pip install ...`
- pandas
- sqlalchemy
- psycopg2
- scipy
- pb_tool (only if you want to develop and deploy the plugin)
- configparser
- watchdog (only if you want to use the directorywatcher)

For compiling the resources and deploying the plugin, the pb_tool library is used (https://g-sherman.github.io/plugin_build_tool/). Therefore, this must also be installed using `pip install pb_tool`.

#### Development
- Ideally you configure your IDE to use the python environment contained in your QGIS Installation. This way your interpreter can see all QGIS- and Qt-Libraries.
- Make the following additions to your Environment:
    - PYTHONHOME --> pointing to the python runtime contained in your QGIS; for example something like `<Path to your QGIS installation>/apps/Python37`
    - PYTHONPATH --> pointing to the python modules in QGIS; something like `<Path to your QGIS installation>/apps/qgis/python`
    - PATH
        - `<Path to your QGIS installation>/apps/Python37`
        - `<Path to your QGIS installation>/apps/Python37/Scripts`
        - `<Path to your QGIS installation>/apps/qt5/bin`
        - `<Path to your QGIS installation>/apps/qgis/bin`
        - `<Path to your PostgreSQL installation>/bin`
- Modify your user interface by opening <b>hydrograph_matcher_dialog_base.ui</b> in Qt Designer, which you find under something like `<Path to your QGIS installation>/apps/Qt5/bin/designer.exe`
- If you add or remove files (python, resources, ...) to or from the module, then check if pb_tool.cfg needs to be modified
- In your IDE (for example PyCharm), make sure to set your project interpreter to the PythonRuntime inside your QGIS Installation, something like `<Path to your QGIS installation>/bin/python3.exe`


#### Deployment
- Deployment means installing the plugin in QGIS
- Execute pyqgis_env.cmd on the commandline to set all the necessary pathes and environment variables 
- Deploy your plugin into QGIS by typing `pb_tool deploy` on the commandline in the module directory. You can find the documentation to pb_tool in http://g-sherman.github.io/plugin_build_tool/


#### Input
The Forecast-Hydrographs must have the following name-pattern:
- floodplain_*.asc
- Example: verlue_tralala.asc


#### Merging and dissolving the shapes
- Merging is done on database level by a union select of the relevant floodplain-shapes.
- Dissolving is done using the postgis-function ST_Union as follows:
`SELECT ST_Union(geom) AS geom, max_depth FROM <tablename> GROUP BY max_depth;`


#### CommandLine Usage
To start the processing on the commandline, type `python hydromatch_starter.py`. The script uses the same properties-files as the plugin.
When finished, it returns the Table-Name of the PostGIS-Table which contains the Merged and dissolved Shape-Layer.
Therefore it can be included in any processing-pipe.


#### Automatic Processing via watched directory
This processing can also be triggered by watching a directory for new files (predicted hydrographs). This can be implemented for example using the watchdog library (https://pypi.org/project/watchdog/).
In this module you find an example implementation in the script `directorywatcher.py`. If started, the directory defined by the property `dirpath` in `properties.ini`
is watched for files having the extension defined by the property `watch_file_extension`. With the appearance of new files, any processing could be triggered. For example call the hydromatch_starter with the
new files. Or even call the hydrological model with new precipitation and temperature grid input data ...


#### The HydroMatcher Project
In MAARE+ there are about 700 floodplains. Each modeled floodplain has 1 input, which is either a discharge hydrograph or a
sealevel hydrograph. For each of these hydrographs several SDHs are defined differing in qmax and discharge volume (only for rivers, not for lakes).
For each SDH the resulting floodplain is calculated and stored as a shape.
The requirement now is the following:
For a given set of forecast hydrographs, find the best matching SDH's and merge the corresponding shapes
into one single shape for Switzerland.
The matching is done first by the nearest qmax. If there is more than one match, then the sdh with the nearest volume is choosen.
