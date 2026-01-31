import time
from datetime import date
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy import select
from database import AsyncSessionLocal, AppConfig, DailyUsage

CONFIG_CACHE = {} 
USAGE_CACHE = {} 
STRIKES_CACHE = {} 
PENALTY_CACHE = {}

# Store the date of the last sync to detect midnight
LAST_SYNC_DATE = date.today()

def add_strike(package):
    """Increments strike and RETURNS the new total"""
    STRIKES_CACHE[package] = STRIKES_CACHE.get(package, 0) + 1
    total = STRIKES_CACHE[package]
    print(f"⚠️ STRIKE {total}: {package}")
    return total

def set_penalty(package, duration_seconds=60):
    expiry = time.time() + duration_seconds
    PENALTY_CACHE[package] = expiry
    print(f"🚫 PENALTY BOX ACTIVATED: {package} for {duration_seconds}s")

def is_penalized(package):
    return time.time() < PENALTY_CACHE.get(package, 0)

async def load_config_to_ram():
    global CONFIG_CACHE, USAGE_CACHE, STRIKES_CACHE
    async with AsyncSessionLocal() as session:
        # Load Config (Same as before)
        result = await session.execute(select(AppConfig))
        for row in result.scalars():
            CONFIG_CACHE[row.package_name] = {
                "limit": row.daily_limit_mins * 60,
                "blocked": row.is_blocked
            }
            
        # Load Usage AND Strikes
        stmt = select(DailyUsage).where(DailyUsage.usage_date == date.today())
        result = await session.execute(stmt)
        for row in result.scalars():
            USAGE_CACHE[row.package_name] = row.seconds_spent
            STRIKES_CACHE[row.package_name] = row.strikes # Load Strikes

    print("✅ Memory State Loaded (Config + Usage + Strikes)")

async def sync_usage_to_db():
    if not USAGE_CACHE and not STRIKES_CACHE: return
    
    # Merge keys from both caches to ensure we save everything
    all_packages = set(USAGE_CACHE.keys()) | set(STRIKES_CACHE.keys())
    
    async with AsyncSessionLocal() as session:
        for pkg in all_packages:
            seconds = USAGE_CACHE.get(pkg, 0)
            strikes = STRIKES_CACHE.get(pkg, 0)
            
            stmt = insert(DailyUsage).values(
                package_name=pkg,
                usage_date=date.today(),
                seconds_spent=int(seconds),
                strikes=int(strikes)
            ).on_conflict_do_update(
                index_elements=['package_name', 'usage_date'],
                set_=dict(
                    seconds_spent=int(seconds),
                    strikes=int(strikes)
                )
            )
            await session.execute(stmt)
        await session.commit()