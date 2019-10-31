from PyQt5 import QtCore
import traceback
import psycopg2
import datetime
from PyQt5.QtCore import *
from qgis.core import Qgis
from qgis.core import QgsMessageLog
from qgis.core import QgsVectorFileWriter


class GeoJsonExportWorker(QObject):
    """Worker for asyncronously merging and dissolving"""

    def __init__(self, inputlayer, geojson_filename):
        QObject.__init__(self)
        self.killed = False
        self.inputlayer = inputlayer
        self.geojson_filename = geojson_filename

    def run(self):
        ret = None
        try:
            QgsMessageLog.logMessage('exporting shape to geojson {filename}'.format(filename=self.geojson_filename), level=Qgis.Info)
            QgsVectorFileWriter.writeAsVectorFormat(layer=self.inputlayer, fileName=self.geojson_filename, fileEncoding='utf-8', destCRS=self.inputlayer.crs(), driverName='GeoJSON',
                                                    layerOptions=['COORDINATE_PRECISION=3'])

            ret = 'Success'

        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str)
