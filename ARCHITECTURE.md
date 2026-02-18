# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        App Crawler System                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   Mobile Device      │         │    Web Browser       │
│   (Android/iOS)      │         │   (User Interface)   │
│                      │         │                      │
│  ┌────────────────┐  │         │  ┌────────────────┐  │
│  │   Mobile App   │  │         │  │  Web Portal    │  │
│  │  Under Test    │  │         │  │  (Flask + JS)  │  │
│  └────────────────┘  │         │  └────────────────┘  │
└──────────┬───────────┘         └───────────┬──────────┘
           │                                 │
           │ Appium Protocol                 │ HTTP REST
           │                                 │
┌──────────▼─────────────────────────────────▼──────────┐
│                  App Crawler Core                      │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Crawler    │  │  AI Service  │  │   Database   │ │
│  │    Engine    │◄─┤   (GPT-4/    │  │   (SQLite)   │ │
│  │  (Appium)    │  │   Claude)    │  │              │ │
│  └──────┬───────┘  └──────────────┘  └──────────────┘ │
│         │                                              │
│         │ Screenshots, DOM, Actions                    │
│         ▼                                              │
│  ┌──────────────────────────────────────────────┐     │
│  │         Path Recording & Replay              │     │
│  └──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
           │
           │ Human Intervention
           ▼
    ┌──────────────┐
    │    Human     │
    │   Operator   │
    └──────────────┘
```

## Component Details

### 1. Crawler Engine (crawler.py)
- **Purpose**: Controls mobile app interaction via Appium
- **Responsibilities**:
  - Connect to mobile devices
  - Extract DOM trees
  - Execute actions (click, input, swipe)
  - Capture screenshots
  - Record paths
  - Replay recorded paths

### 2. AI Service (ai_service.py)
- **Purpose**: Provide intelligent decision-making
- **Responsibilities**:
  - Analyze DOM trees
  - Extract actionable elements
  - Suggest input values
  - Decide next actions
  - Request human help when stuck
- **Providers**: OpenAI (GPT-4) or Anthropic (Claude)

### 3. Database Layer (database.py)
- **Purpose**: Persistent storage for paths
- **Responsibilities**:
  - Store path metadata
  - Store path steps
  - Record human interventions
  - Provide CRUD operations
- **Technology**: SQLite

### 4. Web Portal (web_portal/)
- **Purpose**: User interface for path management
- **Components**:
  - Flask backend (app.py)
  - HTML templates (templates/)
  - CSS styling (static/css/)
  - JavaScript frontend (static/js/)
- **Features**:
  - View all paths
  - View path details and steps
  - Edit path metadata
  - Delete paths
  - View screenshots

### 5. CLI (cli.py)
- **Purpose**: Command-line interface
- **Commands**:
  - `crawl`: Start new crawl
  - `replay`: Replay path
  - `list`: List all paths
  - `info`: Show path details
  - `web`: Start web portal

## Data Flow

### Crawling Flow

```
1. User starts crawl
   ↓
2. Crawler connects to device via Appium
   ↓
3. Crawler extracts current DOM
   ↓
4. AI analyzes DOM and identifies elements
   ↓
5. AI decides next action
   ↓
6. [If AI is uncertain] → Request human help
   ↓
7. Crawler performs action
   ↓
8. Record step in database
   ↓
9. Capture screenshot
   ↓
10. Repeat from step 3 until max_steps or complete
```

### Replay Flow

```
1. User selects path to replay
   ↓
2. Load path steps from database
   ↓
3. Crawler connects to device
   ↓
4. For each step:
   - Wait for UI to load
   - Find element using selector
   - Perform recorded action
   - Wait for specified delay
   ↓
5. Complete replay
```

## Database Schema

```sql
paths
├── id (PRIMARY KEY)
├── path_id (UNIQUE)
├── name
├── platform (android/ios)
├── app_package
├── description
├── created_at
└── updated_at

path_steps
├── id (PRIMARY KEY)
├── path_id (FOREIGN KEY)
├── step_number
├── action_type (click/input/swipe/back)
├── element_selector
├── element_attributes (JSON)
├── input_value
├── screenshot_path
├── dom_snapshot
├── ai_reasoning
└── created_at

human_interventions
├── id (PRIMARY KEY)
├── path_id (FOREIGN KEY)
├── step_number
├── intervention_type
├── ai_question
├── human_response
└── created_at
```

## API Endpoints

### REST API (Web Portal)

```
GET    /api/paths                 - List all paths
GET    /api/paths/<id>           - Get path details
PUT    /api/paths/<id>           - Update path
DELETE /api/paths/<id>           - Delete path
GET    /api/paths/<id>/steps     - Get path steps
GET    /screenshots/<path>       - Serve screenshots
```

## Key Technologies

- **Python 3.8+**: Core language
- **Appium**: Mobile automation framework
- **Selenium**: WebDriver for Appium
- **Flask**: Web framework
- **SQLite**: Database
- **OpenAI API**: GPT-4 for AI decisions
- **Anthropic API**: Claude for AI decisions (alternative)

## Security Considerations

1. **API Keys**: Stored in environment variables, never in code
2. **Database**: Local SQLite, no external exposure by default
3. **Web Portal**: CORS enabled for flexibility
4. **Screenshots**: Stored locally, served through web portal

## Scalability Considerations

### Current MVP
- Single-threaded crawler
- Local SQLite database
- Single device at a time

### Future Enhancements
- Parallel crawling on multiple devices
- Distributed database (PostgreSQL, MongoDB)
- Cloud storage for screenshots
- Kubernetes deployment
- CI/CD integration
- Advanced analytics

## Extension Points

The system is designed to be extensible:

1. **Custom AI Providers**: Add new AI services by extending `AIService`
2. **Custom Actions**: Add new action types in `AppCrawler.perform_action()`
3. **Custom Analysis**: Add post-crawl analysis scripts using database API
4. **Custom UI**: Build alternative UIs using the REST API
5. **Plugins**: Create plugins for specific app types or workflows

## Deployment Options

### Local Development
```bash
python cli.py crawl ...
python cli.py web
```

### Docker
```bash
docker-compose up
```

### Production
- Deploy web portal to cloud (AWS, GCP, Azure)
- Use managed database
- Use cloud storage for screenshots
- Implement authentication and authorization
- Add monitoring and logging

---

For implementation details, see the code in the respective modules.
