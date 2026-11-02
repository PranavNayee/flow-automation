"""
Health check module to verify Flow UI selectors are still valid
"""
from typing import List, Dict, Optional, Tuple
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from .utils import setup_logger, SelectorsConfig

logger = setup_logger(__name__)


class HealthCheckResult:
    """Result of a health check."""
    
    def __init__(self):
        self.passed = True
        self.failures: List[Dict[str, str]] = []
        self.warnings: List[str] = []
    
    def add_failure(self, selector_key: str, selector: str, reason: str):
        """Record a selector failure."""
        self.passed = False
        self.failures.append({
            'selector_key': selector_key,
            'selector': selector,
            'reason': reason
        })
    
    def add_warning(self, message: str):
        """Record a warning."""
        self.warnings.append(message)
    
    def __bool__(self) -> bool:
        """True if health check passed."""
        return self.passed
    
    def __str__(self) -> str:
        """String representation of results."""
        if self.passed:
            msg = "✓ Health check passed"
            if self.warnings:
                msg += f" (with {len(self.warnings)} warnings)"
            return msg
        
        msg = f"✗ Health check FAILED with {len(self.failures)} errors:\n"
        for failure in self.failures:
            msg += f"  - {failure['selector_key']}: {failure['reason']}\n"
            msg += f"    Selector: {failure['selector']}\n"
        
        return msg


