import cv2
import requests
import tempfile
import os
import time

def take_selfie():
    """Take a selfie using the laptop camera"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return None
    
    print("📸 Press SPACE to take a selfie, ESC to cancel")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Show the frame
        cv2.imshow('Selfie Camera - Press SPACE to capture', frame)
        
        key = cv2.waitKey(1)
        if key == 32:  # SPACE key
            # Save the selfie
            temp_selfie = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            cv2.imwrite(temp_selfie.name, frame)
            print(f"✅ Selfie saved to: {temp_selfie.name}")
            cap.release()
            cv2.destroyAllWindows()
            return temp_selfie.name
        elif key == 27:  # ESC key
            print("❌ Cancelled")
            cap.release()
            cv2.destroyAllWindows()
            return None
    
    cap.release()
    cv2.destroyAllWindows()
    return None

# --- MAIN TEST ---
print("="*50)
print("🔐 BIOMETRIC VERIFICATION TEST WITH CAMERA")
print("="*50)

# Step 1: Get ID document path
id_path = input("📄 Enter the path to your ID document (image or PDF): ").strip()
id_path = id_path.strip('"')  # Remove quotes if copied with them

if not os.path.exists(id_path):
    print(f"❌ File not found: {id_path}")
    exit()

print(f"✅ ID document found: {id_path}")

# Step 2: Take selfie
print("\n📸 Opening camera...")
selfie_path = take_selfie()

if selfie_path is None:
    print("❌ Selfie cancelled or failed")
    exit()

print(f"✅ Selfie saved: {selfie_path}")

# Step 3: Send to API
print("\n🚀 Sending to verification service...")

url = "http://127.0.0.1:8000/verify"

files = {
    "id_image": open(id_path, "rb"),
    "selfie_image": open(selfie_path, "rb")
}

try:
    response = requests.post(url, files=files)
    result = response.json()
    
    print("\n" + "="*50)
    print("📊 VERIFICATION RESULT")
    print("="*50)
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Verified: {result.get('verified', False)}")
    print(f"Liveness Passed: {result.get('liveness_passed', False)}")
    print(f"Face Match: {result.get('face_match', False)}")
    print(f"Distance: {result.get('distance', 'N/A')}")
    
    if result.get('reason'):
        print(f"Reason: {result.get('reason')}")
    
    if result.get('message'):
        print(f"Message: {result.get('message')}")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error: {e}")

# Clean up temp files
try:
    files["id_image"].close()
except:
    pass
try:
    files["selfie_image"].close()
except:
    pass
try:
    if os.path.exists(selfie_path):
        os.unlink(selfie_path)
except:
    pass

print("\n✅ Test complete!")