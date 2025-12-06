from flask import Flask, Response, render_template
from picamera2 import Picamera2
import cv2

app = Flask(__name__)

pi_camera = Picamera2()
pi_camera.configure(pi_camera.create_video_configuration(main={"size": (640, 480)}))
pi_camera.start()

def generate_frames():
    while True:
        frame = pi_camera.capture_array()
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

app.run(host="0.0.0.0", port=8080, debug=False)
