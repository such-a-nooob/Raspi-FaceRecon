import dlib
import numpy as np
import cv2
import os
import time
import logging
import tkinter as tk
from tkinter import font as tkFont
from tkinter import LabelFrame
from PIL import Image, ImageTk
import config 

detector = dlib.get_frontal_face_detector()

class FaceRegister:
    def __init__(self):
        self.current_frame_faces_cnt = 0
        self.existing_faces_cnt = 0
        self.ss_cnt = 0
        self.current_face_dir = ""
        self.input_name_char = ""
        self.face_folder_created_flag = False
        self.out_of_range_flag = False
        self.ww = self.hh = 0

        self.win = tk.Tk()
        self.win.title("Face Registration")
        self.win.geometry("1080x540")  # 640 (camera) + 420 (info) + spacing

        self.font_title = tkFont.Font(family='Helvetica', size=16, weight='bold')
        self.font_label = tkFont.Font(family='Helvetica', size=10)

        # Camera Frame
        self.frame_camera = LabelFrame(self.win, text="Camera", padx=5, pady=5)
        self.frame_camera.grid(row=0, column=0, padx=10, pady=10)
        self.label_img = tk.Label(self.frame_camera)
        self.label_img.pack()

        # Info Frame with FIXED SIZE
        self.frame_info = LabelFrame(self.win, text="Info", padx=8, pady=8)
        self.frame_info.grid(row=0, column=1, sticky="n", padx=5, pady=10)
        self.frame_info.config(width=380, height=512)
        self.frame_info.grid_propagate(False)
        self.frame_info.pack_propagate(False)

        self.label_fps = tk.Label(self.frame_info, text="FPS: 0", font=self.font_label, fg="darkgreen")
        self.label_fps.pack(anchor="w", pady=(0, 2))

        self.label_cnt_face = tk.Label(self.frame_info, text="Faces in current frame: 0", font=self.font_label)
        self.label_cnt_face.pack(anchor="w", pady=(0, 2))

        self.label_cnt_db = tk.Label(self.frame_info, text="Faces in database: 0", font=self.font_label)
        self.label_cnt_db.pack(anchor="w", pady=(0, 10))

        self.label_warning = tk.Label(self.frame_info, text="", font=self.font_label, fg='red')
        self.label_warning.pack(anchor="w", pady=(0, 10))

        self.frame_input = LabelFrame(self.frame_info, text="Enter Name", padx=5, pady=5, font=self.font_label)
        self.frame_input.pack(anchor="w", fill="x", pady=5)

        self.entry_name = tk.Entry(self.frame_input, font=self.font_label)
        self.entry_name.pack(fill="x", pady=5)

        self.btn_create_folder = tk.Button(self.frame_input, text="Create Folder", font=self.font_label, command=self.get_input_name)
        self.btn_create_folder.pack(pady=(0, 5))

        self.btn_add_face = tk.Button(
            self.frame_info,
            text="Add Face",
            font=self.font_label,
            command=self.save_current_face
        )
        self.btn_add_face.pack(fill="x", pady=10)

        self.label_log = tk.Label(self.frame_info, text="", wraplength=300, justify="left", font=self.font_label)
        self.label_log.pack(anchor="w", pady=(10, 0))

        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self.frame_start_time = time.time()

        self.prep_dirs()
        self.check_existing_faces_cnt()

    def prep_dirs(self):
        if not os.path.exists(config.KNOWN_FACES_DIR):
            os.makedirs(config.KNOWN_FACES_DIR)

    def check_existing_faces_cnt(self):
        folders = os.listdir(config.KNOWN_FACES_DIR)
        numbers = [int(''.join(filter(str.isdigit, f))) for f in folders if any(char.isdigit() for char in f)]
        self.existing_faces_cnt = max(numbers) if numbers else 0
        self.label_cnt_db.config(text=f"Faces in database: {self.existing_faces_cnt}")

    def get_input_name(self):
        self.input_name_char = self.entry_name.get().strip()
        if self.input_name_char:
            self.existing_faces_cnt += 1
            folder_name = f"person{self.existing_faces_cnt}_{self.input_name_char}"
            self.current_face_dir = os.path.join(config.KNOWN_FACES_DIR, folder_name)
            os.makedirs(self.current_face_dir, exist_ok=True)
            self.label_log.config(text=f"CREATED: {self.current_face_dir.upper()}", fg="green")
            self.face_folder_created_flag = True
            self.ss_cnt = 0
        else:
            self.label_log.config(text="Name cannot be empty!", fg="red")

    def update_fps(self):
        now = time.time()
        fps = 1.0 / (now - self.frame_start_time)
        self.frame_start_time = now
        self.label_fps.config(text=f"FPS: {round(fps, 2)}")

    def save_current_face(self):
        if not self.face_folder_created_flag:
            self.label_log.config(text="Please create a folder first!", fg="red")
            return
        if self.current_frame_faces_cnt != 1:
            self.label_log.config(text="No face or multiple faces detected!", fg="red")
            return
        if self.out_of_range_flag:
            self.label_log.config(text="Face is out of range.", fg="red")
            return

        self.ss_cnt += 1
        roi = self.current_frame[
            self.face_ROI_height_start - self.hh:self.face_ROI_height_start + self.hh,
            self.face_ROI_width_start - self.ww:self.face_ROI_width_start + self.ww
        ]
        face_path = os.path.join(self.current_face_dir, f"face_{self.ss_cnt}.jpg")
        cv2.imwrite(face_path, cv2.cvtColor(roi, cv2.COLOR_RGB2BGR))
        self.label_log.config(text=f"SAVED: {face_path.upper()}", wraplength=300, justify="left", fg="green")

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return cv2.resize(frame, (640, 480))
        return None

    def detect_and_display(self):
        frame = self.get_frame()
        if frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = detector(frame)
        self.current_frame_faces_cnt = len(faces)
        self.label_cnt_face.config(text=f"Faces in current frame: {len(faces)}")

        for d in faces:
            self.face_ROI_width_start = d.left()
            self.face_ROI_height_start = d.top()
            self.face_ROI_width = d.right() - d.left()
            self.face_ROI_height = d.bottom() - d.top()
            self.hh = self.face_ROI_height // 2
            self.ww = self.face_ROI_width // 2

            out_of_bounds = (
                d.right() + self.ww > 640 or d.bottom() + self.hh > 480 or
                d.left() - self.ww < 0 or d.top() - self.hh < 0
            )

            self.out_of_range_flag = out_of_bounds
            if out_of_bounds:
                self.label_warning.config(text="OUT OF RANGE")
                color = (255, 0, 0)
            else:
                self.label_warning.config(text="")
                color = (255, 255, 255)

            cv2.rectangle(
                frame,
                (d.left() - self.ww, d.top() - self.hh),
                (d.right() + self.ww, d.bottom() + self.hh),
                color,
                2
            )

        self.current_frame = frame
        self.update_fps()
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(frame))
        self.label_img.imgtk = imgtk
        self.label_img.configure(image=imgtk)
        self.win.after(20, self.detect_and_display)

    def run(self):
        self.detect_and_display()
        self.win.mainloop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    FaceRegister().run()
