import psycopg2
import datetime


class MergeProcessor(object):

    def exec_merge_dissolve(self, dbproperties, generalproperties, shapenames, logger) -> str:
        """
                Creates a Table with merges
                :param dbconfig: db config
                :param properties additional properties
                :param shapenames: the shapes to merge
                :return: the name of the resulting merged shapes table
                """
        connection = psycopg2.connect(**dbproperties)
        cursor = connection.cursor()
        query = 'CREATE TABLE {table} {select}'
        mergetablename = 't_mergeshape_{}'.format(datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
        union_subselect = []
        for i in range(0, len(shapenames)):
            if i == 0:
                union_subselect.append(' AS ')
            else:
                union_subselect.append(' UNION ')
            union_subselect.append(
                'SELECT gid, round((max_depth::numeric/{maxdepth_precision}), 0) * {maxdepth_precision} as max_depth, geom FROM {shapename} WHERE max_depth > 0'.format(maxdepth_precision=generalproperties.get('maxdepth_precision'),
                                                                                                                                      shapename=shapenames[i]))
        if generalproperties.getboolean('dissolve_merged_shapes'):
            # replace the first element which was ' AS '
            union_subselect[0] = ' FROM ('
            union_subselect.append(') t')
            union_subselect.insert(0, ' AS SELECT ST_Union(geom) AS geom, max_depth')
            union_subselect.append(' GROUP BY max_depth ')
        union_subselect.append(';')
        queryparams = (mergetablename, ''.join(union_subselect))
        query = query.format(table=mergetablename, select=''.join(union_subselect))
        logger.info('Creating merge table: query: {query}; params {params}'.format(query=query, params=queryparams))
        cursor.execute(query)
        connection.commit()
        cursor.close()
        connection.close()
        return mergetablename
