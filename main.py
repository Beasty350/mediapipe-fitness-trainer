import tkinter as tk
import cv2
import mediapipe as mp
import json
from utils.utils import *
from utils.repetition import *
from utils.functions import *
from utils.gui import *

# Setup
setup_directories()
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)
counter = RepetitionCounter()
logger = Logger()
recorder = Recorder()

# Define video source constants but do not initialize VideoCapture here
IP_ADDRESS = "192.168.1.141"
WEBCAM_URL = f"http://{IP_ADDRESS}:4747/mjpegfeed?640x480"
DEFAULT_WEBCAM = 0  # Use 0 for the default built-in webcam

# Load thresholds
with open("txt//thresholds.json", "r") as f:
    reference_data = json.load(f)

exercise_counters = {"hammer_curl": 0, "overhead_press": 0}

# Launch GUI
root = tk.Tk()
gui = GUI(root, exercise_counters, counter)

# Pass webcam source info to the main loop; it will handle the source switching
run_main_loop(gui, pose, mp_pose, counter, logger, recorder, reference_data, exercise_counters, WEBCAM_URL, DEFAULT_WEBCAM)

try:
    root.mainloop()
finally:
    logger.stop()
    recorder.stop()
    cv2.destroyAllWindows()