class HealthChecker:
    """Checks if Flow UI selectors are still valid."""
    
    def __init__(self, selectors_config: SelectorsConfig):
        """
        Initialize health checker.
        
        Args:
            selectors_config: Selectors configuration
        """
        self.selectors = selectors_config
    
    def check_selector(
        self, 
        page: Page, 
        selector: str, 
        timeout: int = 5000,
        should_be_visible: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a selector is valid.
        
        Args:
            page: Playwright page
            selector: CSS selector
            timeout: Timeout in milliseconds
            should_be_visible: If True, check that element is visible
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if should_be_visible:
                page.wait_for_selector(selector, timeout=timeout, state='visible')
            else:
                page.wait_for_selector(selector, timeout=timeout, state='attached')
            return True, None
        except PlaywrightTimeout:
            return False, "Element not found or not visible"
        except Exception as e:
            return False, str(e)
    
    def check_essential_selectors(self, page: Page) -> HealthCheckResult:
        """
        Check essential selectors that must be present on the main page.
        
        Args:
            page: Playwright page (should be on Flow main page)
            
        Returns:
            HealthCheckResult
        """
        result = HealthCheckResult()
        
        # Define essential selectors that should be present
        essential = [
            ('main.prompt_textarea', False),
            ('main.prompt_submit_button', False),
        ]
        
        logger.info("Checking essential selectors...")
        
        for selector_key, must_be_visible in essential:
            try:
                selector = self.selectors.get(selector_key)
                is_valid, error = self.check_selector(
                    page, 
                    selector, 
                    timeout=10000,
                    should_be_visible=must_be_visible
                )
                
                if not is_valid:
                    result.add_failure(selector_key, selector, error)
                    logger.error(f"✗ {selector_key}: {error}")
                else:
                    logger.info(f"✓ {selector_key}")
                    
            except KeyError:
                result.add_failure(
                    selector_key, 
                    "N/A", 
                    "Selector not found in configuration"
                )
                logger.error(f"✗ {selector_key}: not in configuration")
            except Exception as e:
                result.add_failure(selector_key, "N/A", str(e))
                logger.error(f"✗ {selector_key}: {e}")
        
        return result
    
    def check_optional_selectors(self, page: Page) -> HealthCheckResult:
        """
        Check optional selectors with warnings instead of failures.
        
        Args:
            page: Playwright page
            
        Returns:
            HealthCheckResult (warnings only, won't fail health check)
        """
        result = HealthCheckResult()
        
        # Optional selectors that would be nice to have
        optional = [
            'main.aspect_ratio_dropdown',
            'main.duration_input',
            'main.credit_counter',
            'main.download_button',
        ]
        
        logger.info("Checking optional selectors...")
        
        for selector_key in optional:
            try:
                selector = self.selectors.get(selector_key)
                is_valid, error = self.check_selector(
                    page, 
                    selector, 
                    timeout=3000
                )
                
                if not is_valid:
                    result.add_warning(f"{selector_key} not found: {error}")
                    logger.warning(f"⚠ {selector_key}: {error}")
                else:
                    logger.info(f"✓ {selector_key}")
                    
            except KeyError:
                result.add_warning(f"{selector_key} not in configuration")
            except Exception as e:
                result.add_warning(f"{selector_key}: {e}")
        
        return result
    
    def check_for_warnings(self, page: Page) -> List[str]:
        """
        Check for warning messages or unusual activity indicators.
        
        Args:
            page: Playwright page
            
        Returns:
            List of warning messages found
        """
        warnings = []
        
        # Check for various warning indicators
        warning_selectors = [
            ('main.captcha', 'CAPTCHA detected'),
            ('main.warning_message', 'Warning message present'),
            ('main.rate_limit_warning', 'Rate limit warning'),
        ]
        
        for selector_key, message in warning_selectors:
            try:
                selector = self.selectors.get(selector_key)
                if page.locator(selector).count() > 0:
                    warnings.append(message)
                    logger.warning(f"⚠ {message}")
            except (KeyError, Exception):
                pass  # Selector not found is OK for warnings
        
        return warnings
    
    def run_full_check(self, page: Page) -> HealthCheckResult:
        """
        Run a complete health check.
        
        Args:
            page: Playwright page on Flow main page
            
        Returns:
            Combined HealthCheckResult
        """
        logger.info("=" * 50)
        logger.info("Starting Flow UI health check...")
        logger.info("=" * 50)
        
        # Check essential selectors
        essential_result = self.check_essential_selectors(page)
        
        # Check optional selectors (warnings only)
        optional_result = self.check_optional_selectors(page)
        
        # Check for warnings
        warnings = self.check_for_warnings(page)
        
        # Combine results
        final_result = essential_result
        final_result.warnings.extend(optional_result.warnings)
        final_result.warnings.extend(warnings)
        
        logger.info("=" * 50)
        logger.info(str(final_result))
        logger.info("=" * 50)
        
        return final_result


def generate_selector_update_guide(result: HealthCheckResult) -> str:
    """
    Generate a guide for updating broken selectors.
    
    Args:
        result: Health check result
        
    Returns:
        Markdown-formatted guide
    """
    if result.passed:
        return "All selectors are working correctly!"
    
    guide = "# Flow UI Selector Update Guide\n\n"
    guide += "The following selectors need to be updated in `selectors.yaml`:\n\n"
    
    for failure in result.failures:
        guide += f"## {failure['selector_key']}\n\n"
        guide += f"**Current selector:** `{failure['selector']}`\n\n"
        guide += f"**Error:** {failure['reason']}\n\n"
        guide += "**How to fix:**\n"
        guide += "1. Open Flow in your browser\n"
        guide += "2. Open DevTools (F12 or Cmd+Opt+I)\n"
        guide += "3. Use Element Picker (Ctrl+Shift+C / Cmd+Shift+C)\n"
        guide += "4. Click on the relevant UI element\n"
        guide += "5. In the Elements tab, right-click the highlighted element\n"
        guide += "6. Select 'Copy' → 'Copy selector'\n"
        guide += f"7. Update `selectors.yaml` → `{failure['selector_key']}`\n\n"
        guide += "**Prefer selectors in this order:**\n"
        guide += "1. `[data-testid='...']` (most stable)\n"
        guide += "2. `[aria-label='...']` (accessible, fairly stable)\n"
        guide += "3. `id='...'` (stable if present)\n"
        guide += "4. Semantic HTML with attributes (e.g., `button[type='submit']`)\n"
        guide += "5. CSS classes (least stable, avoid if possible)\n\n"
        guide += "---\n\n"
    
    return guide
