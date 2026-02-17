# API Documentation

This document provides detailed API documentation for the App Crawler.

## Table of Contents

1. [AppCrawler Class](#appcrawler-class)
2. [CrawlerDatabase Class](#crawlerdatabase-class)
3. [AIService Class](#aiservice-class)
4. [Web Portal API](#web-portal-api)

---

## AppCrawler Class

The main crawler class for mobile application automation.

### Constructor

```python
AppCrawler(
    platform: str,
    app_package: str,
    app_activity: Optional[str] = None,
    bundle_id: Optional[str] = None,
    device_name: str = "emulator",
    appium_server: str = "http://localhost:4723",
    ai_provider: str = "openai",
    ai_api_key: Optional[str] = None,
    db_path: str = "crawler_paths.db",
    screenshot_dir: str = "screenshots"
)
```

**Parameters:**
- `platform`: Platform type ("android" or "ios")
- `app_package`: Package name (Android) or bundle ID (iOS)
- `app_activity`: Main activity for Android (e.g., ".MainActivity")
- `bundle_id`: Bundle ID for iOS apps
- `device_name`: Device identifier or name
- `appium_server`: Appium server URL
- `ai_provider`: AI provider ("openai" or "anthropic")
- `ai_api_key`: API key for AI service (or use environment variable)
- `db_path`: Path to SQLite database file
- `screenshot_dir`: Directory for storing screenshots

### Methods

#### `connect()`
Connect to Appium server and start the application.

```python
crawler.connect()
```

**Returns:** None

**Raises:** 
- `RuntimeError`: If connection fails
- `ValueError`: If platform is not supported

---

#### `disconnect()`
Disconnect from Appium and close the application.

```python
crawler.disconnect()
```

---

#### `start_crawl(name, description="", max_steps=50, human_callback=None)`
Start a new crawl session with AI-guided exploration.

```python
crawler.start_crawl(
    name="My Crawl",
    description="Testing login flow",
    max_steps=30,
    human_callback=my_callback_function
)
```

**Parameters:**
- `name`: Human-readable name for the crawl
- `description`: Optional description of crawl objectives
- `max_steps`: Maximum number of steps before stopping
- `human_callback`: Function to call when AI needs help
  - Signature: `callback(question: str, state: dict) -> str`

**Returns:** None (stores path_id in `crawler.current_path_id`)

---

#### `replay_path(path_id, delay=2.0)`
Replay a previously recorded path.

```python
crawler.replay_path("path_abc123", delay=2.0)
```

**Parameters:**
- `path_id`: Identifier of the path to replay
- `delay`: Delay in seconds between steps

**Raises:**
- `ValueError`: If path doesn't exist

---

#### `get_page_source()`
Get the current page source (DOM tree).

```python
source = crawler.get_page_source()
```

**Returns:** String containing XML representation of the page

---

#### `take_screenshot(step_number)`
Capture a screenshot of the current screen.

```python
path = crawler.take_screenshot(1)
```

**Parameters:**
- `step_number`: Current step number

**Returns:** String path to saved screenshot file

---

#### `extract_elements()`
Extract actionable UI elements using AI.

```python
elements = crawler.extract_elements()
```

**Returns:** List of dictionaries containing element information

**Example return value:**
```python
[
    {
        "type": "button",
        "selector": "//android.widget.Button[@text='Login']",
        "text": "Login",
        "action": "click",
        "priority": "high",
        "reasoning": "Main login button"
    },
    ...
]
```

---

#### `perform_action(action, element_selector, input_value=None)`
Perform an action on a UI element.

```python
success = crawler.perform_action(
    action="click",
    element_selector="//button[@text='Submit']"
)
```

**Parameters:**
- `action`: Action type ("click", "input", "swipe", "back")
- `element_selector`: XPath or selector for the element
- `input_value`: Value to input (for "input" actions)

**Returns:** Boolean indicating success

---

## CrawlerDatabase Class

SQLite database manager for storing crawler paths.

### Constructor

```python
CrawlerDatabase(db_path: str = "crawler_paths.db")
```

### Methods

#### `create_path(path_id, name, platform, app_package, description="")`
Create a new crawler path record.

```python
db_id = db.create_path(
    path_id="path_123",
    name="Login Test",
    platform="android",
    app_package="com.example.app",
    description="Testing login functionality"
)
```

**Returns:** Database ID (integer) of created path

---

#### `add_path_step(...)`
Add a step to an existing path.

```python
step_id = db.add_path_step(
    path_id="path_123",
    step_number=1,
    action_type="click",
    element_selector="//button[@text='Login']",
    element_attributes={"text": "Login", "type": "button"},
    input_value=None,
    screenshot_path="/path/to/screenshot.png",
    dom_snapshot="<xml>...</xml>",
    ai_reasoning="Clicking login button to proceed"
)
```

**Returns:** Database ID of created step

---

#### `get_all_paths()`
Retrieve all crawler paths.

```python
paths = db.get_all_paths()
```

**Returns:** List of dictionaries with path information

---

#### `get_path_by_id(path_id)`
Get specific path details.

```python
path = db.get_path_by_id("path_123")
```

**Returns:** Dictionary with path info, or None if not found

---

#### `get_path_steps(path_id)`
Get all steps for a path.

```python
steps = db.get_path_steps("path_123")
```

**Returns:** List of step dictionaries ordered by step_number

---

#### `update_path(path_id, name=None, description=None)`
Update path metadata.

```python
success = db.update_path(
    path_id="path_123",
    name="Updated Name",
    description="New description"
)
```

**Returns:** Boolean indicating success

---

#### `delete_path(path_id)`
Delete a path and all its steps.

```python
success = db.delete_path("path_123")
```

**Returns:** Boolean indicating success

---

#### `add_human_intervention(...)`
Record a human intervention.

```python
intervention_id = db.add_human_intervention(
    path_id="path_123",
    step_number=5,
    intervention_type="decision",
    ai_question="What should I do next?",
    human_response="Click the submit button"
)
```

**Returns:** Database ID of intervention record

---

## AIService Class

AI service for intelligent crawling decisions.

### Constructor

```python
AIService(provider: str = "openai", api_key: Optional[str] = None)
```

**Parameters:**
- `provider`: "openai" or "anthropic"
- `api_key`: API key (or use environment variable)

### Methods

#### `extract_actionable_elements(dom_tree, context="")`
Extract actionable elements from DOM using AI.

```python
elements = ai.extract_actionable_elements(
    dom_tree="<xml>...</xml>",
    context="Looking for login elements"
)
```

**Returns:** List of element dictionaries

---

#### `suggest_input_value(element, context="")`
Suggest appropriate input for a text field.

```python
value, reasoning = ai.suggest_input_value(
    element={
        "type": "text_field",
        "text": "Email",
        "hint": "Enter email"
    },
    context="Testing login"
)
```

**Returns:** Tuple of (suggested_value, reasoning)

---

#### `decide_next_action(current_state, explored_paths, goal="")`
Decide the next action to take.

```python
decision = ai.decide_next_action(
    current_state={
        "activity": "MainActivity",
        "elements": [...]
    },
    explored_paths=["state1", "state2"],
    goal="Complete login flow"
)
```

**Returns:** Dictionary with decision information

**Example return:**
```python
{
    "action": "click",
    "element_selector": "//button[@text='Login']",
    "input_value": None,
    "reasoning": "Clicking login to proceed",
    "needs_human_help": False,
    "question_for_human": None
}
```

---

## Web Portal API

REST API endpoints for the web portal.

### Base URL
`http://localhost:5000/api`

---

### GET `/api/paths`
List all crawler paths.

**Response:**
```json
[
    {
        "id": 1,
        "path_id": "path_abc123",
        "name": "Login Test",
        "platform": "android",
        "app_package": "com.example.app",
        "created_at": "2024-01-01 12:00:00",
        "updated_at": "2024-01-01 12:00:00",
        "description": "Testing login",
        "step_count": 15
    }
]
```

---

### GET `/api/paths/<path_id>`
Get specific path with steps and interventions.

**Response:**
```json
{
    "path": {
        "id": 1,
        "path_id": "path_abc123",
        "name": "Login Test",
        ...
    },
    "steps": [
        {
            "id": 1,
            "step_number": 1,
            "action_type": "click",
            "element_selector": "//button",
            ...
        }
    ],
    "interventions": [...]
}
```

---

### PUT `/api/paths/<path_id>`
Update path metadata.

**Request Body:**
```json
{
    "name": "Updated Name",
    "description": "New description"
}
```

**Response:**
```json
{
    "message": "Path updated successfully"
}
```

---

### DELETE `/api/paths/<path_id>`
Delete a path.

**Response:**
```json
{
    "message": "Path deleted successfully"
}
```

---

### GET `/api/paths/<path_id>/steps`
Get all steps for a path.

**Response:**
```json
[
    {
        "id": 1,
        "step_number": 1,
        "action_type": "click",
        ...
    }
]
```

---

## Human Intervention Callback

The callback function for human intervention has this signature:

```python
def my_callback(question: str, current_state: dict) -> str:
    """
    Handle AI request for human help.
    
    Args:
        question: Question from AI
        current_state: Dictionary with:
            - activity: Current screen/activity
            - elements: List of available elements
    
    Returns:
        String response from human
    """
    print(f"AI asks: {question}")
    # ... your logic ...
    return "continue"  # or "stop", or specific instructions
```

---

## Error Handling

All methods may raise:
- `RuntimeError`: For connection/state errors
- `ValueError`: For invalid parameters
- `Exception`: For AI service or database errors

Always wrap calls in try-except blocks for production use:

```python
try:
    crawler.start_crawl(...)
except Exception as e:
    print(f"Error: {e}")
    crawler.disconnect()
```

---

For more examples, see `example_crawl.py` and `cli.py`.
