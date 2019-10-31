import sys
from abstractlogger import AbstractLogger


class ConsoleLogger(AbstractLogger):

    def info(self, message):
        print('{}'.format(message))

    def error(self, message):
        print('{}'.format(message), file=sys.stderr)

    def critical(self, message):
        print('{}'.format(message), file=sys.stderr)
