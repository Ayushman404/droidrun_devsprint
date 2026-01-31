import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select, update
from pydantic import BaseModel

import config
import main
import state_manager
from database import init_db, AsyncSessionLocal, AppConfig, DailyUsage
from droidrun import AdbTools

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL TASK REFERENCE (To kill it later) ---
sync_task = None

# --- BACKGROUND TASKS ---
async def periodic_db_sync():
    """Flushes RAM usage to SQLite every 60 seconds"""
    try:
        while True:
            await asyncio.sleep(60)
            if config.IS_RUNNING:
                print("💾 Syncing usage to DB...")
                await state_manager.sync_usage_to_db()
    except asyncio.CancelledError:
        print("🛑 Sync Task Cancelled. Shutting down...")
        # Force one last save before dying
        await state_manager.sync_usage_to_db()

@app.on_event("startup")
async def startup_event():
    global sync_task
    
    # 1. Init DB
    await init_db()
    
    # 2. Sync Apps
    print("📲 Syncing installed apps...")
    adb = AdbTools()
    try:
        apps = await adb.get_apps(include_system=False)
        async with AsyncSessionLocal() as session:
            for app_info in apps:
                stmt = insert(AppConfig).values(
                    package_name=app_info['package'],
                    friendly_name=app_info['label']
                ).on_conflict_do_nothing()
                await session.execute(stmt)
            await session.commit()
    except Exception as e:
        print(f"⚠️ ADB Sync failed: {e}")

    # 3. Load RAM
    await state_manager.load_config_to_ram()
    
    # 4. Start Sync Task & Keep Reference
    sync_task = asyncio.create_task(periodic_db_sync())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanly kill the background task"""
    print("🔻 Server shutting down...")
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
    print("✅ Clean shutdown complete.")

# --- API ENDPOINTS ---

# Add to server.py

# In server.py, replace the @app.get("/analytics") endpoint with this:

@app.get("/analytics")
def get_analytics():
    """Reads LIVE metrics directly from RAM (Instant Updates)"""
    total_time = 0
    total_strikes = 0
    app_breakdown = []
    
    # 1. Identify all unique apps active today (from both Time and Strikes caches)
    all_packages = set(state_manager.USAGE_CACHE.keys()) | set(state_manager.STRIKES_CACHE.keys())
    
    for pkg in all_packages:
        # Get values (default to 0 if missing)
        seconds = state_manager.USAGE_CACHE.get(pkg, 0)
        strikes = state_manager.STRIKES_CACHE.get(pkg, 0)
        
        mins = int(seconds / 60)
        total_time += mins
        total_strikes += strikes
        
        # Get Friendly Name
        friendly_name = pkg
        if pkg in state_manager.CONFIG_CACHE:
             # Try to find a name, or clean up the package string
             # We rely on the frontend to map package -> name if needed, 
             # but here is a simple fallback:
             friendly_name = pkg.split('.')[-1].capitalize()
             
             # If you have the full app list in memory, you could map it better,
             # but this is usually sufficient for the chart.

        if mins > 0 or strikes > 0:
            app_breakdown.append({
                "name": friendly_name, 
                "package": pkg, # Send package so frontend can match names
                "value": mins,
                "strikes": strikes
            })
            
    # Sort by Time Used (Descending)
    app_breakdown = sorted(app_breakdown, key=lambda x: x['value'], reverse=True)[:5]
    
    return {
        "total_time_mins": total_time,
        "total_strikes": total_strikes,
        "breakdown": app_breakdown
    }

@app.get("/status")
def get_status():
    return {
        "running": config.IS_RUNNING,
        "current_app": main.current_app_name,
        "last_verdict": main.last_verdict,
        "logs": main.dashboard_logs[-50:]
    }

@app.post("/start")
async def start_enforcer(background_tasks: BackgroundTasks):
    if not config.IS_RUNNING:
        config.IS_RUNNING = True
        await state_manager.load_config_to_ram()
        background_tasks.add_task(main.main)
    return {"status": "Started"}

@app.post("/stop")
async def stop_enforcer():
    config.IS_RUNNING = False
    await state_manager.sync_usage_to_db()
    return {"status": "Stopped"}

@app.get("/config")
def get_config():
    return {
        "persona": config.USER_PERSONA,
        "focus": config.USER_CURRENT_FOCUS,
        "study_mode": config.STUDY_MODE,
        "doomscroll_mode": config.DOOMSCROLL_MODE,
        "grace_period": config.GRACE_PERIOD,
        "max_strikes": config.MAX_STRIKES,
        "penalty_duration": getattr(config, "PENALTY_DURATION", 60), # Safety default
        "punishment_type": getattr(config, "PUNISHMENT_TYPE", "HOME"),
        "punishment_target": getattr(config, "PUNISHMENT_TARGET", "")
    }

@app.post("/config")
def update_config(data: dict):
    config.USER_PERSONA = data.get("persona", config.USER_PERSONA)
    config.USER_CURRENT_FOCUS = data.get("focus", config.USER_CURRENT_FOCUS)
    config.STUDY_MODE = data.get("study_mode", config.STUDY_MODE)
    config.DOOMSCROLL_MODE = data.get("doomscroll_mode", config.DOOMSCROLL_MODE)
    config.GRACE_PERIOD = int(data.get("grace_period", config.GRACE_PERIOD))
    config.MAX_STRIKES = int(data.get("max_strikes", config.MAX_STRIKES))
    
    # NEW FIELDS
    config.PENALTY_DURATION = int(data.get("penalty_duration", config.PENALTY_DURATION))
    config.PUNISHMENT_TYPE = data.get("punishment_type", config.PUNISHMENT_TYPE)
    config.PUNISHMENT_TARGET = data.get("punishment_target", config.PUNISHMENT_TARGET)
    
    if config.STUDY_MODE:
        config.DOOMSCROLL_MODE = True
        
    print(f"🔧 CONFIG UPDATED: Penalty={config.PENALTY_DURATION}s | Type={config.PUNISHMENT_TYPE}")
    return {"status": "Updated", "config": get_config()}

# --- APP DATA ---
class AppUpdate(BaseModel):
    limit: int 
    blocked: bool

@app.get("/apps")
async def get_apps():
    apps_data = []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AppConfig))
        db_apps = result.scalars().all()
        
        for app in db_apps:
            ram_seconds = state_manager.USAGE_CACHE.get(app.package_name, 0)
            ram_strikes = state_manager.STRIKES_CACHE.get(app.package_name, 0)
            
            apps_data.append({
                "package": app.package_name,
                "name": app.friendly_name,
                "limit_mins": app.daily_limit_mins,
                "used_mins": int(ram_seconds / 60),
                "strikes": ram_strikes,
                "is_blocked": app.is_blocked
            })
            
    return sorted(apps_data, key=lambda x: x['used_mins'], reverse=True)

@app.post("/apps/{package}")
async def update_app_rule(package: str, rule: AppUpdate):
    async with AsyncSessionLocal() as session:
        stmt = (
            update(AppConfig)
            .where(AppConfig.package_name == package)
            .values(daily_limit_mins=rule.limit, is_blocked=rule.blocked)
        )
        await session.execute(stmt)
        await session.commit()

    state_manager.CONFIG_CACHE[package] = {
        "limit": rule.limit * 60,
        "blocked": rule.blocked
    }
    return {"status": "success", "package": package}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)