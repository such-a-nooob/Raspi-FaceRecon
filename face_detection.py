import os
import sqlite3
import numpy as np
import dlib
import cv2
from datetime import datetime, timedelta

# Database and folder paths
db_path = "found.db"
known_faces_folder = "data/known_faces"
all_faces_folder = "data/all_faces"

detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("data/data_dlib/shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

# Load known face encodings
def load_known_faces():
    known_encodings = []
    known_names = []
    for person_name in os.listdir(known_faces_folder):
        person_folder = os.path.join(known_faces_folder, person_name)
        if os.path.isdir(person_folder):
            for filename in os.listdir(person_folder):
                filepath = os.path.join(person_folder, filename)
                image = cv2.imread(filepath)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                faces = detector(rgb_image)
                
                if len(faces) == 1:
                    shape = shape_predictor(rgb_image, faces[0])
                    encoding = np.array(face_rec_model.compute_face_descriptor(rgb_image, shape))
                    known_encodings.append(encoding)
                    known_names.append(person_name)
    return known_encodings, known_names

known_encodings, known_names = load_known_faces()

# Initialize database
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS detected_faces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Check if a face was detected within the last 5 minutes
def was_recently_detected(name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM detected_faces WHERE name = ? ORDER BY timestamp DESC LIMIT 1", (name,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        last_seen = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_seen < timedelta(minutes=5):
            return True
    return False

# Process new face images
def process_faces():
    today = datetime.now().strftime("%Y-%m-%d")
    date_path = os.path.join(all_faces_folder, today)
    
    if os.path.isdir(date_path):
        for filename in os.listdir(date_path):
            filepath = os.path.join(date_path, filename)
            image = cv2.imread(filepath)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            faces = detector(rgb_image)
            
            if not faces:
                os.remove(filepath)  # Remove unrecognized face images
                continue
            
            shape = shape_predictor(rgb_image, faces[0])
            encoding = np.array(face_rec_model.compute_face_descriptor(rgb_image, shape))
            
            distances = np.linalg.norm(known_encodings - encoding, axis=1)
            min_distance = np.min(distances)
            
            if min_distance < 0.6:
                matched_index = np.argmin(distances)
                name = known_names[matched_index]
                
                if not was_recently_detected(name):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO detected_faces (name, timestamp) VALUES (?, ?)", (name, timestamp))
                    conn.commit()
                    conn.close()
            else:
                os.remove(filepath)  # Remove unrecognized face images

process_faces()
