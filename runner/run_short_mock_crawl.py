"""Run a short local crawl using MockAIService to avoid external API calls.

This script creates an AppCrawler, injects the MockAIService, and runs
a short crawl with `max_steps=3` and no human interaction.
"""
import os
from app_crawler import AppCrawler
from mock_ai_service import MockAIService


def main():
    crawler = AppCrawler(
        platform="android",
        app_package="com.example.app",
        app_activity=".MainActivity",
        device_name=os.getenv("DEVICE_NAME", "emulator-5554"),
        appium_server=os.getenv("APPIUM_SERVER", "http://localhost:4723"),
        ai_provider="openai",  # will be replaced with mock
        db_path="crawler_paths.db",
        screenshot_dir="screenshots"
    )

    # Inject mock AI to avoid external API calls
    crawler.ai = MockAIService()

    try:
        crawler.start_crawl(
            name="Short Mock Crawl",
            description="Short run with mock AI",
            max_steps=3,
            human_callback=None
        )
        print(f"Crawl finished. Path ID: {crawler.current_path_id}")
    except Exception as e:
        print(f"Error running mock crawl: {e}")
        crawler.disconnect()


if __name__ == "__main__":
    main()
