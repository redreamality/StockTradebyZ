#!/usr/bin/env python3
"""
System health check script for Z哥选股策略平台
"""
import sys
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 检查依赖包...")
    try:
        import akshare  # noqa: F401
        import pandas  # noqa: F401
        import numpy  # noqa: F401
        import sqlalchemy  # noqa: F401
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import schedule  # noqa: F401

        print("✅ 所有依赖包已正确安装")
        return True
    except ImportError as e:
        print(f"❌ 依赖包缺失: {e}")
        return False


def check_database():
    """Check database connectivity and structure"""
    print("🔍 检查数据库连接...")
    try:
        from database.operations import DatabaseOperations
        from database.config import init_db

        # Initialize database
        init_db()

        # Test operations
        with DatabaseOperations() as db_ops:
            stats = db_ops.get_selection_stats()
            print(f"✅ 数据库连接正常")
            print(f"   - 总选股数: {stats['total_selections']}")
            print(f"   - 策略统计: {stats['strategy_stats']}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


def check_data_files():
    """Check if data files exist"""
    print("🔍 检查数据文件...")
    data_dir = project_root / "data"
    if not data_dir.exists():
        print("❌ 数据目录不存在")
        return False

    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        print("⚠️  未找到股票数据文件，请先运行数据获取")
        return False

    print(f"✅ 找到 {len(csv_files)} 个股票数据文件")
    return True


def check_api_service():
    """Check if API service is running"""
    print("🔍 检查API服务...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API服务运行正常")
            print(f"   - 状态: {data['status']}")
            print(f"   - 数据库: {data['database_status']}")
            return True
        else:
            print(f"❌ API服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("⚠️  API服务未启动 (这是正常的，如果您还未启动API服务)")
        return False


def check_config_files():
    """Check configuration files"""
    print("🔍 检查配置文件...")

    config_files = ["configs.json", "pyproject.toml"]

    all_exist = True
    for config_file in config_files:
        file_path = project_root / config_file
        if file_path.exists():
            print(f"✅ {config_file} 存在")
        else:
            print(f"❌ {config_file} 缺失")
            all_exist = False

    return all_exist


def check_batch_files():
    """Check batch files"""
    print("🔍 检查批处理文件...")

    batch_files = [
        "run_cli.bat",
        "start_api.bat",
        "system_status.bat",
    ]

    all_exist = True
    for batch_file in batch_files:
        file_path = project_root / batch_file
        if file_path.exists():
            print(f"✅ {batch_file} 存在")
        else:
            print(f"❌ {batch_file} 缺失")
            all_exist = False

    return all_exist


def main():
    """Main system check function"""
    print("=" * 60)
    print("🚀 Z哥选股策略系统健康检查")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks = [
        ("依赖包检查", check_dependencies),
        ("数据库检查", check_database),
        ("数据文件检查", check_data_files),
        ("配置文件检查", check_config_files),
        ("批处理文件检查", check_batch_files),
        ("API服务检查", check_api_service),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 40)
        result = check_func()
        results.append((check_name, result))
        print()

    # Summary
    print("=" * 60)
    print("📊 检查结果汇总")
    print("=" * 60)

    passed = 0
    total = len(results)

    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{check_name}: {status}")
        if result:
            passed += 1

    print()
    print(f"总体状态: {passed}/{total} 项检查通过")

    if passed == total:
        print("🎉 系统状态良好，所有组件正常运行！")
        print_usage_info()
        return 0
    elif passed >= total * 0.8:
        print("⚠️  系统基本正常，但有部分组件需要注意")
        print_usage_info()
        return 1
    else:
        print("❌ 系统存在问题，请检查失败的组件")
        return 2


def print_usage_info():
    """Print usage information and available commands"""
    print()
    print("=" * 60)
    print("📋 系统管理选项")
    print("=" * 60)
    print("1. 运行命令行选股: run_cli.bat")
    print("2. 启动API服务: start_api.bat")
    print("3. 系统健康检查: system_status.bat")
    print()
    print("🌐 访问地址:")
    print("- Web仪表板: http://localhost:8000/")
    print("- API文档: http://localhost:8000/docs")
    print("- 健康检查: http://localhost:8000/api/health")
    print()
    print("💡 命令行使用:")
    print("- 立即运行选股: uv run python scheduler/scheduler.py --run-now")
    print("- 启动定时调度: uv run python scheduler/scheduler.py")
    print("- 启动API服务: uv run uvicorn api.main:app --host 0.0.0.0 --port 8000")
    print("- 获取股票数据: uv run python fetch_kline.py --help")
    print("- 运行选股分析: uv run python select_stock_enhanced.py --help")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
