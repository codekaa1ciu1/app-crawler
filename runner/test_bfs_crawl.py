"""Test script for the enhanced BFS crawler implementation.

This script runs a single Enhanced BFS crawl to test the new systematic element testing functionality
where each actionable element on every screen is tested and observed.
"""
import os
import sys
from dotenv import load_dotenv
from app_crawler import AppCrawler


def test_bfs_crawl():
    """Test the BFS crawler with a short crawl session."""
    # Load environment variables
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    except Exception:
        try:
            load_dotenv()
        except Exception:
            pass

    print("🧪 Testing Enhanced BFS Crawler Implementation")
    print("Strategy: Systematic Element Testing")
    print("=" * 50)

    # Check QWEN API key
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        masked = (qwen_key[:4] + "..." + qwen_key[-4:]) if len(qwen_key) > 8 else "****"
        print(f"QWEN API Key: {masked}")
    else:
        print("❌ QWEN_API_KEY not found!")
        return False

    APK_PATH = os.path.join("app_for_testing", "Android", "wikipedia.apk")
    PACKAGE_NAME = "org.wikipedia"

    try:
        crawler = AppCrawler(
            platform="android",
            app_package=PACKAGE_NAME,
            app_activity="",
            device_name="emulator-5554",
            appium_server="http://localhost:4723",
            ai_provider="qwen",
            ai_api_key=qwen_key,
            db_path="crawler_paths.db",
            screenshot_dir="screenshots",
            app_wait_activity="org.wikipedia.onboarding.InitialOnboardingActivity",
            app_path=APK_PATH
        )

        print("\n🚀 Starting Enhanced BFS test crawl (10 steps max)...")
        print("Strategy: Test every actionable element on each screen systematically")
        
        crawler.start_crawl(
            name="Enhanced BFS Test Crawl",
            description="Testing systematic element testing crawler implementation",
            max_steps=10  # Short test
        )

        print("✅ Enhanced BFS test completed successfully!")
        
        # Check results
        from app_crawler.database import CrawlerDatabase
        db = CrawlerDatabase()
        paths = db.get_all_paths()
        
        print(f"\n📊 Test Results:")
        print(f"   Total paths: {len(paths)}")
        
        for path in paths:
            steps = db.get_path_steps(path['path_id'])
            print(f"   Path {path['path_id'][:8]}...: {len(steps)} steps")
            if len(steps) > 0:
                latest_steps = sorted(steps, key=lambda x: x['step_number'])[-3:]
                print(f"   Latest actions: {[s['action_type'] for s in latest_steps]}")

        return True

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bfs_crawl()
    if success:
        print("\n🎉 Enhanced BFS implementation test passed!")
        print("   Strategy: Systematic testing of every actionable element")
        print("   You can now run the full 20x crawl with:")
        print("   python runner/run_bfs_20x_crawl.py")
    else:
        print("\n❌ Enhanced BFS implementation test failed")
        print("   Please check the errors above and fix before running full crawl")
        sys.exit(1)