# Mijia 360 1080p camera video files monitor

## TODO

1. Convert videos to ffmpeg with `ffmpeg -i StickAround.mp4 -filter_complex "[0:v] fps=12,scale=w=640:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" StickAroundPerFrame.gif`
2. Optimize result GIF with `gifsicle -O3 енот.gif -o енот_opt.gif`
3. Call HA with binary sensor

## Usage

1. Install needed ffmpeg, gifsicle and requirements
2. Create file xiaomi_video_watcher.json with the following content:

```json
{
    "xiaomi_video_watch_dir" : PATH_TO_WATCH,
    "xiaomi_video_temp_dir" : PATH_TO_STORE_TEMP_FILES,
    "xiaomi_video_gif_dir" : PATH_WITH_OUTPUT_GIFS,
    "tg_key" : TELEGRAM_KEY
}
```

3. Run as `python video_watchdog.py xiaomi_video_watcher.json`