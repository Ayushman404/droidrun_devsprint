# config.py

# --- 1. IDENTITY (The Persona) ---
# Your dashboard can update these strings to change the "Brain" instantly.
USER_PERSONA = "Computer Science Engineering Student"
USER_CURRENT_FOCUS = "Data Structures, Algorithms, System Design, and Python"

# --- 2. STRICTNESS SETTINGS ---
# Set to False to allow general entertainment (Movies, Games).
# Set to True to allow ONLY Educational content.
STUDY_MODE = True 

# How many seconds to wait after opening a new app before checking?
GRACE_PERIOD = 15 

# Anti-Cheat: If you reopen a banned app within X seconds, no grace period.
REOPEN_PENALTY_TIME = 200

# --- 3. APP MANAGEMENT ---
# Apps that are ALWAYS allowed (Launcher, Phone, WhatsApp, etc.)
WHITELIST_APPS = [
    "com.android.launcher",
    "com.sec.android.app.launcher",
    "com.google.android.apps.nexuslauncher",
    "com.android.systemui",
    "com.google.android.dialer",
    "com.whatsapp",  # Allow messaging
]

# Apps to NEVER check (Performance optimization)
# If the user is in these apps, the script sleeps to save battery.
IGNORE_APPS = [
    "com.google.android.inputmethod.latin", # Gboard
    "com.spotify.music" # Background music is usually fine
]

# --- 4. SYSTEM PROTECTION ---
# If these keywords appear in the Settings app, we kill it.
PROTECTED_APP_NAMES = ["DroidRun", "Remote Debugging", "Developer options"]