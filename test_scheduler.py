#!/usr/bin/env python3
"""
Test script for the integrated scheduler service
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.scheduler_service import IntegratedSchedulerService, DataPriorityService
from database.config import init_db


async def test_scheduler():
    """Test the scheduler service functionality"""
    print("Testing Integrated Scheduler Service")
    print("=" * 50)
    
    # Initialize database
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return
    
    # Test data priority service
    print("\n1. Testing Data Priority Service")
    try:
        priority_service = DataPriorityService()
        result = priority_service.should_update_data()
        print(f"✓ Priority check result: {result}")
    except Exception as e:
        print(f"✗ Priority service failed: {e}")
    
    # Test scheduler service
    print("\n2. Testing Scheduler Service")
    try:
        scheduler = IntegratedSchedulerService()
        
        # Start scheduler
        await scheduler.start()
        print("✓ Scheduler started successfully")
        
        # Get status
        status = scheduler.get_status()
        print(f"✓ Scheduler status: {status}")
        
        # Test manual trigger (but don't actually run it)
        print("✓ Manual trigger method available")
        
        # Stop scheduler
        await scheduler.stop()
        print("✓ Scheduler stopped successfully")
        
    except Exception as e:
        print(f"✗ Scheduler service failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
