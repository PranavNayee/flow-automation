"""
Flow driver - browser automation for Google Flow
"""
import time
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

from .utils import setup_logger, Config, SelectorsConfig, action_delay, human_typing_delay
from .queue_manager import Job, JobStatus
from .recovery_service import GenerationRecoveryService, GenerationStage

logger = setup_logger(__name__)


class FlowDriver:
    """Drives Google Flow to generate videos."""
    
    def __init__(
        self,
        config: Config,
        selectors: SelectorsConfig,
        headless: bool = False,
        recovery_service: Optional[GenerationRecoveryService] = None
    ):
        """
        Initialize Flow driver.
        
        Args:
            config: Configuration instance
            selectors: Selectors configuration
            headless: Run browser in headless mode
            recovery_service: Optional recovery service for checkpointing
        """
        self.config = config
        self.selectors = selectors
        self.headless = headless
        self.recovery = recovery_service or GenerationRecoveryService()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.flow_url = config.get_env('FLOW_URL', 'https://labs.google/flow')
        self.profile_path = config.get_path('BROWSER_PROFILE_PATH')
        self.screenshot_dir = Path('./data/screenshots')
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self):
        """Start the browser with persistent profile."""
        logger.info("Starting browser...")
        
        self.playwright = sync_playwright().start()
        
        # Launch browser with persistent context (keeps login)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_path),
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ],
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Get or create page
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        logger.info("Browser started successfully")
    
    def stop(self):
        """Stop the browser."""
        if self.context:
            logger.info("Closing browser...")
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser closed")
    
    def navigate_to_flow(self) -> bool:
        """
        Navigate to Flow and wait for page to load.
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Navigating to {self.flow_url}")
            timeout = self.selectors.get_timeout('navigation', 30000)
            self.page.goto(self.flow_url, timeout=timeout, wait_until='domcontentloaded')
            action_delay(2, 4)
            
            # Check if we're logged in (this is a heuristic)
            # If we see a sign-in button, we're not logged in
            try:
                signin_button = self.page.locator('button:has-text("Sign in"), a:has-text("Sign in")')
                if signin_button.count() > 0:
                    logger.warning("Not logged in to Flow. Please log in manually in the browser window.")
                    logger.warning("The browser will stay open. Log in, then press Enter here...")
                    input("Press Enter after logging in...")
                    action_delay(2, 3)
            except:
                pass  # Assume we're logged in
            
            # Click "New project" to reach the creation page
            try:
                new_project_selector = self.selectors.get('main.new_project_button')
                count = self.page.locator(new_project_selector).count()
                logger.info(f"New project button count: {count} (selector: {new_project_selector})")
                if count > 0:
                    logger.info("Clicking 'New project' to start creation...")
                    self.page.locator(new_project_selector).first.click()
                    action_delay(3, 5)
            except KeyError:
                logger.info("No new_project_button selector configured, skipping")
            except Exception as e:
                logger.warning(f"Could not click 'New project': {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to Flow: {e}")
            self._take_screenshot("navigation_failed")
            return False
    
    def check_for_warnings(self) -> Optional[str]:
        """
        Check for CAPTCHAs, warnings, or rate limits.
        
        Returns:
            Warning message if found, None otherwise
        """
        try:
            # Check for CAPTCHA
            captcha_selector = self.selectors.get('main.captcha')
            if self.page.locator(captcha_selector).count() > 0:
                return "CAPTCHA detected"
            
            # Check for warning messages
            warning_selector = self.selectors.get('main.warning_message')
            warnings = self.page.locator(warning_selector)
            if warnings.count() > 0:
                return f"Warning: {warnings.first.inner_text()}"
            
            # Check for rate limit
            rate_limit_selector = self.selectors.get('main.rate_limit_warning')
            if self.page.locator(rate_limit_selector).count() > 0:
                return "Rate limit warning detected"
                
        except KeyError:
            # Selector not configured, skip
            pass
        except Exception as e:
            logger.warning(f"Error checking for warnings: {e}")
        
        return None
    
    def enter_prompt(self, prompt: str) -> bool:
        """
        Enter a prompt in the text area.
        
        Args:
            prompt: Prompt text
            
        Returns:
            True if successful
        """
        try:
            selector = self.selectors.get('main.prompt_textarea')
            timeout = self.selectors.get_timeout('element_visible', 10000)
            
            logger.info("Entering prompt...")
            
            # Wait for textarea
            textarea = self.page.wait_for_selector(selector, timeout=timeout)
            
            # Clear existing text
            textarea.fill('')
            action_delay(0.5, 1)
            
            # Type prompt with human-like delays
            for char in prompt:
                textarea.type(char, delay=50 + (30 * (0.5 - 0.5 * (len(char) > 0))))
                if char in ['.', ',', '!', '?']:
                    human_typing_delay()
            
            action_delay(1, 2)
            logger.info(f"Prompt entered: {prompt[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enter prompt: {e}")
            self._take_screenshot("prompt_entry_failed")
            return False
    
    def set_aspect_ratio(self, aspect_ratio: str) -> bool:
        """
        Set the aspect ratio if available.
        
        Args:
            aspect_ratio: Aspect ratio (e.g., "16:9", "9:16", "1:1")
            
        Returns:
            True if successful or selector not found
        """
        try:
            dropdown_selector = self.selectors.get('main.aspect_ratio_dropdown')
            
            # Click dropdown
            self.page.click(dropdown_selector)
            action_delay(0.5, 1)
            
            # Select option
            option_selector = self.selectors.get(
                'main.aspect_ratio_option',
                ratio=aspect_ratio
            )
            self.page.click(option_selector)
            action_delay(0.5, 1)
            
            logger.info(f"Aspect ratio set to {aspect_ratio}")
            return True
            
        except KeyError:
            logger.info("Aspect ratio selector not configured, skipping")
            return True  # Not a failure
        except Exception as e:
            logger.warning(f"Failed to set aspect ratio: {e}")
            return True  # Don't fail the job for this
    
    def click_generate(self) -> bool:
        """
        Click the generate button.
        
        Returns:
            True if successful
        """
        try:
            selector = self.selectors.get('main.prompt_submit_button')
            timeout = self.selectors.get_timeout('element_visible', 10000)
            
            logger.info("Clicking generate button...")
            
            button = self.page.wait_for_selector(selector, timeout=timeout)
            button.click()
            
            action_delay(2, 4)
            logger.info("Generate button clicked")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click generate button: {e}")
            self._take_screenshot("generate_click_failed")
            return False
    
    def wait_for_completion(self, max_wait_seconds: int = 600) -> Tuple[bool, Optional[str]]:
        """
        Wait for video generation to complete.
        
        Args:
            max_wait_seconds: Maximum time to wait
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"Waiting for generation (max {max_wait_seconds}s)...")
        
        start_time = time.time()
        check_interval = self.config.get('download.check_interval_seconds', 5)
        
        try:
            generating_selector = self.selectors.get('main.generating_indicator')
            complete_selector = self.selectors.get('main.generation_complete')
            error_selector = self.selectors.get('main.generation_error')
        except KeyError as e:
            logger.error(f"Missing selector: {e}")
            return False, f"Selector configuration error: {e}"
        
        while time.time() - start_time < max_wait_seconds:
            # Check for warnings
            warning = self.check_for_warnings()
            if warning:
                logger.error(f"Warning detected: {warning}")
                self._take_screenshot("warning_detected")
                return False, warning
            
            # Check if generation is complete
            try:
                if self.page.locator(complete_selector).count() > 0:
                    logger.info("Generation complete!")
                    return True, None
                
                # Check for error
                if self.page.locator(error_selector).count() > 0:
                    error_text = self.page.locator(error_selector).first.inner_text()
                    logger.error(f"Generation error: {error_text}")
                    self._take_screenshot("generation_error")
                    return False, f"Generation error: {error_text}"
                
                # Still generating
                if self.page.locator(generating_selector).count() > 0:
                    elapsed = int(time.time() - start_time)
                    logger.info(f"Still generating... ({elapsed}s)")
                
            except Exception as e:
                logger.warning(f"Error checking status: {e}")
            
            time.sleep(check_interval)
        
        # Timeout
        logger.error("Generation timeout")
        self._take_screenshot("generation_timeout")
        return False, "Generation timeout"
    
    def get_video_download_info(self) -> Optional[dict]:
        """
        Get information about the generated video (URL or download button).
        
        Returns:
            Dictionary with download info or None
        """
        try:
            # Try to find video element
            video_selector = self.selectors.get('main.video_preview')
            videos = self.page.locator(video_selector)
            
            if videos.count() > 0:
                video = videos.first
                src = video.get_attribute('src')
                if src:
                    logger.info(f"Found video element with src: {src[:100]}")
                    return {'type': 'src', 'url': src}
            
            # Try to find download button
            download_selector = self.selectors.get('main.download_button')
            download_buttons = self.page.locator(download_selector)
            
            if download_buttons.count() > 0:
                button = download_buttons.first
                href = button.get_attribute('href')
                if href:
                    logger.info("Found download link")
                    return {'type': 'link', 'url': href}
                else:
                    logger.info("Found download button (will trigger click)")
                    return {'type': 'button', 'element': button}
            
            logger.warning("No video download method found")
            self._take_screenshot("no_download_found")
            return None
            
        except KeyError as e:
            logger.error(f"Missing selector: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting download info: {e}")
            self._take_screenshot("download_info_error")
            return None
    
    def generate_video(self, job: Job) -> Tuple[bool, Optional[str]]:
        """
        Complete workflow to generate a single video with checkpoint recovery.
        
        Args:
            job: Job to process
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(f"=" * 60)
        logger.info(f"Starting generation for job {job.scene_id}")
        logger.info(f"Prompt: {job.prompt}")
        logger.info(f"=" * 60)
        
        # Check if we can resume from a checkpoint
        resume_point = self.recovery.get_resume_point(job.id)
        
        if resume_point:
            logger.info(f"🔄 Resuming from checkpoint: {resume_point}")
            checkpoint = self.recovery.get_last_checkpoint(job.id)
            
            # If generation is already complete, skip to download
            if resume_point == GenerationStage.DOWNLOAD_STARTED:
                logger.info("Generation already complete, starting download...")
                download_info = checkpoint['data'].get('download_info') if checkpoint['data'] else None
                
                if download_info:
                    # Restore download info to job metadata
                    if not job.metadata:
                        job.metadata = {}
                    job.metadata['download_info'] = download_info
                    return True, None
        else:
            logger.info("Starting fresh generation (no checkpoints)")
            self.recovery.checkpoint(job.id, GenerationStage.INITIALIZED)
        
        # Navigate to Flow (skip if already navigated)
        if not resume_point or resume_point == GenerationStage.NAVIGATED:
            if not self.navigate_to_flow():
                return False, "Failed to navigate to Flow"
            self.recovery.checkpoint(job.id, GenerationStage.NAVIGATED)
        
        # Check for warnings before starting
        warning = self.check_for_warnings()
        if warning:
            return False, warning
        
        # Enter prompt (skip if already entered)
        if not resume_point or resume_point in [GenerationStage.NAVIGATED, GenerationStage.PROMPT_ENTERED]:
            if not self.enter_prompt(job.prompt):
                return False, "Failed to enter prompt"
            self.recovery.checkpoint(job.id, GenerationStage.PROMPT_ENTERED)
        
        # Set aspect ratio if specified (skip if already set)
        if not resume_point or resume_point in [GenerationStage.NAVIGATED, GenerationStage.PROMPT_ENTERED, GenerationStage.SETTINGS_CONFIGURED]:
            if job.aspect_ratio:
                self.set_aspect_ratio(job.aspect_ratio)
            self.recovery.checkpoint(job.id, GenerationStage.SETTINGS_CONFIGURED)
        
        # Click generate (skip if generation already started)
        if not resume_point or resume_point == GenerationStage.GENERATION_STARTED:
            if resume_point != GenerationStage.GENERATION_STARTED:
                if not self.click_generate():
                    return False, "Failed to click generate button"
            self.recovery.checkpoint(job.id, GenerationStage.GENERATION_STARTED)
        
        # Wait for completion
        max_wait = self.config.get('download.timeout_seconds', 600)
        success, error = self.wait_for_completion(max_wait)
        
        if not success:
            return False, error
        
        self.recovery.checkpoint(job.id, GenerationStage.GENERATION_COMPLETE)
        
        # Video is ready - get download info
        download_info = self.get_video_download_info()
        if not download_info:
            return False, "Could not find video download method"
        
        # Store download info in job metadata for downloader to use
        if not job.metadata:
            job.metadata = {}
        job.metadata['download_info'] = download_info
        
        # Checkpoint with download info
        self.recovery.checkpoint(
            job.id,
            GenerationStage.DOWNLOAD_STARTED,
            {'download_info': download_info}
        )
        
        logger.info(f"✓ Generation successful for {job.scene_id}")
        return True, None
    
    def _take_screenshot(self, name: str):
        """
        Take a screenshot for debugging.
        
        Args:
            name: Name for the screenshot
        """
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            path = self.screenshot_dir / filename
            self.page.screenshot(path=str(path))
            logger.info(f"Screenshot saved: {path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
