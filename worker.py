from PyQt5 import QtCore
import traceback
from PyQt5.QtCore import *

from .abstractlogger import AbstractLogger
from .mergeprocessor import MergeProcessor


class Worker(QObject):
    """Worker for asyncronously merging and dissolving"""

    def __init__(self, dbconfig, properties, shapenames, logger: AbstractLogger):
        QObject.__init__(self)
        self.killed = False
        self.dbconfig = dbconfig
        self.properties = properties
        self.shapenames = shapenames
        self.logger = logger

    def run(self):
        ret = None
        try:
            mergeprocessor = MergeProcessor()
            mergetablename = mergeprocessor.exec_merge_dissolve(self.dbconfig, self.properties, self.shapenames, self.logger)

            if self.killed is False:
                ret = mergetablename

        except Exception as e:
            # forward the exception upstream
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(ret)


    def kill(self):
        self.killed = True

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(Exception, str)
