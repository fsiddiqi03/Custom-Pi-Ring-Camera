# Main file for the S3 uploader

import boto3
import cv2
import subprocess
from datetime import datetime
from config import REGION_NAME, BUCKET_NAME, ACCESS_KEY, SECRET_KEY

class S3Uploader:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            region_name=REGION_NAME,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        self.bucket_name = BUCKET_NAME
    
    def create_file_name(self, extension='jpg'):
        return datetime.now().strftime("%Y%m%d_%H%M%S") + f".{extension}"
    
    def upload_file(self, frame):
        """Upload a single frame as JPEG"""
        file_name = self.create_file_name('jpg')
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Failed to encode frame")
            return False
        
        frame_bytes = buffer.tobytes()
        
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=frame_bytes,
                ContentType='image/jpeg'
            )
            print(f"Uploaded image: {file_name}")
            return True
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return False
    
    def upload_video(self, frames, fps=15):
        """
        Upload frames as browser-compatible MP4 video
        """
        if not frames:
            return False
        
        file_name = self.create_file_name('mp4')
        
        try:
            import os
            height, width = frames[0].shape[:2]
            
            # Step 1: Create temporary AVI with MJPG (always works on Pi)
            temp_avi = f'/tmp/temp_{file_name.replace(".mp4", ".avi")}'
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(temp_avi, fourcc, fps, (width, height))
            
            for frame in frames:
                # Convert from RGB/RGBA to BGR for OpenCV
                if len(frame.shape) == 3:
                    if frame.shape[2] == 4:  # RGBA/XRGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    elif frame.shape[2] == 3:  # RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
            
            out.release()
            
            # Verify AVI was created
            avi_size = os.path.getsize(temp_avi)
            print(f"Created temp AVI: {avi_size} bytes, {len(frames)} frames")
            
            if avi_size == 0:
                print("ERROR: AVI file is empty - frame writing failed")
                os.remove(temp_avi)
                return False
            
            # Step 2: Convert to H.264 MP4 using ffmpeg
            temp_mp4 = f'/tmp/{file_name}'
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-i', temp_avi,  # Input file
                '-c:v', 'libx264',  # H.264 codec
                '-preset', 'ultrafast',  # Fast encoding
                '-crf', '23',  # Quality (lower = better, 23 is default)
                '-pix_fmt', 'yuv420p',  # Browser compatibility
                temp_mp4
            ]
            
            # Run ffmpeg conversion
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode != 0:
                print(f"FFmpeg conversion failed: {result.stderr.decode()}")
                if os.path.exists(temp_avi):
                    os.remove(temp_avi)
                return False
            
            # Step 3: Upload to S3
            with open(temp_mp4, 'rb') as video_file:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=file_name,
                    Body=video_file,
                    ContentType='video/mp4'
                )
            
            # Clean up temp files
            os.remove(temp_avi)
            os.remove(temp_mp4)
            
            print(f"Uploaded video: {file_name}")
            return True
            
        except Exception as e:
            print(f"Error uploading video to S3: {e}")
            return False
    
    def list_videos(self, date_filter=None, start_time=None, end_time=None):
        """
        List all videos from S3 bucket with optional date/time filtering
        
        Args:
            date_filter: Optional date string (YYYY-MM-DD)
            start_time: Optional start time string (HH:MM)
            end_time: Optional end time string (HH:MM)
            
        Returns:
            List of video objects with url, filename, and timestamp
        """
        videos = []
        
        try:
            # List all objects in bucket
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return videos
            
            for obj in response['Contents']:
                key = obj['Key']
                
                # Only include mp4 files
                if not key.endswith('.mp4'):
                    continue
                
                # Parse timestamp from filename (format: YYYYMMDD_HHMMSS.mp4)
                try:
                    timestamp_str = key.replace('.mp4', '')
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                except ValueError:
                    continue
                
                # Apply date filter
                if date_filter:
                    filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                    if timestamp.date() != filter_date:
                        continue
                
                # Apply time filters
                if start_time:
                    start_parts = start_time.split(':')
                    start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
                    video_minutes = timestamp.hour * 60 + timestamp.minute
                    if video_minutes < start_minutes:
                        continue
                
                if end_time:
                    end_parts = end_time.split(':')
                    end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
                    video_minutes = timestamp.hour * 60 + timestamp.minute
                    if video_minutes > end_minutes:
                        continue
                
                # Generate presigned URL for video playback
                url = self.s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                
                videos.append({
                    'filename': key,
                    'url': url,
                    'timestamp': timestamp.isoformat()
                })
            
            # Sort by timestamp (newest first)
            videos.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            print(f"Error listing videos from S3: {e}")
        
        return videos