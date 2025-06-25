"""
FastAPI application for Z哥选股策略 stock analysis
"""

import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.operations import DatabaseOperations
from database.config import init_db
from api.models import (
    SelectionResultResponse,
    StockResponse,
    ExecutionLogResponse,
    HealthResponse,
    StatsResponse,
    ErrorResponse,
    SelectionSummaryResponse,
)

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


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
