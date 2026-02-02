import asyncio
import datetime
from sqlalchemy import select
from database import AsyncSessionLocal, ScheduleRule
import config

async def sync_schedule_to_config():
    """
    PRIORITY LOGIC:
    1. If Schedule Rule matches NOW -> Overwrite Config (Force Mode)
    2. Else -> Restore Config to Manual Defaults (Manual Mode)
    """
    while True:
        now = datetime.datetime.now().time()
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ScheduleRule))
            rules = result.scalars().all()
            
            active_rule = None
            
            # Find matching rule
            for rule in rules:
                # Logic to check if NOW is inside the rule's Time Window
                if rule.start_time <= rule.end_time:
                    if rule.start_time <= now <= rule.end_time:
                        active_rule = rule
                        break
                else: # Overnight rule (e.g. 10 PM to 2 AM)
                    if now >= rule.start_time or now <= rule.end_time:
                        active_rule = rule
                        break
            
            # --- PRIORITY LOGIC ---
            if active_rule:
                # CASE 1: SCHEDULE OVERRIDE
                # We force the runtime config to match the schedule
                config.STUDY_MODE = active_rule.study_mode
                config.DOOMSCROLL_MODE = active_rule.doomscroll_mode
                config.PUNISHMENT_TYPE = active_rule.punishment_type
                config.PUNISHMENT_TARGET = active_rule.punishment_target
                
                config.USER_CURRENT_FOCUS = f"SCHEDULE: {active_rule.label}"
                
            else:
                # CASE 2: RESTORE MANUAL SETTINGS
                # No schedule is active, so we let the user's manual toggles take over
                config.STUDY_MODE = config.MANUAL_STUDY_MODE
                config.DOOMSCROLL_MODE = config.MANUAL_DOOMSCROLL_MODE
                config.PUNISHMENT_TYPE = config.MANUAL_PUNISHMENT_TYPE
                config.PUNISHMENT_TARGET = config.MANUAL_PUNISHMENT_TARGET
                
                config.USER_CURRENT_FOCUS = "General Maths, Coding, Artificial Intelligence, Development"

        # Check every 5 seconds for responsiveness
        await asyncio.sleep(5)