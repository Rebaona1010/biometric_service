import requests
import os

# Change these paths to your actual image locations
id_image_path = r"C:\Users\Rebaona\Downloads\Verify.pdf"
selfie_image_path = r"C:\Users\Rebaona\Downloads\selfie_reba.jpeg"

url = "http://127.0.0.1:8000/verify"

files = {
    "id_image": open(id_image_path, "rb"),
    "selfie_image": open(selfie_image_path, "rb")
}

response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response:", response.json())

# Close files
files["id_image"].close()
files["selfie_image"].close()