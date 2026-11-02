"""
Generation Recovery Service - Checkpoint-based crash recovery
Never waste API credits by restarting from scratch
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from .utils import setup_logger

logger = setup_logger(__name__)


class GenerationStage:
    """Generation stage constants."""
    INITIALIZED = 'initialized'
    NAVIGATED = 'navigated'
    PROMPT_ENTERED = 'prompt_entered'
    SETTINGS_CONFIGURED = 'settings_configured'
    GENERATION_STARTED = 'generation_started'
    GENERATION_COMPLETE = 'generation_complete'
    DOWNLOAD_STARTED = 'download_started'
    DOWNLOAD_COMPLETE = 'download_complete'


class GenerationRecoveryService:
    """
    Checkpoint-based recovery for video generation.
    
    Each stage is checkpointed so crashes can resume from the last
    successful point instead of starting over.
    """
    
    def __init__(self, db_path: str = "./data/queue.db"):
        """
        Initialize recovery service.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_checkpoints_table()
    
    def _init_checkpoints_table(self):
        """Create checkpoints table if it doesn't exist."""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    job_id INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    stage_data TEXT,
                    attempt INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (job_id, stage)
                )
            """)
            
            # Index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_job 
                ON checkpoints(job_id, timestamp DESC)
            """)
            
            conn.commit()
        
        logger.info("Checkpoints table initialized")
    
    def checkpoint(self, job_id: int, stage: str, data: Optional[Dict[str, Any]] = None):
        """
        Save a checkpoint for the current stage.
        
        Args:
            job_id: Job ID
            stage: Current stage (use GenerationStage constants)
            data: Optional data to store with checkpoint
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints 
                (job_id, stage, stage_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                job_id,
                stage,
                json.dumps(data) if data else None,
                datetime.now().isoformat()
            ))
            conn.commit()
        
        logger.info(f"Checkpoint saved: Job {job_id} → {stage}")
    
    def get_last_checkpoint(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the last successful checkpoint for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Checkpoint data or None if no checkpoints exist
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT stage, stage_data, timestamp, attempt
                FROM checkpoints
                WHERE job_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (job_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'stage': row['stage'],
                'data': json.loads(row['stage_data']) if row['stage_data'] else None,
                'timestamp': row['timestamp'],
                'attempt': row['attempt']
            }
    
    def get_all_checkpoints(self, job_id: int) -> list:
        """
        Get all checkpoints for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of checkpoints ordered by timestamp
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT stage, stage_data, timestamp, attempt
                FROM checkpoints
                WHERE job_id = ?
                ORDER BY timestamp ASC
            """, (job_id,))
            
            return [
                {
                    'stage': row['stage'],
                    'data': json.loads(row['stage_data']) if row['stage_data'] else None,
                    'timestamp': row['timestamp'],
                    'attempt': row['attempt']
                }
                for row in cursor.fetchall()
            ]
    
    def can_resume_from(self, job_id: int, stage: str) -> bool:
        """
        Check if a job can resume from a specific stage.
        
        Args:
            job_id: Job ID
            stage: Stage to check
            
        Returns:
            True if checkpoint exists for this stage
        """
        checkpoint = self.get_last_checkpoint(job_id)
        
        if not checkpoint:
            return False
        
        return checkpoint['stage'] == stage
    
    def get_resume_point(self, job_id: int) -> Optional[str]:
        """
        Determine where to resume generation from.
        
        Args:
            job_id: Job ID
            
        Returns:
            Stage name to resume from, or None if should start fresh
        """
        checkpoint = self.get_last_checkpoint(job_id)
        
        if not checkpoint:
            return None
        
        stage = checkpoint['stage']
        
        # Define resume logic based on last checkpoint
        resume_map = {
            GenerationStage.INITIALIZED: GenerationStage.NAVIGATED,
            GenerationStage.NAVIGATED: GenerationStage.PROMPT_ENTERED,
            GenerationStage.PROMPT_ENTERED: GenerationStage.SETTINGS_CONFIGURED,
            GenerationStage.SETTINGS_CONFIGURED: GenerationStage.GENERATION_STARTED,
            GenerationStage.GENERATION_STARTED: GenerationStage.GENERATION_STARTED,  # Resume waiting
            GenerationStage.GENERATION_COMPLETE: GenerationStage.DOWNLOAD_STARTED,
            GenerationStage.DOWNLOAD_STARTED: GenerationStage.DOWNLOAD_STARTED,  # Retry download
            GenerationStage.DOWNLOAD_COMPLETE: None  # Job is complete
        }
        
        return resume_map.get(stage)
    
    def clear_checkpoints(self, job_id: int):
        """
        Clear all checkpoints for a job.
        
        Args:
            job_id: Job ID
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM checkpoints WHERE job_id = ?", (job_id,))
            conn.commit()
        
        logger.info(f"Checkpoints cleared for job {job_id}")
    
    def increment_attempt(self, job_id: int, stage: str):
        """
        Increment the attempt counter for a stage.
        
        Args:
            job_id: Job ID
            stage: Stage name
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE checkpoints 
                SET attempt = attempt + 1
                WHERE job_id = ? AND stage = ?
            """, (job_id, stage))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get recovery service statistics.
        
        Returns:
            Dictionary with stats
        """
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT job_id) as total_jobs_with_checkpoints,
                    COUNT(*) as total_checkpoints,
                    AVG(attempt) as avg_attempts_per_stage
                FROM checkpoints
            """)
            
            row = cursor.fetchone()
            
            return {
                'total_jobs_with_checkpoints': row[0],
                'total_checkpoints': row[1],
                'avg_attempts_per_stage': round(row[2], 2) if row[2] else 0
            }
