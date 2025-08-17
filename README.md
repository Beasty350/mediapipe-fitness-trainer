# STRAPS: A Real-time Strength Training Assistive System 

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/Beasty350/mediapipe-fitness-trainer)
![Repo Size](https://img.shields.io/github/repo-size/Beasty350/mediapipe-fitness-trainer)

STRAPS 2.0 is an AI-powered fitness assistant that uses your webcam to provide real-time feedback on your exercise form. It accurately counts your reps, analyzes your posture, and gives you a detailed performance summary to help you train smarter and safer.

## ✨ Key Features

* **🤖 Real-time Pose Estimation**: Uses MediaPipe to track 33 body landmarks.
* **💪 Automatic Exercise Detection**: Currently supports **Hammer Curls** and **Overhead Press**.
* **🔢 Accurate Repetition Counting**: Differentiates between raw attempts and reps performed with correct form.
* **🗣️ Live Form Feedback**: Provides on-screen text feedback for static posture, dynamic range of motion, and wrist spacing.
* **📊 Performance Scoring**: Scores each correct rep based on form consistency, providing a quantitative measure of quality.
* **📈 Session Summary**: Generates a detailed post-workout report with average scores and areas for improvement.
* **📹 Logging & Recording**: Automatically saves session logs to a `.csv` file and can record a video of your workout.
* **🚻 Gender-Specific Thresholds**: Uses different evaluation criteria for male and female body types for higher accuracy.

---

## 🛠️ Built With

This project is built with Python and these key libraries:

| Library | Description |
| :--- | :--- |
| **OpenCV** | For video capture and image processing. |
| **MediaPipe** | For high-fidelity body pose tracking. |
| **Tkinter** | For the graphical user interface (GUI). |
| **NumPy** | For efficient numerical calculations and array manipulation. |
| **Pillow (PIL)** | For handling images within the Tkinter GUI. |

---

## 🚀 Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

Make sure you have **Python 3.8+** and **pip** installed on your system.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/Beasty350/mediapipe-fitness-trainer.git](https://github.com/Beasty350/mediapipe-fitness-trainer.git)
    ```

2.  **Navigate to the project directory:**
    ```sh
    cd Your-Repo
    ```

3.  **Create and activate a virtual environment (recommended):**
    * **Windows:**
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * **macOS / Linux:**
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

4.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

---

## ⚙️ How It Works

<details>
<summary>Click to expand the technical pipeline</summary>

The application follows a computer vision pipeline:
1. **Video Input**: Captures frames from a webcam or video file.
2. **Pose Estimation**: MediaPipe's Pose model processes each frame to detect 33 body landmarks.
3. **Feature Extraction**: The code calculates key metrics from the landmarks, such as joint angles, distances between points (e.g., wrists), and the convex hull area of the body.
4. **Exercise Detection**: Based on the shoulder angles over a short time window, the system determines if you are performing a Hammer Curl or an Overhead Press.
5. **State Machine for Rep Counting**: A state machine tracks the "up" and "down" phases of each arm's movement. A repetition is counted only when a full, valid cycle is completed.
6. **Feedback & Scoring**: At each frame, your current metrics are compared against the pre-defined "correct" ranges in `thresholds.json`. Feedback is displayed, and at the end of a rep, a score is calculated.

</details>

---

## 🔧 Configuration

All thresholds for exercise detection, form correction, and scoring are centralized in the `txt/thresholds.json` file. This makes it easy to fine-tune the application's sensitivity without changing the Python code.

<details>
<summary>Click to expand the file structure</summary>

    .
    ├── img/                # GUI images and assets
    ├── logs/               # Output directory for session .csv logs
    ├── recordings/         # Output directory for recorded .avi videos
    ├── txt/
    │   └── thresholds.json # All configuration parameters
    ├── utils/              # Helper modules
    │   ├── feedback.py     # Functions for generating on-screen feedback
    │   ├── functions.py    # Core calculations (angles, distances, scores)
    │   ├── gui.py          # The Tkinter GUI class
    │   ├── repetition.py   # The RepetitionCounter class and state machine
    │   └── utils.py        # Main loop, Logger, and Recorder classes
    ├── .gitignore          # Files and folders to ignore for Git
    ├── main.py             # Main script to run the application
    ├── README.md           # This documentation file
    └── requirements.txt    # Project dependencies

</details>

---

## 📈 Future Improvements

* [ ] Add support for more exercises (e.g., Squats, Bicep Curls).
* [ ] Implement a user profile system to track progress over time.
* [ ] Improve the UI/UX with more modern design elements.

---
