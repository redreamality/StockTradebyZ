"""
Stock data service for reading and processing CSV files
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from api.models import OHLCDataPoint, OHLCResponse, StockInfoResponse


class StockDataService:
    """Service for reading and processing stock OHLC data from CSV files"""
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the stock data service
        
        Args:
            data_directory: Directory containing CSV files
        """
        self.data_directory = Path(data_directory)
        self._cache = {}  # Simple in-memory cache for CSV data
        
    def get_available_stocks(self) -> List[str]:
        """
        Get list of available stock codes from CSV files
        
        Returns:
            List of stock codes
        """
        stock_codes = []
        if self.data_directory.exists():
            for file_path in self.data_directory.glob("*.csv"):
                # Extract stock code from filename (e.g., "000001.csv" -> "000001")
                stock_code = file_path.stem
                if stock_code != "stock_analysis":  # Skip database file
                    stock_codes.append(stock_code)
        return sorted(stock_codes)
    
    def get_stock_info(self, stock_code: str) -> StockInfoResponse:
        """
        Get basic information about a stock
        
        Args:
            stock_code: Stock code (e.g., "000001")
            
        Returns:
            StockInfoResponse with basic stock information
        """
        csv_path = self.data_directory / f"{stock_code}.csv"
        
        if not csv_path.exists():
            return StockInfoResponse(
                code=stock_code,
                name=None,
                has_data=False,
                data_start_date=None,
                data_end_date=None,
                total_records=0
            )
        
        try:
            # Read just the first and last few rows to get date range
            df = pd.read_csv(csv_path)
            
            if df.empty:
                return StockInfoResponse(
                    code=stock_code,
                    name=None,
                    has_data=False,
                    data_start_date=None,
                    data_end_date=None,
                    total_records=0
                )
            
            # Get date range
            df['date'] = pd.to_datetime(df['date'])
            start_date = df['date'].min().strftime('%Y-%m-%d')
            end_date = df['date'].max().strftime('%Y-%m-%d')
            
            return StockInfoResponse(
                code=stock_code,
                name=None,  # We don't have stock names in CSV files
                has_data=True,
                data_start_date=start_date,
                data_end_date=end_date,
                total_records=len(df)
            )
            
        except Exception as e:
            print(f"Error reading stock info for {stock_code}: {e}")
            return StockInfoResponse(
                code=stock_code,
                name=None,
                has_data=False,
                data_start_date=None,
                data_end_date=None,
                total_records=0
            )
    
    def get_ohlc_data(
        self, 
        stock_code: str, 
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> OHLCResponse:
        """
        Get OHLC data for a stock
        
        Args:
            stock_code: Stock code (e.g., "000001")
            period: Time period ("daily", "weekly", "monthly")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of data points to return (most recent)
            
        Returns:
            OHLCResponse with OHLC data
        """
        csv_path = self.data_directory / f"{stock_code}.csv"
        
        if not csv_path.exists():
            return OHLCResponse(
                stock_code=stock_code,
                stock_name=None,
                period=period,
                data=[],
                total_points=0
            )
        
        try:
            # Check cache first
            cache_key = f"{stock_code}_{period}_{start_date}_{end_date}_{limit}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Read CSV data
            df = pd.read_csv(csv_path)
            
            if df.empty:
                return OHLCResponse(
                    stock_code=stock_code,
                    stock_name=None,
                    period=period,
                    data=[],
                    total_points=0
                )
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter by date range if specified
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['date'] >= start_dt]
            
            if end_date:
                end_dt = pd.to_datetime(end_date)
                df = df[df['date'] <= end_dt]
            
            # Sort by date
            df = df.sort_values('date')
            
            # Apply period aggregation
            if period == "weekly":
                df = self._aggregate_weekly(df)
            elif period == "monthly":
                df = self._aggregate_monthly(df)
            # For daily, use data as-is
            
            # Apply limit if specified (take most recent)
            if limit and len(df) > limit:
                df = df.tail(limit)
            
            # Convert to OHLC data points
            data_points = []
            for _, row in df.iterrows():
                data_points.append(OHLCDataPoint(
                    time=row['date'].strftime('%Y-%m-%d'),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']) if pd.notna(row['volume']) else None
                ))
            
            response = OHLCResponse(
                stock_code=stock_code,
                stock_name=None,
                period=period,
                data=data_points,
                total_points=len(data_points)
            )
            
            # Cache the response
            self._cache[cache_key] = response
            
            return response
            
        except Exception as e:
            print(f"Error reading OHLC data for {stock_code}: {e}")
            return OHLCResponse(
                stock_code=stock_code,
                stock_name=None,
                period=period,
                data=[],
                total_points=0
            )
    
    def _aggregate_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily data to weekly"""
        df_weekly = df.set_index('date').resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'amount': 'sum',
            'turnover': 'mean'
        }).dropna()
        
        return df_weekly.reset_index()
    
    def _aggregate_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily data to monthly"""
        df_monthly = df.set_index('date').resample('M').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'amount': 'sum',
            'turnover': 'mean'
        }).dropna()
        
        return df_monthly.reset_index()
    
    def clear_cache(self):
        """Clear the data cache"""
        self._cache.clear()
