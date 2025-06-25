"""
Pydantic models for API requests and responses
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StockResponse(BaseModel):
    """Stock information response model"""
    id: int
    code: str
    name: Optional[str] = None
    market_cap: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SelectionResultResponse(BaseModel):
    """Selection result response model"""
    id: int
    stock_code: str = Field(..., description="Stock code")
    stock_name: Optional[str] = Field(None, description="Stock name")
    strategy_name: str = Field(..., description="Strategy name")
    selection_date: datetime = Field(..., description="Selection date")
    is_selected: bool = Field(..., description="Whether stock was selected")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    selection_criteria: Optional[str] = Field(None, description="Selection criteria")
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionLogResponse(BaseModel):
    """Execution log response model"""
    id: int
    execution_date: date
    execution_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    stocks_processed: int = 0
    stocks_selected: int = 0
    error_message: Optional[str] = None
    log_details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SelectionSummaryResponse(BaseModel):
    """Summary of selection results"""
    date: date
    total_selected: int
    strategies: Dict[str, int]
    results: List[SelectionResultResponse]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    database_status: str
    version: str = "1.0.0"


class StatsResponse(BaseModel):
    """Statistics response"""
    total_selections: int
    strategy_stats: Dict[str, int]
    latest_execution: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
