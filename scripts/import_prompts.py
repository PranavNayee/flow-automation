#!/usr/bin/env python3
"""
Import prompts from CSV or JSON file
"""
import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.queue_manager import QueueManager, import_from_csv, import_from_json
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Import prompts from file."""
    parser = argparse.ArgumentParser(description="Import video prompts into queue")
    parser.add_argument('file', help="Path to CSV or JSON file")
    parser.add_argument(
        '--clear',
        action='store_true',
        help="Clear existing queue before importing (DANGEROUS!)"
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    # Initialize queue manager
    queue_manager = QueueManager()
    
    # Clear queue if requested
    if args.clear:
        logger.warning("Clearing existing queue...")
        response = input("Are you sure? This will delete all jobs. (yes/no): ")
        if response.lower() == 'yes':
            queue_manager.clear_queue()
            logger.info("Queue cleared")
        else:
            logger.info("Cancelled")
            sys.exit(0)
    
    # Import based on file type
    suffix = file_path.suffix.lower()
    
    try:
        if suffix == '.csv':
            logger.info(f"Importing from CSV: {file_path}")
            count = import_from_csv(str(file_path), queue_manager)
        elif suffix == '.json':
            logger.info(f"Importing from JSON: {file_path}")
            count = import_from_json(str(file_path), queue_manager)
        else:
            logger.error(f"Unsupported file type: {suffix}")
            logger.error("Use .csv or .json files")
            sys.exit(1)
        
        logger.info(f"✓ Imported {count} jobs successfully")
        
        # Show stats
        stats = queue_manager.get_stats()
        logger.info(f"Queue status: {stats['pending']} pending, {stats['total']} total")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
