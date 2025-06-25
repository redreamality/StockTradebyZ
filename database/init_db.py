"""
Database initialization script
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.config import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization completed!")
