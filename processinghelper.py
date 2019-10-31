import os
import pandas as pd
import psycopg2
from scipy.integrate import quad
from scipy.interpolate import interp1d


class ProcessingHelper(object):

    @staticmethod
    def getDataFrameForFile(self, filename):
        """ Read the content of the file into a Dataframe, using col 1 as 'time', col 2 as 'q' """

        df_forecast = pd.read_csv(filename, sep=None, engine='python', usecols=[0, 1], names=['time', 'q'])
        # TODO better read all columns with the following line and then test for river or lake by checking the columns
        # df_forecast = pd.read_csv(filename, sep=None, engine='python')
        # with the following code can the later be tested, if it is a river or a lake and therefore of volume has to be calculated
        # if 'Q' in df_forecast.columns:
        # Then extract the desired subset of columns, just in case there are any other columns
        # df_forecast = df_forecast[['Time','Q']]

        df_forecast.reset_index(inplace=True, drop=True)

        # replace values on x-Axe by hourly sec-values; this is needed to make the timeline comparable with the sdh's
        # for row in df_forecast.itertuples():
        #     df_forecast.at[row.Index, 'time'] = row.Index * 3600

        # set datatypes, just to make sure they can be handled correctly
        df_forecast_typed = df_forecast.astype(dtype={'time': 'int64', 'q': 'float64'})
        return df_forecast_typed

    @staticmethod
    def getVolume(dataframe):
        """ Determine the cubic interpolation function for the data in dataframe. Then calculate the integral for the data with this function. """
        function_cubic = interp1d(dataframe['time'], dataframe['q'], kind='cubic')
        integral, err = quad(function_cubic, 0, dataframe['time'].max())
        return integral, err

    @staticmethod
    def getmatchingshapefromdb(self, qmax_forecast, qvol_forecast, floodplain, dbproperties, logger):
        """
        Get the matching shape: first match qmax.
        If more than 1 match: for rivers match by qvol, for lakes just take the highest of the matches
        """

        connection = psycopg2.connect(**dbproperties)
        cursor = connection.cursor()
        query = 'select a.id, qmax, qvol, shapefile_tablename from t_sdh_metadata a, t_floodplain b where a.floodplain_id = b.id and b.floodplain_name = %s and abs(%s - qmax) = (select min(abs(%s - qmax)) from t_sdh_metadata c, t_floodplain d where c.floodplain_id = d.id and d.floodplain_name = %s);'
        data = (floodplain, qmax_forecast, qmax_forecast, floodplain)
        cursor.execute(query, data)

        try:
            results = cursor.fetchall()  # all rows; can fail if no rows are found!
        except Exception as e:
            logger.error('no matching shapes found in the database for floodplain {}. This floodplain is therefore skipped'.format(floodplain))
            return None

        for result in results:
            logger.info('resultrow: {}'.format(result))

        cursor.close()
        connection.close()

        if len(results) == 1:
            # if qmax_forecast is lower than qmax_sdh then no match is found
            if qmax_forecast < results[0][1]:
                ProcessingHelper.logForecastBelowLowestSDH(floodplain, qmax_forecast, results, logger)
                return None
            else:
                return results[0][3]  # fourth col is the shapefile_tablename
        elif len(results) == 0:
            logger.info('no matching shapes found in the database for floodplain {}. This floodplain is therefore skipped'.format(floodplain))
            return None
        else:
            # several matches for qmax ...
            # find the lowest value of qmax in the sdh's
            min_qmax = min([qmax[1] for qmax in results])
            if qmax_forecast < min_qmax:
                ProcessingHelper.logForecastBelowLowestSDH(None, floodplain, qmax_forecast, results, logger)
                return None
            elif results[0][2]:  # true if qvol, which is the third col in the result, is not null
                # for a river find the closest match in volume
                diffold = 0
                for result in results:
                    diffnew = abs(qvol_forecast - result[2])
                    if diffnew <= diffold:
                        return result[3]
                    else:
                        diffold = diffnew
            else:  # qvol is null, therefore this is a lake: return the highest sdh
                oldqmax = 0
                shapefilenname = None
                for row in results:
                    if row[1] > oldqmax:  # compare the qmax
                        oldqmax = row[1]
                        shapefilenname = row[3]
                return shapefilenname

    @staticmethod
    def logForecastBelowLowestSDH(self, floodplain, qmax_forecast, results, logger):
        logger.info(
            'qmax_forecast {qmax_forecast} is below lowest qmax_sdh {qmax_sdh} for floodplain {floodplain}. Therefore no matching shape is found and floodplain {floodplain} is skipped.'.format(
                qmax_forecast=qmax_forecast, qmax_sdh=results[0][1], floodplain=floodplain))

    @staticmethod
    def replacebackslashes(filename):
        return filename.replace('\\', '/')

    @staticmethod
    def getfloodplainNameFromFilename(filename):
        return os.path.basename(filename).split('.')[0].split('_')[0]