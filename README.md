STRAPS 2.0: Real-time Exercise & Posture System 🏋️‍♂️
STRAPS 2.0 is an AI-powered fitness assistant that uses your webcam to provide real-time feedback on your exercise form. It accurately counts your reps, analyzes your posture, and gives you a detailed performance summary to help you train smarter and safer.

## Table of Contents
About The Project

Key Features

Built With

Getting Started

Prerequisites

Installation

Usage

How It Works

Configuration

File Structure

## About The Project
This project was built to make effective exercise form correction accessible to everyone. By leveraging computer vision with MediaPipe, STRAPS 2.0 acts as a virtual personal trainer. It analyzes key body angles and movements to detect exercises, count repetitions, and identify common mistakes in form. After each session, it provides a summary with actionable feedback, highlighting areas for improvement.

## Key Features ✨
Real-time Pose Estimation: Uses MediaPipe to track 33 body landmarks.

Automatic Exercise Detection: Currently supports Hammer Curls and Overhead Press.

Accurate Repetition Counting: Differentiates between raw attempts and reps performed with correct form.

Live Form Feedback: Provides on-screen text feedback for:

Static joint angles (e.g., keeping your knees and hips stable).

Dynamic joint angles (range of motion for elbows and shoulders).

Wrist spacing and overall body posture (via convex hull analysis).

Performance Scoring: Scores each correct rep based on form consistency, providing a quantitative measure of quality.

Session Summary: Generates a detailed post-workout report with average scores and areas for improvement.

Logging & Recording: Automatically saves session logs to a .csv file and can record a video of your workout.

Gender-Specific Thresholds: Uses different evaluation criteria for male and female body types for higher accuracy.

## Built With
This project is built with Python and the following key libraries:

OpenCV

MediaPipe

Tkinter

NumPy

Pillow (PIL)

## Getting Started
Follow these steps to get a local copy up and running.

### Prerequisites
Make sure you have Python 3.8+ and pip installed on your system.

### Installation
Clone the repository:

Bash

git clone https://github.com/your-username/your-repository-name.git
Navigate to the project directory:

Bash

cd your-repository-name
Create and activate a virtual environment (recommended):

Windows:

Bash

python -m venv venv
.\venv\Scripts\activate
macOS / Linux:

Bash

python3 -m venv venv
source venv/bin/activate
Install the required packages:

Bash

pip install -r requirements.txt
## Usage 🚀
To start the application, run main.py from the root directory:

Bash

python main.py
The GUI will launch, and you can control the application using the on-screen buttons:

Start/Stop: Begins or ends the pose detection process.

Choose Video / Use Webcam: Toggles between a pre-recorded video file and your live webcam feed.

Start/Stop Record: Enables or disables session logging (.csv) and video recording (.avi).

Clear Reps: Resets all repetition counters to zero.

Switch Gender: Toggles between "male" and "female" evaluation thresholds.

Instructions: Shows the welcome popup with user instructions.

## How It Works
The application follows a computer vision pipeline:

Video Input: Captures frames from a webcam or video file.

Pose Estimation: MediaPipe's Pose model processes each frame to detect 33 body landmarks.

Feature Extraction: The code calculates key metrics from the landmarks, such as joint angles, distances between points (e.g., wrists), and the convex hull area of the body.

Exercise Detection: Based on the shoulder angles over a short time window, the system determines if you are performing a Hammer Curl or an Overhead Press.

State Machine for Rep Counting: A state machine tracks the "up" and "down" phases of each arm's movement. A repetition is counted only when a full, valid cycle is completed.

Feedback & Scoring: At each frame, your current metrics are compared against the pre-defined "correct" ranges in thresholds.json. Feedback is displayed, and at the end of a rep, a score is calculated.

## Configuration
All thresholds for exercise detection, form correction, and scoring are centralized in the txt/thresholds.json file. This makes it easy to fine-tune the application's sensitivity without changing the Python code.

The JSON is structured by exercise and contains:

detection: Angle ranges used to identify the current exercise.

dynamic_angles: The target "up" and "down" angle ranges for moving joints.

male/female: Gender-specific thresholds for static posture, wrist distance, and convex hull area.

## File Structure
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