"""
Automated daily execution scheduler for stock analysis
"""

import logging
import schedule
import time
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.operations import DatabaseOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "scheduler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("scheduler")


class TradingDayChecker:
    """
    Check if a given date is a trading day for Chinese stock market
    """

    def __init__(self):
        # Chinese stock market holidays (approximate - should be updated annually)
        # This is a simplified version - in production, use a proper holiday API
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
            # Dragon Boat Festival
            date(2025, 5, 31),
            date(2025, 6, 2),
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
        """
        Check if the given date is a trading day
        """
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Holiday check
        if check_date in self.holidays_2025:
            return False

        return True

    def get_next_trading_day(self, from_date: date = None) -> date:
        """
        Get the next trading day from the given date
        """
        if from_date is None:
            from_date = date.today()

        check_date = from_date + timedelta(days=1)
        while not self.is_trading_day(check_date):
            check_date += timedelta(days=1)

        return check_date


class StockAnalysisScheduler:
    """
    Automated scheduler for stock analysis workflow
    """

    def __init__(self):
        self.trading_checker = TradingDayChecker()
        self.project_root = project_root
        self.max_retries = 3
        self.retry_delay = 300  # 5 minutes

    def run_command(self, command: List[str], description: str) -> bool:
        """
        Run a command with error handling and logging
        """
        logger.info(f"Starting: {description}")
        logger.info(f"Command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info(f"Success: {description}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout}")
                return True
            else:
                logger.error(f"Failed: {description}")
                logger.error(f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout: {description}")
            return False
        except Exception as e:
            logger.error(f"Exception in {description}: {e}")
            return False

    def run_data_fetch(self) -> bool:
        """
        Run data fetching with retry logic
        """
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

        for attempt in range(self.max_retries):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)

            if self.run_command(command, "Data Fetch"):
                return True

        logger.error("Data fetch failed after all retries")
        return False

    def run_stock_selection(self) -> bool:
        """
        Run stock selection with retry logic
        """
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

        for attempt in range(self.max_retries):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)

            if self.run_command(command, "Stock Selection"):
                return True

        logger.error("Stock selection failed after all retries")
        return False

    def run_full_workflow(self):
        """
        Run the complete stock analysis workflow
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info(f"Starting automated stock analysis workflow at {start_time}")

        # Check if today is a trading day
        today = date.today()
        if not self.trading_checker.is_trading_day(today):
            logger.info(f"Today ({today}) is not a trading day. Skipping execution.")
            return

        # Log execution start
        try:
            with DatabaseOperations() as db_ops:
                db_ops.log_execution(
                    execution_type="full_workflow",
                    status="started",
                    start_time=start_time,
                )
        except Exception as e:
            logger.warning(f"Failed to log execution start: {e}")

        # Run data fetch
        fetch_success = self.run_data_fetch()

        # Run stock selection (even if fetch fails, we might have existing data)
        selection_success = self.run_stock_selection()

        # Determine overall status
        end_time = datetime.now()
        if fetch_success and selection_success:
            status = "success"
            logger.info("Full workflow completed successfully")
        elif selection_success:
            status = "partial"
            logger.warning("Workflow completed with data fetch issues")
        else:
            status = "failed"
            logger.error("Workflow failed")

        # Log execution completion
        try:
            with DatabaseOperations() as db_ops:
                db_ops.log_execution(
                    execution_type="full_workflow",
                    status=status,
                    start_time=start_time,
                    end_time=end_time,
                    log_details=f"Fetch: {'success' if fetch_success else 'failed'}, Selection: {'success' if selection_success else 'failed'}",
                )
        except Exception as e:
            logger.warning(f"Failed to log execution completion: {e}")

        logger.info(f"Workflow completed at {end_time}")
        logger.info("=" * 60)

    def start_scheduler(self):
        """
        Start the scheduler with daily execution at 4:00 PM Beijing time
        """
        logger.info("Starting stock analysis scheduler...")
        logger.info("Scheduled to run daily at 16:00 (4:00 PM) Beijing time")

        # Schedule daily execution at 4:00 PM
        schedule.every().day.at("16:00").do(self.run_full_workflow)

        # Also allow manual trigger for testing
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        logger.info("Next scheduled run: " + str(schedule.next_run()))

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")


def main():
    """
    Main function to start the scheduler
    """
    scheduler = StockAnalysisScheduler()

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        # Run immediately for testing
        logger.info("Running workflow immediately (test mode)")
        scheduler.run_full_workflow()
    else:
        # Start the scheduler
        scheduler.start_scheduler()


if __name__ == "__main__":
    main()
