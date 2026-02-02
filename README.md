# 🛡️ Android Enforcer Platform

> **A High-Frequency, Stateful Anti-Procrastination System powered by Computer Vision, ADB, and Local LLMs.**

The Android Enforcer is an external supervision system that transforms a PC into a ruthless productivity governor for an Android device. Unlike on-device app blockers that can be uninstalled or bypassed, this system operates via **ADB (Android Debug Bridge)**, making it immune to standard evasion tactics.

It combines **Stateful Persistence (SQLite)**, and **Generative AI (Qwen 2.5)** to analyze screen content in real-time, enforcing strict protocols with zero-latency intervention.



---

## ⚡ Technical Architecture

The system is built on a **FastAPI** backend and a **React (Vite)** frontend, employing a "Double-Buffer" cache strategy to manage state.

### 1. The Core Loop (Backend)
* **Stateful Persistence:** Uses **SQLite + Async SQLAlchemy** to track usage, strikes, and limits across sessions.
* **Zero-Latency Monitoring:** Checks hard limits against a RAM cache ($O(1)$) every 0.5s, syncing to the disk asynchronously every 60s.
* **Hybrid Analysis:**
    * **Fast Lane:** Regex/Keyword detection for immediate threats (Shorts, Reels).
    * **Smart Lane:** **Ollama (Qwen 2.5)** analyzes video titles to distinguish between "Educational" and "Brainrot" content.

### 2. The Control Center (Frontend)
* **Cyberpunk UI:** A responsive dashboard built with **React, Tailwind, and Framer Motion**.
* **Real-Time Telemetry:** WebSockets/Polling for live logs, screen time analytics, and strike visualization.

---

## 🛠️ Installation & Setup

### Prerequisites
1.  **Python 3.10+**
2.  **Node.js & npm** (v18+)
3.  **Ollama** installed locally (`ollama run qwen2.5`)
4.  **Android Device** connected via USB with "USB Debugging" enabled.

---

### Phase 1: Dependencies

Use a file named `requirements.txt` 



Then, run the installation commands:

```bash
# 1. Install DroidRun (Your ADB Wrapper)
pip install droidrun

# 2. Install Project Dependencies
pip install -r requirements.txt
```

Phase 2: Backend Setup
The backend initializes the SQLite database automatically on the first run.

Navigate to the server directory.

Start the FastAPI server:

Bash
python server.py
Expected Output:

📲 Syncing installed apps... ✅ Database Initialized: enforcer.db created. 🚀 SYSTEM INITIALIZED | Strict Father Persona

Phase 3: Frontend Setup
The dashboard provides the interface to configure rules, view analytics, and control the system.

Navigate to the frontend directory:

Bash
cd frontend
Install Node dependencies:

Bash
npm install
Start the Development Server:

Bash
npm run dev
Open your browser to: http://localhost:5173

🔒 Engineering: Loopholes Plugged
This project was specifically engineered to defeat sophisticated procrastination habits.

1. The "Infinite Grace" Loophole
The Exploit: Users would close and reopen an app repeatedly to abuse the 10-second "Grace Period" window before checks began.

The Fix: The Penalty Box. If an app triggers a distraction block, it is marked as "Hostile" in RAM. Subsequent launches of that app have 0 seconds grace period for the next 2 minutes.

2. The "Chrome Backdoor"
The Exploit: Using a mobile browser (Chrome/Edge) to access Instagram or YouTube, bypassing app-level package blocks.

The Fix: URL & UI Hunting. The OCR logic specifically scans the browser's URL bar and tab titles. Detecting instagram.com, shorts, or reels inside a browser triggers an immediate kill switch.

3. The "Landscape" Blindspot
The Exploit: Watching YouTube in full-screen landscape mode hides the video title, blinding the AI from analyzing the content.

The Fix: Active Interrogation. If Study Mode is active and Landscape orientation is detected, the system simulates a physical Tap on the screen to wake up the UI overlays, captures the title, and then performs the AI assessment.

4. The "Zombie" Process
The Exploit: Background database sync tasks keeping the terminal/process alive even after the server was stopped.

The Fix: Implemented a robust shutdown_event in FastAPI to strictly cancel background tasks and force a final DB commit before process termination.

📊 Analytics & Metrics
The system tracks granular data to provide a "Mission Report" via the dashboard:

Daily Screen Time: Live counter of productive vs. wasted time.

Strike Count: Tracks how many times the Enforcer had to intervene.

Punishment Logs: Detailed history of why an action was taken (e.g., "Browser Shorts detected").

🤝 Usage Guide
Initialize: Click "INITIALIZE" on the Dashboard.

Configure: Go to App Rules to set daily limits or block apps entirely.

Settings:

Doomscroll Guard: Instantly kills Shorts/Reels.

Study Mode: Enables Qwen 2.5 to judge video relevance.

Punishment Type: Choose between HOME (Gentle), BACK (Annoying), or OPEN_APP (Force redirection to Duolingo/Clock).
