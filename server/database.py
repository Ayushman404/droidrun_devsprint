import asyncio
from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Date, UniqueConstraint, Time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Setup the Engine
DATABASE_URL = "sqlite+aiosqlite:///enforcer.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# 2. Setup the Session
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# 3. Base Class
Base = declarative_base()

# --- TABLES ---

class AppConfig(Base):
    __tablename__ = "app_config"
    package_name = Column(String, primary_key=True)
    friendly_name = Column(String)
    daily_limit_mins = Column(Integer, default=30)
    is_blocked = Column(Boolean, default=False)

class DailyUsage(Base):
    __tablename__ = "daily_usage"
    id = Column(Integer, primary_key=True)
    package_name = Column(String, nullable=False)
    usage_date = Column(Date, default=date.today)
    seconds_spent = Column(Integer, default=0)
    strikes = Column(Integer, default=0)  # <--- NEW COLUMN ADDED HERE
    
    __table_args__ = (UniqueConstraint('package_name', 'usage_date', name='_pkg_date_uc'),)
    

class ScheduleRule(Base):
    __tablename__ = "schedule_rules"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Time, nullable=False) # e.g., 09:00:00
    end_time = Column(Time, nullable=False)   # e.g., 17:00:00
    label = Column(String)                    # "Deep Work"
    
    # The Configs to Enforce
    study_mode = Column(Boolean, default=False)
    doomscroll_mode = Column(Boolean, default=True)
    punishment_type = Column(String, default="HOME")
    punishment_target = Column(String, default="")

# --- INITIALIZATION ---

async def init_db():
    async with engine.begin() as conn:
        # This creates tables only if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    print("Database Initialized: enforcer.db created.")

if __name__ == "__main__":
    asyncio.run(init_db())