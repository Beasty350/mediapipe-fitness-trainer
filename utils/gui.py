import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np

class GUI:
    def __init__(self, root, exercise_counters, rep_counter):
        self.root = root
        self.exercise_counters = exercise_counters
        self.rep_counter = rep_counter
        self.root.title("STRAPS 2.0")
        self.root.geometry("1280x760")

        self.is_running = False
        self.is_logging = False
        self.gender = "male"
        self.source_type = 'webcam'
        self.video_path = None

        style = ttk.Style()
        style.configure("Custom.TButton", font=("Arial", 17))

        bg_image = Image.open("img//background.jpg")
        bg_image = bg_image.resize((1280, 760), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(bg_image)

        self.canvas_bg = tk.Canvas(self.root, width=1280, height=760, highlightthickness=0, bg="black")
        self.canvas_bg.pack(fill="both", expand=True)
        self.canvas_bg.create_image(0, 0, anchor="nw", image=self.bg_photo)

        self.hammer_img = Image.open("img//hammer.png").resize((260, 160), Image.Resampling.LANCZOS)
        self.press_img = Image.open("img//overhead.png").resize((260, 160), Image.Resampling.LANCZOS)

        self.hammer_photo = ImageTk.PhotoImage(self.hammer_img)
        self.press_photo = ImageTk.PhotoImage(self.press_img)

        self.frame_display_group = tk.Frame(self.canvas_bg, bg="black", highlightthickness=0)
        self.canvas_bg.create_window(640, 40, anchor="n", window=self.frame_display_group)

        self.canvas_main = tk.Label(self.frame_display_group, bg="black")
        self.canvas_main.pack(side=tk.LEFT, padx=5)

        self.canvas_feedback = tk.Label(self.frame_display_group, width=780, height=480, bg="black")
        self.canvas_feedback.pack(side=tk.LEFT, padx=5)

        self.frame_bottom_group = tk.Frame(self.canvas_bg, bg="black", highlightthickness=0)
        self.canvas_bg.create_window(640, 550, anchor="n", window=self.frame_bottom_group)

        self.info_frame_border = tk.Frame(self.frame_bottom_group, padx=5, pady=5, bg="black")
        self.info_frame_border.pack(side=tk.LEFT, padx=10)

        self.info_frame = tk.Frame(self.info_frame_border, bg="black")
        self.info_frame.pack()

        self.exercise_label = tk.Label(self.info_frame, text="Exercise: -", font=("Arial", 14), bg="black", fg="white")
        self.exercise_label.grid(row=0, column=0, padx=20)

        self.raw_label = tk.Label(self.info_frame, text="Raw Reps: 0", font=("Arial", 14), bg="black", fg="white")
        self.raw_label.grid(row=3, column=0, padx=20)

        self.hammer_label = tk.Label(self.info_frame, text="Hammer Curl Reps: 0", font=("Arial", 14), bg="black", fg="white")
        self.hammer_label.grid(row=1, column=0, padx=20)

        self.press_label = tk.Label(self.info_frame, text="Overhead Press Reps: 0", font=("Arial", 14), bg="black", fg="white")
        self.press_label.grid(row=2, column=0, padx=20)

        self.stage_label = tk.Label(self.info_frame, text="Stage R: - | Stage L: -", font=("Arial", 14), bg="black", fg="white")
        self.stage_label.grid(row=4, column=0, padx=20)

        self.frame_bottom = tk.Frame(self.frame_bottom_group, bg="black")
        self.frame_bottom.pack(side=tk.RIGHT, padx=20)

        self.source_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Choose Video", width=20, command=self.choose_video)
        self.source_btn.grid(row=0, column=0, padx=10, pady=5)

        self.toggle_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Start", width=20, command=self.toggle)
        self.toggle_btn.grid(row=0, column=1, padx=10, pady=5)

        self.log_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Start Record", width=20, command=self.toggle_logging)
        self.log_btn.grid(row=1, column=0, padx=10, pady=5)

        self.clear_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Clear Reps", width=20, command=self.clear_reps)
        self.clear_btn.grid(row=1, column=1, padx=10, pady=5)

        self.gender_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Switch to Female", width=20, command=self.toggle_gender)
        self.gender_btn.grid(row=2, column=0, padx=10, pady=5)
        
        self.instruction_btn = ttk.Button(self.frame_bottom, style="Custom.TButton", text="Instructions", width=20, command=self.show_welcome_popup)
        self.instruction_btn.grid(row=2, column=1, padx=10, pady=5)

        self.show_welcome_popup()

    def choose_video(self):
        """Opens a file dialog to select a video and switches the source type."""
        path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=(("Video files", "*.avi *.mp4 *.mov"), ("All files", "*.*"))
        )
        if path:
            self.video_path = path
            self.source_type = 'video'
            if self.is_running:
                self.toggle()
            print(f"Video source selected: {self.video_path}")
            self.source_btn.config(text="Use Webcam", command=self.use_webcam)

    def use_webcam(self):
        """Switches the source back to the webcam."""
        self.source_type = 'webcam'
        self.video_path = None
        if self.is_running:
            self.toggle()
        print("Switched to webcam source.")
        self.source_btn.config(text="Choose Video", command=self.choose_video)

    def toggle(self):
        self.is_running = not self.is_running
        self.toggle_btn.config(text="Stop" if self.is_running else "Start")
        if not self.is_running and self.rep_counter.all_scores:
            self.show_summary_popup()

    def toggle_logging(self):
        self.is_logging = not self.is_logging
        self.log_btn.config(text="Stop Record" if self.is_logging else "Start Record")

    def toggle_gender(self):
        self.gender = "female" if self.gender == "male" else "male"
        self.gender_btn.config(text=f"Switch to {'Male' if self.gender == 'female' else 'Female'}")

    def clear_reps(self):
        self.hammer_count = 0
        self.press_count = 0
        self.raw_reps = 0

        self.exercise_counters["hammer_curl"] = 0
        self.exercise_counters["overhead_press"] = 0
        
        self.rep_counter.raw_reps["hammer_curl"] = 0
        self.rep_counter.raw_reps["overhead_press"] = 0
        self.rep_counter.right_phase = "idle"
        self.rep_counter.left_phase = "idle"
        self.rep_counter.stage_right = None
        self.rep_counter.stage_left = None
        self.rep_counter.raw_right_phase = "idle"
        self.rep_counter.raw_left_phase = "idle"
        self.rep_counter.reset_summary()
        
        self.update_info("-", 0, 0, "-", "-", 0)

    def update_frames(self, main_frame, feedback_frame):
        img1 = cv2.cvtColor(main_frame, cv2.COLOR_BGR2RGB)
        img1 = ImageTk.PhotoImage(Image.fromarray(img1))
        self.canvas_main.configure(image=img1)
        self.canvas_main.image = img1

        img2 = cv2.cvtColor(feedback_frame, cv2.COLOR_BGR2RGB)
        img2 = ImageTk.PhotoImage(Image.fromarray(img2))
        self.canvas_feedback.configure(image=img2)
        self.canvas_feedback.image = img2

    def update_info(self, exercise, hammer_count, press_count, stage_r, stage_l, raw_reps=0):
        self.hammer_count = hammer_count
        self.press_count = press_count
        self.exercise_label.config(text=f"Exercise: {exercise.upper()}")
        self.hammer_label.config(text=f"Hammer Curl Reps: {hammer_count}")
        self.press_label.config(text=f"Overhead Press Reps: {press_count}")
        self.stage_label.config(text=f"Stage R: {stage_r or '-'} | Stage L: {stage_l or '-'}")
        self.raw_label.config(text=f"Raw Reps: {raw_reps}")

    def show_summary_popup(self):
        scores_data = self.rep_counter.all_scores
        if not scores_data:
            return

        summary = {}
        for item in scores_data:
            exercise = item['exercise']
            scores = item['scores']

            if exercise not in summary:
                summary[exercise] = {'reps': 0}
            
            summary[exercise]['reps'] += 1
            for key, value in scores.items():
                if key not in summary[exercise]:
                    summary[exercise][key] = []
                summary[exercise][key].append(value)
        
        summary_text = "Session Summary\n"
        summary_text += "---------------------------------\n"

        for exercise, data in summary.items():
            if data['reps'] == 0: continue
            
            summary_text += f"\nExercise: {exercise.replace('_', ' ').title()}\n"
            summary_text += f"  Total Reps: {data['reps']}\n\n  Average Scores:\n"
            
            areas_for_improvement = []
            improvement_threshold = 95

            for key, value_list in data.items():
                if key == 'reps': continue

                if isinstance(value_list[0], dict):
                    all_sub_scores = {}
                    for rep_scores in value_list:
                        for sub_key, sub_value in rep_scores.items():
                            if sub_key not in all_sub_scores:
                                all_sub_scores[sub_key] = []
                            all_sub_scores[sub_key].append(sub_value)
                    
                    if not all_sub_scores: continue

                    avg_sub_scores = {k: np.mean(v) for k, v in all_sub_scores.items()}
                    overall_avg = np.mean(list(avg_sub_scores.values()))
                    summary_text += f"    - {key}: {overall_avg:.1f}%\n"

                    for sub_key, sub_avg in avg_sub_scores.items():
                        if sub_avg < improvement_threshold:
                            formatted_name = sub_key.replace('_', ' ').title()
                            areas_for_improvement.append(formatted_name)
                else:
                    avg = np.mean(value_list)
                    summary_text += f"    - {key}: {avg:.1f}%\n"
                    if avg < improvement_threshold:
                        areas_for_improvement.append(key)

            if areas_for_improvement:
                summary_text += f"\n  >> Areas for Improvement:\n"
                for area in sorted(list(set(areas_for_improvement))):
                    summary_text += f"     - {area}\n"
            else:
                summary_text += f"\n  >> Great job! All scores are above {improvement_threshold}%!\n"

            summary_text += "---------------------------------\n"
        
        popup = tk.Toplevel(self.root)
        popup.title("Session Summary")
        popup.geometry("500x500")
        popup.configure(bg="black")
        
        label = tk.Label(popup, text=summary_text, justify=tk.LEFT, font=("Courier", 12), fg="white", bg="black")
        label.pack(padx=20, pady=20, fill="both", expand=True)

        close_btn = ttk.Button(popup, text="OK", command=popup.destroy, style="Custom.TButton")
        close_btn.pack(pady=10)
        
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

    def show_welcome_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Welcome to STRAPS 2.0")
        popup.geometry("600x600")
        popup.configure(bg="black")

        title = tk.Label(popup, text="Thank you for using STRAPS 2.0!", font=("Arial", 16, "bold"), bg="black", fg="white")
        title.pack(pady=(20, 10))

        instructions = (
            "INSTRUCTIONS:\n\n"
            "• Press 'Start' to begin\n"
            "• Use 'Choose Video' to select a local file\n"
            "• Press 'Start Record' to log and record reps\n"
            "• Press 'Clear Reps' to reset counters\n"
            "• Use 'Switch Gender' for gender-specific evaluation\n"
            "• Press 'Instructions' to show user guide\n\n"
            "Supported Exercises:\n"
            "1. Hammer Curl\n"
            "2. Overhead Press"
        )

        message = tk.Label(popup, text=instructions, font=("Arial", 12), bg="black", fg="white", justify="left")
        message.pack(padx=20, pady=10)

        image_container = tk.Frame(popup, bg="black")
        image_container.pack(pady=(10, 5))

        hammer_frame = tk.Frame(image_container, bg="black")
        tk.Label(hammer_frame, image=self.hammer_photo, bg="black").pack()
        tk.Label(hammer_frame, text="Hammer Curl", font=("Arial", 12), bg="black", fg="white").pack()
        hammer_frame.pack(side=tk.LEFT, padx=20)

        press_frame = tk.Frame(image_container, bg="black")
        tk.Label(press_frame, image=self.press_photo, bg="black").pack()
        tk.Label(press_frame, text="Overhead Press", font=("Arial", 12), bg="black", fg="white").pack()
        press_frame.pack(side=tk.LEFT, padx=20)

        close_btn = ttk.Button(popup, text="Let's Go", command=popup.destroy)
        close_btn.pack(pady=20)
        
        self.root.update()
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)
        self.root.update_idletasks()