import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from subprocess import call
import os
import sys
import logging
import json

def parse_config(config_path):
    with open(config_path, 'r') as config_file:
        config_data = json.load(config_file)
    return config_data


class Watcher:
    def __init__(self, config):
        self.config = config
        self.dir = os.path.abspath(self.config['video_watch_dir'])
        self.observer = Observer()

    def run(self):
        event_handler = Handler(self.config)
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
            print("Received created event - {0}.".format(event.src_path))
            command = "ffmpeg -i %s -s 1920x1080 -i /home/pi/Videos/tff_overlay_1920x1080.png -filter_complex overlay=0:0 -b 4000000 -q:v 1 /home/pi/Videos/output.mp4" % event.src_path
            call([command], shell=True)


def main():
    logging.basicConfig(filename='filewatcher.log', level=logging.INFO)
    logging.info('Started')
    _, config_filename = sys.argv
    config = parse_config(config_filename)

    #event_handler = UniFiVideoEventHandler(config)

    observer = Observer()
    event_handler = Handler(config)
    observer.schedule(
        event_handler, config["unifi_video_watch_dir"], recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
