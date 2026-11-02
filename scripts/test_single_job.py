#!/usr/bin/env python3
"""
Quick test with a single job - use this to verify setup
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.queue_manager import QueueManager, Job
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Create and add a single test job."""
    
    queue_manager = QueueManager()
    
    # Clear any existing jobs (optional)
    response = input("Clear existing queue? (yes/no): ")
    if response.lower() == 'yes':
        queue_manager.clear_queue()
        logger.info("Queue cleared")
    
    # Create test job
    test_job = Job(
        scene_id="test_01",
        prompt="A peaceful mountain lake at golden hour, mirror-like water reflecting surrounding pine trees, gentle mist rising from the surface, cinematic wide shot",
        aspect_ratio="16:9",
        duration=5
    )
    
    # Add to queue
    job_id = queue_manager.add_job(test_job)
    logger.info(f"✓ Test job added with ID: {job_id}")
    
    # Show stats
    stats = queue_manager.get_stats()
    logger.info(f"Queue status: {stats['pending']} pending, {stats['total']} total")
    
    logger.info("\nNext steps:")
    logger.info("1. Run: python scripts/run_automation.py")
    logger.info("2. Browser will open - log in if needed")
    logger.info("3. Watch the automation generate your test video")
    logger.info("4. Check ./data/downloads/test_01.mp4")


if __name__ == "__main__":
    main()
