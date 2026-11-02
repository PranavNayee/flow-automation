#!/usr/bin/env python3
"""
Main automation script - runs the Flow video generation pipeline
"""
import sys
import time
import signal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.queue_manager import QueueManager, JobStatus
from src.flow_driver import FlowDriver
from src.downloader import Downloader
from src.health_check import HealthChecker, generate_selector_update_guide
from src.credit_tracker import CreditTracker
from src.recovery_service import GenerationRecoveryService
from src.notifications import NotificationService
from src.utils import (
    setup_logger, 
    Config, 
    SelectorsConfig, 
    RateLimiter,
    action_delay
)

logger = setup_logger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global shutdown_requested
    logger.info("\n🛑 Shutdown signal received. Finishing current job...")
    shutdown_requested = True


def check_emergency_stop(config: Config) -> bool:
    """Check if emergency stop file exists."""
    emergency_file = config.get('safety.emergency_stop_file', './EMERGENCY_STOP')
    if Path(emergency_file).exists():
        logger.error(f"🚨 EMERGENCY STOP file detected: {emergency_file}")
        return True
    return False


def main():
    """Run the automation."""
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Flow Automation Starting")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = Config()
        selectors = SelectorsConfig()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Initialize components
    queue_manager = QueueManager()
    downloader = Downloader()
    recovery_service = GenerationRecoveryService()
    notifier = NotificationService(config.get_env('NOTIFICATION_WEBHOOK_URL'))
    credit_tracker = CreditTracker(
        monthly_limit=config.get_env('MONTHLY_CREDIT_LIMIT', None)
    )
    rate_limiter = RateLimiter(
        max_per_hour=config.get_env('MAX_GENERATIONS_PER_HOUR', 10),
        max_per_day=config.get_env('MAX_GENERATIONS_PER_DAY', 50)
    )
    health_checker = HealthChecker(selectors)
    
    # Test notification if configured
    if notifier.enabled:
        logger.info("Testing notification system...")
        if notifier.test_notification():
            logger.info("✓ Notification system working")
        else:
            logger.warning("⚠ Notification test failed")
    
    # Reset any stuck "running" jobs from previous crashes
    queue_manager.reset_running_jobs()
    
    # Check queue
    stats = queue_manager.get_stats()
    logger.info(f"Queue: {stats['pending']} pending, {stats['completed']} completed, {stats['failed']} failed")
    
    if stats['pending'] == 0:
        logger.warning("No pending jobs in queue. Exiting.")
        return 0
    
    # Start browser
    try:
        with FlowDriver(config, selectors, headless=False, recovery_service=recovery_service) as driver:
            logger.info("Browser started successfully")
            
            # Navigate to Flow
            if not driver.navigate_to_flow():
                logger.error("Failed to navigate to Flow. Exiting.")
                return 1
            
            # Health check
            if config.get('health_check.test_selectors_before_run', True):
                logger.info("Running health check...")
                health_result = health_checker.run_full_check(driver.page)
                
                if not health_result.passed:
                    logger.error("Health check failed! Flow UI has likely changed.")
                    
                    # Notify about health check failure
                    notifier.health_check_failed(health_result.failures)
                    
                    # Generate update guide
                    guide = generate_selector_update_guide(health_result)
                    guide_path = Path("./SELECTOR_UPDATE_GUIDE.md")
                    with open(guide_path, 'w') as f:
                        f.write(guide)
                    
                    logger.error(f"Update guide saved to: {guide_path}")
                    logger.error("Please update selectors.yaml and try again.")
                    return 1
                
                logger.info("✓ Health check passed!")
            
            # Main processing loop
            max_retries = config.get_env('MAX_RETRIES', 3)
            retry_delay = config.get_env('RETRY_DELAY_SECONDS', 30)
            min_gen_delay = config.get_env('MIN_DELAY_BETWEEN_GENERATIONS', 60)
            max_gen_delay = config.get_env('MAX_DELAY_BETWEEN_GENERATIONS', 180)
            
            processed_count = 0
            
            while not shutdown_requested:
                # Check emergency stop
                if check_emergency_stop(config):
                    logger.error("Emergency stop activated. Exiting.")
                    break
                
                # Check rate limits
                can_generate, rate_reason = rate_limiter.can_generate()
                if not can_generate:
                    logger.warning(f"Rate limit: {rate_reason}")
                    
                    # Notify if approaching limit
                    stats = rate_limiter.get_stats()
                    if stats['hourly']['remaining'] <= 2:
                        notifier.rate_limit_warning(
                            stats['hourly']['used'],
                            stats['hourly']['limit']
                        )
                    
                    logger.info("Waiting 60 seconds...")
                    time.sleep(60)
                    continue
                
                # Check credit limits
                can_generate, credit_reason = credit_tracker.can_generate()
                if not can_generate:
                    logger.warning(f"Credit limit: {credit_reason}")
                    break
                
                # Get next job
                job = queue_manager.get_next_job()
                if not job:
                    logger.info("No more jobs in queue. Exiting.")
                    notifier.queue_empty()
                    break
                
                logger.info(f"\n{'=' * 60}")
                logger.info(f"Processing job: {job.scene_id} ({processed_count + 1})")
                logger.info(f"{'=' * 60}\n")
                
                # Mark as running
                queue_manager.update_job(job.id, status=JobStatus.RUNNING.value)
                
                # Notify job started
                notifier.job_started(job)
                
                # Generate video (with checkpoint recovery)
                success, error_message = driver.generate_video(job)
                
                if success:
                    logger.info(f"✓ Generation successful: {job.scene_id}")
                    
                    # Download video
                    logger.info("Downloading video...")
                    output_path = downloader.download_from_job(job, driver.page)
                    
                    if output_path:
                        logger.info(f"✓ Downloaded: {output_path}")
                        
                        # Update job as completed
                        queue_manager.update_job(
                            job.id,
                            status=JobStatus.COMPLETED.value,
                            output_path=output_path
                        )
                        
                        # Clear checkpoints for completed job
                        recovery_service.clear_checkpoints(job.id)
                        
                        # Record credit usage
                        credit_tracker.record_generation(job.scene_id)
                        rate_limiter.record_generation()
                        
                        # Notify success
                        notifier.job_complete(job, output_path)
                        
                        processed_count += 1
                    else:
                        logger.error("✗ Download failed")
                        error_message = "Download failed"
                        success = False
                
                if not success:
                    # Handle failure
                    retry_count = job.retry_count + 1
                    
                    # Notify failure
                    notifier.job_failed(job, error_message, retry_count, max_retries)
                    
                    if retry_count < max_retries:
                        logger.warning(f"Job failed (attempt {retry_count}/{max_retries}). Will retry.")
                        queue_manager.update_job(
                            job.id,
                            status=JobStatus.RETRY.value,
                            error_message=error_message,
                            retry_count=retry_count
                        )
                        
                        logger.info(f"Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Job failed after {max_retries} attempts: {error_message}")
                        
                        # Clear checkpoints for failed job
                        recovery_service.clear_checkpoints(job.id)
                        
                        queue_manager.update_job(
                            job.id,
                            status=JobStatus.FAILED.value,
                            error_message=error_message,
                            retry_count=retry_count
                        )
                    
                    # Check if we should stop on warnings
                    if error_message and any(word in error_message.lower() for word in ['captcha', 'warning', 'rate limit']):
                        if config.get('safety.stop_on_warning', True):
                            logger.error("Stopping due to warning/CAPTCHA. Please check manually.")
                            
                            # Notify CAPTCHA/warning
                            if 'captcha' in error_message.lower():
                                notifier.captcha_detected()
                            
                            break
                
                # Delay between generations (human-like behavior)
                if not shutdown_requested:
                    logger.info(f"Waiting before next generation...")
                    action_delay(min_gen_delay, max_gen_delay)
            
            # Final stats
            logger.info("\n" + "=" * 60)
            logger.info("Automation session complete")
            logger.info("=" * 60)
            final_stats = queue_manager.get_stats()
            logger.info(f"Total processed: {processed_count}")
            logger.info(f"Pending: {final_stats['pending']}")
            logger.info(f"Completed: {final_stats['completed']}")
            logger.info(f"Failed: {final_stats['failed']}")
            
            # Credit usage
            credit_usage = credit_tracker.get_usage()
            logger.info(f"Credits used this month: {credit_usage['monthly_usage']}")
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
