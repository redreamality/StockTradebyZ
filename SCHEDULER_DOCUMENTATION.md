# Integrated Scheduler System Documentation

## Overview

The trading system now includes an integrated scheduler that automatically runs daily at 4:00 PM Beijing time (UTC+8) to execute the trading data collection and analysis workflow. This replaces the previous manual command-line approach with a fully automated, background-running system within the FastAPI application.

## Key Features

### 1. **Automated Scheduling**
- **Daily Execution**: Runs automatically at 16:00 Beijing time
- **Trading Day Awareness**: Only executes on trading days (excludes weekends and Chinese holidays)
- **Background Processing**: Runs in the background without blocking the web service
- **Timezone Handling**: Properly handles Beijing timezone (Asia/Shanghai)

### 2. **Data Priority Logic**
The system implements intelligent data update logic:
- **Local-First Approach**: Web dashboard displays data from local CSV files
- **Conditional Updates**: Only triggers data updates when:
  - No data exists for the current date, OR
  - Current time has reached or passed 4 PM Beijing time
- **Prevents Duplicate Updates**: Avoids unnecessary data collection if already updated today

### 3. **Status Tracking**
- **Database Tracking**: Maintains records of when data was last updated
- **Status Monitoring**: Tracks success/failure of each update attempt
- **Error Logging**: Captures and stores error messages for troubleshooting

### 4. **API Management**
New endpoints for scheduler management:
- `GET /api/scheduler/status` - Check scheduler status and next run times
- `POST /api/scheduler/trigger` - Manually trigger a data update
- `GET /api/scheduler/update-status` - View data update history and status

## Architecture

### Components

1. **IntegratedSchedulerService** (`api/scheduler_service.py`)
   - Main scheduler service using APScheduler
   - Handles job scheduling and execution
   - Manages background task execution

2. **DataPriorityService** (within scheduler_service.py)
   - Implements data update priority logic
   - Checks if updates are needed based on time and existing data
   - Handles trading day validation

3. **TradingDayChecker** (within scheduler_service.py)
   - Validates Chinese stock market trading days
   - Excludes weekends and holidays
   - Provides next trading day calculation

4. **DataUpdateStatus** (`database/models.py`)
   - New database model for tracking update status
   - Stores last update times, status, and error information

### Database Schema

New table: `data_update_status`
```sql
- id: Primary key
- update_type: Type of update (e.g., "full_update")
- last_update_time: When the update was performed
- last_update_date: Trading date for which data was updated
- status: "success", "failed", "in_progress"
- next_scheduled_time: When next update is scheduled
- update_count: Number of successful updates
- last_error_message: Error details if failed
- extra_data: JSON metadata
- created_at, updated_at: Timestamps
```

## Usage

### Starting the System

1. **Automatic Startup**: The scheduler starts automatically when the FastAPI application starts:
   ```bash
   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Manual Testing**: Use the test scripts:
   ```bash
   uv run python test_scheduler.py
   uv run python test_api.py
   ```

### API Endpoints

#### Check Scheduler Status
```bash
GET /api/scheduler/status
```
Returns:
```json
{
  "is_running": true,
  "jobs": [
    {
      "id": "daily_trading_workflow",
      "name": "Daily Trading Data Collection",
      "next_run_time": "2025-06-27T16:00:00+08:00",
      "trigger": "cron[hour='16', minute='0']"
    }
  ],
  "timezone": "Asia/Shanghai"
}
```

#### Manual Trigger
```bash
POST /api/scheduler/trigger
```
Manually triggers a data update regardless of schedule.

#### Update Status History
```bash
GET /api/scheduler/update-status
```
Returns history of data updates with timestamps and status.

### Data Update Logic

The system follows this priority logic:

1. **Check Trading Day**: Skip if not a trading day
2. **Check Time**: Only update after 4 PM Beijing time (unless manual trigger)
3. **Check Existing Data**: Skip if already updated today successfully
4. **Execute Update**: Run data fetch and stock selection if needed

### Workflow Execution

When triggered (automatically or manually), the system:

1. **Data Fetch**: Runs `fetch_kline.py` to collect latest stock data
2. **Stock Selection**: Runs `select_stock_enhanced.py` to analyze and select stocks
3. **Status Update**: Records success/failure in database
4. **Error Handling**: Logs errors and continues operation

## Configuration

### Scheduling Time
- **Default**: 16:00 Beijing time (Asia/Shanghai timezone)
- **Modification**: Edit the CronTrigger in `IntegratedSchedulerService.start()`

### Trading Days
- **Holidays**: Defined in `TradingDayChecker.holidays_2025`
- **Updates**: Manually update holiday list annually

### Retry Logic
- **Data Fetch**: Up to 3 retries with 5-minute delays
- **Stock Selection**: Up to 3 retries with 5-minute delays
- **Timeout**: 1 hour per operation

## Monitoring and Troubleshooting

### Logs
- **Application Logs**: Check FastAPI application logs
- **Scheduler Logs**: Detailed logging in scheduler service
- **Database Logs**: Update status stored in `data_update_status` table

### Common Issues

1. **Scheduler Not Starting**: Check APScheduler dependencies
2. **Database Errors**: Ensure database is initialized with new table
3. **Trading Day Issues**: Verify holiday calendar is up to date
4. **Timezone Problems**: Confirm system timezone settings

### Health Checks
- Use `/api/health` endpoint to verify system status
- Check `/api/scheduler/status` for scheduler health
- Monitor `/api/scheduler/update-status` for update history

## Migration from Manual System

The new system replaces manual execution while maintaining compatibility:

1. **Existing Scripts**: `fetch_kline.py` and `select_stock_enhanced.py` remain unchanged
2. **Data Format**: CSV files and database structure unchanged
3. **Web Dashboard**: No changes to frontend display logic
4. **Manual Override**: Can still trigger updates manually via API

## Benefits

1. **Automation**: No manual intervention required
2. **Reliability**: Automatic retries and error handling
3. **Efficiency**: Avoids unnecessary data updates
4. **Monitoring**: Built-in status tracking and logging
5. **Flexibility**: Manual trigger capability for testing/emergency updates
6. **Integration**: Seamlessly integrated with existing FastAPI application
