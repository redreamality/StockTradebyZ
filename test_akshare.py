#!/usr/bin/env python3
"""
Test script to check AkShare API response and debug stock name collection
"""

import akshare as ak
import pandas as pd

def test_akshare_api():
    """Test AkShare API and check available columns"""
    print("Testing AkShare API...")
    
    try:
        # Get the data
        df = ak.stock_zh_a_spot_em()
        print(f"✓ Successfully fetched {len(df)} records")
        
        # Check columns
        print(f"\nAvailable columns ({len(df.columns)}):")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. '{col}'")
        
        # Check if our expected columns exist
        expected_cols = ["代码", "名称", "总市值"]
        print(f"\nChecking for expected columns:")
        for col in expected_cols:
            if col in df.columns:
                print(f"  ✓ '{col}' found")
            else:
                print(f"  ✗ '{col}' NOT found")
        
        # Show sample data
        print(f"\nSample data (first 3 rows):")
        if "代码" in df.columns and "名称" in df.columns:
            sample_cols = ["代码", "名称"]
            if "总市值" in df.columns:
                sample_cols.append("总市值")
            print(df[sample_cols].head(3))
        else:
            print("Cannot show sample - expected columns not found")
            print("First 3 rows of all data:")
            print(df.head(3))
            
        return df
        
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_modified_function():
    """Test our modified _get_mktcap_ak function"""
    print("\n" + "="*50)
    print("Testing modified _get_mktcap_ak function...")
    
    try:
        import sys
        sys.path.append('.')
        from fetch_kline import _get_mktcap_ak
        
        df = _get_mktcap_ak()
        print(f"✓ Successfully processed {len(df)} records")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Data types:\n{df.dtypes}")
        print(f"Null values:\n{df.isnull().sum()}")
        print(f"\nSample data:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"✗ Error in modified function: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test original API
    original_df = test_akshare_api()
    
    # Test our modified function
    modified_df = test_modified_function()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    if original_df is not None:
        print(f"✓ Original API works - {len(original_df)} records")
    else:
        print("✗ Original API failed")
        
    if modified_df is not None:
        print(f"✓ Modified function works - {len(modified_df)} records")
        has_names = modified_df['name'].notna().sum()
        print(f"  - Records with names: {has_names}/{len(modified_df)}")
    else:
        print("✗ Modified function failed")
