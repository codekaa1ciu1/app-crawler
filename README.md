# 🤖 App Crawler - AI-Powered Mobile Application Crawler

An intelligent mobile application crawler that uses AI to automatically explore and test Android and iOS apps through Appium. The crawler can record interaction paths, replay them, and provides a web portal for path management.

## ✨ Features

### Core Capabilities
- 🤖 **AI-Powered Exploration**: Uses OpenAI or Anthropic AI to intelligently navigate mobile apps
- 📱 **Cross-Platform**: Supports both Android and iOS via Appium
- 💾 **Path Recording**: Saves all interaction paths to SQLite database
- 🔄 **Replay Functionality**: Replay any saved path to reproduce user flows
- 🌐 **Web Portal**: View and manage all crawler paths through a beautiful web interface
- 👤 **Human-in-the-Loop**: AI can request human help when it gets stuck
- 📸 **Screenshot Capture**: Automatically captures screenshots at each step
- 🎯 **Smart Element Detection**: AI extracts actionable elements from DOM tree
- 💬 **Input Suggestions**: AI suggests appropriate inputs for text fields

### MVP Features (All Implemented)
1. ✅ Save paths to local SQLite database
2. ✅ Replay saved paths
3. ✅ AI-powered crawling with DOM analysis
4. ✅ Extract actionable WebElements using AI
5. ✅ AI-assisted input handling
6. ✅ Web portal to view all paths
7. ✅ Web portal to manage paths (edit name, description, delete)
8. ✅ Human intervention when AI needs help

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Appium Server
- Android SDK (for Android) or Xcode (for iOS)
- OpenAI or Anthropic API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/codekaa1ciu1/app-crawler.git
cd app-crawler
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Start Appium Server**
```bash
appium
```

### Basic Usage

#### 1. Start a Crawl

```python
from app_crawler import AppCrawler

# Create crawler instance
crawler = AppCrawler(
    platform="android",
    app_package="com.example.app",
    app_activity=".MainActivity",
    ai_provider="openai"  # or "anthropic"
)

# Define human intervention callback
def handle_human_help(question, state):
    print(f"AI asks: {question}")
    return input("Your response: ")

# Start crawling
crawler.start_crawl(
    name="My First Crawl",
    description="Exploring the app",
    max_steps=50,
    human_callback=handle_human_help
)
```

#### 2. Replay a Path

```python
from app_crawler import AppCrawler

crawler = AppCrawler(
    platform="android",
    app_package="com.example.app",
    app_activity=".MainActivity"
)

# Replay saved path
crawler.replay_path("path_abc123", delay=2.0)
```

#### 3. Launch Web Portal

```bash
cd web_portal
python app.py
```

Then open http://localhost:5000 in your browser to view and manage paths.

## 📖 Detailed Documentation

### Project Structure

