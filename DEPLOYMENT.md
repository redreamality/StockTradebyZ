# Z哥选股策略系统 - 部署指南

## 系统概述

本系统是一个完整的股票分析平台，包含以下核心功能：

- **自动化数据获取**: 每日自动从AkShare获取股票数据
- **智能选股分析**: 运行三种选股策略（少妇战法、补票战法、TePu战法）
- **数据库存储**: 使用SQLite+SQLAlchemy存储所有分析结果
- **REST API服务**: FastAPI提供数据访问接口
- **Web仪表板**: 现代化的前端界面展示分析结果
- **定时调度**: 每日下午4点自动执行完整工作流

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   数据获取层     │    │   分析处理层     │    │   展示服务层     │
│                │    │                │    │                │
│ • AkShare API  │───▶│ • 选股策略      │───▶│ • FastAPI      │
│ • 股票数据      │    │ • 技术指标      │    │ • Web Dashboard │
│ • 市值筛选      │    │ • 结果存储      │    │ • REST API     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   数据存储层     │
                       │                │
                       │ • SQLite DB    │
                       │ • 选股结果      │
                       │ • 执行日志      │
                       └─────────────────┘
```

## 环境要求

- **Python**: 3.11+
- **包管理器**: uv (推荐) 或 pip
- **操作系统**: Windows/Linux/macOS
- **内存**: 最少2GB RAM
- **存储**: 最少5GB可用空间

## 安装步骤

### 1. 环境准备

```bash
# 安装uv包管理器 (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用pip安装
pip install uv
```

### 2. 项目初始化

```bash
# 克隆或下载项目到本地
cd StockTradebyZ

# 初始化Python环境
uv sync

# 初始化数据库
uv run python database/init_db.py
```

### 3. 配置验证

```bash
# 测试依赖安装
uv run python -c "import akshare, pandas, numpy, sqlalchemy, fastapi; print('所有依赖安装成功!')"

# 测试数据库连接
uv run python -c "from database.operations import DatabaseOperations; print('数据库连接正常!')"
```

## 运行方式

### 方式一：使用批处理文件 (推荐)

```bash
# 1. 获取股票数据
.\fetch_data.bat

# 2. 运行选股分析
.\select_stocks.bat

# 3. 启动API服务
.\start_api.bat

# 4. 启动自动调度器
.\start_scheduler.bat

# 5. 运行完整工作流 (测试)
.\run_workflow_now.bat
```

### 方式二：命令行运行

```bash
# 数据获取
uv run python fetch_kline.py --small-player True --min-mktcap 2.5e10 --start 20050101 --end today --out ./data --workers 20

# 选股分析
uv run python select_stock_enhanced.py --data-dir ./data --config ./configs.json

# API服务
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000

# 调度器
uv run python scheduler/scheduler.py
```

## 服务访问

启动API服务后，可通过以下地址访问：

- **Web仪表板**: http://localhost:8000/
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **最新选股结果**: http://localhost:8000/api/selections/latest

## 配置说明

### 选股策略配置 (configs.json)

```json
{
  "selectors": [
    {
      "class": "BBIKDJSelector",
      "alias": "少妇战法",
      "activate": true,
      "params": {
        "threshold": -6,
        "bbi_min_window": 17,
        "bbi_offset_n": 2,
        "max_window": 60
      }
    }
  ]
}
```

### 数据库配置

- **位置**: `./data/stock_analysis.db`
- **类型**: SQLite
- **自动创建**: 首次运行时自动创建表结构

### 调度器配置

- **执行时间**: 每日16:00 (北京时间)
- **节假日处理**: 自动跳过非交易日
- **重试机制**: 失败时最多重试3次
- **日志记录**: 所有执行记录保存到数据库

## 监控和维护

### 日志文件

- `fetch.log`: 数据获取日志
- `select_results.log`: 选股结果日志
- `scheduler.log`: 调度器执行日志

### 数据库维护

```bash
# 查看数据库状态
uv run python -c "
from database.operations import DatabaseOperations
with DatabaseOperations() as db:
    stats = db.get_selection_stats()
    print(f'总选股数: {stats[\"total_selections\"]}')
    print(f'策略统计: {stats[\"strategy_stats\"]}')
"
```

### 性能优化

1. **数据获取优化**:
   - 调整`--workers`参数控制并发数
   - 设置合适的`--min-mktcap`阈值

2. **存储优化**:
   - 定期清理过期数据
   - 考虑数据库索引优化

3. **内存优化**:
   - 监控内存使用情况
   - 必要时重启服务

## 故障排除

### 常见问题

1. **网络连接问题**:
   ```
   解决方案: 检查网络连接，确保能访问akshare数据源
   ```

2. **数据库锁定**:
   ```
   解决方案: 重启相关进程，确保数据库文件未被占用
   ```

3. **依赖版本冲突**:
   ```
   解决方案: 使用uv sync重新安装依赖
   ```

### 调试模式

```bash
# 启用详细日志
uv run python select_stock_enhanced.py --data-dir ./data --config ./configs.json --debug

# 测试单个股票
uv run python select_stock_enhanced.py --data-dir ./data --config ./configs.json --tickers 600519
```

## 生产环境部署

### 1. 系统服务配置

创建systemd服务文件 (Linux):

```ini
[Unit]
Description=Stock Analysis API
After=network.target

[Service]
Type=simple
User=stockuser
WorkingDirectory=/path/to/StockTradebyZ
ExecStart=/path/to/uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. 反向代理配置

Nginx配置示例:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 安全配置

- 修改默认端口
- 配置防火墙规则
- 设置API访问限制
- 定期备份数据库

## 扩展开发

### 添加新的选股策略

1. 在`Selector.py`中实现新策略类
2. 在`configs.json`中添加配置
3. 重启服务应用更改

### API扩展

1. 在`api/main.py`中添加新端点
2. 在`api/models.py`中定义响应模型
3. 更新API文档

### 前端定制

1. 修改`static/index.html`页面结构
2. 更新`static/styles.css`样式
3. 扩展`static/app.js`功能

## 技术支持

如遇到问题，请检查：

1. 系统日志文件
2. 数据库连接状态
3. 网络连接情况
4. 依赖版本兼容性

更多技术细节请参考项目源码和API文档。
