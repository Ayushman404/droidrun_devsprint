import asyncio
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select, update
from pydantic import BaseModel
from datetime import datetime, time

import config
import main
import state_manager
from database import init_db, AsyncSessionLocal, AppConfig, DailyUsage, ScheduleRule
from droidrun import AdbTools
from agent_service import agent_router
from scheduler_service import sync_schedule_to_config 

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/agent")

# --- GLOBAL TASK REFERENCE ---
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
    
    # 4. Start Tasks
    sync_task = asyncio.create_task(periodic_db_sync())
    # Start the Scheduler Loop (Priority Logic)
    asyncio.create_task(sync_schedule_to_config())

@app.on_event("shutdown")
async def shutdown_event():
    print("🔻 Server shutting down...")
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
    print("✅ Clean shutdown complete.")

# --- API ENDPOINTS ---

@app.get("/analytics")
def get_analytics():
    """Reads LIVE metrics directly from RAM (Instant Updates)"""
    total_time = 0
    total_strikes = 0
    app_breakdown = []
    
    all_packages = set(state_manager.USAGE_CACHE.keys()) | set(state_manager.STRIKES_CACHE.keys())
    
    for pkg in all_packages:
        seconds = state_manager.USAGE_CACHE.get(pkg, 0)
        strikes = state_manager.STRIKES_CACHE.get(pkg, 0)
        
        mins = int(seconds / 60)
        total_time += mins
        total_strikes += strikes
        
        friendly_name = pkg
        if pkg in state_manager.CONFIG_CACHE:
             friendly_name = pkg.split('.')[-1].capitalize()

        if mins > 0 or strikes > 0:
            app_breakdown.append({
                "name": friendly_name, 
                "package": pkg,
                "value": mins,
                "strikes": strikes
            })
            
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
        "penalty_duration": getattr(config, "PENALTY_DURATION", 60),
        "punishment_type": getattr(config, "PUNISHMENT_TYPE", "HOME"),
        "punishment_target": getattr(config, "PUNISHMENT_TARGET", "")
    }

# --- 🔥 UPDATED ENDPOINT (The Priority Logic Fix) ---
@app.post("/config")
def update_config(data: dict):
    """
    Updates the Runtime Config AND the Manual Preference Memory.
    This ensures that when a Schedule ends, we revert to these 'Manual' settings.
    """
    # 1. Update Basic Settings
    if "persona" in data: config.USER_PERSONA = data["persona"]
    if "grace_period" in data: config.GRACE_PERIOD = int(data["grace_period"])
    if "max_strikes" in data: config.MAX_STRIKES = int(data["max_strikes"])
    
    # 2. Update Toggles (Both Active & Manual Memory)
    if "study_mode" in data:
        config.MANUAL_STUDY_MODE = data["study_mode"]
        config.STUDY_MODE = data["study_mode"] # Instant Apply
        
    if "doomscroll_mode" in data:
        config.MANUAL_DOOMSCROLL_MODE = data["doomscroll_mode"]
        config.DOOMSCROLL_MODE = data["doomscroll_mode"]
        
    if "punishment_type" in data:
        config.MANUAL_PUNISHMENT_TYPE = data["punishment_type"]
        config.PUNISHMENT_TYPE = data["punishment_type"]
        
    if "punishment_target" in data:
        config.MANUAL_PUNISHMENT_TARGET = data["punishment_target"]
        config.PUNISHMENT_TARGET = data["punishment_target"]
        
    if "focus" in data:
        # If user manually sets focus, we tag it as MANUAL so scheduler knows
        config.USER_CURRENT_FOCUS = data["focus"]

    # 3. New Penalty Duration
    if "penalty_duration" in data:
        config.PENALTY_DURATION = int(data["penalty_duration"])

    print(f"🔧 MANUAL CONFIG UPDATE: Study={config.STUDY_MODE} | Doom={config.DOOMSCROLL_MODE}")
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

# --- SCHEDULE API ---
class ScheduleRequest(BaseModel):
    start: str 
    end: str   
    label: str
    study_mode: bool
    doomscroll_mode: bool
    punishment_type: str
    punishment_target: str = ""

@app.get("/schedule")
async def get_schedule():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ScheduleRule).order_by(ScheduleRule.start_time))
        rules = result.scalars().all()
        return rules

@app.post("/schedule")
async def add_schedule(req: ScheduleRequest):
    try:
        start_t = datetime.strptime(req.start, "%H:%M").time()
        end_t = datetime.strptime(req.end, "%H:%M").time()
        
        async with AsyncSessionLocal() as session:
            new_rule = ScheduleRule(
                start_time=start_t,
                end_time=end_t,
                label=req.label,
                study_mode=req.study_mode,
                doomscroll_mode=req.doomscroll_mode,
                punishment_type=req.punishment_type,
                punishment_target=req.punishment_target
            )
            session.add(new_rule)
            await session.commit()
        return {"status": "added"}
    except Exception as e:
        print(f"❌ Schedule Add Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/schedule/{id}")
async def delete_schedule(id: int):
    async with AsyncSessionLocal() as session:
        rule = await session.get(ScheduleRule, id)
        if rule:
            await session.delete(rule)
            await session.commit()
    return {"status": "deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)