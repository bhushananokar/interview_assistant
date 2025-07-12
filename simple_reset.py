#!/usr/bin/env python3
"""
Force reset the database with correct schema
"""

import os
from pathlib import Path
from database import reset_database

def main():
    # Get the correct database path (same as in database.py)
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = os.path.join(BASE_DIR, "interview_assistant.db")
    
    print(f"🔍 Looking for database at: {DB_PATH}")
    
    # Check if database exists
    if os.path.exists(DB_PATH):
        print(f"📁 Found existing database: {DB_PATH}")
        
        # Delete the file completely
        os.remove(DB_PATH)
        print("🗑️ Deleted old database file")
    else:
        print("📁 No existing database found")
    
    # Create new database with correct schema
    print("🔧 Creating new database with correct schema...")
    reset_database()
    
    print("✅ Database reset completed!")
    print("\nYou can now start your server with: python app.py")

if __name__ == "__main__":
    main()