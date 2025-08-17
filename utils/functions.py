import cv2
import numpy as np
import math
from collections import deque
import copy

def in_range(val, low, high):
    return low <= val <= high

def in_any_range(val, ranges):
    return any(low <= val <= high for (low, high) in ranges)

def classify_stage_by_proximity(val, up_range, down_range):
    up_center = sum(up_range) / 2
    down_center = sum(down_range) / 2
    return "up" if abs(val - up_center) < abs(val - down_center) else "down"

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180 else angle

def normalize_by_least_squares(landmarks):
    indices = [11, 12, 23, 24]
    pts = np.array([[landmarks[i].x, landmarks[i].y] for i in indices])
    X = pts[:, 0].reshape(-1, 1)
    Y = pts[:, 1]
    X_aug = np.hstack([X, np.ones_like(X)])
    m, c = np.linalg.lstsq(X_aug, Y, rcond=None)[0]
    theta = math.atan(m)
    cos_t, sin_t = math.cos(-theta), math.sin(-theta)
    mid_hip = np.mean([[landmarks[23].x, landmarks[23].y], [landmarks[24].x, landmarks[24].y]], axis=0)
    normalized = []
    for lm in landmarks:
        x, y = lm.x - mid_hip[0], lm.y - mid_hip[1]
        x_rot = x * cos_t - y * sin_t
        y_rot = x * sin_t + y * cos_t
        normalized.append((x_rot, y_rot))
    return normalized

def compute_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def compute_convex_hull_area(normalized_landmarks):
    points = np.array(normalized_landmarks, dtype=np.float32)
    hull = cv2.convexHull(points)
    return cv2.contourArea(hull)

def detect_stage(angle, up_range, down_range):
    if in_range(angle, *down_range): return "down"
    elif in_range(angle, *up_range): return "up"
    return None

def _calculate_containment_score(user_range, ref_range):
    if not user_range or not ref_range: return 0.0
    user_min, user_max = user_range
    ref_min, ref_max = ref_range
    if user_min == user_max: return 1.0 if ref_min <= user_min <= ref_max else 0.0
    user_length = user_max - user_min
    if user_length <= 0: return 1.0
    intersection_min = max(user_min, ref_min)
    intersection_max = min(user_max, ref_max)
    intersection_length = max(0, intersection_max - intersection_min)
    return intersection_length / user_length

def _calculate_dynamic_angle_score(rep_data, ref_dynamic_thresholds, relevant_joints, buffer):
    joint_scores = {}
    for joint in relevant_joints:
        joint_base_name = joint.split('_')[0] 
        for stage in ['up', 'down']:
            user_angles = rep_data.get(joint, {}).get(stage)
            score_key = f"{joint}_{stage}"
            if user_angles:
                user_min, user_max = (min(user_angles), max(user_angles))
                ref_key = f"{joint_base_name}_{stage}"
                ref_min, ref_max = ref_dynamic_thresholds.get(ref_key, (0,0))
                
                out_of_bounds_low = max(0, ref_min - user_min)
                out_of_bounds_high = max(0, user_max - ref_max)
                penalty_low = max(0, out_of_bounds_low - buffer)
                penalty_high = max(0, out_of_bounds_high - buffer)
                total_penalty = penalty_low + penalty_high
                user_length = user_max - user_min

                score = 1.0 if ref_min <= user_min <= ref_max else max(0, (user_length - total_penalty) / user_length) if user_length > 0 else 0.0
                joint_scores[score_key] = score * 100
    return joint_scores

def _calculate_wrist_distance_score(user_wrist_dist_values, ref_wrist_dist_range):
    if not user_wrist_dist_values or not ref_wrist_dist_range: return 0.0
    user_range = (min(user_wrist_dist_values), max(user_wrist_dist_values))
    return _calculate_containment_score(user_range, ref_wrist_dist_range)

def _calculate_static_angle_score(user_static_angles, ref_static_angles, tolerance):
    joint_scores = {}
    for joint, ref_angle in ref_static_angles.items():
        user_angles = user_static_angles.get(joint)
        if user_angles:
            user_range = (min(user_angles), max(user_angles))
            score = _calculate_containment_score(user_range, (ref_angle, ref_angle + tolerance))
            joint_scores[joint] = score * 100
    return joint_scores

