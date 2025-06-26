#!/usr/bin/env python3
"""
Startup script for the trading system with integrated scheduler
"""

import asyncio
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.config import init_db
from api.scheduler_service import IntegratedSchedulerService


class TradingSystemManager:
    """Manager for the trading system with scheduler"""
    
    def __init__(self):
        self.scheduler = None
        self.running = False
    
    async def start(self):
        """Start the trading system"""
        print("🚀 Starting Trading System with Integrated Scheduler")
        print("=" * 60)
        
        try:
            # Initialize database
            print("📊 Initializing database...")
            init_db()
            print("✅ Database initialized successfully")
            
            # Create and start scheduler
            print("⏰ Starting scheduler service...")
            self.scheduler = IntegratedSchedulerService()
            await self.scheduler.start()
            print("✅ Scheduler started successfully")
            
            # Display status
            status = self.scheduler.get_status()
            print(f"\n📋 Scheduler Status:")
            print(f"   Running: {status['is_running']}")
            print(f"   Timezone: {status['timezone']}")
            
            for job in status['jobs']:
                print(f"   Job: {job['name']}")
                print(f"   Next Run: {job['next_run_time']}")
            
            print(f"\n🌐 FastAPI server should be started separately:")
            print(f"   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000")
            
            print(f"\n📊 Dashboard will be available at:")
            print(f"   http://localhost:8000")
            
            print(f"\n🔧 Scheduler API endpoints:")
            print(f"   GET  /api/scheduler/status")
            print(f"   POST /api/scheduler/trigger")
            print(f"   GET  /api/scheduler/update-status")
            
            self.running = True
            print(f"\n✅ System ready! Press Ctrl+C to stop.")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Shutdown requested...")
            await self.stop()
        except Exception as e:
            print(f"❌ Error starting system: {e}")
            import traceback
            traceback.print_exc()
            await self.stop()
    
    async def stop(self):
        """Stop the trading system"""
        print("🛑 Stopping trading system...")
        self.running = False
        
        if self.scheduler:
            try:
                await self.scheduler.stop()
                print("✅ Scheduler stopped successfully")
            except Exception as e:
                print(f"⚠️  Error stopping scheduler: {e}")
        
        print("👋 Trading system stopped")


async def main():
    """Main function"""
    manager = TradingSystemManager()
    
    # Handle signals for graceful shutdown
    def signal_handler():
        print(f"\n🛑 Signal received, shutting down...")
        asyncio.create_task(manager.stop())
    
    # Set up signal handlers
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)
    
    await manager.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
