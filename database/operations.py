"""
Database operations for stock analysis
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from database.config import SessionLocal
from database.models import Stock, SelectionResult, ExecutionLog


class DatabaseOperations:
    """
    Database operations class for stock analysis
    """

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_or_create_stock(
        self, code: str, name: str = None, market_cap: float = None
    ) -> Stock:
        """
        Get existing stock or create new one
        """
        stock = self.db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            stock = Stock(code=code, name=name, market_cap=market_cap)
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        elif name and stock.name != name:
            # Update stock name if provided and different
            stock.name = name
            stock.updated_at = datetime.utcnow()
            self.db.commit()
        return stock

    def save_selection_result(
        self,
        stock_code: str,
        strategy_name: str,
        selection_date: datetime,
        is_selected: bool = True,
        confidence_score: float = None,
        criteria: str = None,
    ) -> SelectionResult:
        """
        Save stock selection result
        """
        stock = self.get_or_create_stock(stock_code)

        # Check if result already exists for this date and strategy
        existing = (
            self.db.query(SelectionResult)
            .filter(
                and_(
                    SelectionResult.stock_id == stock.id,
                    SelectionResult.strategy_name == strategy_name,
                    SelectionResult.selection_date == selection_date,
                )
            )
            .first()
        )

        if existing:
            # Update existing result
            existing.is_selected = is_selected
            existing.confidence_score = confidence_score
            existing.selection_criteria = criteria
            result = existing
        else:
            # Create new result
            result = SelectionResult(
                stock_id=stock.id,
                strategy_name=strategy_name,
                selection_date=selection_date,
                is_selected=is_selected,
                confidence_score=confidence_score,
                selection_criteria=criteria,
            )
            self.db.add(result)

        self.db.commit()
        self.db.refresh(result)
        return result

    def get_latest_selections(self, limit: int = 100) -> List[SelectionResult]:
        """
        Get latest selection results
        """
        return (
            self.db.query(SelectionResult)
            .join(Stock)
            .filter(SelectionResult.is_selected == True)
            .order_by(desc(SelectionResult.selection_date))
            .limit(limit)
            .all()
        )

    def get_selections_by_date(self, target_date: date) -> List[SelectionResult]:
        """
        Get selection results for specific date
        """
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        return (
            self.db.query(SelectionResult)
            .join(Stock)
            .filter(
                and_(
                    SelectionResult.selection_date >= start_datetime,
                    SelectionResult.selection_date <= end_datetime,
                    SelectionResult.is_selected == True,
                )
            )
            .order_by(SelectionResult.strategy_name)
            .all()
        )

    def get_selections_by_strategy(
        self, strategy_name: str, limit: int = 100
    ) -> List[SelectionResult]:
        """
        Get selection results filtered by strategy
        """
        return (
            self.db.query(SelectionResult)
            .join(Stock)
            .filter(
                and_(
                    SelectionResult.strategy_name == strategy_name,
                    SelectionResult.is_selected == True,
                )
            )
            .order_by(desc(SelectionResult.selection_date))
            .limit(limit)
            .all()
        )

    def get_stock_history(self, stock_code: str) -> List[SelectionResult]:
        """
        Get historical selection data for specific stock
        """
        return (
            self.db.query(SelectionResult)
            .join(Stock)
            .filter(and_(Stock.code == stock_code, SelectionResult.is_selected == True))
            .order_by(desc(SelectionResult.selection_date))
            .all()
        )

    def log_execution(
        self,
        execution_type: str,
        status: str,
        start_time: datetime,
        end_time: datetime = None,
        stocks_processed: int = 0,
        stocks_selected: int = 0,
        error_message: str = None,
        log_details: str = None,
    ) -> ExecutionLog:
        """
        Log execution details
        """
        duration = None
        if end_time and start_time:
            duration = (end_time - start_time).total_seconds()

        log_entry = ExecutionLog(
            execution_date=start_time.date(),
            execution_type=execution_type,
            status=status,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            stocks_processed=stocks_processed,
            stocks_selected=stocks_selected,
            error_message=error_message,
            log_details=log_details,
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    def get_execution_logs(self, limit: int = 50) -> List[ExecutionLog]:
        """
        Get recent execution logs
        """
        return (
            self.db.query(ExecutionLog)
            .order_by(desc(ExecutionLog.start_time))
            .limit(limit)
            .all()
        )

    def get_selection_stats(self) -> Dict[str, Any]:
        """
        Get selection statistics
        """
        total_selections = (
            self.db.query(SelectionResult)
            .filter(SelectionResult.is_selected == True)
            .count()
        )

        strategy_stats = (
            self.db.query(
                SelectionResult.strategy_name,
                func.count(SelectionResult.id).label("count"),
            )
            .filter(SelectionResult.is_selected == True)
            .group_by(SelectionResult.strategy_name)
            .all()
        )

        latest_execution = (
            self.db.query(ExecutionLog).order_by(desc(ExecutionLog.start_time)).first()
        )

        return {
            "total_selections": total_selections,
            "strategy_stats": {
                stat.strategy_name: stat.count for stat in strategy_stats
            },
            "latest_execution": (
                latest_execution.start_time if latest_execution else None
            ),
        }
