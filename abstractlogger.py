class AbstractLogger(object):

    def info(self, message):
        raise NotImplementedError()

    def error(self, message):
        raise NotImplementedError()

    def critical(self, message):
        raise NotImplementedError()
