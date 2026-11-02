"""
Human-like delays and rate limiting
"""
import time
import random
from datetime import datetime, timedelta
from typing import Optional


class RateLimiter:
    """Enforces rate limits for generations."""
    
    def __init__(self, max_per_hour: int, max_per_day: int):
        """
        Initialize rate limiter.
        
        Args:
            max_per_hour: Maximum generations per hour
            max_per_day: Maximum generations per day
        """
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.generation_times = []
    
    def can_generate(self) -> tuple[bool, Optional[str]]:
        """
        Check if we can generate now without exceeding limits.
        
        Returns:
            Tuple of (can_generate, reason_if_not)
        """
        now = datetime.now()
        
        # Clean old entries
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        self.generation_times = [
            t for t in self.generation_times if t > day_ago
        ]
        
        # Check daily limit
        daily_count = len(self.generation_times)
        if daily_count >= self.max_per_day:
            oldest = min(self.generation_times)
            reset_time = oldest + timedelta(days=1)
            wait_seconds = (reset_time - now).total_seconds()
            return False, f"Daily limit reached ({daily_count}/{self.max_per_day}). Resets in {wait_seconds/3600:.1f}h"
        
        # Check hourly limit
        hourly_count = len([t for t in self.generation_times if t > hour_ago])
        if hourly_count >= self.max_per_hour:
            oldest_in_hour = min([t for t in self.generation_times if t > hour_ago])
            reset_time = oldest_in_hour + timedelta(hours=1)
            wait_seconds = (reset_time - now).total_seconds()
            return False, f"Hourly limit reached ({hourly_count}/{self.max_per_hour}). Resets in {wait_seconds/60:.1f}m"
        
        return True, None
    
    def record_generation(self):
        """Record that a generation occurred."""
        self.generation_times.append(datetime.now())
    
    def get_stats(self) -> dict:
        """Get current usage stats."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        hourly_count = len([t for t in self.generation_times if t > hour_ago])
        daily_count = len([t for t in self.generation_times if t > day_ago])
        
        return {
            'hourly': {
                'used': hourly_count,
                'limit': self.max_per_hour,
                'remaining': self.max_per_hour - hourly_count
            },
            'daily': {
                'used': daily_count,
                'limit': self.max_per_day,
                'remaining': self.max_per_day - daily_count
            }
        }


def random_delay(min_seconds: float, max_seconds: float):
    """
    Sleep for a random duration to mimic human behavior.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def human_typing_delay():
    """Add a realistic delay as if a human is typing."""
    time.sleep(random.uniform(0.05, 0.15))


def action_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """
    Delay between UI actions.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
    """
    random_delay(min_delay, max_delay)
