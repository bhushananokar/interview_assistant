"""
Database connection and configuration
Handles SQLite connection and table creation
"""
import os
import sqlite3
from sqlite3 import Error
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the database file path
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.path.join(BASE_DIR, "interview_assistant.db")

def get_db_connection():
    """
    Create a database connection to the SQLite database
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Error as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def execute_sql(sql, params=None):
    """
    Execute SQL statements
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        result = cursor.fetchall() if cursor.description else None
        cursor.close()
        conn.close()
        return result
    except Error as e:
        logger.error(f"Error executing SQL: {e}")
        logger.error(f"SQL: {sql}")
        if params:
            logger.error(f"Params: {params}")
        raise

def create_tables():
    """
    Create all required tables if they don't exist
    """
    logger.info("Creating database tables if they don't exist...")
    
    # Create interviews table
    interviews_table = """
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT,
        skill_area TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        score REAL,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """
    
    # Create interview_questions table
    interview_questions_table = """
    CREATE TABLE IF NOT EXISTS interview_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interview_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        question_type TEXT NOT NULL,
        response TEXT,
        evaluation TEXT,
        score REAL,
        FOREIGN KEY (interview_id) REFERENCES interviews (id)
    );
    """
    
    # Execute all table creation SQL
    tables = [interviews_table, interview_questions_table]
    
    for table in tables:
        execute_sql(table)
    
    logger.info("Database tables created successfully")

def reset_database():
    """
    Drop and recreate all tables (use this to fix schema issues)
    """
    logger.info("Resetting database...")
    
    # Drop existing tables
    execute_sql("DROP TABLE IF EXISTS interview_questions")
    execute_sql("DROP TABLE IF EXISTS interviews")
    
    # Recreate tables
    create_tables()
    
    logger.info("Database reset completed")