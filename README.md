# TODO

1. Convert videos to ffmpeg with `ffmpeg -ss 61.0 -t 2.5 -i StickAround.mp4 -filter_complex "[0:v] fps=12,scale=w=480:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" StickAroundPerFrame.gif`
2. Call HA with binary sensor
