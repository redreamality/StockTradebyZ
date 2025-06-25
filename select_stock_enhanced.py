"""
Enhanced stock selection script with database integration
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

# Database imports
from database.operations import DatabaseOperations
from database.config import init_db

# ---------- 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("select_results.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("select")


# ---------- 工具 ----------


def load_data(data_dir: Path, codes: Iterable[str]) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for code in codes:
        fp = data_dir / f"{code}.csv"
        if not fp.exists():
            logger.warning("%s 不存在，跳过", fp.name)
            continue
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")
        frames[code] = df
    return frames


def load_config(cfg_path: Path) -> List[Dict[str, Any]]:
    if not cfg_path.exists():
        logger.error("配置文件 %s 不存在", cfg_path)
        sys.exit(1)
    with cfg_path.open(encoding="utf-8") as f:
        cfg_raw = json.load(f)

    # 兼容三种结构：单对象、对象数组、或带 selectors 键
    if isinstance(cfg_raw, list):
        cfgs = cfg_raw
    elif isinstance(cfg_raw, dict) and "selectors" in cfg_raw:
        cfgs = cfg_raw["selectors"]
    else:
        cfgs = [cfg_raw]

    return cfgs


def instantiate_selector(cfg: Dict[str, Any]):
    cls_name = cfg["class"]
    alias = cfg.get("alias", cls_name)
    params = cfg.get("params", {})

    # 动态导入 Selector 模块
    mod = importlib.import_module("Selector")
    cls = getattr(mod, cls_name)
    selector = cls(**params)
    return alias, selector


def get_stock_codes(data_dir: Path, tickers: str) -> List[str]:
    if tickers.lower() == "all":
        # 扫描 data_dir 下所有 CSV 文件
        csv_files = list(data_dir.glob("*.csv"))
        codes = [fp.stem for fp in csv_files]
    else:
        codes = [t.strip() for t in tickers.split(",") if t.strip()]
    return codes


def save_selection_results(
    db_ops: DatabaseOperations,
    strategy_name: str,
    alias: str,
    trade_date: datetime,
    selected_stocks: List[str],
    all_stocks: List[str],
) -> None:
    """
    Save selection results to database
    """
    try:
        # Save selected stocks
        for stock_code in selected_stocks:
            db_ops.save_selection_result(
                stock_code=stock_code,
                strategy_name=alias,
                selection_date=trade_date,
                is_selected=True,
            )

        # Optionally save non-selected stocks for complete tracking
        # This can be disabled for performance if not needed
        save_non_selected = False  # Set to True if you want complete tracking

        if save_non_selected:
            non_selected = set(all_stocks) - set(selected_stocks)
            for stock_code in non_selected:
                db_ops.save_selection_result(
                    stock_code=stock_code,
                    strategy_name=alias,
                    selection_date=trade_date,
                    is_selected=False,
                )

        logger.info(
            "Database: Saved %d selected stocks for strategy %s",
            len(selected_stocks),
            alias,
        )

    except Exception as e:
        logger.error("Failed to save results to database: %s", e)


def main():
    parser = argparse.ArgumentParser(description="批量选股")
    parser.add_argument("--data-dir", default="./data", help="CSV 行情目录")
    parser.add_argument("--config", default="./configs.json", help="Selector 配置文件")
    parser.add_argument("--date", help="交易日 YYYY-MM-DD，缺省=最新")
    parser.add_argument("--tickers", default="all", help="股票代码，逗号分隔或 'all'")
    parser.add_argument("--no-db", action="store_true", help="禁用数据库保存")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("数据目录 %s 不存在", data_dir)
        sys.exit(1)

    # Initialize database if not disabled
    db_ops = None
    if not args.no_db:
        try:
            init_db()
            db_ops = DatabaseOperations()
            logger.info("Database connection established")
        except Exception as e:
            logger.warning(
                "Failed to initialize database: %s. Continuing without DB.", e
            )

    codes = get_stock_codes(data_dir, args.tickers)
    if not codes:
        logger.error("股票池为空！")
        sys.exit(1)

    data = load_data(data_dir, codes)
    if not data:
        logger.error("未能加载任何行情数据")
        sys.exit(1)

    trade_date = (
        pd.to_datetime(args.date)
        if args.date
        else max(df["date"].max() for df in data.values())
    )
    if not args.date:
        logger.info("未指定 --date，使用最近日期 %s", trade_date.date())

    # --- 加载 Selector 配置 ---
    selector_cfgs = load_config(Path(args.config))

    # Track execution for logging
    start_time = datetime.now()
    total_selected = 0
    strategies_run = 0

    try:
        # --- 逐个 Selector 运行 ---
        for cfg in selector_cfgs:
            if cfg.get("activate", True) is False:
                continue

            try:
                alias, selector = instantiate_selector(cfg)
                strategies_run += 1
            except Exception as e:
                logger.error("跳过配置 %s：%s", cfg, e)
                continue

            picks = selector.select(trade_date, data)
            total_selected += len(picks)

            # 将结果写入日志，同时输出到控制台
            logger.info("")
            logger.info("============== 选股结果 [%s] ==============", alias)
            logger.info("交易日: %s", trade_date.date())
            logger.info("符合条件股票数: %d", len(picks))
            logger.info("%s", ", ".join(picks) if picks else "无符合条件股票")

            # Save to database if enabled
            if db_ops:
                save_selection_results(
                    db_ops, cfg["class"], alias, trade_date, picks, codes
                )

        # Log execution summary
        end_time = datetime.now()
        if db_ops:
            try:
                db_ops.log_execution(
                    execution_type="stock_selection",
                    status="success",
                    start_time=start_time,
                    end_time=end_time,
                    stocks_processed=len(codes),
                    stocks_selected=total_selected,
                    log_details=f"Strategies run: {strategies_run}",
                )
            except Exception as e:
                logger.error("Failed to log execution: %s", e)

    except Exception as e:
        # Log failed execution
        if db_ops:
            try:
                db_ops.log_execution(
                    execution_type="stock_selection",
                    status="failed",
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=str(e),
                )
            except:
                pass
        raise

    finally:
        if db_ops:
            db_ops.db.close()


if __name__ == "__main__":
    main()
