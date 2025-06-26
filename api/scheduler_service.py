"""
Integrated scheduler service for automated trading data collection
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.operations import DatabaseOperations
from database.models import DataUpdateStatus

# Configure logging
logger = logging.getLogger("scheduler_service")


class TradingDayChecker:
    """
    Check if a given date is a trading day for Chinese stock market
    """

    def __init__(self):
        # Chinese stock market holidays (approximate - should be updated annually)
        self.holidays_2025 = {
            # New Year
            date(2025, 1, 1),
            # Spring Festival
            date(2025, 1, 28),
            date(2025, 1, 29),
            date(2025, 1, 30),
            date(2025, 1, 31),
            date(2025, 2, 3),
            date(2025, 2, 4),
            # Tomb Sweeping Day
            date(2025, 4, 5),
            date(2025, 4, 6),
            date(2025, 4, 7),
            # Labor Day
            date(2025, 5, 1),
            date(2025, 5, 2),
            date(2025, 5, 5),
            # Dragon Boat Festival (端午节)
            date(2025, 5, 31),  # Saturday (端午节当天)
            date(2025, 6, 2),  # Monday (调休)
            # Mid-Autumn Festival
            date(2025, 10, 6),
            date(2025, 10, 7),
            date(2025, 10, 8),
            # National Day
            date(2025, 10, 1),
            date(2025, 10, 2),
            date(2025, 10, 3),
        }

    def is_trading_day(self, check_date: date) -> bool:
        """Check if the given date is a trading day"""
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        # Holiday check
        if check_date in self.holidays_2025:
            return False
        return True

    def get_next_trading_day(self, from_date: Optional[date] = None) -> date:
        """Get the next trading day from the given date"""
        if from_date is None:
            from_date = date.today()
        check_date = from_date + timedelta(days=1)
        while not self.is_trading_day(check_date):
            check_date += timedelta(days=1)
        return check_date


class DataPriorityService:
    """
    Service to determine when data updates are needed
    """

    def __init__(self):
        self.trading_checker = TradingDayChecker()
        self.beijing_tz = pytz.timezone("Asia/Shanghai")

    def should_update_data(self, update_type: str = "full_update") -> Dict[str, Any]:
        """
        Determine if data should be updated based on priority logic
        """
        try:
            with DatabaseOperations() as db_ops:
                # Get the latest update status
                status = db_ops.get_latest_data_update_status(update_type)

                now_beijing = datetime.now(self.beijing_tz)
                today = now_beijing.date()

                # Check if today is a trading day
                if not self.trading_checker.is_trading_day(today):
                    return {
                        "should_update": False,
                        "reason": f"Today ({today}) is not a trading day",
                        "next_trading_day": self.trading_checker.get_next_trading_day(
                            today
                        ),
                    }

                # Check if it's past 4 PM Beijing time
                update_time = now_beijing.replace(
                    hour=16, minute=0, second=0, microsecond=0
                )
                is_past_update_time = now_beijing >= update_time

                # If no previous update exists, we should update
                if not status:
                    return {
                        "should_update": True,
                        "reason": "No previous update record found",
                        "is_past_update_time": is_past_update_time,
                    }

                # Check if we already updated today
                last_update_date = (
                    status.last_update_date.date() if status.last_update_date else None
                )
                if last_update_date == today and status.status == "success":
                    return {
                        "should_update": False,
                        "reason": f"Data already updated today ({today})",
                        "last_update": status.last_update_time,
                    }

                # If we haven't updated today and it's past update time, we should update
                if last_update_date != today and is_past_update_time:
                    return {
                        "should_update": True,
                        "reason": f"Past update time ({update_time.strftime('%H:%M')}) and no update today",
                        "is_past_update_time": is_past_update_time,
                    }

                # If we haven't updated today but it's not yet update time
                if last_update_date != today and not is_past_update_time:
                    return {
                        "should_update": False,
                        "reason": f"Not yet update time (current: {now_beijing.strftime('%H:%M')}, scheduled: 16:00)",
                        "next_update_time": update_time,
                    }

                return {
                    "should_update": False,
                    "reason": "Default case - no update needed",
                    "status": status.status if status else None,
                }

        except Exception as e:
            logger.error(f"Error checking update priority: {e}")
            return {
                "should_update": True,
                "reason": f"Error checking status, defaulting to update: {e}",
                "error": str(e),
            }


class IntegratedSchedulerService:
    """
    Integrated scheduler service for FastAPI application
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Shanghai"))
        self.trading_checker = TradingDayChecker()
        self.priority_service = DataPriorityService()
        self.project_root = project_root
        self.is_running = False

        # Setup event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

    async def start(self):
        """Start the scheduler"""
        if not self.is_running:
            # Add the daily job
            self.scheduler.add_job(
                self._run_daily_workflow,
                CronTrigger(hour=16, minute=0, timezone=pytz.timezone("Asia/Shanghai")),
                id="daily_trading_workflow",
                name="Daily Trading Data Collection",
                replace_existing=True,
            )

            self.scheduler.start()
            self.is_running = True
            logger.info(
                "Integrated scheduler started - Daily execution at 16:00 Beijing time"
            )

    async def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Integrated scheduler stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status information"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

        return {
            "is_running": self.is_running,
            "jobs": jobs,
            "timezone": str(self.scheduler.timezone),
        }

    async def trigger_manual_update(
        self, update_type: str = "full_update"
    ) -> Dict[str, Any]:
        """Manually trigger a data update"""
        logger.info(f"Manual update triggered: {update_type}")
        return await self._run_daily_workflow(manual_trigger=True)

    def _job_executed(self, event):
        """Handle job execution events"""
        logger.info(f"Job {event.job_id} executed successfully")

    def _job_error(self, event):
        """Handle job error events"""
        logger.error(f"Job {event.job_id} failed: {event.exception}")

    async def _run_daily_workflow(self, manual_trigger: bool = False):
        """Run the complete daily workflow"""
        start_time = datetime.now(pytz.timezone("Asia/Shanghai"))
        logger.info("=" * 60)
        logger.info(f"Starting daily workflow at {start_time}")

        # Check if update is needed (unless manually triggered)
        if not manual_trigger:
            priority_check = self.priority_service.should_update_data()
            if not priority_check["should_update"]:
                logger.info(f"Skipping update: {priority_check['reason']}")
                return {"status": "skipped", "reason": priority_check["reason"]}

        # Update status to in_progress
        try:
            await self._update_status("full_update", "in_progress", start_time)
        except Exception as e:
            logger.warning(f"Failed to update status: {e}")

        # Run data fetch
        fetch_success = await self._run_data_fetch()

        # Run stock selection
        selection_success = await self._run_stock_selection()

        # Determine overall status
        end_time = datetime.now(pytz.timezone("Asia/Shanghai"))
        if fetch_success and selection_success:
            status = "success"
            logger.info("Daily workflow completed successfully")
        elif selection_success:
            status = "partial"
            logger.warning("Workflow completed with data fetch issues")
        else:
            status = "failed"
            logger.error("Workflow failed")

        # Update final status
        try:
            await self._update_status("full_update", status, start_time, end_time)
        except Exception as e:
            logger.warning(f"Failed to update final status: {e}")

        logger.info(f"Workflow completed at {end_time}")
        logger.info("=" * 60)

        return {
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "fetch_success": fetch_success,
            "selection_success": selection_success,
        }

    async def _run_data_fetch(self) -> bool:
        """Run data fetching"""
        command = [
            "uv",
            "run",
            "python",
            "fetch_kline.py",
            "--small-player",
            "True",
            "--min-mktcap",
            "2.5e10",
            "--start",
            "20050101",
            "--end",
            "today",
            "--out",
            "./data",
            "--workers",
            "20",
        ]
        return await self._run_command(command, "Data Fetch")

    async def _run_stock_selection(self) -> bool:
        """Run stock selection"""
        command = [
            "uv",
            "run",
            "python",
            "select_stock_enhanced.py",
            "--data-dir",
            "./data",
            "--config",
            "./configs.json",
        ]
        return await self._run_command(command, "Stock Selection")

    async def _run_command(self, command: List[str], description: str) -> bool:
        """Run a command asynchronously"""
        logger.info(f"Starting: {description}")
        logger.info(f"Command: {' '.join(command)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=3600)

            if process.returncode == 0:
                logger.info(f"Success: {description}")
                if stdout:
                    try:
                        logger.info(f"Output: {stdout.decode('utf-8')}")
                    except UnicodeDecodeError:
                        logger.info(
                            f"Output: {stdout.decode('utf-8', errors='replace')}"
                        )
                return True
            else:
                logger.error(f"Failed: {description}")
                try:
                    logger.error(f"Error: {stderr.decode('utf-8')}")
                except UnicodeDecodeError:
                    logger.error(f"Error: {stderr.decode('utf-8', errors='replace')}")
                return False

        except asyncio.TimeoutError:
            logger.error(f"Timeout: {description}")
            return False
        except Exception as e:
            logger.error(f"Exception in {description}: {e}")
            return False

    async def _update_status(
        self,
        update_type: str,
        status: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ):
        """Update the data update status"""
        try:
            with DatabaseOperations() as db_ops:
                db_ops.update_data_update_status(
                    update_type=update_type,
                    status=status,
                    last_update_time=start_time,
                    last_update_date=start_time,
                    end_time=end_time,
                )
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            raise
