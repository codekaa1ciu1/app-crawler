"""Example script for running the app crawler with Qwen AI."""
import os
from dotenv import load_dotenv
from app_crawler import AppCrawler

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
    print("🤖 AI NEEDS HELP!")
    print("="*60)
    print(f"\nQuestion: {question}")
    print(f"\nCurrent Screen: {current_state.get('activity', 'Unknown')}")
    print(f"Available Elements: {len(current_state.get('elements', []))}")
    print("\n" + "="*60)

    response = input("\nYour response (or 'stop' to end crawl): ")
    return response


def main():
    """Run Android app crawl with Qwen AI."""

    # Configuration for Android with Qwen AI
    crawler = AppCrawler(
        platform="android",
        app_package="org.wikipedia",  # Wikipedia app package
        app_activity=".main.MainActivity",  # Main activity
        device_name="emulator-5554",
        appium_server="http://localhost:4723",
        ai_provider="qwen",
        ai_api_key=os.getenv("QWEN_API_KEY"),
        db_path="crawler_paths.db",
        screenshot_dir="screenshots"
    )

    try:
        # Start crawling
        print("Starting crawler with Qwen AI...")
        crawler.connect()

        # Start crawling with max 10 steps for testing
        crawler.start_crawl(
            name="Wikipedia App with Qwen AI",
            description="Testing Wikipedia app crawling with Qwen AI",
            max_steps=10,
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