rem @echo off
SET OSGEO4W_ROOT=c:\mobilab\apps\OSGeo4W64
call "%OSGEO4W_ROOT%"\bin\o4w_env.bat
rem call "%OSGEO4W_ROOT%"\apps\grass\grass-7.6.0\etc\env.bat
rem @echo off
path %PATH%;%OSGEO4W_ROOT%\apps\qgis\bin
rem path %PATH%;%OSGEO4W_ROOT%\apps\grass\grass-7.6.0\lib
path %PATH%;%OSGEO4W_ROOT%\apps\Qt5\bin
path %PATH%;%OSGEO4W_ROOT%\apps\Python37\Scripts

set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\qgis\python
set PYTHONPATH=%PYTHONPATH%;%OSGEO4W_ROOT%\apps\Python37\Lib\site-packages
set PYTHONHOME=%OSGEO4W_ROOT%\apps\Python37

set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis

rem start "PyCharm Aware QGIS" /B %PYCHARM% %*
cmd.exe /K cd /d "C:\mobilab\pythonprojects\hydromatcher_plugin