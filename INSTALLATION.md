# Installation & Setup Guide - PROXY BOT WARS

This guide details how to install, configure, and execute the PROXY BOT WARS platform on Windows, macOS, or Linux.

---

## 1. Prerequisites

- **Python 3.9+** (Tested and verified on Python 3.10, 3.11, 3.12, 3.13).
- **Git** (optional, for version control).
- Any modern web browser (Chrome, Firefox, Edge, Safari) for the visualizer.

Verify your Python installation:
```bash
python --version
```

---

## 2. Setup Instructions

### Step 1: Clone or Navigate to the Workspace
```bash
cd "c:\Users\LENOVO\OneDrive\Desktop\Bot War"
```

### Step 2: (Optional) Create a Python Virtual Environment
```bash
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Test Dependencies
The core game engine, tournament system, and visualizer web server use only the Python standard library. Install `pytest` for automated test execution:
```bash
pip install -r requirements.txt
```

---

## 3. Verifying Installation

Run the complete automated test suite to ensure all subsystems are functioning:
```bash
python -m pytest tests/ -v
```
You should see 25 passing tests.

---

## 4. Running Your First Match

Run an automated 50-turn match between the starter bot and the baseline bot:
```bash
python run_match.py --blue bots/starter_bot.py --red bots/baseline_bot.py --turns 50
```

---

## 5. Starting the Live Visualizer Web Arena

Start the built-in HTTP server:
```bash
python server.py
```
Open your browser and navigate to:
```
http://localhost:8080
```
From here you can watch replays, simulate matches in real time, view leaderboards, and manage tournaments!

