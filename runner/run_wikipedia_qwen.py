"""Run crawler against the bundled Wikipedia APK using Qwen as AI provider.

This script will attempt to install the APK on a connected device/emulator
using `adb install -r` and then start a short crawl.

Requirements:
- Ensure `adb` is available on PATH and a device/emulator is connected.
- Set `QWEN_API_KEY` and `QWEN_API_URL` in environment if using a remote Qwen endpoint.
"""
import os
import subprocess
import sys
from dotenv import load_dotenv
from app_crawler import AppCrawler


APK_PATH = os.path.join("app_for_testing", "Android", "wikipedia.apk")
PACKAGE_NAME = "org.wikipedia"


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


def main():
    # Load environment variables from ./.env if present
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    except Exception:
        # Fallback to default load (cwd .env)
        try:
            load_dotenv()
        except Exception:
            pass

    # Debug: show whether QWEN_API_KEY is available (masked)
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        masked = (qwen_key[:4] + "..." + qwen_key[-4:]) if len(qwen_key) > 8 else "****"
        print(f"Using QWEN_API_KEY from env: {masked}")
    else:
        print("Warning: QWEN_API_KEY not set in environment")

    # Try to install APK first (best-effort)
    installed = install_apk(APK_PATH)
    if not installed:
        print("Continuing without installing APK (device may already have app).")

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

    # Fail-fast option: if set, detect invalid/unauthorized API keys and exit
    # immediately instead of continuing the crawl.
    fail_fast = os.getenv("FAIL_FAST_ON_INVALID_AI", "false").lower() in ("1", "true", "yes")
    if fail_fast:
        try:
            # Do a very small health-check call and detect auth-related errors.
            try:
                crawler.ai._send_chat([{"role": "user", "content": "health_check"}], temperature=0.0, max_tokens=5)
            except Exception as e:
                msg = str(e).lower()
                if "invalid_api_key" in msg or "incorrect api key" in msg or "401" in msg or "unauthorized" in msg:
                    print("AI provider authentication failed and FAIL_FAST_ON_INVALID_AI is set. Exiting.")
                    sys.exit(2)
                else:
                    print("AI provider health check failed (non-auth):", e)
        except Exception:
            # If the health check itself fails unexpectedly, do not prevent normal
            # execution unless we matched an auth error above.
            pass

    try:
        print("Starting crawler (Qwen provider)...")
        crawler.start_crawl(
            name="Wikipedia Qwen Crawl",
            description="Crawl Wikipedia test app with Qwen",
            max_steps=20,  # Increase to see more ID extractions
            human_callback=None,
        )

        print(f"Crawl completed. Path ID: {crawler.current_path_id}")
        print("SUCCESS: Script completed without errors!")

    except KeyboardInterrupt:
        print("Crawl interrupted by user")
        crawler.disconnect()
    except Exception as e:
        print("Error during crawl:")
        import traceback
        traceback.print_exc()
        crawler.disconnect()


if __name__ == "__main__":
    main()
