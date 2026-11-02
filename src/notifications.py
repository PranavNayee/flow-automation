"""
Notification service for alerting via webhooks (Slack/Discord/etc.)
"""
import requests
from datetime import datetime
from typing import Optional
from .utils import setup_logger

logger = setup_logger(__name__)


class NotificationLevel:
    """Notification level constants."""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'


class NotificationService:
    """Send notifications to external services via webhooks."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize notification service.
        
        Args:
            webhook_url: Webhook URL (Slack, Discord, etc.)
        """
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url)
        
        if not self.enabled:
            logger.info("Notifications disabled (no webhook URL configured)")
        else:
            logger.info(f"Notifications enabled: {webhook_url[:30]}...")
    
    def send(
        self, 
        title: str, 
        message: str, 
        level: str = NotificationLevel.INFO,
        fields: Optional[dict] = None
    ):
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info/success/warning/error)
            fields: Optional additional fields
        """
        if not self.enabled:
            return
        
        # Color coding
        color_map = {
            NotificationLevel.INFO: 0x0066cc,      # Blue
            NotificationLevel.SUCCESS: 0x00cc66,   # Green
            NotificationLevel.WARNING: 0xff9900,   # Orange
            NotificationLevel.ERROR: 0xcc0000      # Red
        }
        
        # Emoji mapping
        emoji_map = {
            NotificationLevel.INFO: 'ℹ️',
            NotificationLevel.SUCCESS: '✅',
            NotificationLevel.WARNING: '⚠️',
            NotificationLevel.ERROR: '❌'
        }
        
        # Build payload (Discord/Slack webhook format)
        payload = {
            'embeds': [{
                'title': f"{emoji_map.get(level, 'ℹ️')} {title}",
                'description': message,
                'color': color_map.get(level, 0x0066cc),
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': 'Flow Automation'
                }
            }]
        }
        
        # Add fields if provided
        if fields:
            payload['embeds'][0]['fields'] = [
                {'name': k, 'value': str(v), 'inline': True}
                for k, v in fields.items()
            ]
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"Notification sent: {title}")
        
        except requests.RequestException as e:
            logger.error(f"Failed to send notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
    
    def job_started(self, job):
        """Notify when job starts."""
        self.send(
            'Generation Started',
            f"**{job.scene_id}**\n"
            f"Prompt: {job.prompt[:150]}{'...' if len(job.prompt) > 150 else ''}",
            NotificationLevel.INFO,
            {
                'Job ID': job.id,
                'Aspect Ratio': job.aspect_ratio
            }
        )
    
    def job_complete(self, job, output_path: str):
        """Notify when job completes successfully."""
        self.send(
            'Generation Complete',
            f"**{job.scene_id}**\n"
            f"Video generated successfully!\n"
            f"File: `{output_path}`",
            NotificationLevel.SUCCESS,
            {
                'Job ID': job.id,
                'Duration': f"{job.duration}s"
            }
        )
    
    def job_failed(self, job, error: str, attempt: int, max_attempts: int):
        """Notify when job fails."""
        self.send(
            'Generation Failed',
            f"**{job.scene_id}**\n"
            f"Error: {error}\n"
            f"Attempt: {attempt}/{max_attempts}",
            NotificationLevel.ERROR if attempt >= max_attempts else NotificationLevel.WARNING,
            {
                'Job ID': job.id,
                'Retry Count': job.retry_count
            }
        )
    
    def captcha_detected(self):
        """Notify when CAPTCHA is detected."""
        self.send(
            'CAPTCHA Detected',
            '🛑 Automation stopped due to CAPTCHA.\n'
            'Manual intervention required.\n'
            'Please complete the CAPTCHA and lower your rate limits.',
            NotificationLevel.ERROR
        )
    
    def rate_limit_warning(self, hourly_used: int, hourly_limit: int):
        """Notify when approaching rate limit."""
        self.send(
            'Rate Limit Warning',
            f'Approaching hourly rate limit.\n'
            f'Used: {hourly_used}/{hourly_limit}',
            NotificationLevel.WARNING
        )
    
    def health_check_failed(self, failures: list):
        """Notify when health check fails."""
        failure_list = '\n'.join([f"• {f['selector_key']}: {f['reason']}" for f in failures])
        
        self.send(
            'Health Check Failed',
            f"Flow UI selectors are broken!\n\n{failure_list}\n\n"
            f"Update `selectors.yaml` before continuing.",
            NotificationLevel.ERROR
        )
    
    def queue_empty(self):
        """Notify when queue is empty."""
        self.send(
            'Queue Empty',
            'No pending jobs in queue.\n'
            'Import more prompts to continue automation.',
            NotificationLevel.INFO
        )
    
    def daily_summary(self, stats: dict):
        """Send daily summary notification."""
        self.send(
            'Daily Summary',
            f"Today's automation results:",
            NotificationLevel.INFO,
            {
                'Completed': stats.get('completed', 0),
                'Failed': stats.get('failed', 0),
                'Pending': stats.get('pending', 0)
            }
        )
    
    def emergency_stop(self):
        """Notify emergency stop was triggered."""
        self.send(
            'Emergency Stop',
            '🚨 EMERGENCY STOP file detected!\n'
            'Automation has been halted.',
            NotificationLevel.ERROR
        )
    
    def test_notification(self) -> bool:
        """
        Send a test notification.
        
        Returns:
            True if successful
        """
        try:
            self.send(
                'Test Notification',
                'This is a test notification from Flow Automation.\n'
                'If you see this, notifications are working correctly! 🎉',
                NotificationLevel.SUCCESS
            )
            return True
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return False
