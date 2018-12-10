# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HydrographMatcherDialog
                                 A QGIS plugin
 This plugin searches the best match for a given hydrograph
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-11-16
        git sha              : $Format:%H$
        copyright            : (C) 2018 by MobiliarLab Giub Unibe
        email                : johannes.lang@giub.unibe.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog, QDialogButtonBox

from qgis.core import Qgis
from qgis.core import QgsMessageLog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'hydrograph_matcher_dialog_base.ui'))


class HydrographMatcherDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(HydrographMatcherDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.pushButton.clicked.connect(self.selectDirectory)
        self.filenames = []
        self.filename = None
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def selectDirectory(self):
        dirpath = QFileDialog.getExistingDirectory(parent=self, caption='Verzeichnis mit Ganglinien-Dateien auswählen', directory='c:/ieu/work')
        if dirpath:
            self.scandir(dirpath)

    def scandir(self, dirpath):
        """
        Traverses recursively through dirpath and searches for files with extension *.asc
        Adds all files to self.filenames from which they can be consumed by other modules
        :param dirpath:
        """
        self.lineEdit.setText(dirpath)
        asc_files = [f for f in os.listdir(dirpath) if f.endswith('.asc')]
        asc_files_with_path = []
        for file in asc_files:
            asc_files_with_path.append(os.path.join(dirpath, file))

        QgsMessageLog.logMessage('found hydrograph-files: {}'.format(asc_files_with_path), level=Qgis.Info)

        filecount = len(asc_files)
        self.fileCountValueLabel.setText('{}'.format(filecount))

        if filecount > 0:
            self.filenames = asc_files_with_path
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.filenames = None
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)