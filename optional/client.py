import cv2
import subprocess
import requests
import time
from datetime import datetime
import os

# Load OpenCV Haar cascade face detector
face_cascade = cv2.CascadeClassifier("/home/ourRasp/haarcascade_frontalface_default.xml")

# Flask server URL
SERVER_URL = "http://192.168.182.83:5000/upload"

# Image capture settings
IMAGE_WIDTH = "1024"
IMAGE_HEIGHT = "768"
IMAGE_PATH = "/home/ourRasp/last_capture.jpg"

def capture_image():
    """Capture image using libcamera-jpeg"""
    try:
        print("Capturing image...")
        result = subprocess.run(
            ["libcamera-jpeg", "-o", IMAGE_PATH, "--width", IMAGE_WIDTH, "--height", IMAGE_HEIGHT],
            check=True,
            capture_output=True,
            text=True
        )
        print("Capture successful")
    except subprocess.CalledProcessError as e:
        print("Failed to capture image")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

def detect_and_send_faces():
    """Detect faces and send to server"""
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print("Failed to read captured image")
        return

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        print("No faces detected.")
        return

    print(f"Detected {len(faces)} face(s). Sending to server...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, (x, y, w, h) in enumerate(faces):
        face_img = image[y:y+h, x:x+w]
        filename = f"face_{timestamp}_{i}.jpg"
        face_path = os.path.join("/home/ourRasp", filename)
        cv2.imwrite(face_path, face_img)

        # Send to server with filename
        try:
            with open(face_path, 'rb') as img_file:
                files = {'image': (filename, img_file, 'image/jpeg')}
                response = requests.post(SERVER_URL, files=files)
                print(f"✅ Sent face {i+1}: {response.text}")
        except Exception as e:
            print("Error sending image:", e)

        os.remove(face_path)

def main():
    print("Starting face detection loop using libcamera...")
    try:
        while True:
            capture_image()
            detect_and_send_faces()
            time.sleep(3)  # Capture every 3 seconds
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    main()
