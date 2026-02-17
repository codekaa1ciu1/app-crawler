"""Example script for running the app crawler."""
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
    """Run example Android app crawl."""
    
    # Configuration for Android
    crawler = AppCrawler(
        platform="android",
        app_package="com.example.app",  # Replace with your app package
        app_activity=".MainActivity",    # Replace with your main activity
        device_name="emulator-5554",
        appium_server="http://localhost:4723",
        ai_provider="openai",  # or "anthropic"
        ai_api_key=os.getenv("OPENAI_API_KEY"),  # or ANTHROPIC_API_KEY
        db_path="crawler_paths.db",
        screenshot_dir="screenshots"
    )
    
    try:
        # Start crawling
        print("Starting crawler...")
        crawler.start_crawl(
            name="Example App Exploration",
            description="Exploring main app features",
            max_steps=30,
            human_callback=human_intervention_callback
        )
        
        print(f"\nCrawl completed! Path ID: {crawler.current_path_id}")
        print("View results in the web portal at http://localhost:5000")
        
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user")
        crawler.disconnect()
    except Exception as e:
        print(f"\nError during crawl: {e}")
        crawler.disconnect()


def replay_example():
    """Example of replaying a saved path."""
    
    path_id = input("Enter path ID to replay: ")
    
    crawler = AppCrawler(
        platform="android",
        app_package="com.example.app",
        app_activity=".MainActivity",
        device_name="emulator-5554",
        appium_server="http://localhost:4723",
        ai_provider="openai",
        db_path="crawler_paths.db"
    )
    
    try:
        print(f"Replaying path: {path_id}")
        crawler.replay_path(path_id, delay=2.0)
        print("Replay completed!")
        
    except Exception as e:
        print(f"Error during replay: {e}")
        crawler.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "replay":
        replay_example()
    else:
        main()
