from flask import Flask, Response, render_template, jsonify, request
from picamera2 import Picamera2
import cv2
from s3_uploader import S3Uploader
import time
import threading
from detection import detect_person_lambda

app = Flask(__name__)
s3_uploader = S3Uploader()

pi_camera = Picamera2()
pi_camera.configure(pi_camera.create_video_configuration(main={"size": (640, 480)}))
pi_camera.start()

# Detection/upload state
last_check_time = 0
last_upload_time = 0
is_recording = False
person_present = False
recording_lock = threading.Lock()

CHECK_INTERVAL = 15          # Check less frequently when idle
UPLOAD_COOLDOWN = 120
ACTIVE_CHECK_INTERVAL = 15   # Check less frequently when active too

def record_and_upload():
    """Record 5 seconds and upload to S3"""
    global is_recording
    
    print("Recording 5-second clip...")
    frames = []
    fps = 10  # Reduced from 15 to lower CPU load
    duration = 5
    total_frames = fps * duration
    
    for i in range(total_frames):
        frame = pi_camera.capture_array()
        frames.append(frame)
        time.sleep(1/fps)
    
    print("Uploading video to S3...")
    
    if s3_uploader.upload_video(frames, fps):
        print("Video uploaded successfully!")
    else:
        print("Failed to upload video")
    
    with recording_lock:
        is_recording = False

def check_for_person():
    """Background thread that periodically checks for person"""
    global last_check_time, last_upload_time, is_recording, person_present
    
    while True:
        current_time = time.time()
        
        if person_present:
            check_interval = ACTIVE_CHECK_INTERVAL
        else:
            check_interval = CHECK_INTERVAL
        
        if current_time - last_check_time >= check_interval:
            last_check_time = current_time
            
            frame = pi_camera.capture_array()
            
            print(f"Checking for person... (interval: {check_interval}s)")
            person_detected = detect_person_lambda(frame)
            
            if person_detected:
                print("Person detected!")
                person_present = True
                
                if current_time - last_upload_time >= UPLOAD_COOLDOWN:
                    with recording_lock:
                        if not is_recording:
                            print("Triggering recording!")
                            is_recording = True
                            last_upload_time = current_time
                            
                            thread = threading.Thread(target=record_and_upload)
                            thread.daemon = True
                            thread.start()
                else:
                    time_left = int(UPLOAD_COOLDOWN - (current_time - last_upload_time))
                    print(f"Cooldown active. Next upload in {time_left}s")
            else:
                if person_present:
                    print("Person no longer detected")
                person_present = False
        
        time.sleep(1)

def generate_frames():
    """Stream video to browser"""
    while True:
        frame = pi_camera.capture_array()
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        ret, buffer = cv2.imencode('.jpg', frame_bgr)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.1)  # ~10fps instead of 30fps to reduce CPU load

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/alerts')
def alerts():
    return render_template('alerts.html')

@app.route('/api/videos')
def api_videos():
    """API endpoint to list videos from S3 with optional filtering"""
    date_filter = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    videos = s3_uploader.list_videos(date_filter, start_time, end_time)
    return jsonify({'videos': videos})

if __name__ == '__main__':
    detection_thread = threading.Thread(target=check_for_person)
    detection_thread.daemon = True
    detection_thread.start()
    
    app.run(host="0.0.0.0", port=8080, debug=False)
