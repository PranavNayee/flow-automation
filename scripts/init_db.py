#!/usr/bin/env python3
"""
Initialize the database and create necessary directories
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.queue_manager import QueueManager
from src.utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Initialize database and directories."""
    logger.info("Initializing Flow Automation...")
    
    # Create directories
    directories = [
        "./data",
        "./data/downloads",
        "./data/projects",
        "./data/screenshots",
        "./logs",
        "./playwright-state"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Create .gitkeep files
    for directory in ["./data/downloads", "./data/projects", "./data/screenshots"]:
        gitkeep = Path(directory) / ".gitkeep"
        gitkeep.touch()
    
    # Initialize database
    logger.info("Initializing database...")
    queue_manager = QueueManager()
    logger.info("Database initialized")
    
    # Create EMERGENCY_STOP file template
    emergency_stop = Path("./EMERGENCY_STOP.template")
    with open(emergency_stop, 'w') as f:
        f.write("# Remove .template extension to activate emergency stop\n")
        f.write("# The automation will check for this file and stop immediately\n")
    
    logger.info("✓ Initialization complete!")
    logger.info("Next steps:")
    logger.info("1. Copy .env.example to .env and fill in your settings")
    logger.info("2. Update selectors.yaml with current Flow UI selectors")
    logger.info("3. Run: playwright install chromium")
    logger.info("4. Import prompts: python scripts/import_prompts.py examples/prompts.csv")


if __name__ == "__main__":
    main()
