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
from watchdog.observers.polling import PollingObserver
import shutil


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
            filepath, tempfile, giffile, processfile = self._get_paths(event.src_path)
            if PurePath(filepath).suffix == ".mp4":
                # TODO: Add timings
                try:
                    self._fix_moov(filepath)
                    self._convert_gif(filepath, tempfile)
                    self._optimize_gif(tempfile, giffile)
                    self._create_screenshot(filepath,processfile)
                    tempfile.unlink()
                    logging.info("Deleted file {0}".format(tempfile.name))
                    print("Deleted file {0}".format(tempfile.name))
                except Exception as error:
                    logging.error("Problem {0} converting file {1}".format(error, filepath))
                self._send_to_telegram(filepath)
               

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
        tempfile = Path(self.config["video_temp_dir"], filename + ".gif")
        giffile = Path(self.config["video_gif_dir"], filename + ".gif")
        processfile = Path(self.config["video_processed_dir"], filename)
        return filepath, tempfile, giffile, processfile

    def _fix_moov(self, videofile):
        logging.info(
            "Processing file {0} with size of {1} MB".format(
                videofile.name, videofile.stat().st_size / 1024
            )
        )
        print(
            "Processing file {0} with size of {1} MB".format(
                videofile.name, videofile.stat().st_size / 1024
            )
        )

        command = ["MP4Box", "-inter", "500", videofile]
        call(command)

    def _convert_gif(self, filepath, tempfile):
        command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-hide_banner",
            "-nostats",
            "-i",
            filepath,
            "-y",
            "-filter_complex",
            "[0:v] fps=12,scale=w=640:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1",
            "-flags",
            "+global_header",
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

    def _optimize_gif(self, tempfile, giffile):
        command = [
            "gifsicle",
            "-f",
            "-O3",
            tempfile,
            "-o",
            giffile,
        ]

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

    def _create_screenshot(self, filepath, processfile):
        command = [
            "ffmpeg",
            "-loglevel",
            "error",
            "-hide_banner",
            "-nostats",
            "-ss",
            "00:00:10",
            "-i",
            filepath,
            "-y",
            "-vframes",
            "1",
            "-q:v",
            "2",
            processfile.with_suffix(".jpg"),
        ]
        call(command)
        shutil.copy(str(filepath), str(processfile.with_suffix(".mp4")))

    def _send_to_telegram(self, filepath):

        for attempt in range(10):
            try:
                logging.debug("Sending to telegram {0}".format(filepath))
                with open(filepath, "rb") as videofile:
                    self.updater.bot.send_video(
                        chat_id="@baimuratov_bot_group",
                        video=videofile,
                        duration=60,
                        caption="Motion detected!",
                        supports_streaming=True,
                        disable_notification=True,
                        timout=30,
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
    logging.basicConfig(filename="video_watcher.log", level=logging.INFO)
    logging.info("[INFO] :: Started watching folder")
    print("[INFO] :: Started watching")
    _, config_filename = sys.argv
    config = parse_config(config_filename)
    print("[INFO] :: Config is {0}".format(json.dumps(config)))

    observer = PollingObserver()
    event_handler = Handler(config)
    observer.schedule(
        event_handler, os.path.realpath(config["video_watch_dir"]), recursive=True
    )
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
