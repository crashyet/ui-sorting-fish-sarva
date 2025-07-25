# Sorting Fish with Object Detection

Clone this repository and run this.
```bash
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python3 ui-design.py
```


command start video
```bash
libcamera-vid -t 0 --width 640 --height 480 --framerate 25 -o - | ffmpeg -re -i - -vcodec libx264 -f rtsp rtsp://127.0.0.1:8554/mystream
```
atau
```bash
libcamera-vid -t 0 --width 640 --height 480 --framerate 25 -o - | ffmpeg -re -i - -vcodec libx264 -tune zerolatency -preset ultrafast -pix_fmt yuv420p -g 25 -keyint_min 25 -sc_threshold 0 -f rtsp rtsp://0.0.0.0:8554/mystream
```

command start server
```bash
./mediamtx
```