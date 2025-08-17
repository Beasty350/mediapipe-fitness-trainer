import cv2
import csv
import datetime
import os
import numpy as np
from utils.functions import *
from utils.feedback import *
from utils.gui import *
import mediapipe as mp
import json
import time

mp_drawing = mp.solutions.drawing_utils

class Logger:
    def __init__(self):
        self.log_file = None
        self.csv_writer = None
        self.start_time = None
        self.headers = []

    def start(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = open(f"logs//log_{timestamp}.csv", "w", newline='')
        self.csv_writer = csv.writer(self.log_file)
        
        self.headers = [
            "timestamp", "exercise", "raw_rep_count", "correct_rep_count", "gender",
            "avg_fps", "feedback_summary",
            "Hull Score", "Wrist Distance Score",
            "Static Angle Score (Avg)", "Dynamic Angle Score (Avg)"
        ]
        self.csv_writer.writerow(self.headers)
        self.start_time = datetime.datetime.now()
        print("Started logging to CSV")

    def log(self, exercise, raw_rep_count, correct_rep_count, gender, rep_summary):
        if not self.csv_writer: return

        timestamp = (datetime.datetime.now() - self.start_time).total_seconds()
        
        scores = rep_summary.get('scores', {})
        hull_score = scores.get("Hull Score", "")
        wrist_score = scores.get("Wrist Distance Score", "")

        static_scores = scores.get("Static Angle Score", {})
        static_avg = np.mean(list(static_scores.values())) if static_scores else ""

        dynamic_scores = scores.get("Dynamic Angle Score", {})
        dynamic_avg = np.mean(list(dynamic_scores.values())) if dynamic_scores else ""

        self.csv_writer.writerow([
            f"{timestamp:.3f}", exercise, raw_rep_count, correct_rep_count, gender,
            rep_summary.get('fps', 0), rep_summary.get('feedback', ''),
            hull_score, wrist_score, static_avg, dynamic_avg
        ])

    def stop(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
            self.csv_writer = None
            print("Stopped logging")

class Recorder:
    def __init__(self):
        self.video_writer = None
        self.filename = None

    def start(self, frame):
        if frame is None or frame.shape[0] == 0 or frame.shape[1] == 0:
            print("❌ Cannot start recording: invalid frame.")
            return
        height, width = frame.shape[:2]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f"recordings//recording_{timestamp}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.video_writer = cv2.VideoWriter(self.filename, fourcc, 20.0, (width, height))
        if not self.video_writer.isOpened():
            print("❌ VideoWriter failed to open."); self.video_writer = None
        else:
            print(f"✅ Recording started: {self.filename}")

    def record_frame(self, frame):
        if self.video_writer and frame is not None:
            self.video_writer.write(frame)

    def stop(self):
        if self.video_writer:
            self.video_writer.release()
            print(f"✅ Recording saved: {self.filename}")
            self.video_writer = None

def setup_directories():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("recordings", exist_ok=True)
    
def run_main_loop(gui, pose, mp_pose, counter, logger, recorder, reference_data, exercise_counters, webcam_url, default_webcam):
    last_rep_score = {}
    cap = None
    current_source = None

    def loop():
        nonlocal last_rep_score, cap, current_source
        start_time = time.time()

        # Video Source Management
        source_changed = current_source != gui.source_type
        if gui.is_running and (cap is None or not cap.isOpened() or source_changed):
            if cap: cap.release()
            if gui.source_type == 'video':
                cap = cv2.VideoCapture(gui.video_path)
                current_source = 'video'
                if not gui.video_path or not cap.isOpened():
                    print(f"Error opening video: {gui.video_path}"); gui.toggle()
            else:
                cap = cv2.VideoCapture(webcam_url)
                if not cap.isOpened():
                    print(f"IP Cam failed. Trying default."); cap = cv2.VideoCapture(default_webcam)
                    if not cap.isOpened(): print("Webcam failed."); gui.toggle()
                current_source = 'webcam'

        if not gui.is_running:
            if cap: cap.release(); cap = None; current_source = None
            if logger.log_file: logger.stop()
            if recorder.video_writer: recorder.stop()
            black = np.zeros((480, 640, 3), dtype=np.uint8)
            gui.update_frames(black, black)
            return gui.root.after(10, loop)

        if not cap or not cap.isOpened(): return gui.root.after(10, loop)

        ret, frame = cap.read()
        if not ret:
            if gui.source_type == 'video': print("Video finished."); gui.toggle(); gui.use_webcam()
            return gui.root.after(10, loop)

        image = cv2.resize(frame, (640, 480))
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        current_exercise, stage_r, stage_l, raw_reps = "-", "-", "-", 0
        display_frame, feedback_frame = image.copy(), np.zeros_like(image)

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            norm = normalize_by_least_squares(lm)

            joint_angles = {
                "knee_r": angle_from_ids(24, 26, 28, lm), "knee_l": angle_from_ids(23, 25, 27, lm),
                "hip_r": angle_from_ids(12, 24, 26, lm), "hip_l": angle_from_ids(11, 23, 25, lm),
                "shoulder_r": angle_from_ids(14, 12, 24, lm), "shoulder_l": angle_from_ids(13, 11, 23, lm),
            }
            elbow_r = calculate_angle((norm[12]), (norm[14]), (norm[16]))
            shoulder_r = calculate_angle((norm[14]), (norm[12]), (norm[24]))
            elbow_l = calculate_angle((norm[11]), (norm[13]), (norm[15]))
            shoulder_l = calculate_angle((norm[13]), (norm[11]), (norm[23]))
            
            dynamic_angles = (elbow_r, elbow_l, shoulder_r, shoulder_l)
            counter.update_angles(*dynamic_angles)
            current_exercise = counter.detect_exercise(shoulder_r, shoulder_l, reference_data)
            
            gender_thresholds = reference_data.get(current_exercise, {}).get(gui.gender, {})
            dynamic_thresholds = reference_data.get(current_exercise, {}).get("dynamic_angles", {})
            static_tolerance = reference_data.get("global_config", {}).get("static_angle_tolerance", 12)

            wrist_dist = compute_distance(norm[15], norm[16])
            hull_area = compute_convex_hull_area(norm)

            feedback_lines = generate_feedback(current_exercise, dynamic_angles, gender_thresholds, joint_angles, wrist_dist, hull_area, static_tolerance)
            visual_dynamic, log_dynamic = get_dynamic_feedback_lines(current_exercise, dynamic_angles, dynamic_thresholds)
            violations = check_dynamic_angle_violations(current_exercise, dynamic_angles, dynamic_thresholds)
            
            feedback_text_list = [item[0] if isinstance(item, tuple) else item for item in feedback_lines] + log_dynamic
            
            stage_r, stage_l, completed, rep_summary = counter.count_repetitions(dynamic_angles, wrist_dist, hull_area, reference_data, gender_thresholds, joint_angles, feedback_text_list, time.time() - start_time)
            raw_reps = counter.get_raw_reps(current_exercise)

            if rep_summary:
                last_rep_score = rep_summary.get('scores', {})
                if gui.is_logging:
                    if not logger.log_file: logger.start()
                    correct_reps = exercise_counters.get(current_exercise, 0) + (1 if completed else 0)
                    logger.log(current_exercise, raw_reps, correct_reps, gui.gender, rep_summary)
            
            if completed and current_exercise in exercise_counters:
                exercise_counters[current_exercise] += 1
            
            if gui.is_logging:
                if not recorder.video_writer: recorder.start(display_frame)
                recorder.record_frame(image)
            elif recorder.video_writer: recorder.stop()

            # Drawing and Display
            insert_idx = next((i + 1 for i, item in enumerate(feedback_lines) if "Wrist Distance" in (item[0] if isinstance(item, tuple) else item)), len(feedback_lines))
            feedback_lines[insert_idx:insert_idx] = visual_dynamic
            
            if gender_thresholds:
                feedback = check_static_angles(joint_angles, gender_thresholds.get("static_angles", {}), static_tolerance)
                highlight_problematic_keypoints(display_frame, results.pose_landmarks, feedback, current_exercise)
            for idx in violations:
                if idx < len(lm): cv2.circle(display_frame, (int(lm[idx].x * 640), int(lm[idx].y * 480)), 10, (0, 0, 255), -1)

            display_feedback_with_colors(feedback_frame, feedback_lines)
            display_scores_on_frame(feedback_frame, last_rep_score)

            scaled_points = np.array([ (int(p.x * image.shape[1]), int(p.y * image.shape[0])) for p in lm ], dtype=np.int32)
            if len(scaled_points) >= 3:
                hull = cv2.convexHull(scaled_points)
                cv2.polylines(display_frame, [hull], True, (0, 255, 0), 2)

        mp_drawing.draw_landmarks(display_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        gui.update_frames(display_frame, feedback_frame)
        gui.update_info(current_exercise, exercise_counters["hammer_curl"], exercise_counters["overhead_press"], stage_r, stage_l, raw_reps)
        gui.root.after(10, loop)

    loop()