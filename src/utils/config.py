"""
Configuration management for Flow Automation
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager that loads from .env and YAML files."""
    
    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to YAML config file
            env_path: Path to .env file
        """
        self.root_dir = Path(__file__).parent.parent.parent
        
        # Load .env
        env_file = self.root_dir / env_path
        if env_file.exists():
            load_dotenv(env_file)
        
        # Load YAML config
        self.config_data = {}
        config_file = self.root_dir / config_path
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
        
        # Check for local override
        local_config = self.root_dir / "config.local.yaml"
        if local_config.exists():
            with open(local_config, 'r') as f:
                local_data = yaml.safe_load(f) or {}
                self._deep_merge(self.config_data, local_data)
    
    def _deep_merge(self, base: dict, override: dict):
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-separated key.
        
        Args:
            key: Config key (e.g., 'video.default_aspect_ratio')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value
        """
        value = os.getenv(key, default)
        
        # Type conversion for common cases
        if isinstance(default, bool) and isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int) and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        elif isinstance(default, float) and isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        
        return value
    
    def get_path(self, key: str) -> Path:
        """
        Get a path, resolving it relative to the project root.
        
        Args:
            key: Environment variable name for the path
            
        Returns:
            Absolute Path object
        """
        path_str = self.get_env(key)
        if not path_str:
            raise ValueError(f"Path environment variable '{key}' not set")
        
        path = Path(path_str)
        if not path.is_absolute():
            path = self.root_dir / path
        
        return path


class SelectorsConfig:
    """Manages UI selectors for Flow."""
    
    def __init__(self, selectors_path: str = "selectors.yaml"):
        """
        Initialize selectors configuration.
        
        Args:
            selectors_path: Path to selectors YAML file
        """
        root_dir = Path(__file__).parent.parent.parent
        selectors_file = root_dir / selectors_path
        
        if not selectors_file.exists():
            raise FileNotFoundError(f"Selectors file not found: {selectors_file}")
        
        with open(selectors_file, 'r') as f:
            self.selectors = yaml.safe_load(f) or {}
    
    def get(self, key: str, **format_args) -> str:
        """
        Get a selector by dot-separated key with optional formatting.
        
        Args:
            key: Selector key (e.g., 'main.prompt_textarea')
            **format_args: Values to format into the selector string
            
        Returns:
            Selector string
        """
        keys = key.split('.')
        value = self.selectors
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Selector not found: {key}")
        
        if not isinstance(value, (str, int, float)):
            raise TypeError(f"Selector '{key}' is not a string value")
        
        selector = str(value)
        
        # Format the selector if args provided
        if format_args:
            selector = selector.format(**format_args)
        
        return selector
    
    def get_timeout(self, key: str, default: int = 10000) -> int:
        """
        Get a timeout value in milliseconds.
        
        Args:
            key: Timeout key (e.g., 'navigation')
            default: Default timeout in milliseconds
            
        Returns:
            Timeout in milliseconds
        """
        timeouts = self.selectors.get('timeouts', {})
        return timeouts.get(key, default)
    
    def get_wait(self, key: str, default: int = 1000) -> int:
        """
        Get a wait duration in milliseconds.
        
        Args:
            key: Wait key (e.g., 'after_click')
            default: Default wait in milliseconds
            
        Returns:
            Wait duration in milliseconds
        """
        waits = self.selectors.get('waits', {})
        return waits.get(key, default)
