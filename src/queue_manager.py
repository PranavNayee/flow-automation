"""
Queue manager for tracking video generation jobs
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Job:
    """Represents a video generation job."""
    scene_id: str
    prompt: str
    aspect_ratio: str = "16:9"
    duration: int = 5
    status: str = JobStatus.PENDING.value
    retry_count: int = 0
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert job to dictionary."""
        data = asdict(self)
        if self.metadata:
            data['metadata'] = json.dumps(self.metadata)
        return data
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Job':
        """Create Job from database row."""
        data = dict(row)
        if data.get('metadata'):
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)


class QueueManager:
    """Manages the job queue in SQLite."""
    
    def __init__(self, db_path: str = "./data/queue.db"):
        """
        Initialize queue manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT UNIQUE NOT NULL,
                    prompt TEXT NOT NULL,
                    aspect_ratio TEXT DEFAULT '16:9',
                    duration INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    output_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON jobs(status)
            """)
            conn.commit()
    
    def add_job(self, job: Job) -> int:
        """
        Add a job to the queue.
        
        Args:
            job: Job to add
            
        Returns:
            Job ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO jobs (
                    scene_id, prompt, aspect_ratio, duration, 
                    status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job.scene_id,
                job.prompt,
                job.aspect_ratio,
                job.duration,
                job.status,
                json.dumps(job.metadata) if job.metadata else None
            ))
            conn.commit()
            return cursor.lastrowid
    
    def add_jobs_bulk(self, jobs: List[Job]) -> int:
        """
        Add multiple jobs in a single transaction.
        
        Args:
            jobs: List of jobs to add
            
        Returns:
            Number of jobs added
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR IGNORE INTO jobs (
                    scene_id, prompt, aspect_ratio, duration,
                    status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                (
                    job.scene_id,
                    job.prompt,
                    job.aspect_ratio,
                    job.duration,
                    job.status,
                    json.dumps(job.metadata) if job.metadata else None
                )
                for job in jobs
            ])
            conn.commit()
            return conn.total_changes
    
    def get_next_job(self) -> Optional[Job]:
        """
        Get the next pending job.
        
        Returns:
            Next job or None if queue is empty
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM jobs 
                WHERE status IN ('pending', 'retry')
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return Job.from_row(row) if row else None
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return Job.from_row(row) if row else None
    
    def get_job_by_scene_id(self, scene_id: str) -> Optional[Job]:
        """
        Get a job by scene ID.
        
        Args:
            scene_id: Scene ID
            
        Returns:
            Job or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE scene_id = ?", 
                (scene_id,)
            )
            row = cursor.fetchone()
            return Job.from_row(row) if row else None
    
    def update_job(
        self,
        job_id: int,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        output_path: Optional[str] = None,
        retry_count: Optional[int] = None
    ):
        """
        Update a job's fields.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if failed
            output_path: Path to generated video
            retry_count: Updated retry count
        """
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
            
            if status == JobStatus.RUNNING.value:
                updates.append("started_at = ?")
                params.append(datetime.now().isoformat())
            elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
        
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        
        if output_path is not None:
            updates.append("output_path = ?")
            params.append(output_path)
        
        if retry_count is not None:
            updates.append("retry_count = ?")
            params.append(retry_count)
        
        if updates:
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with counts by status
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM jobs
                GROUP BY status
            """)
            stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Ensure all statuses are present
            for status in JobStatus:
                if status.value not in stats:
                    stats[status.value] = 0
            
            stats['total'] = sum(stats.values())
            return stats
    
    def get_all_jobs(
        self, 
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Job]:
        """
        Get all jobs, optionally filtered by status.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to return (optional)
            
        Returns:
            List of jobs
        """
        query = "SELECT * FROM jobs"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [Job.from_row(row) for row in cursor.fetchall()]
    
    def reset_running_jobs(self):
        """Reset any jobs stuck in 'running' status (e.g., after a crash)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE jobs 
                SET status = 'pending', started_at = NULL
                WHERE status = 'running'
            """)
            conn.commit()
    
    def clear_queue(self):
        """Clear all jobs from the queue. USE WITH CAUTION!"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs")
            conn.commit()


def import_from_csv(csv_path: str, queue_manager: QueueManager) -> int:
    """
    Import jobs from a CSV file.
    
    CSV format: scene_id,prompt,aspect_ratio,duration
    
    Args:
        csv_path: Path to CSV file
        queue_manager: QueueManager instance
        
    Returns:
        Number of jobs imported
    """
    import csv
    
    jobs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            job = Job(
                scene_id=row['scene_id'],
                prompt=row['prompt'],
                aspect_ratio=row.get('aspect_ratio', '16:9'),
                duration=int(row.get('duration', 5))
            )
            jobs.append(job)
    
    return queue_manager.add_jobs_bulk(jobs)


def import_from_json(json_path: str, queue_manager: QueueManager) -> int:
    """
    Import jobs from a JSON file.
    
    JSON format: [{"scene_id": "...", "prompt": "...", ...}, ...]
    
    Args:
        json_path: Path to JSON file
        queue_manager: QueueManager instance
        
    Returns:
        Number of jobs imported
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    jobs = []
    for item in data:
        job = Job(
            scene_id=item['scene_id'],
            prompt=item['prompt'],
            aspect_ratio=item.get('aspect_ratio', '16:9'),
            duration=int(item.get('duration', 5)),
            metadata=item.get('metadata')
        )
        jobs.append(job)
    
    return queue_manager.add_jobs_bulk(jobs)
