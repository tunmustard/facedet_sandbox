###### This is my experimental/training project with face-detection API, OpenCV webcam capture and Flash web server. 
This project is based on following packages:  
https://github.com/miguelgrinberg/flask-video-streaming - wonderfull tutorial for webcam video streaming Flask server  
https://github.com/ageitgey/face_recognition - awesome CNN face recongition system with API  

**What it does:**
- Start local Flask web server on http://0.0.0.0:5000
- Capture video stream from your webcam (check if your webcam is supported by [Linux UVC driver](http://www.ideasonboard.org/uvc/#devices))
- Find face locations in each captured frame
