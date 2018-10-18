# About project
###### This is my experimental/training project with face-detection API, OpenCV webcam capture and Flash web server with video streaming. 
This project is based on following packages:  
https://github.com/miguelgrinberg/flask-video-streaming - wonderfull tutorial for webcam video streaming Flask server  
https://github.com/ageitgey/face_recognition - awesome CNN face recongition system with API  
https://docs.opencv.org/4.0.0-alpha/ OpenCV API 

**What it does:**
- Start local Flask web server on http://0.0.0.0:5000
- Capture video stream from your webcam (check if your webcam is supported by [Linux UVC driver](http://www.ideasonboard.org/uvc/#devices))
- Find face locations in each captured frame (facerecognition API)
- Classify each unique face and add it to internal face encoding list with it's unique ID, crop new face image and save it in jpg.
- Get ID from internal list for each face in frame, add rectangle mark, add it's internal ID
- It can import dictionary from 'dict.csv' file with pairs "ID","Name" and mark a proper name instead of face internal ID
- Automatic import/export internal encoding base in .csv file, so all encodings will be save in case of application restart
- Web interface allows to login into "report" page (login/pass = admin/secret) and take a look on internal encolding face images (ID/NAME/IMAGE)

**Next step:**
- Add event list (pairs ID/time) and make web interface for this

**Future steps:**
- In progressssssssss....................................

# Installation guide
I'm too lazy to finish this ....
Maybe next time...
# How to run
I'm too lazy to finish this ....
Maybe next time...
