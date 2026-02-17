# Quick Start Guide - App Crawler

This guide will help you get started with the App Crawler in under 10 minutes.

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.8+** installed
2. **Appium Server** installed (`npm install -g appium`)
3. **Android SDK** or **Xcode** (depending on your target platform)
4. **OpenAI or Anthropic API key**

## Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/codekaa1ciu1/app-crawler.git
cd app-crawler

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your preferred editor
```

Add your API key:
```
OPENAI_API_KEY=sk-your-api-key-here
```

## Step 3: Start Appium Server

In a new terminal:
```bash
appium
```

Leave this running in the background.

## Step 4: Start Your Android Emulator or iOS Simulator

### For Android:
```bash
# List available emulators
emulator -list-avds

# Start an emulator
emulator -avd Pixel_5_API_30
```

### For iOS:
```bash
# Start iOS simulator
open -a Simulator
```

## Step 5: Run Your First Crawl

Create a simple script `my_first_crawl.py`:

```python
from app_crawler import AppCrawler
import os

# For Android
crawler = AppCrawler(
    platform="android",
    app_package="com.android.settings",  # Built-in Settings app
    app_activity=".Settings",
    ai_provider="openai"
)

# Simple human intervention handler
def human_help(question, state):
    print(f"\nAI Question: {question}")
    return input("Your response (or 'stop'): ")

# Start crawling
crawler.start_crawl(
    name="Settings App Exploration",
    description="Exploring Android Settings",
    max_steps=20,
    human_callback=human_help
)

print(f"Crawl complete! Path ID: {crawler.current_path_id}")
```

Run it:
```bash
python my_first_crawl.py
```

## Step 6: View Results in Web Portal

Start the web portal:
```bash
cd web_portal
python app.py
```

Open your browser to: http://localhost:5000

You'll see:
- All your crawler paths
- Screenshots from each step
- AI reasoning for each action
- Human interventions (if any)

## Step 7: Replay a Path

```python
from app_crawler import AppCrawler

crawler = AppCrawler(
    platform="android",
    app_package="com.android.settings",
    app_activity=".Settings"
)

# Replay the path you just created
crawler.replay_path("path_abc123", delay=2.0)
```

## Common Issues

### Appium Connection Error
- Make sure Appium is running on `http://localhost:4723`
- Check that your device/emulator is connected: `adb devices`

### AI API Error
- Verify your API key is correct in `.env`
- Check you have credits/quota available

### App Not Starting
- For Android, verify package and activity names: `adb shell dumpsys window | grep -E 'mCurrentFocus'`
- For iOS, verify bundle ID

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Check out more examples in `example_crawl.py`
- Customize the AI prompts in `app_crawler/ai_service.py`
- Build custom analysis tools using the database API

## Getting Help

- Check the [README](README.md) for detailed documentation
- Open an issue on GitHub if you encounter problems
- Review the example scripts for usage patterns

Happy crawling! 🤖📱
