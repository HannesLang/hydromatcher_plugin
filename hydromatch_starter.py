import os
import sys
from consolelogger import ConsoleLogger
from confighelper import ConfigHelper
from mergeprocessor import MergeProcessor
from processinghelper import ProcessingHelper
from spinner import Spinner


def main():
    logger = ConsoleLogger()
    propertiespath = os.path.join( os.path.dirname(os.path.realpath(__file__)), 'properties')
    generalproperties = ConfigHelper.config(None, path=propertiespath, filename='properties.ini', section='general')
    dbproperties = ConfigHelper.config(None, path=propertiespath, filename='database.ini', section=generalproperties.get('db'))

    dirpath = generalproperties.get('dirpath')
    watch_file_extension = generalproperties.get('watch_file_extension')
    asc_files = [f for f in os.listdir(dirpath) if f.endswith(watch_file_extension)]
    asc_files_with_path = []
    for file in asc_files:
        asc_files_with_path.append(os.path.join(dirpath, file))

    logger.info('found hydrograph-files: {}'.format(asc_files_with_path))

    filecount = len(asc_files)
    logger.info('Number of forecast files found: {}'.format(filecount))

    shapenames = []

    if filecount > 0:
        filenames = asc_files_with_path

        for filename in filenames:
            filename = ProcessingHelper.replacebackslashes(filename)
            logger.info("filename {}".format(filename))

            dataframe_forecast = ProcessingHelper.getDataFrameForFile(None, filename)
            floodplain_name = ProcessingHelper.getfloodplainNameFromFilename(filename)

            # Determine Interpolation function for infile and calculate max Q from infile and Volume from interpol-func
            qvol, err = ProcessingHelper.getVolume(dataframe_forecast)
            qmax = dataframe_forecast['q'].max()

            logger.info("Floodplain: {0}; Input-Hydrograph: Q [m3]: {1:n}; Qmax [m3/s]: {2:n}".format(floodplain_name, int(round(qvol)), qmax))

            # match hydrograph from infile to SDH's via Qmax and Volume
            # grab matching shapefile from postgis-database and display it
            shapenames.append(ProcessingHelper.getmatchingshapefromdb(None, qmax, qvol, floodplain_name, dbproperties, logger))

    filteredShapeNames = list(filter(None.__ne__, shapenames))
    if len(filteredShapeNames) > 0:

        mergeprocessor = MergeProcessor()
        logger.info('Merging and dissolving starts ...')
        spinner = Spinner()
        spinner.start()

        mergetablename = mergeprocessor.exec_merge_dissolve(dbproperties, generalproperties, filteredShapeNames, logger)

        spinner.stop()
        logger.info('Merging and dissolving finished. Resulting tablename is {}.'.format(mergetablename))

        sys.stdout.write(mergetablename)
        sys.stdout.flush()
        sys.exit(0)
    else:
        logger.error('No resulting shapes available. Processing finished.')
        sys.exit(1)


if __name__ == "__main__":
    main()
