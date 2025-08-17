from utils.functions import *

def check_dynamic_angle_violations(current_exercise, angles, dynamic_thresholds):
    elbow_r, elbow_l, shoulder_r, shoulder_l = angles
    violations = []

    def outside_all(val, ranges):
        return not any(low <= val <= high for (low, high) in ranges)

    if not dynamic_thresholds:
        return violations

    if current_exercise == "hammer_curl":
        elbow_ranges = [dynamic_thresholds.get("elbow_up", (0,0)), dynamic_thresholds.get("elbow_down", (0,0))]
        shoulder_ranges = [dynamic_thresholds.get("shoulder_up", (0,0)), dynamic_thresholds.get("shoulder_down", (0,0))]

    elif current_exercise == "overhead_press":
        elbow_ranges = [dynamic_thresholds.get("elbow_up", (0,0)), dynamic_thresholds.get("elbow_down", (0,0))]
        shoulder_ranges = [dynamic_thresholds.get("shoulder_up", (0,0)), dynamic_thresholds.get("shoulder_down", (0,0))]
    else:
        return violations

    if outside_all(elbow_r, elbow_ranges): violations.append(14)  # Right elbow
    if outside_all(elbow_l, elbow_ranges): violations.append(13)  # Left elbow
    if outside_all(shoulder_r, shoulder_ranges): violations.append(12)  # Right shoulder
    if outside_all(shoulder_l, shoulder_ranges): violations.append(11)  # Left shoulder
        
    return violations

def generate_feedback(current_exercise, angles, gender_thresholds, joint_angles, wrist_dist, hull_area, static_tolerance):
    elbow_r, elbow_l, shoulder_r, shoulder_l = angles
    feedback_lines = []
    
    # Static angle feedback
    if gender_thresholds:
        ref_angles = gender_thresholds.get("static_angles", {})
        feedback = check_static_angles(joint_angles, ref_angles, static_tolerance)
        
        for joint, (ok, cur_val, ref_val) in feedback.items():
            text = f"{joint}: {cur_val:.1f}deg (ref: {ref_val:.1f}) {'OK' if ok else 'REMAIN STATIONARY'}"
            feedback_lines.append(text)
    
    if current_exercise in ["hammer_curl", "overhead_press"]:
        if gender_thresholds:
            wrist_ok = in_range(wrist_dist, *gender_thresholds.get("wrist_distance", (0.0, 1.0)))
            feedback_lines.append(f"Wrist Distance: {wrist_dist:.3f} in range {'OK' if wrist_ok else 'ADJUST WRIST'}")
            
    # Convex hull feedback
    if gender_thresholds and 'convex_hull' in gender_thresholds:
        convex_hull_thresholds = gender_thresholds['convex_hull']
        if 'up' in convex_hull_thresholds and 'down' in convex_hull_thresholds:
            up_low, up_high = convex_hull_thresholds["up"]
            down_low, down_high = convex_hull_thresholds["down"]

            dist_up = abs(hull_area - (up_low + up_high) / 2)
            dist_down = abs(hull_area - (down_low + down_high) / 2)
            
            stage_label, (low, high) = ("up", (up_low, up_high)) if dist_up < dist_down else ("down", (down_low, down_high))

            convex_ok = in_range(hull_area, low, high)
            msg = f"Convex Hull (~{stage_label}): {hull_area:.6f} in range [{low}, {high}] {'OK' if convex_ok else 'ADJUST DISTANCE'}"
            color = (0, 255, 0) if convex_ok else (0, 0, 255)
        else:
            msg = f"Convex Hull: {hull_area:.6f} - Thresholds missing"; color = (0, 0, 255)
    else:
        msg = f"Convex Hull: {hull_area:.6f} - No thresholds set"; color = (0, 0, 255)

    feedback_lines.append((msg, color))
    return feedback_lines

def get_dynamic_feedback_lines(current_exercise, angles, dynamic_thresholds):
    elbow_r, elbow_l, shoulder_r, shoulder_l = angles
    visual_lines, log_lines = [], []
    
    if not dynamic_thresholds:
        return visual_lines, log_lines

    joint_data_map = {
        "hammer_curl": [
            ("Right Elbow", elbow_r, [dynamic_thresholds.get("elbow_up"), dynamic_thresholds.get("elbow_down")]),
            ("Left Elbow", elbow_l, [dynamic_thresholds.get("elbow_up"), dynamic_thresholds.get("elbow_down")]),
        ],
        "overhead_press": [
            ("Right Elbow", elbow_r, [dynamic_thresholds.get("elbow_up"), dynamic_thresholds.get("elbow_down")]),
            ("Left Elbow", elbow_l, [dynamic_thresholds.get("elbow_up"), dynamic_thresholds.get("elbow_down")]),
            ("Right Shoulder", shoulder_r, [dynamic_thresholds.get("shoulder_up"), dynamic_thresholds.get("shoulder_down")]),
            ("Left Shoulder", shoulder_l, [dynamic_thresholds.get("shoulder_up"), dynamic_thresholds.get("shoulder_down")]),
        ]
    }

    joint_data = joint_data_map.get(current_exercise, [])
    
    for label, angle, ranges in joint_data:
        if not all(ranges): continue
        color = (0, 255, 0) if in_any_range(angle, ranges) else (0, 0, 255)
        approx = classify_stage_by_proximity(angle, *ranges)
        line = f"{label}: {angle:.1f}deg ~ {approx.upper()}"
        visual_lines.append((line, color))
        log_lines.append(line)

    return visual_lines, log_lines