def calculate_repetition_score(rep_data, ref_static_thresholds, ref_dynamic_thresholds, current_exercise, global_config):
    # Get config values with defaults
    static_tolerance = global_config.get("static_angle_tolerance", 12)
    dynamic_buffer = global_config.get("dynamic_angle_buffer", 10)

    # 1. Convex Hull Score
    hull_scores = []
    for stage in ['up', 'down']:
        user_hull_values = rep_data['hull_area'][stage]
        if user_hull_values:
            user_range = (min(user_hull_values), max(user_hull_values))
            ref_range = ref_static_thresholds.get('convex_hull', {}).get(stage)
            if ref_range: hull_scores.append(_calculate_containment_score(user_range, ref_range))
    avg_hull_score = np.mean(hull_scores) if hull_scores else 0.0

    # 2. Dynamic Angle Score
    exercise_joints_map = {
        "hammer_curl": ["elbow_r", "elbow_l"],
        "overhead_press": ["elbow_r", "elbow_l", "shoulder_r", "shoulder_l"]
    }
    relevant_joints = exercise_joints_map.get(current_exercise, [])
    dynamic_angle_scores = _calculate_dynamic_angle_score(rep_data, ref_dynamic_thresholds, relevant_joints, dynamic_buffer)
    
    # 3. Static Angle Score
    ref_static_angles = ref_static_thresholds.get("static_angles", {})
    static_angle_scores = _calculate_static_angle_score(rep_data.get('static_angles', {}), ref_static_angles, static_tolerance)

    # 4. Wrist Distance Score
    ref_wrist_range = ref_static_thresholds.get('wrist_distance')
    wrist_score = _calculate_wrist_distance_score(rep_data.get('wrist_dist', []), ref_wrist_range)
    
    return {
        "Hull Score": avg_hull_score * 100,
        "Dynamic Angle Score": dynamic_angle_scores,
        "Static Angle Score": static_angle_scores,
        "Wrist Distance Score": wrist_score * 100,
    }

def check_static_angles(current_angles, reference_angles, tolerance):
    feedback = {}
    for joint, ref_val in reference_angles.items():
        cur_val = current_angles.get(joint)
        if cur_val is not None:
            ok = ref_val <= cur_val <= ref_val + tolerance
            feedback[joint] = (ok, cur_val, ref_val)
    return feedback

def display_feedback_with_colors(feedback_frame, feedback_lines):
    for i, item in enumerate(feedback_lines):
        line, color = item if isinstance(item, tuple) else (item, (0, 255, 0))
        if "ADJUST" in line or "REMAIN" in line or "outside" in line.lower():
            color = (0, 0, 255)
        cv2.putText(feedback_frame, line, (10, 30 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

def highlight_problematic_keypoints(image, landmarks, feedback, current_exercise):
    joint_map = {
        "hammer_curl": {"shoulder_r": [12], "shoulder_l": [11], "knee_r": [26], "knee_l": [25], "hip_r": [24], "hip_l": [23]},
        "overhead_press": {"knee_r": [26], "knee_l": [25], "hip_r": [24], "hip_l": [23]}
    }
    landmarks_to_highlight = {idx for joint, (ok, _, _) in feedback.items() if not ok for idx in joint_map.get(current_exercise, {}).get(joint, [])}
    
    for idx in landmarks_to_highlight:
        lm = landmarks.landmark[idx]
        h, w, _ = image.shape
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(image, (cx, cy), 10, (0, 0, 255), -1)
            
def angle_from_ids(a, b, c, landmarks):
    return calculate_angle((landmarks[a].x, landmarks[a].y), (landmarks[b].x, landmarks[b].y), (landmarks[c].x, landmarks[c].y))

def display_scores_on_frame(frame, scores):
    if not scores or not isinstance(scores, dict): return
    y_pos = 360
    cv2.putText(frame, "Last Rep Scores:", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
    
    for key, value in scores.items():
        if value is None: continue
        y_pos += 25
        display_value = np.mean(list(value.values())) if isinstance(value, dict) and value else value if not isinstance(value, dict) else 0
        line = f"  {key}: {display_value:.1f}"
        cv2.putText(frame, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)