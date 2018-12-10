# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HydrographMatcher
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
from configparser import ConfigParser

import os.path
import pandas as pd
import psycopg2
import datetime
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QToolBar
from qgis.core import Qgis
from qgis.core import QgsDataSourceUri
from qgis.core import QgsMessageLog
from scipy.integrate import quad
from scipy.interpolate import interp1d

# Initialize Qt resources from file resources.py
# Import the code for the dialog
from .hydrograph_matcher_dialog import HydrographMatcherDialog


class HydrographMatcher:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        self.locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'HydrographMatcher_{}.qm'.format(self.locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = HydrographMatcherDialog(self.iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Hydrograph Matcher')

        # TODO: We are going to let the user set this up in a future iteration
        # self.toolbar = self.iface.addToolBar(u'HydrographMatcher')
        # self.toolbar.setObjectName(u'HydrographMatcher')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('HydrographMatcher', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            parent.findChildren(QToolBar, 'mPluginToolBar')[0].addAction(action)
            # self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = self.plugin_dir + '/hydromatcher.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Search Best Match for Hydrograph ...'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Hydrograph Matcher'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        # del self.toolbar

    def run(self):
        """Run method that performs all the real work"""

        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            if len(self.dlg.filenames) > 0:
                shapenames = []
                for filename in self.dlg.filenames:
                    dataframe_messung = self.getDataFrameForFile(filename)

                    QgsMessageLog.logMessage("filename {}".format(filename), level=Qgis.Info)
                    floodplain_name = os.path.basename(filename).split('_')[0]
                    QgsMessageLog.logMessage("floodplain {}".format(floodplain_name), level=Qgis.Info)

                    ## Determine Interpolation function for infile
                    ## calculate max Q from infile and Volume from interpol-func
                    qvol, err = self.getVolume(dataframe_messung)
                    qmax = dataframe_messung['q'].max()

                    self.iface.messageBar().pushMessage(
                        "Floodplain: {0}; Input-Hydrograph: Q [m3]: {1:n}; Qmax [m3/s]: {2:n}".format(floodplain_name, int(round(qvol)), qmax),
                        level=Qgis.Info, duration=10)
                    QgsMessageLog.logMessage("Q [m3]: {0:n}; Qmax [m3/s]: {1:n}".format(int(round(qvol)), qmax), level=Qgis.Info, notifyUser=True)

                    ## match hydrograph from infile to SDH's via Qmax and Volume
                    ## grab matching shapefile from postgis-database and display it
                    shapenames.append(self.getmatchingshape(qmax, qvol, floodplain_name))

                self.displayshapes(shapenames)


    def displayshapes(self, shapenames):
        """
        Display the resulting merged shapefile
        :param shapenames: list of shapenames to display
        """
        uri, shapename = self.get_datasource_uri_for_shapefile(self.config(), shapenames)

        floodlayer = self.iface.addVectorLayer(uri.uri(False), ''.join(shapename.split('_')[1:]), "postgres")
        stylepath = self.getStyle()
        QgsMessageLog.logMessage('stylepath: ' + stylepath, level=Qgis.Info)
        floodlayer.loadNamedStyle(stylepath)
        floodlayer.triggerRepaint()
        self.iface.layerTreeView().refreshLayerSymbology(floodlayer.id())

    def getStyle(self):
        return os.path.join(self.plugin_dir, 'style') + '/floodlayer_defaultstyle.qml'


    def mergeshapes(self, config, shapenames):
        """
        Creates a Table with merges
        :param config: db config
        :param shapenames: the shapes to merge
        :return: the name of the resulting merged shapes table
        """
        connection = psycopg2.connect(**config)
        cursor = connection.cursor()


        query = 'CREATE TABLE PUBLIC.{table} {select}'
        mergetablename = 't_mergeshape_{}'.format(datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
        subselect = []

        for i in range(0, len(shapenames)):
            if i == 0:
                subselect.append(' AS ')
            else:
                subselect.append(' UNION ')
            subselect.append('SELECT gid, ext_id, round((max_depth::numeric/0.2), 0) * 0.2 as max_depth, t_max_dept, geom FROM {}'.format(shapenames[i]))
        subselect.append(';')

        queryparams = (mergetablename, ''.join(subselect))
        QgsMessageLog.logMessage('Creating merge table: query: {query}; params {params}'.format(query=query, params=queryparams), level=Qgis.Info)

        cursor.execute(query.format(table=mergetablename, select=''.join(subselect)))
        connection.commit()
        cursor.close()
        connection.close()

        ## Dann koennte der layer noch via PostGIS nach der max_depth dissolved werden, damit die anzahl geometrien drastisch reduziert wird.
        ## Aber dies dauert sehr lange!!
        ## CREATE TABLE t_mergeshape_union_test AS SELECT ST_Union(geom) AS geom, max_depth FROM public.t_mergeshape_181206_155143 GROUP BY max_depth;

        return mergetablename

    def getmatchingshape(self, qmax_messung, qvol_messung, floodplain):
        """ Get the matching shape: first match qmax, if more than 1 match: second match qvol """

        params = self.config()
        connection = psycopg2.connect(**params)
        cursor = connection.cursor()
        ## select id, qmax, qvol, shapefile_tablename from public."t_sdh_metadata" where abs(252 - qmax) = (select min(abs(252 - qmax)) from public."t_sdh_metadata" where position('ststephano' in shapefile_tablename) > 0);
        query = 'select id, qmax, qvol, shapefile_tablename from public.t_sdh_metadata where abs(%s - qmax) = (select min(abs(%s - qmax)) from public.t_sdh_metadata where position(%s in shapefile_tablename) > 0);'
        data = (qmax_messung, qmax_messung, floodplain)
        cursor.execute(query, data)
        results = cursor.fetchall()  # all rows; can fail if no rows are found!

        for result in results:
            QgsMessageLog.logMessage('resultrow: {}'.format(result), level=Qgis.Info)

        cursor.close()
        connection.close()

        if len(results) == 1:
            return results[0][3]  # third col is the shapefile_tablename
        else:
            # several matches for qmax, therefore match for volume
            diffold = 0
            for result in results:
                diffnew = abs(qvol_messung - result[2])
                if diffnew <= diffold:
                    return result[3]
                else:
                    diffold = diffnew

    def get_datasource_uri_for_shapefile(self, config, shapenames):

        if len(shapenames) == 1:
            tablename = shapenames[0]
        elif len(shapenames) > 1:
            tablename = self.mergeshapes(config, shapenames)
        else:
            QgsMessageLog.logMessage('No shapenames found. Datasource uri cannot be defined.', level=Qgis.Error)
            raise Exception('No shapenames found. Datasource uri cannot be defined.')


        uri = QgsDataSourceUri()
        uri.setConnection(config.get('host'), config.get('port'), config.get('database'), config.get('user'), config.get('password'))
        uri.setDataSource('public', tablename, 'geom', "", 'id')
        return uri, tablename


    def config(self, filename='database.ini', section='postgresql'):
        """ Read the datasource-config into a dictionary """

        parser = ConfigParser()
        parser.read(os.path.join(self.plugin_dir, 'datasource') + '/' + filename)

        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return db

    def getDataFrameForFile(self, filename):
        """Read the content of the file into a Dataframe, using col 1 as 'time', col 2 as 'q'"""

        df_messung_gesamt = pd.read_csv(filename, ';', engine='python', usecols=[1, 2], names=['time', 'q'], header=0)

        # extract section with Qmax and reset index
        df_messung_gesamt.reset_index(inplace=True, drop=True)

        # replace values on x-Axe by hourly sec-values; this is needed to make the timeline comparable with the sdh's
        for row in df_messung_gesamt.itertuples():
            df_messung_gesamt.at[row.Index, 'time'] = row.Index * 3600

        # Datentypen korrekt setzen; ist nötig wegen der obigen Konvertierung der x-Werte
        df_messung_ausschnitt = df_messung_gesamt.astype(dtype={'time': 'int64', 'q': 'float64'})

        return df_messung_ausschnitt

    def getVolume(self, dataframe):
        """Determine the cubic interpolation function for the data in dataframe. Then calculate the integral for the data with this function."""

        function_cubic = interp1d(dataframe['time'], dataframe['q'], kind='cubic')
        integral, err = quad(function_cubic, 0, dataframe['time'].max())
        return integral, err