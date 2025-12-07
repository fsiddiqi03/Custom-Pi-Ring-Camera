import cv2
import base64
import requests
from config import LAMBDA_URL

def detect_person_lambda(frame):
    """
    Send frame to Lambda for person detection
    
    Args:
        frame: numpy array (image frame)
        
    Returns:
        bool: True if person detected
    """
    try:
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            print("Failed to encode frame")
            return False
        
        # Convert to base64
        image_b64 = base64.b64encode(buffer).decode('utf-8')
        
        # Send to Lambda
        response = requests.post(
            LAMBDA_URL,
            json={'image': image_b64},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            person_detected = result.get('person_detected', False)
            if person_detected:
                print(f"Person detected! ({result.get('num_detections', 0)} detections)")
            return person_detected
        else:
            print(f"Lambda error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("Lambda request timed out")
        return False
    except Exception as e:
        print(f"Detection error: {e}")
        return False