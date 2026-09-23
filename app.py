from fastapi import FastAPI, File, UploadFile
import cv2
import numpy as np
import tempfile
import os
import traceback
from pdf2image import convert_from_path
import io
from liveness import LivenessDetector

# Only set Poppler path on Windows (local development)
if os.name == 'nt':
    os.environ['PATH'] = r'C:\Users\Rebaona\biometric_service\poppler-26.02.0\Library\bin' + os.pathsep + os.environ['PATH']

app = FastAPI()

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}

# PDF extension
PDF_EXTENSIONS = {'.pdf'}

# ============================================
# IMAGE QUALITY VALIDATION
# ============================================
def validate_id_image_quality(image_path):
    """Validate ID image quality before processing"""
    try:
        import cv2
        
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            return False, "Could not read image. Please upload a valid image file."
        
        height, width = image.shape[:2]
        
        # Check minimum size
        if height < 200 or width < 200:
            return False, "Image is too small. Please upload a clearer photo."
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Check image clarity using Laplacian variance (blur detection)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 30:
            return False, "Image is blurry. Please take a clearer photo with better lighting."
        
        # Detect face using OpenCV
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        # Try with scaled image for better detection
        scale = 2
        scaled_gray = cv2.resize(gray, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        faces = face_cascade.detectMultiScale(scaled_gray, 1.05, 3, minSize=(50, 50))
        
        if len(faces) == 0:
            return False, "No face detected in the ID photo. Please ensure the photo is clear and contains your face."
        
        # Check face size
        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        if w < 60 or h < 60:
            return False, "Face is too small. Please upload a closer photo of your ID."
        
        return True, "Image quality check passed"
        
    except Exception as e:
        print(f"Quality check error: {e}")
        return False, f"Error checking image quality: {str(e)}"

# ============================================
# FACE EXTRACTION FROM ID
# ============================================
def extract_face_from_image(image_path):
    """Extract face from image using OpenCV"""
    try:
        import cv2
        import numpy as np
        
        image = cv2.imread(image_path)
        if image is None:
            print("Could not read image")
            return None
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        
        faces = face_cascade.detectMultiScale(gray, 1.05, 3, minSize=(30, 30))
        
        if len(faces) == 0:
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(20, 20))
        
        if len(faces) == 0:
            print("No face detected in ID")
            return None
        
        x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
        
        padding = int(max(w, h) * 0.2)
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + padding * 2)
        h = min(image.shape[0] - y, h + padding * 2)
        
        face_roi = image[y:y+h, x:x+w]
        enlarged_face = cv2.resize(face_roi, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
        
        temp_face = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        cv2.imwrite(temp_face.name, enlarged_face)
        print(f"✅ Face extracted and enlarged: {temp_face.name}")
        return temp_face.name
        
    except Exception as e:
        print(f"Face extraction error: {e}")
        return None

# ============================================
# PDF CONVERSION
# ============================================
def convert_pdf_to_image(pdf_path):
    """Convert first page of PDF to image"""
    try:
        poppler_path = None
        if os.name == 'nt':
            poppler_path = r'C:\Users\Rebaona\biometric_service\poppler-26.02.0\Library\bin'
        images = convert_from_path(pdf_path, poppler_path=poppler_path, first_page=1, last_page=1)
        if images:
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            images[0].save(temp_img.name, 'JPEG')
            return temp_img.name
        return None
    except Exception as e:
        print(f"PDF conversion error: {e}")
        return None

# ============================================
# FILE VALIDATION
# ============================================
def validate_image_file(file: UploadFile):
    """Check if the uploaded file is a valid image by extension"""
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension in ALLOWED_EXTENSIONS:
        return True, "image", ""
    
    if file_extension in PDF_EXTENSIONS:
        return True, "pdf", ""
    
    return False, "unknown", f"Unsupported file format: {file_extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS | PDF_EXTENSIONS)}"

# ============================================
# ROOT ENDPOINT
# ============================================
@app.get("/")
def home():
    return {"message": "Biometric Verification Service is running"}

# ============================================
# VERIFICATION ENDPOINT
# ============================================
@app.post("/verify")
async def verify_face(
    id_image: UploadFile = File(...),
    selfie_image: UploadFile = File(...)
):
    id_path = None
    selfie_path = None
    temp_id_path = None
    extracted_face_path = None
    
    try:
        # Validate both files
        valid_id, id_type, msg_id = validate_image_file(id_image)
        valid_selfie, selfie_type, msg_selfie = validate_image_file(selfie_image)
        
        if not valid_id:
            return {"status": "error", "message": msg_id}
        if not valid_selfie:
            return {"status": "error", "message": msg_selfie}
        
        # --- Handle ID Image ---
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf" if id_type == "pdf" else ".jpg") as temp_id:
            temp_id.write(await id_image.read())
            temp_id_path = temp_id.name
        
        if id_type == "pdf":
            id_path = convert_pdf_to_image(temp_id_path)
            if id_path is None:
                return {"status": "error", "message": "Failed to convert PDF to image."}
            os.unlink(temp_id_path)
            temp_id_path = None
        else:
            id_path = temp_id_path
            temp_id_path = None
        
        # --- VALIDATE ID IMAGE QUALITY ---
        if id_path:
            quality_ok, quality_message = validate_id_image_quality(id_path)
            if not quality_ok:
                return {
                    "status": "failed",
                    "verified": False,
                    "reason": quality_message,
                    "quality_check": False,
                    "face_match": False,
                    "liveness_passed": False,
                    "distance": None
                }
            print(f"✅ ID image quality check: {quality_message}")
        
        # --- EXTRACT FACE FROM ID ---
        if id_path:
            extracted_face_path = extract_face_from_image(id_path)
            if extracted_face_path:
                os.unlink(id_path)
                id_path = extracted_face_path
                print(f"✅ Using extracted face for verification")
        
        # --- Handle Selfie ---
        if selfie_type != "image":
            return {"status": "error", "message": "Selfie must be an image file"}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_selfie:
            temp_selfie.write(await selfie_image.read())
            selfie_path = temp_selfie.name
        
        # --- RESIZE SELFIE ---
        selfie_img = cv2.imread(selfie_path)
        if selfie_img is not None:
            h, w = selfie_img.shape[:2]
            max_size = 640
            if w > max_size or h > max_size:
                scale = max_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                resized = cv2.resize(selfie_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                cv2.imwrite(selfie_path, resized)
                print(f"Selfie resized from {w}x{h} to {new_w}x{new_h}")
        
        # --- LIVENESS DETECTION ---
        liveness_detector = LivenessDetector()
        liveness_result = liveness_detector.check_liveness(selfie_path)

        if not liveness_result['passed']:
            if id_path and os.path.exists(id_path):
                os.unlink(id_path)
            if selfie_path and os.path.exists(selfie_path):
                os.unlink(selfie_path)
            
            return {
                "status": "failed",
                "verified": False,
                "reason": liveness_result['reason'],
                "liveness_passed": False,
                "face_match": False,
                "distance": None,
                "quality_check": True
            }

                # --- FACE VERIFICATION with DeepFace (lightweight) ---
        try:
            from deepface import DeepFace
            
            verification_result = DeepFace.verify(
                img1_path=id_path,
                img2_path=selfie_path,
                model_name='VGG-Face',
                detector_backend='opencv',
                enforce_detection=False
            )
            face_match = verification_result['verified']
            distance = float(verification_result['distance'])
            print(f"Face verification: {'MATCH' if face_match else 'NO MATCH'} (distance: {distance})")
            
        except Exception as verify_error:
            face_match = False
            distance = None
            print(f"Face verification FAILED: {str(verify_error)}")
            return {"status": "error", "message": f"Face verification failed: {str(verify_error)}"}
        
        # Clean up
        if id_path and os.path.exists(id_path):
            os.unlink(id_path)
        if selfie_path and os.path.exists(selfie_path):
            os.unlink(selfie_path)
        
        if face_match:
            return {
                "status": "success",
                "verified": True,
                "message": "Identity verified successfully!",
                "liveness_passed": True,
                "face_match": True,
                "distance": distance,
                "quality_check": True
            }
        else:
            return {
                "status": "failed",
                "verified": False,
                "reason": "Face does not match the ID document.",
                "liveness_passed": True,
                "face_match": False,
                "distance": distance,
                "quality_check": True
            }
        
    except Exception as e:
        try:
            if id_path and os.path.exists(id_path):
                os.unlink(id_path)
        except:
            pass
        try:
            if selfie_path and os.path.exists(selfie_path):
                os.unlink(selfie_path)
        except:
            pass
        
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")
        
        return {
            "status": "error",
            "message": str(e),
            "trace": error_trace
        }