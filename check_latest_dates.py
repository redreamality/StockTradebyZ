#!/usr/bin/env python3
"""检查所有CSV文件的最新日期"""

import pandas as pd
from pathlib import Path
import sys

def check_latest_dates():
    data_dir = Path("data")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("没有找到CSV文件")
        return
    
    latest_dates = {}
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if 'date' in df.columns and len(df) > 0:
                df['date'] = pd.to_datetime(df['date'])
                latest_date = df['date'].max()
                latest_dates[csv_file.name] = latest_date
            else:
                latest_dates[csv_file.name] = None
        except Exception as e:
            print(f"读取 {csv_file.name} 时出错: {e}")
            latest_dates[csv_file.name] = None
    
    # 按日期排序
    sorted_dates = sorted(latest_dates.items(), key=lambda x: x[1] if x[1] else pd.Timestamp.min)
    
    print("所有CSV文件的最新日期:")
    print("-" * 50)
    
    for filename, date in sorted_dates:
        if date:
            print(f"{filename}: {date.date()}")
        else:
            print(f"{filename}: 无数据或错误")
    
    # 找出最新的日期
    valid_dates = [date for date in latest_dates.values() if date is not None]
    if valid_dates:
        overall_latest = max(valid_dates)
        print(f"\n整体最新日期: {overall_latest.date()}")
        
        # 找出有最新日期的文件
        files_with_latest = [filename for filename, date in latest_dates.items() 
                           if date == overall_latest]
        print(f"有最新日期的文件: {', '.join(files_with_latest)}")
    else:
        print("\n没有有效的日期数据")

if __name__ == "__main__":
    check_latest_dates()
