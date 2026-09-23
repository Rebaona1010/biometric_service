import requests
import os

id_image_path = r"C:\Users\Rebaona\Downloads\ID.jpeg"
selfie_image_path = r"C:\Users\Rebaona\Downloads\selfie_reba.jpeg"

url = "https://biometric-service-3ymt.onrender.com/verify"

files = {
    "id_image": open(id_image_path, "rb"),
    "selfie_image": open(selfie_image_path, "rb")
}

response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Full Response:", response.text)  # ← Changed to .text

files["id_image"].close()
files["selfie_image"].close()