# Z哥选股策略的Python实战 - 企业级股票分析平台

## 🚀 项目简介

本项目是一个完整的企业级股票分析平台，基于Z哥的选股策略，提供从数据获取、策略分析到结果展示的全流程自动化解决方案。

### 🌟 系统特性

- **🤖 自动化数据获取**: 每日自动从AkShare获取最新股票数据
- **📊 智能选股分析**: 内置三种经典选股策略（少妇战法、补票战法、TePu战法）
- **💾 数据库存储**: SQLite + SQLAlchemy ORM，完整的数据持久化
- **🔌 REST API服务**: FastAPI提供高性能API接口
- **📱 现代化仪表板**: 响应式Web界面，支持图表展示和数据导出
- **⏰ 定时调度系统**: 每日下午4点自动执行，支持节假日识别
- **📈 实时监控**: 完整的执行日志和性能监控

## 🏗️ 系统架构

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

## 🚀 快速上手

### 1. 环境准备

```bash
# 安装uv包管理器 (推荐)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 初始化项目环境
uv sync

# 初始化数据库
uv run python database/init_db.py
```

### 2. 一键启动

```bash
# 方式一：使用批处理文件 (Windows)
.\run_workflow_now.bat    # 立即运行完整工作流
.\start_api.bat          # 启动API服务
.\start_scheduler.bat    # 启动定时调度器

# 方式二：命令行运行
uv run python scheduler/scheduler.py --run-now  # 立即执行
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000  # 启动API
```

### 3. 访问系统

- **Web仪表板**: http://localhost:8000/
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## 📊 Web仪表板

现代化的股票分析仪表板，提供：

- **📈 实时数据展示**: 最新选股结果和统计信息
- **🔍 智能筛选**: 按日期、策略、股票代码筛选
- **📊 可视化图表**: 策略分布饼图和选股趋势图
- **📤 数据导出**: 支持CSV格式导出
- **📱 响应式设计**: 完美适配桌面和移动设备

### 主要功能

1. **状态卡片**: 显示总选股数和各策略统计
2. **筛选控制**: 多维度数据筛选和搜索
3. **结果表格**: 分页显示选股结果，支持股票详情查看
4. **图表分析**: 策略分布和历史趋势可视化

## 🔌 API服务

基于FastAPI的高性能REST API，提供完整的数据访问接口：

### 核心端点

- `GET /api/selections/latest` - 获取最新选股结果
- `GET /api/selections/date/{date}` - 获取指定日期结果
- `GET /api/selections/strategy/{strategy}` - 按策略筛选
- `GET /api/stocks/{code}/history` - 股票历史选择记录
- `GET /api/stats` - 获取统计信息
- `GET /api/logs` - 获取执行日志

### API特性

- **🔒 自动验证**: Pydantic模型验证
- **📚 自动文档**: Swagger/OpenAPI文档
- **🌐 CORS支持**: 跨域资源共享
- **⚡ 高性能**: 异步处理和数据库连接池

## ⏰ 自动化调度

智能调度系统，确保数据的及时性和准确性：

### 调度特性

- **🕐 定时执行**: 每日16:00自动运行
- **📅 节假日识别**: 自动跳过非交易日
- **🔄 重试机制**: 失败时自动重试（最多3次）
- **📝 完整日志**: 详细的执行记录和错误追踪

### 执行流程

1. **数据获取**: 从AkShare获取最新股票数据
2. **策略分析**: 运行三种选股策略
3. **结果存储**: 保存到数据库
4. **日志记录**: 记录执行状态和统计信息

## 📋 内置策略

### 1. BBIKDJSelector（少妇战法）
- **核心逻辑**: BBI单调上升 + KDJ低位
- **参数**: J值阈值、BBI窗口、偏移量
- **适用**: 趋势启动阶段的低吸机会

### 2. BBIShortLongSelector（补票战法）
- **核心逻辑**: 短长期RSV差异 + BBI上升
- **参数**: 短期窗口、长期窗口、检测区间
- **适用**: 回调后的补仓时机

### 3. BreakoutVolumeKDJSelector（TePu战法）
- **核心逻辑**: 放量突破 + 缩量回调 + KDJ低位
- **参数**: 涨幅阈值、成交量比例、回溯窗口
- **适用**: 突破后的低吸布局

## 🗂️ 项目结构

```
StockTradebyZ/
├── 📁 api/                    # FastAPI服务
│   ├── main.py               # API主程序
│   └── models.py             # 数据模型
├── 📁 database/              # 数据库层
│   ├── config.py             # 数据库配置
│   ├── models.py             # SQLAlchemy模型
│   └── operations.py         # 数据库操作
├── 📁 scheduler/             # 调度系统
│   └── scheduler.py          # 调度器主程序
├── 📁 static/                # 前端资源
│   ├── index.html            # 仪表板页面
│   ├── styles.css            # 样式文件
│   └── app.js                # JavaScript应用
├── 📁 data/                  # 数据目录
│   ├── *.csv                 # 股票数据文件
│   └── stock_analysis.db     # SQLite数据库
├── 📄 fetch_kline.py         # 数据获取脚本
├── 📄 select_stock.py        # 原始选股脚本
├── 📄 select_stock_enhanced.py # 增强选股脚本
├── 📄 Selector.py            # 策略实现
├── 📄 configs.json           # 策略配置
├── 📄 *.bat                  # 批处理文件
├── 📄 DEPLOYMENT.md          # 部署指南
└── 📄 README.md              # 项目说明
```

## 🛠️ 技术栈

- **后端**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **数据源**: AkShare
- **包管理**: uv
- **调度**: Python schedule
- **部署**: Uvicorn, 支持Docker

## 📈 性能指标

- **数据处理**: 支持500+股票并发分析
- **API响应**: 平均响应时间 < 100ms
- **存储效率**: SQLite数据库，支持千万级记录
- **内存占用**: 运行时内存 < 500MB
- **并发支持**: 支持多用户同时访问

## 🔧 配置说明

详细的配置参数请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 📞 技术支持

如遇到问题，请：

1. 查看系统日志文件
2. 检查API健康状态
3. 验证数据库连接
4. 参考部署文档

## ⚠️ 免责声明

本项目仅供学习与技术研究使用，**不构成任何投资建议**。股市有风险，投资需谨慎。

感谢师尊 **@Zettaranc** 的无私分享！

---

**🌟 如果这个项目对您有帮助，请给个Star支持一下！**
