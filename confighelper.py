from configparser import ConfigParser
import os.path

class ConfigHelper(object):

    @staticmethod
    def config(self, path, filename='database.ini', section='postgresql'):
        properties = ConfigParser()
        properties.read(os.path.join(path, filename))
        if properties.has_section(section):
            return properties[section]
        else:
            raise Exception('Section {0} not found in file {1}'.format(section, filename))
