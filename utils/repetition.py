from utils.functions import *
from collections import deque
import numpy as np

class RepetitionCounter:
    def __init__(self):
        from collections import deque
        self.elbow_hist_r = deque(maxlen=15)
        self.elbow_hist_l = deque(maxlen=15)
        self.shoulder_hist_r = deque(maxlen=15)
        self.shoulder_hist_l = deque(maxlen=15)

        self.stage_right = None
        self.stage_left = None
        self.current_exercise = "unknown"

        self.right_phase = "idle"
        self.left_phase = "idle"
        self.hull_phase = "idle"  # can be 'down', 'up', or 'idle'

        self.raw_reps = {
            "hammer_curl": 0,
            "overhead_press": 0
        }
        self.raw_right_phase = "idle"
        self.raw_left_phase = "idle"

        self.bad_frame_count_r = 0
        self.bad_frame_count_l = 0

        # New attributes for scoring
        self.last_score = {}
        self.rep_data = self._reset_rep_data()
        self.all_scores = []

    def _reset_rep_data(self):
        """Resets the data collector for a new repetition."""
        return {
            'elbow_r': {'up': [], 'down': []}, 'elbow_l': {'up': [], 'down': []},
            'shoulder_r': {'up': [], 'down': []}, 'shoulder_l': {'up': [], 'down': []},
            'hull_area': {'up': [], 'down': []},
            'wrist_dist': [],
            'static_angles': {
                'knee_r': [], 'knee_l': [],
                'hip_r': [], 'hip_l': [],
                'shoulder_r': [], 'shoulder_l': []
            },
            'feedback': [],
            'frame_times': []
        }

    def reset_summary(self):
        """Clears the summary data."""
        self.all_scores = []

    def detect_exercise(self, shoulder_r, shoulder_l, all_thresholds):
        avg_sr = sum(self.shoulder_hist_r) / len(self.shoulder_hist_r) if self.shoulder_hist_r else 0
        avg_sl = sum(self.shoulder_hist_l) / len(self.shoulder_hist_l) if self.shoulder_hist_l else 0

        hc_detect = all_thresholds.get("hammer_curl", {}).get("detection", {})
        op_detect = all_thresholds.get("overhead_press", {}).get("detection", {})

        if hc_detect and in_range(avg_sr, *hc_detect["shoulder_static"]) and \
           in_range(avg_sl, *hc_detect["shoulder_static"]):
            self.current_exercise = "hammer_curl"
        elif op_detect and in_range(avg_sr, *op_detect["shoulder_down"]) and \
             in_range(avg_sl, *op_detect["shoulder_down"]):
            self.current_exercise = "overhead_press"
        else:
            self.current_exercise = "unknown"
        return self.current_exercise

    def update_angles(self, elbow_r, elbow_l, shoulder_r, shoulder_l):
        self.elbow_hist_r.append(elbow_r)
        self.shoulder_hist_r.append(shoulder_r)
        self.elbow_hist_l.append(elbow_l)
        self.shoulder_hist_l.append(shoulder_l)
    
    def get_raw_reps(self, exercise_name):
        return self.raw_reps.get(exercise_name, 0)

    def count_repetitions(self, angles, wrist_dist, hull_area, all_thresholds, gender_thresholds, joint_angles, feedback_list, frame_time):
        
        elbow_r, elbow_l, shoulder_r, shoulder_l = angles
        stage_r, stage_l = None, None
        completed = False
        rep_summary = {}

        # Load dynamic thresholds for the current exercise
        exercise_thresholds = all_thresholds.get(self.current_exercise, {})
        dynamic_thresholds = exercise_thresholds.get("dynamic_angles", {})
        if not dynamic_thresholds:
             return self.stage_right, self.stage_left, completed, rep_summary
        
        static_tolerance = all_thresholds.get("global_config", {}).get("static_angle_tolerance", 12)

        # --- NEW: Strict validation for all parameters ---
        wrist_ok = False
        static_ok = False
        if gender_thresholds:
            # Check wrist distance
            wrist_range = gender_thresholds.get("wrist_distance")
            if wrist_range:
                wrist_ok = in_range(wrist_dist, *wrist_range)
            
            # Check static angles
            ref_static_angles = gender_thresholds.get("static_angles", {})
            static_feedback = check_static_angles(joint_angles, ref_static_angles, static_tolerance)
            static_ok = all(item[0] for item in static_feedback.values()) if static_feedback else True

        frame_is_valid = wrist_ok and static_ok

        if self.current_exercise == "hammer_curl":
            elbow_stage_r_hc = detect_stage(elbow_r, dynamic_thresholds["elbow_up"], dynamic_thresholds["elbow_down"])
            elbow_stage_l_hc = detect_stage(elbow_l, dynamic_thresholds["elbow_up"], dynamic_thresholds["elbow_down"])
            shoulder_stage_r_hc = detect_stage(shoulder_r, dynamic_thresholds["shoulder_up"], dynamic_thresholds["shoulder_down"])
            shoulder_stage_l_hc = detect_stage(shoulder_l, dynamic_thresholds["shoulder_up"], dynamic_thresholds["shoulder_down"])
            
            ch_thresholds = gender_thresholds.get("convex_hull", {})
            if not hasattr(self, 'hull_phase'): self.hull_phase = "idle"
            if ch_thresholds and in_range(hull_area, *ch_thresholds.get("down", (0, 0))): self.hull_phase = "down"
            elif self.hull_phase == "down" and ch_thresholds and in_range(hull_area, *ch_thresholds.get("up", (0, float("inf")))): self.hull_phase = "up"
            
            stage_r = "up" if elbow_stage_r_hc == "up" or shoulder_stage_r_hc == "up" else "down" if elbow_stage_r_hc == "down" and shoulder_stage_r_hc == "down" else None
            stage_l = "up" if elbow_stage_l_hc == "up" or shoulder_stage_l_hc == "up" else "down" if elbow_stage_l_hc == "down" and shoulder_stage_l_hc == "down" else None

        elif self.current_exercise == "overhead_press":
            shoulder_stage_r_ov = detect_stage(shoulder_r, dynamic_thresholds["shoulder_up"], dynamic_thresholds["shoulder_down"])
            shoulder_stage_l_ov = detect_stage(shoulder_l, dynamic_thresholds["shoulder_up"], dynamic_thresholds["shoulder_down"])
            elbow_stage_r_ov = detect_stage(elbow_r, dynamic_thresholds["elbow_up"], dynamic_thresholds["elbow_down"])
            elbow_stage_l_ov = detect_stage(elbow_l, dynamic_thresholds["elbow_up"], dynamic_thresholds["elbow_down"])

            ch_thresholds = gender_thresholds.get("convex_hull", {})
            if not hasattr(self, 'hull_phase'): self.hull_phase = "idle"
            if ch_thresholds and in_range(hull_area, *ch_thresholds.get("down", (0, 0))): self.hull_phase = "down"
            elif self.hull_phase == "down" and ch_thresholds and in_range(hull_area, *ch_thresholds.get("up", (0, float("inf")))): self.hull_phase = "up"
            
            stage_r = shoulder_stage_r_ov if shoulder_stage_r_ov == elbow_stage_r_ov and shoulder_stage_r_ov is not None else None
            stage_l = shoulder_stage_l_ov if shoulder_stage_l_ov == elbow_stage_l_ov and shoulder_stage_l_ov is not None else None
        else:
            stage_r = stage_l = None

        current_stage = self.stage_right
        if current_stage in ['up', 'down']:
            self.rep_data['elbow_r'][current_stage].append(elbow_r)
            self.rep_data['elbow_l'][current_stage].append(elbow_l)
            self.rep_data['shoulder_r'][current_stage].append(shoulder_r)
            self.rep_data['shoulder_l'][current_stage].append(shoulder_l)
            self.rep_data['hull_area'][current_stage].append(hull_area)
            self.rep_data['wrist_dist'].append(wrist_dist)
            self.rep_data['feedback'].extend(feedback_list)
            self.rep_data['frame_times'].append(frame_time)
            
            for joint, angle in joint_angles.items():
                if joint in self.rep_data['static_angles']:
                    if 'shoulder' in joint:
                        if self.current_exercise == 'hammer_curl':
                            self.rep_data['static_angles'][joint].append(angle)
                    else:
                        self.rep_data['static_angles'][joint].append(angle)
        
        bad_frame_max = all_thresholds.get("global_config", {}).get("bad_frame_tolerance", 5)

        if stage_r:
            self.stage_right = stage_r
            self.bad_frame_count_r = 0
        else:
            self.bad_frame_count_r += 1
            if self.bad_frame_count_r < bad_frame_max: stage_r = self.stage_right
            else: self.stage_right = None

        if stage_l:
            self.stage_left = stage_l
            self.bad_frame_count_l = 0
        else:
            self.bad_frame_count_l += 1
            if self.bad_frame_count_l < bad_frame_max: stage_l = self.stage_left
            else: self.stage_left = None

        # --- MODIFIED STATE MACHINE (Strict) ---
        if frame_is_valid:
            if self.current_exercise in ["overhead_press", "hammer_curl"]:
                if self.right_phase == "idle" and self.stage_right == "down" and self.hull_phase == "down": self.right_phase = "down_prep"
                elif self.right_phase == "down_prep" and self.stage_right == "up" and self.hull_phase == "up": self.right_phase = "up"
                elif self.right_phase == "up" and self.stage_right == "down" and self.hull_phase == "down": self.right_phase = "done"

                if self.left_phase == "idle" and self.stage_left == "down" and self.hull_phase == "down": self.left_phase = "down_prep"
                elif self.left_phase == "down_prep" and self.stage_left == "up" and self.hull_phase == "up": self.left_phase = "up"
                elif self.left_phase == "up" and self.stage_left == "down" and self.hull_phase == "down": self.left_phase = "done"

                if self.right_phase == "done" and self.left_phase == "done":
                    completed = True
                    self.right_phase, self.left_phase = "idle", "idle"
        
        if self.current_exercise in self.raw_reps:
            if self.raw_right_phase == "idle" and self.stage_right == "down": self.raw_right_phase = "down_prep"
            elif self.raw_right_phase == "down_prep" and self.stage_right == "up": self.raw_right_phase = "up"
            elif self.raw_right_phase == "up" and self.stage_right == "down": self.raw_right_phase = "done"

            if self.raw_left_phase == "idle" and self.stage_left == "down": self.raw_left_phase = "down_prep"
            elif self.raw_left_phase == "down_prep" and self.stage_left == "up": self.raw_left_phase = "up"
            elif self.raw_left_phase == "up" and self.stage_left == "down": self.raw_left_phase = "done"

            if self.raw_right_phase == "done" and self.raw_left_phase == "done":
                self.raw_reps[self.current_exercise] += 1
                
                if gender_thresholds:
                    self.last_score = calculate_repetition_score(
                        self.rep_data, gender_thresholds, dynamic_thresholds, self.current_exercise, all_thresholds.get("global_config", {})
                    )
                    self.all_scores.append({'exercise': self.current_exercise, 'scores': self.last_score})

                    problem_keypoints = {msg.split(':')[0].strip() for msg in self.rep_data.get('feedback', []) if "ADJUST" in msg or "REMAIN" in msg}
                    feedback_str = "; ".join(sorted(list(problem_keypoints)))
                    
                    frame_times = self.rep_data.get('frame_times', [])
                    avg_fps = (1 / np.mean(frame_times)) if frame_times and np.mean(frame_times) > 0 else 0
                    
                    rep_summary = {'scores': self.last_score, 'feedback': feedback_str, 'fps': avg_fps}
                    self.rep_data = self._reset_rep_data()

                self.raw_right_phase, self.raw_left_phase = "idle", "idle"

        return self.stage_right, self.stage_left, completed, rep_summary