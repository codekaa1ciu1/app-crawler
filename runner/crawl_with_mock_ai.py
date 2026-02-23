"""Example script for running the app crawler with Mock AI (for testing)."""
import os
from dotenv import load_dotenv
from app_crawler import AppCrawler
from mock_ai_service import MockAIService

# Load environment variables
load_dotenv()


def human_intervention_callback(question: str, current_state: dict) -> str:
    """Callback function for human intervention.

    Args:
        question: Question from AI
        current_state: Current app state

    Returns:
        Human's response
    """
    print("\n" + "="*60)
    print("🤖 MOCK AI NEEDS HELP!")
    print("="*60)
    print(f"\nQuestion: {question}")
    print(f"\nCurrent Screen: {current_state.get('activity', 'Unknown')}")
    print(f"Available Elements: {len(current_state.get('elements', []))}")
    print("\n" + "="*60)

    response = input("\nYour response (or 'stop' to end crawl): ")
    return response


class MockAppCrawler(AppCrawler):
    """App crawler with mock AI service."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace the real AI service with mock
        self.ai = MockAIService()


def main():
    """Run Android app crawl with Mock AI."""

    # Configuration for Android with Mock AI
    crawler = MockAppCrawler(
        platform="android",
        app_package="org.wikipedia",  # Wikipedia app package
        app_activity=".main.MainActivity",  # Main activity
        device_name="emulator-5554",
        appium_server="http://localhost:4723",
        ai_provider="openai",  # Not used with mock
        ai_api_key="dummy",  # Not used with mock
        db_path="crawler_paths.db",
        screenshot_dir="screenshots"
    )

    try:
        # Start crawling
        print("Starting crawler with Mock AI...")
        crawler.connect()

        # Start crawling with max 5 steps for testing
        crawler.start_crawl(
            name="Wikipedia App with Mock AI",
            description="Testing Wikipedia app crawling with Mock AI",
            max_steps=5,
            human_callback=human_intervention_callback
        )

        print(f"\nCrawl completed! Path ID: {crawler.current_path_id}")

    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.")
    except Exception as e:
        print(f"Error during crawling: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.disconnect()


if __name__ == "__main__":
    main()