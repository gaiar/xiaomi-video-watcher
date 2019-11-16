# TODO

1. Convert videos to ffmpeg with `ffmpeg -i StickAround.mp4 -filter_complex "[0:v] fps=12,scale=w=640:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" StickAroundPerFrame.gif`
2. Optimize result GIF with `gifsicle -O3 енот.gif -o енот_opt.gif`
3. Call HA with binary sensor
