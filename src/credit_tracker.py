"""
Credit tracking to monitor usage against plan limits
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from .utils import setup_logger

logger = setup_logger(__name__)


class CreditTracker:
    """Tracks generation credits used."""
    
    def __init__(
        self, 
        tracker_file: str = "./data/credit_tracker.json",
        monthly_limit: Optional[int] = None
    ):
        """
        Initialize credit tracker.
        
        Args:
            tracker_file: Path to JSON file for persistence
            monthly_limit: Monthly credit limit (optional)
        """
        self.tracker_file = Path(tracker_file)
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure monthly_limit is an int if provided
        if monthly_limit is not None:
            try:
                monthly_limit = int(monthly_limit)
            except (ValueError, TypeError):
                monthly_limit = None
        self.monthly_limit = monthly_limit
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load tracking data from file."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load credit tracker: {e}")
        
        # Initialize with default structure
        return {
            'current_month': datetime.now().strftime('%Y-%m'),
            'monthly_usage': 0,
            'total_usage': 0,
            'history': []
        }
    
    def _save(self):
        """Save tracking data to file."""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save credit tracker: {e}")
    
    def _check_month_rollover(self):
        """Check if we've entered a new month and reset counter."""
        current_month = datetime.now().strftime('%Y-%m')
        
        if self.data['current_month'] != current_month:
            logger.info(f"Month changed: {self.data['current_month']} → {current_month}")
            
            # Archive previous month
            self.data['history'].append({
                'month': self.data['current_month'],
                'usage': self.data['monthly_usage']
            })
            
            # Reset for new month
            self.data['current_month'] = current_month
            self.data['monthly_usage'] = 0
            self._save()
    
    def record_generation(self, scene_id: str, credits: int = 1):
        """
        Record a generation.
        
        Args:
            scene_id: Scene ID
            credits: Number of credits used (default 1)
        """
        self._check_month_rollover()
        
        self.data['monthly_usage'] += credits
        self.data['total_usage'] += credits
        
        logger.info(f"Credits used: {credits} for {scene_id}")
        logger.info(f"Monthly usage: {self.data['monthly_usage']}" + 
                   (f"/{self.monthly_limit}" if self.monthly_limit else ""))
        
        self._save()
    
    def get_usage(self) -> Dict[str, any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary with usage stats
        """
        self._check_month_rollover()
        
        stats = {
            'monthly_usage': self.data['monthly_usage'],
            'total_usage': self.data['total_usage'],
            'current_month': self.data['current_month']
        }
        
        if self.monthly_limit:
            stats['monthly_limit'] = self.monthly_limit
            stats['remaining'] = max(0, self.monthly_limit - self.data['monthly_usage'])
            stats['percentage_used'] = (self.data['monthly_usage'] / self.monthly_limit) * 100
        
        return stats
    
    def can_generate(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can generate based on credit limit.
        
        Returns:
            Tuple of (can_generate, reason_if_not)
        """
        self._check_month_rollover()
        
        if not self.monthly_limit:
            return True, None
        
        if self.data['monthly_usage'] >= self.monthly_limit:
            return False, f"Monthly credit limit reached ({self.data['monthly_usage']}/{self.monthly_limit})"
        
        return True, None
    
    def get_history(self) -> list:
        """
        Get historical usage.
        
        Returns:
            List of historical monthly usage
        """
        return self.data.get('history', [])
