import subprocess
import sys
import time
import os
import hydromatch_starter
from confighelper import ConfigHelper
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class DirectoryWatcher(PatternMatchingEventHandler):

    def __init__(self, watch_file_extension):
        super().__init__(patterns=[watch_file_extension])

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print (event.src_path, event.event_type)

    def on_modified(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)
        time.sleep(10)
        hydromatch_starter.main()

    def on_deleted(self, event):
        self.process(event)


def main():
    propertiespath = os.path.join( os.path.dirname(os.path.realpath(__file__)), 'properties')
    properties = ConfigHelper.config(None, path=propertiespath, filename='properties.ini', section='general')
    dirpath = properties.get('dirpath')
    watch_path = dirpath if dirpath else '.'
    watch_file_extension = '*{}'.format(properties.get('watch_file_extension'))

    observer = Observer()
    observer.schedule(DirectoryWatcher(watch_file_extension), path=watch_path, recursive=False)
    print('Starting to watch directory \'{0}\' for files with extension \'{1}\' ...'.format(watch_path, watch_file_extension))
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


main()
