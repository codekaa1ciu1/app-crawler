"""Run Enhanced BFS crawler 20 times against Wikipedia APK using Qwen AI provider.

This script will run the enhanced BFS crawler multiple times to explore the app
comprehensively using systematic element testing strategy where every actionable 
element on every screen is tested and observed.

Requirements:
- Ensure `adb` is available on PATH and a device/emulator is connected.
- Ensure Appium server is running on localhost:4723
- Set `QWEN_API_KEY` in environment for AI API access.
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from app_crawler import AppCrawler


APK_PATH = os.path.join("app_for_testing", "Android", "wikipedia.apk")
PACKAGE_NAME = "org.wikipedia"
MAX_CRAWL_RUNS = 20
STEPS_PER_RUN = 500


def install_apk(apk_path: str) -> bool:
    """Install APK via adb. Returns True on success."""
    if not os.path.exists(apk_path):
        print(f"APK not found: {apk_path}")
        return False

    cmd = ["adb", "install", "-r", apk_path]
    print("Running:", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
        print("APK installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("Failed to install APK:", e)
        return False


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check ADB connection
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        devices = [line for line in result.stdout.split('\n') if 'device' in line and 'List of' not in line]
        if not devices:
            print("❌ No ADB devices found. Please start an Android emulator.")
            return False
        print(f"✅ ADB device found: {devices[0].strip()}")
    except Exception as e:
        print(f"❌ ADB check failed: {e}")
        return False
    
    # Check Appium server
    try:
        import requests
        response = requests.get("http://localhost:4723/status", timeout=5)
        if response.status_code == 200:
            print("✅ Appium server is running")
        else:
            print("❌ Appium server not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Appium server check failed: {e}")
        print("   Please start Appium server: appium")
        return False
    
    # Check QWEN API key
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        masked = (qwen_key[:4] + "..." + qwen_key[-4:]) if len(qwen_key) > 8 else "****"
        print(f"✅ QWEN_API_KEY found: {masked}")
    else:
        print("❌ QWEN_API_KEY not set in environment")
        return False
    
    return True


def run_single_crawl(run_number: int, max_steps: int = STEPS_PER_RUN) -> dict:
    """Run a single crawl session and return results."""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Crawl Run #{run_number}/{MAX_CRAWL_RUNS}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        crawler = AppCrawler(
            platform="android",
            app_package=PACKAGE_NAME,
            app_activity="",
            device_name=os.getenv("DEVICE_NAME", "emulator-5554"),
            appium_server=os.getenv("APPIUM_SERVER", "http://localhost:4723"),
            ai_provider="qwen",
            ai_api_key=os.getenv("QWEN_API_KEY"),
            db_path="crawler_paths.db",
            screenshot_dir="screenshots",
            app_wait_activity="org.wikipedia.onboarding.InitialOnboardingActivity",
            app_path=APK_PATH
        )

        print(f"🎯 Starting Enhanced BFS crawl (max {max_steps} steps)...")
        print("Strategy: Test every actionable element systematically")
        
        crawler.start_crawl(
            name=f"Enhanced BFS Wikipedia Crawl #{run_number}",
            description=f"Systematic element testing of Wikipedia app - Run {run_number} of {MAX_CRAWL_RUNS}",
            max_steps=max_steps
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Get final statistics
        from app_crawler.database import CrawlerDatabase
        db = CrawlerDatabase()
        paths = db.get_all_paths()
        total_steps = 0
        for path in paths:
            steps = db.get_path_steps(path['path_id'])
            total_steps += len(steps)
        
        result = {
            'run_number': run_number,
            'success': True,
            'duration_seconds': duration,
            'total_steps': total_steps,
            'error': None
        }
        
        print(f"✅ Crawl #{run_number} completed successfully")
        print(f"⏱️  Duration: {duration:.1f}s")
        print(f"📊 Total database steps: {total_steps}")
        
        return result
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Crawl #{run_number} interrupted by user")
        return {
            'run_number': run_number,
            'success': False,
            'duration_seconds': (datetime.now() - start_time).total_seconds(),
            'total_steps': 0,
            'error': 'User interrupt'
        }
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"❌ Crawl #{run_number} failed: {e}")
        return {
            'run_number': run_number,
            'success': False,
            'duration_seconds': duration,
            'total_steps': 0,
            'error': str(e)
        }


def print_final_report(results: list):
    """Print comprehensive final report."""
    print(f"\n{'='*80}")
    print(f"🎯 ENHANCED BFS CRAWLER - FINAL REPORT")
    print(f"{'='*80}")
    
    successful_runs = [r for r in results if r['success']]
    failed_runs = [r for r in results if not r['success']]
    
    print(f"📊 SUMMARY:")
    print(f"   Total runs attempted: {len(results)}")
    print(f"   Successful runs: {len(successful_runs)}")
    print(f"   Failed runs: {len(failed_runs)}")
    print(f"   Success rate: {len(successful_runs)/len(results)*100:.1f}%")
    
    if successful_runs:
        total_duration = sum(r['duration_seconds'] for r in successful_runs)
        avg_duration = total_duration / len(successful_runs)
        final_steps = max(r['total_steps'] for r in successful_runs)
        
        print(f"\n⏱️  TIMING:")
        print(f"   Total crawling time: {total_duration/60:.1f} minutes")
        print(f"   Average run duration: {avg_duration:.1f} seconds")
        
        print(f"\n📈 EXPLORATION:")
        print(f"   Final total steps in database: {final_steps}")
        print(f"   Average steps per run: {final_steps/len(results):.1f}")
    
    if failed_runs:
        print(f"\n❌ FAILURES:")
        for run in failed_runs:
            print(f"   Run #{run['run_number']}: {run['error']}")
    
    print(f"\n🌐 Web portal available at: http://localhost:5050")
    print(f"📱 Database file: crawler_paths.db")
    print(f"🖼️  Screenshots: screenshots/")
    print(f"📝 Logs: logs/")


def main():
    """Main function to run multiple BFS crawl sessions."""
    # Load environment variables
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    except Exception:
        try:
            load_dotenv()
        except Exception:
            pass

    print("🔥 ENHANCED BFS CRAWLER - 20x CRAWL SESSION")
    print(f"Target: {PACKAGE_NAME}")
    print(f"Strategy: Systematic Element Testing (Enhanced BFS)")
    print(f"Runs: {MAX_CRAWL_RUNS}")
    print(f"Steps per run: {STEPS_PER_RUN}")

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Exiting.")
        sys.exit(1)

    # Install APK
    print(f"\n📱 Installing APK...")
    installed = install_apk(APK_PATH)
    if not installed:
        print("Continuing without installing APK (device may already have app).")

    # Wait for user confirmation
    print(f"\n🚦 Ready to start {MAX_CRAWL_RUNS} BFS crawl runs.")
    input("Press Enter to start or Ctrl+C to cancel...")

    # Track results
    results = []
    start_time = datetime.now()
    
    try:
        # Run multiple crawl sessions
        for run_num in range(1, MAX_CRAWL_RUNS + 1):
            # Small delay between runs
            if run_num > 1:
                time.sleep(3)
            
            result = run_single_crawl(run_num, STEPS_PER_RUN)
            results.append(result)
            
            print(f"\n📋 Progress: {run_num}/{MAX_CRAWL_RUNS} completed")
            
            # Allow user to stop early
            if run_num < MAX_CRAWL_RUNS:
                print("Press Ctrl+C to stop or wait 5 seconds for next run...")
                try:
                    time.sleep(5)
                except KeyboardInterrupt:
                    print("\n🛑 Multi-crawl session stopped by user")
                    break
        
    except KeyboardInterrupt:
        print("\n🛑 Multi-crawl session interrupted")
    
    # Calculate total time
    total_time = datetime.now() - start_time
    
    # Print final report
    print_final_report(results)
    
    print(f"\n🏁 Multi-crawl session completed in {total_time.total_seconds()/60:.1f} minutes")
    print(f"🎯 Enhanced BFS strategy systematically tested every actionable element")
    
    return results


if __name__ == "__main__":
    results = main()