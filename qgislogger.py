from .abstractlogger import AbstractLogger
from qgis.core import Qgis
from qgis.core import QgsMessageLog


class QGISLogger(AbstractLogger):

    def info(self, message):
        QgsMessageLog.logMessage(message, level=Qgis.Info)

    def error(self, message):
        QgsMessageLog.logMessage(message, level=Qgis.Error)

    def critical(self, message):
        QgsMessageLog.logMessage(message, level=Qgis.Critical)