```
app-crawler/
├── app_crawler/
│   ├── __init__.py          # Package initialization
│   ├── crawler.py           # Main crawler implementation
│   ├── database.py          # SQLite database layer
│   └── ai_service.py        # AI integration (OpenAI/Anthropic)
├── web_portal/
│   ├── app.py              # Flask web application
│   ├── templates/
│   │   └── index.html      # Web interface
│   └── static/
│       ├── css/style.css   # Styling
│       └── js/main.js      # Frontend JavaScript
├── screenshots/             # Captured screenshots (auto-created)
├── example_crawl.py        # Example usage script
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

### Configuration

The crawler can be configured using the following parameters:

#### AppCrawler Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `platform` | str | Platform ('android' or 'ios') | Required |
| `app_package` | str | Package name or bundle ID | Required |
| `app_activity` | str | Main activity (Android only) | None |
| `bundle_id` | str | Bundle ID (iOS only) | None |
| `device_name` | str | Device identifier | "emulator" |
| `appium_server` | str | Appium server URL | "http://localhost:4723" |
| `ai_provider` | str | AI provider ('openai' or 'anthropic') | "openai" |
| `ai_api_key` | str | API key for AI service | From env |
| `db_path` | str | SQLite database path | "crawler_paths.db" |
| `screenshot_dir` | str | Screenshot directory | "screenshots" |

### Database Schema

The crawler uses SQLite with the following tables:

#### `paths` Table
Stores metadata about crawler paths.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| path_id | TEXT | Unique path identifier |
| name | TEXT | Human-readable name |
| platform | TEXT | 'android' or 'ios' |
| app_package | TEXT | Package/bundle ID |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| description | TEXT | Optional description |

#### `path_steps` Table
Stores individual steps in each path.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| path_id | TEXT | Foreign key to paths |
| step_number | INTEGER | Sequential step number |
| action_type | TEXT | Action type (click, input, etc.) |
| element_selector | TEXT | Element selector (XPath, etc.) |
| element_attributes | TEXT | JSON of element properties |
| input_value | TEXT | Input value (if applicable) |
| screenshot_path | TEXT | Path to screenshot |
| dom_snapshot | TEXT | DOM tree snapshot |
| ai_reasoning | TEXT | AI's reasoning for action |
| created_at | TIMESTAMP | Creation time |

#### `human_interventions` Table
Records when humans helped the AI.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| path_id | TEXT | Foreign key to paths |
| step_number | INTEGER | Step where help was needed |
| intervention_type | TEXT | Type of intervention |
| ai_question | TEXT | Question from AI |
| human_response | TEXT | Human's response |
| created_at | TIMESTAMP | Creation time |

### AI Service

The AI service analyzes the app's DOM tree and makes intelligent decisions about:

1. **Element Extraction**: Identifies clickable buttons, input fields, and other interactive elements
2. **Input Suggestions**: Proposes appropriate values for text fields (emails, passwords, etc.)
3. **Next Action Decision**: Chooses the best next step based on exploration goals
4. **Human Help Requests**: Asks for human guidance when uncertain

#### Supported AI Providers

- **OpenAI**: Uses GPT-4 Turbo for analysis
- **Anthropic**: Uses Claude 3 Opus for analysis

### Web Portal API

The web portal provides a REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/paths` | GET | List all paths |
| `/api/paths/<id>` | GET | Get path details |
| `/api/paths/<id>` | PUT | Update path metadata |
| `/api/paths/<id>` | DELETE | Delete path |
| `/api/paths/<id>/steps` | GET | Get path steps |
| `/screenshots/<path>` | GET | Serve screenshots |

## 🔧 Advanced Usage

### Custom Human Intervention Handler

```python
def advanced_human_callback(question, state):
    """Custom handler with rich context."""
    print(f"\n{'='*60}")
    print(f"AI Question: {question}")
    print(f"Current Activity: {state.get('activity')}")
    print(f"Elements Found: {len(state.get('elements', []))}")
    
    # Show available elements
    for i, elem in enumerate(state.get('elements', [])[:5]):
        print(f"  {i+1}. {elem.get('type')}: {elem.get('text')}")
    
    response = input("\nYour response: ")
    return response
```

### Using Different AI Providers

```python
# Using OpenAI
crawler_openai = AppCrawler(
    platform="android",
    app_package="com.example.app",
    ai_provider="openai",
    ai_api_key="sk-..."
)

# Using Anthropic
crawler_anthropic = AppCrawler(
    platform="android",
    app_package="com.example.app",
    ai_provider="anthropic",
    ai_api_key="sk-ant-..."
)
```

### iOS Configuration

```python
# iOS crawler setup
crawler_ios = AppCrawler(
    platform="ios",
    app_package="com.example.MyApp",
    bundle_id="com.example.MyApp",
    device_name="iPhone 14",
    ai_provider="openai"
)
```

## 🛠️ Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/
```

### Starting the Web Portal in Development

```bash
cd web_portal
python app.py
```

The portal will be available at http://localhost:5000

### Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
APPIUM_SERVER=http://localhost:4723
DATABASE_PATH=crawler_paths.db
SCREENSHOT_DIR=screenshots
```

## 📝 Examples

See `example_crawl.py` for complete examples:

```bash
# Run a new crawl
python example_crawl.py

# Replay an existing path
python example_crawl.py replay
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the terms in the LICENSE file.

## 🙏 Acknowledgments

- Built with [Appium](http://appium.io/) for mobile automation
- Powered by [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/) AI
- Web interface built with [Flask](https://flask.palletsprojects.com/)

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

Made with ❤️ for automated mobile testing