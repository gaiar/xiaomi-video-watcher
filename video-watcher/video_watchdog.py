import json
import logging
import os
import subprocess
import sys
import time
from collections import deque, namedtuple
from pathlib import Path, PurePath
from subprocess import call
from tempfile import mkstemp

import paho.mqtt.client as mqtt
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def parse_config(config_path):
    with open(config_path, "r") as config_file:
        config_data = json.load(config_file)
    return config_data


class Watcher:
    def __init__(self, config):
        self.config = config
        self.dir = os.path.abspath(self.config["video_watch_dir"])
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
    def __init__(self, config):
        self.config = config
        # self.mqtt_client = mqtt.Client()
        self.updater = Updater(config["tg_key"], use_context=True)
        # Keep a FIFO of files processed so we can guard against duplicate
        # filesystem events
        self.processed_files = deque(maxlen=20)
        super().__init__()

    def on_created(self, event):
        if event.is_directory:
            return None

        elif event.event_type == "created":
            # Take any action here when a file is first created.
            print("Received created event - {0}".format(event.src_path))
            filepath, tempfile, giffile = self._get_paths(event.src_path)
            if PurePath(filepath).suffix == ".mp4":
                # TODO: Add timings
                logging.info(
                    "Processing file {0} with size of {1} MB".format(
                        filepath.name, filepath.stat().st_size / 1024
                    )
                )
                print(
                    "Processing file {0} with size of {1} MB".format(
                        filepath.name, filepath.stat().st_size / 1024
                    )
                )

                # cmd = [ffmpeg,'-i', inFile,'-f', 'image2','-vf',
                # "select='eq(pict_type,PICT_TYPE_I)'",'-vsync','vfr', imgFilenames]

                command = [
                    "ffmpeg",
                    "-i",
                    filepath,
                    "-filter_complex",
                    "[0:v] fps=12,scale=w=640:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1",
                    tempfile,
                ]
                call(command)

                logging.info(
                    "Created file {0} with size of {1} MB".format(
                        tempfile.name, tempfile.stat().st_size / 1024
                    )
                )
                print(
                    "Created file {0} with size of {1} MB".format(
                        tempfile.name, tempfile.stat().st_size / 1024
                    )
                )

                command = ["gifsicle", "-O3", tempfile, "-o", giffile]
                
                call(command)
                logging.info(
                    "Created optimized file {0} with size of {1} MB".format(
                        giffile.name, giffile.stat().st_size / 1024
                    )
                )
                print(
                    "Created optimized file {0} with size of {1} MB".format(
                        giffile.name, giffile.stat().st_size / 1024
                    )
                )

                self._send_to_telegram(filepath)

                tempfile.unlink()
                # filepath.unlink()
                logging.info("Deleted file {0}".format(tempfile.name))
                print("Deleted file {0}".format(tempfile.name))

            else:
                logging.warning(
                    "[INFO] :: Ignoring non-video file {0}".format(event.src_path)
                )
                print("[INFO] :: Ignoring non-video file {0}".format(event.src_path))

    def on_any_event(self, event):
        print(event)

    def _get_paths(self, path):
        filepath = Path(path)
        filename = str(filepath.name).split(".")[0]
        tempfile = Path(self.config["xiaomi_video_temp_dir"], filename + ".gif")
        giffile = Path(self.config["xiaomi_video_gif_dir"], filename + ".gif")
        return filepath, tempfile, giffile

    def _send_to_telegram(self, filepath):

        for attempt in range(10):
            try:
                logging.debug("Sending to telegram {0}".format(filepath))
                self.updater.bot.send_video(
                    "@baimuratov_bot_group", open(filepath, "rb")
                )
                logging.debug("{0} sent successfully ".format(filepath))
                break
            except Exception as e:
                print(e)
                logging.warning(
                    'Module "%s": tg connection error {0}, retry.'.format(e)
                )
                time.sleep(5)

        return None


def main():
    logging.basicConfig(filename="xiaomi_video_watcher.log", level=logging.INFO)
    logging.info("[INFO] :: Started watching folder")
    print("[INFO] :: Started watching")
    _, config_filename = sys.argv
    config = parse_config(config_filename)
    print("[INFO] :: Config is {0}".format(json.dumps(config)))

    observer = Observer()
    event_handler = Handler(config)
    observer.schedule(event_handler, config["xiaomi_video_watch_dir"], recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
