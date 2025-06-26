# Z哥选股策略的Python实战

## 目录

* [项目简介](#项目简介)
* [快速上手](#快速上手)
* [Web界面使用](#Web界面使用)
* [命令行使用](#命令行使用)
* [参数说明](#参数说明)
* [项目结构](#项目结构)
* [免责声明](#免责声明)

---

## 项目简介

本仓库提供完整的股票选股分析系统，包含：

| 组件                    | 作用                                                                                     |
| --------------------- | -------------------------------------------------------------------------------------- |
| **Web仪表板**  | 现代化的Web界面，提供选股结果展示、历史记录查询、系统状态监控、**交互式K线图表**等功能           |
| **K线图表功能**  | 基于TradingView Lightweight Charts的专业金融图表，支持日线/周线/月线切换、成交量显示、移动端优化           |
| **API服务**  | RESTful API接口，支持程序化访问选股数据、系统状态、**OHLC数据**等           |
| **自动调度器**  | 每日下午4点自动执行数据获取和选股分析，支持交易日判断           |
| **`fetch_kline.py`**  | 从 AkShare 实时快照筛选出总市值 ≥ 指定阈值且排除创业板的股票，抓取其历史日 K 线并保存为 CSV。支持多线程、增量更新和今日快照自动补齐。           |
| **`select_stock_enhanced.py`** | 读取本地 CSV 行情，根据 `configs.json` 中定义的策略（Selector）进行批量选股，并把结果写入数据库和日志。 |

默认内置三大选股策略（位于 `Selector.py`）：

* **BBIKDJSelector**（中文别名：**少妇战法**）
* **BBIShortLongSelector**（中文别名：**补票战法**）
* **BreakoutVolumeKDJSelector**（中文别名：**TePu 战法**）

---

## 快速上手

### 1. 安装依赖

```bash
# 建议 Python 3.10+，使用 uv 包管理器
uv sync
```

> 依赖主要包括：`akshare`、`pandas`、`numpy`、`fastapi`、`uvicorn` 等。

### 2. 系统检查

运行系统健康检查，确保所有组件正常：

```bash
# 方式一：使用批处理文件
system_status.bat

# 方式二：直接运行
uv run python system_check.py
```

### 3. 自动化调度系统（推荐）

系统现在包含集成的调度器，可自动在每天下午4点（北京时间）执行数据收集和分析：

```bash
# 启动 FastAPI 服务器（包含集成调度器）
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000

# 或使用便捷脚本测试调度器
uv run python test_scheduler.py
```

**调度器特性：**
- ✅ 自动在交易日下午4点执行
- ✅ 智能数据更新逻辑（避免重复更新）
- ✅ 后台运行，不阻塞Web服务
- ✅ 完整的状态跟踪和错误处理
- ✅ 手动触发功能

**调度器API端点：**
- `GET /api/scheduler/status` - 查看调度器状态
- `POST /api/scheduler/trigger` - 手动触发更新
- `GET /api/scheduler/update-status` - 查看更新历史

### 4. 启动Web界面

启动API服务和Web仪表板：

```bash
# 方式一：使用批处理文件
start_api.bat

# 方式二：直接运行
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：
- **Web仪表板**: http://localhost:8000/
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

### 4. 命令行运行选股

```bash
# 方式一：使用批处理文件（立即运行一次）
run_cli.bat

# 方式二：直接运行
uv run python scheduler/scheduler.py --run-now

# 方式三：启动定时调度器（每天下午4点自动运行）
uv run python scheduler/scheduler.py
```

---

## Web界面使用

### 启动Web服务

1. **启动API服务**：
   ```bash
   start_api.bat
   # 或者
   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **访问Web界面**：
   - 打开浏览器访问：http://localhost:8000/
   - 界面提供选股结果展示、历史记录查询等功能

### Web界面功能

- **选股结果展示**：查看最新的选股结果，按策略分类显示
- **历史记录查询**：查询指定日期范围内的选股历史
- **系统状态监控**：实时查看系统运行状态和执行日志
- **📈 K线图表功能**：点击股票表格中的"图表"按钮，查看专业的交互式K线图
  - 支持日线/周线/月线切换
  - 实时OHLC价格显示
  - 成交量指标
  - 缩放、平移等交互功能
  - 移动端优化，支持触摸操作
- **API文档**：访问 http://localhost:8000/docs 查看完整API文档

### K线图表使用说明

1. **打开图表**：在选股结果表格中，点击任意股票行的"图表"按钮
2. **时间周期切换**：使用"日线"、"周线"、"月线"按钮切换不同时间周期
3. **图表交互**：
   - 鼠标滚轮或手势缩放
   - 拖拽平移查看历史数据
   - 悬停查看具体OHLC数据
4. **控制按钮**：
   - "适应内容"：自动调整图表显示全部数据
   - "刷新"：重新加载最新数据

> 📖 **详细文档**：查看 [CANDLESTICK_CHART_DOCUMENTATION.md](./CANDLESTICK_CHART_DOCUMENTATION.md) 了解K线图表功能的完整技术文档，包括API接口、性能优化、浏览器兼容性等详细信息。

### API接口

#### 系统接口
- `GET /api/health` - 系统健康检查
- `GET /api/selections/latest` - 获取最新选股结果
- `GET /api/selections/history` - 获取历史选股记录
- `GET /api/executions/logs` - 获取执行日志

#### K线数据接口
- `GET /api/stocks` - 获取可用股票代码列表
- `GET /api/stocks/{stock_code}/info` - 获取股票基本信息
- `GET /api/stocks/{stock_code}/ohlc` - 获取OHLC数据（支持日线/周线/月线）
  - 参数：`period`（daily/weekly/monthly）、`limit`（数据点数量）、`start_date`、`end_date`

---

## 命令行使用

### 手动获取数据和选股

```bash
# 下载历史行情
uv run python fetch_kline.py \
  --small-player True \
  --min-mktcap 2.5e10 \
  --start 20050101 \
  --end today \
  --out ./data \
  --workers 20

# 运行选股分析
uv run python select_stock_enhanced.py \
  --data-dir ./data \
  --config ./configs.json
```

### 自动化调度

```bash
# 立即运行一次完整工作流
uv run python scheduler/scheduler.py --run-now

# 启动定时调度器（每天下午4点自动运行）
uv run python scheduler/scheduler.py
```

---

## 参数说明

### 脚本参数

| 脚本                | 关键参数              | 说明                                       |
| ----------------- | ----------------- | ---------------------------------------- |
| `fetch_kline.py`  | `--small-player`  | 是否包含创业板数据。设为 True 则不包含创业板数据              |
|                   | `--min-mktcap`    | 市值过滤阈值（元）。默认 2.5e10                      |
|                   | `--start / --end` | 日期范围，格式 `YYYYMMDD`；`--end today` 自动取当前日期 |
|                   | `--workers`       | 并发线程数，默认 20                              |
| `select_stock_enhanced.py` | `--date`          | 选股所用交易日；缺省时自动取数据中最新日期                    |
|                   | `--tickers`       | `all` 或逗号分隔股票代码列表，精细控制股票池                |
|                   | `--config`        | Selector 配置文件路径，默认 `configs.json`        |

### 内置策略参数

> 以下参数来自 `configs.json`，可按需调整。

#### 1. BBIKDJSelector（少妇战法）

| 参数               | 示例值  | 说明                                              |
| ---------------- | ---- | ----------------------------------------------- |
| `threshold`      | `-5` | 日线 **J 值上限**。当当天 J < threshold 时满足条件，阈值越低要求越严格。 |
| `bbi_min_window` | `10` | 用于检测 **BBI 单调上升** 的最短窗口长度（交易日数）。                |
| `bbi_offset_n`   | `8`  | 选定距今日 *n* 日的"锚点"作为 BBI 上升段的终点，可避免近期震荡。          |
| `max_window`     | `60` | 计算技术指标时最多读取的 K 线天数，限制窗口大小防止性能下降。                |

#### 2. BBIShortLongSelector（补票战法）

| 参数               | 示例值  | 说明                                          |
| ---------------- | ---- | ------------------------------------------- |
| `n_short`        | `3`  | **短期 RSV** 的计算窗口 N1。滚动取近 N1 日最低 / 收盘价。      |
| `n_long`         | `21` | **长期 RSV** 的计算窗口 N2。                        |
| `m`              | `3`  | **检测区间长度**。在最近 m 个交易日内同时满足 RSV、BBI、DIF 等条件。 |
| `bbi_min_window` | `5`  | BBI 上升段的最短窗口。                               |
| `bbi_offset_n`   | `0`  | BBI 锚点距离当前日的偏移量。                            |
| `max_window`     | `60` | 读取历史 K 线最大长度。                               |

#### 3. BreakoutVolumeKDJSelector（TePu 战法）

| 参数                 | 示例值      | 说明                                                      |
| ------------------ | -------- | ------------------------------------------------------- |
| `j_threshold`      | `1`      | 指定日 T0 的 **J 值上限**（当日 J 须 < 该阈值）。                       |
| `up_threshold`     | `3.0`    | 在向前 `offset` 个交易日窗口内，存在某日 T **较前一日涨幅** ≥ 此阈值 (%)。       |
| `volume_threshold` | `0.6667` | **缩量比例**。区间内除 T 外所有成交量 ≤ `volume_threshold × volume_T`。 |
| `offset`           | `15`     | 回溯窗口大小（交易日数）。                                           |
| `max_window`       | `60`     | 参与指标计算的最大 K 线数。                                         |

---

## 项目结构

```
.
├── api/                     # API服务模块
│   ├── main.py             # FastAPI应用主文件
│   ├── models.py           # API数据模型
│   └── stock_data_service.py # 股票数据服务（OHLC数据处理）
├── database/               # 数据库模块
│   ├── config.py           # 数据库配置
│   ├── models.py           # 数据库模型
│   ├── operations.py       # 数据库操作
│   └── init_db.py          # 数据库初始化
├── scheduler/              # 调度器模块
│   └── scheduler.py        # 自动调度器
├── static/                 # Web界面静态文件
│   ├── index.html          # 主页面
│   ├── app.js              # JavaScript逻辑
│   ├── candlestick-chart.js # K线图表组件
│   ├── chart-modal.js      # 图表模态框组件
│   └── styles.css          # 样式文件
├── data/                   # 数据目录
│   ├── *.csv               # 股票历史数据
│   └── stock_analysis.db   # SQLite数据库
├── appendix.json           # 额外自选股票池
├── configs.json            # 策略配置
├── fetch_kline.py          # 历史行情抓取脚本
├── select_stock_enhanced.py # 批量选股脚本
├── Selector.py             # 策略实现
├── system_check.py         # 系统健康检查
├── run_cli.bat             # 命令行运行
├── start_api.bat           # 启动API服务
├── system_status.bat       # 系统状态检查
└── pyproject.toml          # 项目配置
```

---

## 免责声明

* 本仓库代码仅供学习与技术研究之用，**不构成任何投资建议**。股市有风险，入市需谨慎。
* 感谢师尊 **@Zettaranc** [https://b23.tv/JxIOaNE](https://b23.tv/JxIOaNE) 的无私分享
