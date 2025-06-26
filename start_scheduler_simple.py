#!/usr/bin/env python3
"""
Simple scheduler startup script
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

from database.config import init_db
from api.scheduler_service import IntegratedSchedulerService

async def start_scheduler():
    print('🚀 Starting Trading System Scheduler')
    print('=' * 50)
    
    scheduler = None
    try:
        # Initialize database
        print('📊 Initializing database...')
        init_db()
        print('✅ Database initialized successfully')
        
        # Create and start scheduler
        print('⏰ Starting scheduler service...')
        scheduler = IntegratedSchedulerService()
        await scheduler.start()
        print('✅ Scheduler started successfully')
        
        # Display status
        status = scheduler.get_status()
        print('📋 Scheduler Status:')
        print(f'   Running: {status["is_running"]}')
        print(f'   Timezone: {status["timezone"]}')
        
        for job in status['jobs']:
            print(f'   Job: {job["name"]}')
            print(f'   Next Run: {job["next_run_time"]}')
        
        print('✅ System ready! Scheduler will run daily at 4:00 PM Beijing time.')
        print('🔄 Keeping scheduler running...')
        
        # Keep running
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print('🛑 Shutdown requested...')
        if scheduler:
            await scheduler.stop()
        print('✅ Scheduler stopped')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        if scheduler:
            await scheduler.stop()

if __name__ == "__main__":
    # Run the scheduler
    asyncio.run(start_scheduler())
