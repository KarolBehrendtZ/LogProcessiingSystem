"""
Database connection module for analytics service
Provides functions to retrieve log data from PostgreSQL database
"""

import os
import psycopg2
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
from structured_logger import create_logger_from_env, performance_monitor, log_context

# Initialize structured logger
logger = create_logger_from_env("analytics", "database")

class DatabaseConnector:
    """Database connector for analytics service."""
    
    def __init__(self):
        self.connection = None
        self.load_config()
    
    def load_config(self):
        """Load database configuration from environment variables."""
        with log_context(operation="load_config"):
            logger.debug("Loading database configuration")
            
            # Load .env from project root
            env_path = Path(__file__).resolve().parents[2] / '.env'
            load_dotenv(dotenv_path=env_path)
            
            self.config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'user': os.getenv('DB_USER', ''),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'log_processing_db')
            }
            
            logger.info("Database configuration loaded", 
                       db_host=self.config['host'],
                       db_port=self.config['port'],
                       db_name=self.config['database'],
                       db_user=self.config['user'])
            
            # Build connection string (don't log password)
            self.connection_string = (
                f"host={self.config['host']} "
                f"port={self.config['port']} "
                f"user={self.config['user']} "
                f"password={self.config['password']} "
                f"dbname={self.config['database']}"
            )
    
    @performance_monitor(logger, "database_connect")
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            logger.info("Attempting to connect to database", 
                       db_host=self.config['host'],
                       db_name=self.config['database'])
            
            self.connection = psycopg2.connect(self.connection_string)
            self.connection.autocommit = False
            
            logger.info("Database connection established successfully")
            return True
            
        except psycopg2.Error as e:
            logger.error("Database connection failed", 
                        error=str(e),
                        error_type=type(e).__name__,
                        db_host=self.config['host'],
                        db_name=self.config['database'])
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_recent_logs(self, limit: int = 1000) -> List[Dict]:
        """
        Retrieve recent log entries.
        
        Args:
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT id, level, message, timestamp, source, created_at
                FROM logs 
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'source': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return logs
            
        except psycopg2.Error as e:
            print(f"Failed to retrieve logs: {e}")
            return []
    
    def get_logs_by_time_range(self, start_time: str, end_time: str) -> List[Dict]:
        """
        Retrieve logs within a specific time range.
        
        Args:
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            
        Returns:
            List of log dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT id, level, message, timestamp, source, created_at
                FROM logs 
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (start_time, end_time))
            rows = cursor.fetchall()
            cursor.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'source': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return logs
            
        except psycopg2.Error as e:
            print(f"Failed to retrieve logs by time range: {e}")
            return []
    
    def get_logs_by_level(self, level: str, limit: int = 1000) -> List[Dict]:
        """
        Retrieve logs by specific level.
        
        Args:
            level: Log level to filter by
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT id, level, message, timestamp, source, created_at
                FROM logs 
                WHERE level = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (level, limit))
            rows = cursor.fetchall()
            cursor.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'source': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return logs
            
        except psycopg2.Error as e:
            print(f"Failed to retrieve logs by level: {e}")
            return []
    
    def get_logs_by_source(self, source: str, limit: int = 1000) -> List[Dict]:
        """
        Retrieve logs from a specific source.
        
        Args:
            source: Source to filter by
            limit: Maximum number of logs to retrieve
            
        Returns:
            List of log dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT id, level, message, timestamp, source, created_at
                FROM logs 
                WHERE source = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (source, limit))
            rows = cursor.fetchall()
            cursor.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'source': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return logs
            
        except psycopg2.Error as e:
            print(f"Failed to retrieve logs by source: {e}")
            return []
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with error summary statistics
        """
        if not self.connection:
            if not self.connect():
                return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get error counts by level
            query = """
                SELECT level, COUNT(*) as count
                FROM logs 
                WHERE timestamp >= %s AND level IN ('error', 'fatal', 'warn')
                GROUP BY level
            """
            cursor.execute(query, (start_time,))
            level_counts = dict(cursor.fetchall())
            
            # Get error counts by source
            query = """
                SELECT source, COUNT(*) as count
                FROM logs 
                WHERE timestamp >= %s AND level IN ('error', 'fatal')
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """
            cursor.execute(query, (start_time,))
            source_counts = dict(cursor.fetchall())
            
            # Get total log count
            query = """
                SELECT COUNT(*) as total
                FROM logs 
                WHERE timestamp >= %s
            """
            cursor.execute(query, (start_time,))
            total_logs = cursor.fetchone()[0]
            
            cursor.close()
            
            error_total = level_counts.get('error', 0) + level_counts.get('fatal', 0)
            error_rate = (error_total / total_logs * 100) if total_logs > 0 else 0
            
            return {
                'time_range': f"Last {hours} hours",
                'total_logs': total_logs,
                'error_counts_by_level': level_counts,
                'error_counts_by_source': source_counts,
                'total_errors': error_total,
                'error_rate': error_rate
            }
            
        except psycopg2.Error as e:
            print(f"Failed to get error summary: {e}")
            return {}
    
    def get_historical_baseline(self, days: int = 7) -> List[Dict]:
        """
        Get historical data for baseline analysis.
        
        Args:
            days: Number of days of historical data to retrieve
            
        Returns:
            List of historical log dictionaries
        """
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate time range (excluding today to get clean historical data)
            end_time = datetime.now() - timedelta(days=1)
            start_time = end_time - timedelta(days=days)
            
            query = """
                SELECT id, level, message, timestamp, source, created_at
                FROM logs 
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """
            cursor.execute(query, (start_time, end_time))
            rows = cursor.fetchall()
            cursor.close()
            
            logs = []
            for row in rows:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'source': row[4],
                    'created_at': row[5].isoformat() if row[5] else None
                })
            
            return logs
            
        except psycopg2.Error as e:
            print(f"Failed to retrieve historical baseline: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            if self.connect():
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                self.disconnect()
                return result[0] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
        
        return False

# Global database connector instance
db_connector = DatabaseConnector()

# Convenience functions
def get_recent_logs(limit: int = 1000) -> List[Dict]:
    """Get recent logs from database."""
    return db_connector.get_recent_logs(limit)

def get_logs_by_time_range(start_time: str, end_time: str) -> List[Dict]:
    """Get logs by time range."""
    return db_connector.get_logs_by_time_range(start_time, end_time)

def get_error_summary(hours: int = 24) -> Dict[str, Any]:
    """Get error summary."""
    return db_connector.get_error_summary(hours)

def get_historical_baseline(days: int = 7) -> List[Dict]:
    """Get historical baseline data."""
    return db_connector.get_historical_baseline(days)
