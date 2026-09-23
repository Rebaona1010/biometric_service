import cv2
import numpy as np
import math

class LivenessDetector:
    def __init__(self):
        # Load OpenCV face detector using local haarcascade file
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        # Circle parameters
        self.circle_radius =400
        self.tolerance = 0.5
        self.min_radius = self.circle_radius * (1 - self.tolerance)
        self.max_radius = self.circle_radius * (1 + self.tolerance)
        
    def detect_face(self, image):
        """Detect face in image using OpenCV"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Get the largest face
        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        
        return {
            'x': x,
            'y': y,
            'width': w,
            'height': h,
            'center_x': x + w // 2,
            'center_y': y + h // 2,
            'face_size': max(w, h)
        }
    
    def check_face_position(self, face_data):
        """Check if face is within the circle"""
        if face_data is None:
            return False, "No face detected"
        
        face_size = face_data['face_size']
        
        if self.min_radius <= face_size <= self.max_radius:
            return True, "Face fits the circle"
        elif face_size < self.min_radius:
            return False, "Move closer to the camera"
        else:
            return False, "Move further from the camera"
    
    def check_liveness(self, image_path):
        """Main liveness check function"""
        image = cv2.imread(image_path)
        if image is None:
            return {'passed': False, 'reason': 'Could not read image', 'score': 0}
        
        face_data = self.detect_face(image)
        if face_data is None:
            return {'passed': False, 'reason': 'No face detected', 'score': 0}
        
        position_ok, position_reason = self.check_face_position(face_data)
        if not position_ok:
            return {'passed': False, 'reason': position_reason, 'score': 0}
        
        # Simple liveness check passed
        return {
            'passed': True,
            'reason': 'Liveness check passed',
            'score': 1.0,
            'face_size': face_data['face_size'],
            'center': (face_data['center_x'], face_data['center_y'])
        }