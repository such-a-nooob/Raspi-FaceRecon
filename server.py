from flask import Flask, request
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "data/all_faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure base directory exists

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    if file:
        filename = file.filename
        
        # Extract date from the filename (assumes format like "face_YYYYMMDD_HHMMSS.jpg")
        try:
            date_part = filename.split('_')[1]  # Extract YYYYMMDD
            date_folder = os.path.join(UPLOAD_FOLDER, date_part)
            os.makedirs(date_folder, exist_ok=True)  # Ensure date folder exists
            
            file_path = os.path.join(date_folder, filename)
            file.save(file_path)
            print(f"Image received and saved: {file_path}")
            return "Success", 200
        except IndexError:
            return "Invalid filename format", 400

    return "Failed", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
