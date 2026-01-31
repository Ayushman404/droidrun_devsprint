# config.py

# System State
IS_RUNNING = False

# AI Context
USER_PERSONA = "CS Undergrad"
USER_CURRENT_FOCUS = "Data Structures and Algorithms, Maths, Development, AI"

# Toggles
STUDY_MODE = False        
DOOMSCROLL_MODE = True    

# Thresholds
GRACE_PERIOD = 10
MAX_STRIKES = 3
PENALTY_DURATION = 60

PUNISHMENT_TYPE = "HOME" # Options: "HOME", "BACK", "OPEN_APP"
PUNISHMENT_TARGET = ""   # e.g., "com.duolingo" if OPEN_APP is selected

# --- IGNORED APPS ---
# These are skipped by the loop entirely (Launchers, System UI, etc.)
WHITELIST_APPS = [
    "com.sec.android.app.launcher",   # Samsung Launcher
    "com.google.android.apps.nexuslauncher", # Pixel Launcher
    "com.android.launcher3",          # Generic Launcher
    "com.miui.home",                  # Xiaomi Launcher
    "com.android.systemui",           # System UI
    "com.android.settings",           # Settings (Optional, keep if you want to allow settings)
    "com.google.android.inputmethod.latin" # Keyboard
]