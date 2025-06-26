"""
FastAPI application for Z哥选股策略 stock analysis
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd

import pytz
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.operations import DatabaseOperations
from database.config import init_db
from api.scheduler_service import TradingDayChecker
from api.models import (
    SelectionResultResponse,
    StockResponse,
    ExecutionLogResponse,
    HealthResponse,
    StatsResponse,
    ErrorResponse,
    SelectionSummaryResponse,
    OHLCResponse,
    StockInfoResponse,
)
from api.stock_data_service import StockDataService

# Initialize FastAPI app
app = FastAPI(
    title="Z哥选股策略 API",
    description="REST API for stock selection analysis results",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=project_root / "static"), name="static")

# Initialize stock data service
stock_data_service = StockDataService(data_directory=str(project_root / "data"))

# Initialize scheduler service
from api.scheduler_service import IntegratedSchedulerService

scheduler_service = IntegratedSchedulerService()


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    try:
        init_db()
        print("Database initialized successfully")

        # Start the integrated scheduler
        await scheduler_service.start()
        print("Integrated scheduler started successfully")
    except Exception as e:
        print(f"Failed to initialize database or scheduler: {e}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        await scheduler_service.stop()
        print("Scheduler stopped successfully")
    except Exception as e:
        print(f"Error stopping scheduler: {e}")


# Dependency to get database operations
def get_db_ops():
    """Dependency to get database operations instance"""
    try:
        return DatabaseOperations()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )


# Exception handler for database errors
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", detail=str(exc), timestamp=datetime.now()
        ).dict(),
    )


@app.get("/")
async def root():
    """Serve the dashboard"""
    return FileResponse(project_root / "static" / "index.html")


@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard"""
    return FileResponse(project_root / "static" / "index.html")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        with DatabaseOperations() as db_ops:
            # Test database connection
            db_ops.get_selection_stats()
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(timestamp=datetime.now(), database_status=db_status)


