"""
Configuration file for App Crawler.
You can import and use this in your scripts for cleaner configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CrawlerConfig:
    """Configuration for App Crawler."""
    
    # Platform settings
    platform: str = "android"  # "android" or "ios"
    app_package: str = ""
    app_activity: Optional[str] = None  # Android only
    bundle_id: Optional[str] = None  # iOS only
    
    # Device settings
    device_name: str = "emulator-5554"
    appium_server: str = "http://localhost:4723"
    platform_version: str = "11"
    
    # AI settings
    ai_provider: str = "openai"  # "openai" or "anthropic"
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None  # Optional override
    
    # Crawler settings
    max_steps: int = 50
    step_delay: float = 2.0
    screenshot_enabled: bool = True
    
    # Storage settings
    db_path: str = "crawler_paths.db"
    screenshot_dir: str = "screenshots"
    
    # Advanced settings
    auto_grant_permissions: bool = True
    no_reset: bool = True
    
    def __post_init__(self):
        """Load from environment if not provided."""
        if not self.ai_api_key:
            if self.ai_provider == "openai":
                self.ai_api_key = os.getenv("OPENAI_API_KEY")
            elif self.ai_provider == "anthropic":
                self.ai_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.appium_server:
            self.appium_server = os.getenv("APPIUM_SERVER", "http://localhost:4723")


# Example configurations for common scenarios

ANDROID_DEBUG_CONFIG = CrawlerConfig(
    platform="android",
    app_package="com.example.myapp",
    app_activity=".MainActivity",
    device_name="emulator-5554",
    max_steps=30
)

IOS_DEBUG_CONFIG = CrawlerConfig(
    platform="ios",
    app_package="com.example.MyApp",
    bundle_id="com.example.MyApp",
    device_name="iPhone 14",
    platform_version="16.0",
    max_steps=30
)

PRODUCTION_ANDROID_CONFIG = CrawlerConfig(
    platform="android",
    app_package="com.example.myapp",
    app_activity=".MainActivity",
    device_name="real-device-id",
    max_steps=100,
    step_delay=1.5,
    ai_provider="anthropic"  # Claude for production
)


def load_config_from_file(filepath: str) -> CrawlerConfig:
    """Load configuration from a JSON or YAML file.
    
    Args:
        filepath: Path to config file
        
    Returns:
        CrawlerConfig instance
    """
    import json
    
    with open(filepath, 'r') as f:
        if filepath.endswith('.json'):
            data = json.load(f)
        else:
            raise ValueError("Only JSON config files supported currently")
    
    return CrawlerConfig(**data)


# Usage example:
# from config import ANDROID_DEBUG_CONFIG
# crawler = AppCrawler(**ANDROID_DEBUG_CONFIG.__dict__)
