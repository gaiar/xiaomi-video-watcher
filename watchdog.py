import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import call
import os
import logging


class Watcher:
    def __init__(self):
        self.dir = os.path.abspath('data/')
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.dir, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print ("Received created event - {0}.".format(event.src_path))
            command = "ffmpeg -i %s -s 1920x1080 -i /home/pi/Videos/tff_overlay_1920x1080.png -filter_complex overlay=0:0 -b 4000000 -q:v 1 /home/pi/Videos/output.mp4" % event.src_path
            call([command], shell=True)


if __name__ == '__main__':
    logging.basicConfig(filename='filewatcher.log', level=logging.INFO)
    logging.info('Started')
    w = Watcher()
    w.run()