@app.get("/api/selections/latest", response_model=List[SelectionResultResponse])
async def get_latest_selections(
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    db_ops: DatabaseOperations = Depends(get_db_ops),
):
    """Get latest selection results"""
    try:
        with db_ops:
            results = db_ops.get_latest_selections(limit=limit)
            return [
                SelectionResultResponse(
                    id=result.id,
                    stock_code=result.stock.code,
                    stock_name=result.stock.name,
                    strategy_name=result.strategy_name,
                    selection_date=result.selection_date,
                    is_selected=result.is_selected,
                    confidence_score=result.confidence_score,
                    selection_criteria=result.selection_criteria,
                    created_at=result.created_at,
                )
                for result in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/selections/date/{target_date}", response_model=SelectionSummaryResponse)
async def get_selections_by_date(
    target_date: date, db_ops: DatabaseOperations = Depends(get_db_ops)
):
    """Get selection results for specific date"""
    try:
        with db_ops:
            results = db_ops.get_selections_by_date(target_date)

            # Group by strategy
            strategy_counts = {}
            response_results = []

            for result in results:
                strategy_counts[result.strategy_name] = (
                    strategy_counts.get(result.strategy_name, 0) + 1
                )
                response_results.append(
                    SelectionResultResponse(
                        id=result.id,
                        stock_code=result.stock.code,
                        stock_name=result.stock.name,
                        strategy_name=result.strategy_name,
                        selection_date=result.selection_date,
                        is_selected=result.is_selected,
                        confidence_score=result.confidence_score,
                        selection_criteria=result.selection_criteria,
                        created_at=result.created_at,
                    )
                )

            return SelectionSummaryResponse(
                date=target_date,
                total_selected=len(results),
                strategies=strategy_counts,
                results=response_results,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/selections/strategy/{strategy_name}",
    response_model=List[SelectionResultResponse],
)
async def get_selections_by_strategy(
    strategy_name: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    db_ops: DatabaseOperations = Depends(get_db_ops),
):
    """Get selection results filtered by strategy"""
    try:
        with db_ops:
            results = db_ops.get_selections_by_strategy(strategy_name, limit=limit)
            return [
                SelectionResultResponse(
                    id=result.id,
                    stock_code=result.stock.code,
                    stock_name=result.stock.name,
                    strategy_name=result.strategy_name,
                    selection_date=result.selection_date,
                    is_selected=result.is_selected,
                    confidence_score=result.confidence_score,
                    selection_criteria=result.selection_criteria,
                    created_at=result.created_at,
                )
                for result in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/stocks/{stock_code}/history", response_model=List[SelectionResultResponse]
)
async def get_stock_history(
    stock_code: str, db_ops: DatabaseOperations = Depends(get_db_ops)
):
    """Get historical selection data for specific stock"""
    try:
        with db_ops:
            results = db_ops.get_stock_history(stock_code)
            return [
                SelectionResultResponse(
                    id=result.id,
                    stock_code=result.stock.code,
                    stock_name=result.stock.name,
                    strategy_name=result.strategy_name,
                    selection_date=result.selection_date,
                    is_selected=result.is_selected,
                    confidence_score=result.confidence_score,
                    selection_criteria=result.selection_criteria,
                    created_at=result.created_at,
                )
                for result in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db_ops: DatabaseOperations = Depends(get_db_ops)):
    """Get selection statistics"""
    try:
        with db_ops:
            stats = db_ops.get_selection_stats()
            return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs", response_model=List[ExecutionLogResponse])
async def get_execution_logs(
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    db_ops: DatabaseOperations = Depends(get_db_ops),
):
    """Get execution logs"""
    try:
        with db_ops:
            logs = db_ops.get_execution_logs(limit=limit)
            return [
                ExecutionLogResponse(
                    id=log.id,
                    execution_date=log.execution_date,
                    execution_type=log.execution_type,
                    status=log.status,
                    start_time=log.start_time,
                    end_time=log.end_time,
                    duration_seconds=log.duration_seconds,
                    stocks_processed=log.stocks_processed,
                    stocks_selected=log.stocks_selected,
                    error_message=log.error_message,
                    log_details=log.log_details,
                    created_at=log.created_at,
                )
                for log in logs
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New OHLC Data Endpoints


@app.get("/api/stocks", response_model=List[str])
async def get_available_stocks():
    """Get list of available stock codes"""
    try:
        return stock_data_service.get_available_stocks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{stock_code}/info", response_model=StockInfoResponse)
async def get_stock_info(stock_code: str):
    """Get basic information about a stock"""
    try:
        return stock_data_service.get_stock_info(stock_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks/{stock_code}/ohlc", response_model=OHLCResponse)
async def get_stock_ohlc_data(
    stock_code: str,
    period: str = Query(
        "daily", regex="^(daily|weekly|monthly)$", description="Time period"
    ),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(
        None, ge=1, le=5000, description="Maximum number of data points"
    ),
):
    """Get OHLC data for candlestick charts"""
    try:
        return stock_data_service.get_ohlc_data(
            stock_code=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Scheduler Management Endpoints


@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and job information"""
    try:
        return scheduler_service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/trigger")
async def trigger_manual_update():
    """Manually trigger a data update"""
    try:
        result = await scheduler_service.trigger_manual_update()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scheduler/update-status")
async def get_update_status(db_ops: DatabaseOperations = Depends(get_db_ops)):
    """Get data update status information"""
    try:
        with db_ops:
            statuses = db_ops.get_all_data_update_statuses()
            return [
                {
                    "id": status.id,
                    "update_type": status.update_type,
                    "last_update_time": (
                        status.last_update_time.isoformat()
                        if status.last_update_time
                        else None
                    ),
                    "last_update_date": (
                        status.last_update_date.isoformat()
                        if status.last_update_date
                        else None
                    ),
                    "status": status.status,
                    "next_scheduled_time": (
                        status.next_scheduled_time.isoformat()
                        if status.next_scheduled_time
                        else None
                    ),
                    "update_count": status.update_count,
                    "last_error_message": status.last_error_message,
                    "created_at": (
                        status.created_at.isoformat() if status.created_at else None
                    ),
                    "updated_at": (
                        status.updated_at.isoformat() if status.updated_at else None
                    ),
                }
                for status in statuses
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data-update-status/latest")
async def get_latest_data_update_status(
    db_ops: DatabaseOperations = Depends(get_db_ops),
):
    """Get the latest data update status with Beijing timezone formatting"""
    try:
        beijing_tz = pytz.timezone("Asia/Shanghai")

        with db_ops:
            # Get the latest full_update status
            status = db_ops.get_latest_data_update_status("full_update")

            if not status:
                return {
                    "has_update": False,
                    "message": "No data updates found",
                    "last_update_time": None,
                    "last_update_date": None,
                    "status": None,
                }

            # Convert UTC times to Beijing timezone
            last_update_time_beijing = None
            last_update_date_beijing = None

            if status.last_update_time is not None:
                # Assume stored time is UTC, convert to Beijing
                if status.last_update_time.tzinfo is None:
                    utc_time = pytz.utc.localize(status.last_update_time)
                else:
                    utc_time = status.last_update_time.astimezone(pytz.utc)
                last_update_time_beijing = utc_time.astimezone(beijing_tz)

            if status.last_update_date is not None:
                # Assume stored date is UTC, convert to Beijing
                if status.last_update_date.tzinfo is None:
                    utc_date = pytz.utc.localize(status.last_update_date)
                else:
                    utc_date = status.last_update_date.astimezone(pytz.utc)
                last_update_date_beijing = utc_date.astimezone(beijing_tz)

            return {
                "has_update": True,
                "last_update_time": (
                    last_update_time_beijing.isoformat()
                    if last_update_time_beijing
                    else None
                ),
                "last_update_date": (
                    last_update_date_beijing.isoformat()
                    if last_update_date_beijing
                    else None
                ),
                "status": status.status,
                "update_count": status.update_count,
                "last_error_message": status.last_error_message,
                "formatted_time": (
                    last_update_time_beijing.strftime("%Y-%m-%d %H:%M:%S")
                    if last_update_time_beijing
                    else None
                ),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data-freshness")
async def get_data_freshness():
    """Check data freshness by analyzing CSV files for most recent trading day data"""
    try:
        beijing_tz = pytz.timezone("Asia/Shanghai")
        trading_checker = TradingDayChecker()
        data_dir = project_root / "data"

        # Get current Beijing time and date
        now_beijing = datetime.now(beijing_tz)
        today = now_beijing.date()

        # Find the most recent trading day
        if trading_checker.is_trading_day(today):
            expected_date = today
        else:
            # Go back to find the last trading day
            check_date = today - timedelta(days=1)
            while (
                not trading_checker.is_trading_day(check_date)
                and (today - check_date).days < 10
            ):
                check_date -= timedelta(days=1)
            expected_date = check_date

        # Check a sample of CSV files to determine data freshness
        csv_files = list(data_dir.glob("*.csv"))
        csv_files = [
            f for f in csv_files if f.name != "stock_analysis.db"
        ]  # Exclude database file

        if not csv_files:
            return {
                "status": "no_data",
                "message": "No CSV data files found",
                "expected_date": expected_date.isoformat(),
                "files_checked": 0,
                "files_current": 0,
                "sample_files": [],
            }

        # Sample up to 10 files for checking
        sample_files = csv_files[:10]
        files_current = 0
        sample_results = []
        latest_data_date = None

        for csv_file in sample_files:
            try:
                # Read last 5 rows to check for recent data
                df = pd.read_csv(csv_file)
                if df.empty:
                    continue

                df["date"] = pd.to_datetime(df["date"])
                last_date = df["date"].max().date()

                # Update latest data date found
                if latest_data_date is None or last_date > latest_data_date:
                    latest_data_date = last_date

                is_current = last_date >= expected_date
                if is_current:
                    files_current += 1

                sample_results.append(
                    {
                        "file": csv_file.name,
                        "last_date": last_date.isoformat(),
                        "is_current": is_current,
                    }
                )

            except Exception as e:
                sample_results.append(
                    {"file": csv_file.name, "error": str(e), "is_current": False}
                )

        # Determine overall status
        if files_current == 0:
            status = "stale"
            if latest_data_date:
                days_behind = (expected_date - latest_data_date).days
                message = f"Data is {days_behind} trading day(s) behind. Latest data: {latest_data_date}"
            else:
                message = "No valid data found in CSV files"
        elif files_current == len(sample_results):
            status = "current"
            message = f"All checked files have current data for {expected_date}"
        else:
            status = "partial"
            message = f"{files_current}/{len(sample_results)} files have current data"

        return {
            "status": status,
            "message": message,
            "expected_date": expected_date.isoformat(),
            "latest_data_date": (
                latest_data_date.isoformat() if latest_data_date else None
            ),
            "files_checked": len(sample_results),
            "files_current": files_current,
            "sample_files": sample_results[:5],  # Return first 5 for display
            "is_trading_day": trading_checker.is_trading_day(today),
            "check_time": now_beijing.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
