"""
SQLAlchemy models for stock analysis database
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from database.config import Base


class Stock(Base):
    """
    Stock metadata table
    """

    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(10), unique=True, index=True, nullable=False
    )  # Stock code like "600519"
    name = Column(String(100), nullable=True)  # Stock name
    market_cap = Column(Float, nullable=True)  # Market capitalization
    sector = Column(String(100), nullable=True)  # Industry sector
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    selection_results = relationship("SelectionResult", back_populates="stock")

    def __repr__(self):
        return f"<Stock(code='{self.code}', name='{self.name}')>"


class SelectionResult(Base):
    """
    Daily stock selection results from strategies
    """

    __tablename__ = "selection_results"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    strategy_name = Column(
        String(50), nullable=False
    )  # "少妇战法", "补票战法", "TePu战法"
    strategy_alias = Column(String(100), nullable=True)  # English alias if needed
    selection_date = Column(DateTime, nullable=False)  # Trading date for selection
    is_selected = Column(Boolean, default=True)  # True if stock was selected
    confidence_score = Column(Float, nullable=True)  # Optional confidence score
    selection_criteria = Column(Text, nullable=True)  # JSON string of criteria met
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    stock = relationship("Stock", back_populates="selection_results")

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_selection_date_strategy", "selection_date", "strategy_name"),
        Index("idx_stock_strategy", "stock_id", "strategy_name"),
    )

    def __repr__(self):
        return f"<SelectionResult(stock_id={self.stock_id}, strategy='{self.strategy_name}', date='{self.selection_date}')>"


class ExecutionLog(Base):
    """
    Execution logs for automated runs
    """

    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_date = Column(DateTime, nullable=False)
    execution_type = Column(
        String(50), nullable=False
    )  # "fetch_data", "stock_selection", "full_workflow"
    status = Column(String(20), nullable=False)  # "success", "failed", "partial"
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    stocks_processed = Column(Integer, default=0)
    stocks_selected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    log_details = Column(Text, nullable=True)  # Additional execution details
    created_at = Column(DateTime, default=datetime.utcnow)

    # Index for better query performance
    __table_args__ = (
        Index("idx_execution_date_type", "execution_date", "execution_type"),
    )

    def __repr__(self):
        return f"<ExecutionLog(date='{self.execution_date}', type='{self.execution_type}', status='{self.status}')>"
