"""Main crawler implementation using Appium."""
import os
import time
import uuid
import base64
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .database import CrawlerDatabase
from .ai_service import AIService


class AppCrawler:
    """Mobile app crawler supporting Android and iOS via Appium."""
    
    def __init__(self, 
                 platform: str,
                 app_package: str,
                 app_activity: Optional[str] = None,  # Android only
                 bundle_id: Optional[str] = None,  # iOS only
                 device_name: str = "emulator",
                 appium_server: str = "http://localhost:4723",
                 ai_provider: str = "openai",
                 ai_api_key: Optional[str] = None,
                 db_path: str = "crawler_paths.db",
                 screenshot_dir: str = "screenshots"):
        """Initialize the crawler.
        
        Args:
            platform: 'android' or 'ios'
            app_package: Package name (Android) or bundle ID (iOS)
            app_activity: Main activity for Android
            bundle_id: Bundle ID for iOS
            device_name: Device name for Appium
            appium_server: Appium server URL
            ai_provider: 'openai' or 'anthropic'
            ai_api_key: API key for AI service
            db_path: Path to SQLite database
            screenshot_dir: Directory for screenshots
        """
        self.platform = platform.lower()
        self.app_package = app_package
        self.app_activity = app_activity
        self.bundle_id = bundle_id or app_package
        self.device_name = device_name
        self.appium_server = appium_server
        self.screenshot_dir = screenshot_dir
        
        # Create screenshot directory
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Initialize services
        self.db = CrawlerDatabase(db_path)
        self.ai = AIService(provider=ai_provider, api_key=ai_api_key)
        
        # Appium driver
        self.driver: Optional[webdriver.Remote] = None
        
        # Crawler state
        self.current_path_id: Optional[str] = None
        self.step_count = 0
        self.explored_states = set()
        self.human_callback: Optional[Callable] = None
    
    def connect(self):
        """Connect to Appium server and start app."""
        if self.platform == "android":
            desired_caps = {
                "platformName": "Android",
                "platformVersion": "11",
                "deviceName": self.device_name,
                "appPackage": self.app_package,
                "appActivity": self.app_activity,
                "automationName": "UiAutomator2",
                "noReset": True
            }
        elif self.platform == "ios":
            desired_caps = {
                "platformName": "iOS",
                "platformVersion": "15.0",
                "deviceName": self.device_name,
                "bundleId": self.bundle_id,
                "automationName": "XCUITest",
                "noReset": True
            }
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
        
        self.driver = webdriver.Remote(self.appium_server, desired_caps)
        print(f"Connected to {self.platform} app: {self.app_package}")
    
    def disconnect(self):
        """Disconnect from Appium."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_page_source(self) -> str:
        """Get current page source (DOM tree)."""
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        return self.driver.page_source
    
    def take_screenshot(self, step_number: int) -> str:
        """Take screenshot and save to file.
        
        Args:
            step_number: Current step number
            
        Returns:
            Path to screenshot file
        """
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"step_{step_number:04d}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, self.current_path_id, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.driver.save_screenshot(filepath)
        
        return filepath
    
    def get_current_activity(self) -> str:
        """Get current activity/screen identifier."""
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        
        if self.platform == "android":
            return self.driver.current_activity
        else:
            # For iOS, use the source as identifier
            return "iOS Screen"
    
    def extract_elements(self) -> List[Dict[str, Any]]:
        """Extract UI elements from current page source.
        
        Returns:
            List of element dictionaries
        """
        page_source = self.get_page_source()
        
        # Use AI to analyze DOM and extract actionable elements
        elements = self.ai.extract_actionable_elements(
            dom_tree=page_source,
            context=f"Crawling {self.app_package}"
        )
        
        return elements
    
    def perform_action(self, action: str, element_selector: str,
                      input_value: Optional[str] = None) -> bool:
        """Perform an action on an element.
        
        Args:
            action: Action type (click, input, swipe, back)
            element_selector: Element selector (xpath, id, etc.)
            input_value: Value for input actions
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        
        try:
            if action == "click":
                element = self.driver.find_element(AppiumBy.XPATH, element_selector)
                element.click()
                return True
                
            elif action == "input":
                element = self.driver.find_element(AppiumBy.XPATH, element_selector)
                element.clear()
                if input_value:
                    element.send_keys(input_value)
                return True
                
            elif action == "back":
                self.driver.back()
                return True
                
            elif action == "swipe":
                # Simple swipe up
                size = self.driver.get_window_size()
                self.driver.swipe(
                    size['width'] // 2, size['height'] * 3 // 4,
                    size['width'] // 2, size['height'] // 4,
                    duration=500
                )
                return True
                
            else:
                print(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"Error performing action {action}: {e}")
            return False
    
    def start_crawl(self, name: str, description: str = "",
                   max_steps: int = 50,
                   human_callback: Optional[Callable] = None):
        """Start a new crawl session.
        
        Args:
            name: Name for this crawl path
            description: Description of crawl goal
            max_steps: Maximum number of steps
            human_callback: Callback function for human intervention
        """
        # Generate path ID
        self.current_path_id = f"path_{uuid.uuid4().hex[:8]}"
        self.step_count = 0
        self.human_callback = human_callback
        
        # Create path in database
        self.db.create_path(
            path_id=self.current_path_id,
            name=name,
            platform=self.platform,
            app_package=self.app_package,
            description=description
        )
        
        print(f"Started crawl: {self.current_path_id}")
        
        # Connect to app
        self.connect()
        
        # Crawl loop
        while self.step_count < max_steps:
            self.step_count += 1
            print(f"\n--- Step {self.step_count} ---")
            
            # Wait for page to load
            time.sleep(2)
            
            # Get current state
            page_source = self.get_page_source()
            activity = self.get_current_activity()
            screenshot_path = self.take_screenshot(self.step_count)
            
            # Extract elements using AI
            elements = self.extract_elements()
            
            if not elements:
                print("No actionable elements found")
                break
            
            # Get current state signature
            state_sig = f"{activity}_{len(elements)}"
            
            # Prepare state for AI decision
            current_state = {
                "activity": activity,
                "elements": elements[:10]  # Send top 10 elements to AI
            }
            
            # AI decides next action
            decision = self.ai.decide_next_action(
                current_state=current_state,
                explored_paths=list(self.explored_states),
                goal=description
            )
            
            print(f"AI Decision: {decision.get('action')}")
            print(f"Reasoning: {decision.get('reasoning')}")
            
            # Check if human help is needed
            if decision.get("needs_human_help"):
                if self.human_callback:
                    question = decision.get("question_for_human", "What should I do next?")
                    response = self.human_callback(question, current_state)
                    
                    # Record intervention
                    self.db.add_human_intervention(
                        path_id=self.current_path_id,
                        step_number=self.step_count,
                        intervention_type="decision",
                        ai_question=question,
                        human_response=response
                    )
                    
                    # Parse human response (simplified - should be more robust)
                    if "stop" in response.lower():
                        break
                    # Otherwise continue with AI's decision
                else:
                    print("Human help needed but no callback provided. Stopping.")
                    break
            
            # Stop if AI says so
            if decision.get("action") == "stop":
                break
            
            # Perform the action
            action = decision.get("action", "click")
            element_selector = decision.get("element_selector", "")
            input_value = decision.get("input_value")
            
            if element_selector:
                success = self.perform_action(action, element_selector, input_value)
                
                if success:
                    # Record step in database
                    selected_element = next(
                        (e for e in elements if element_selector in str(e.get("selector", ""))),
                        {}
                    )
                    
                    self.db.add_path_step(
                        path_id=self.current_path_id,
                        step_number=self.step_count,
                        action_type=action,
                        element_selector=element_selector,
                        element_attributes=selected_element,
                        input_value=input_value,
                        screenshot_path=screenshot_path,
                        dom_snapshot=page_source[:5000],  # Truncate for storage
                        ai_reasoning=decision.get("reasoning", "")
                    )
                    
                    # Mark state as explored
                    self.explored_states.add(state_sig)
                else:
                    print("Action failed, continuing...")
            
            # Safety delay
            time.sleep(1)
        
        print(f"\nCrawl completed: {self.step_count} steps")
        self.disconnect()
    
    def replay_path(self, path_id: str, delay: float = 2.0):
        """Replay a saved crawler path.
        
        Args:
            path_id: Path identifier to replay
            delay: Delay between steps in seconds
        """
        # Get path and steps from database
        path = self.db.get_path_by_id(path_id)
        if not path:
            raise ValueError(f"Path not found: {path_id}")
        
        steps = self.db.get_path_steps(path_id)
        if not steps:
            print("No steps to replay")
            return
        
        print(f"Replaying path: {path['name']} ({len(steps)} steps)")
        
        # Connect to app
        self.connect()
        
        # Replay each step
        for step in steps:
            print(f"\nReplaying step {step['step_number']}: {step['action_type']}")
            
            time.sleep(delay)
            
            success = self.perform_action(
                action=step['action_type'],
                element_selector=step['element_selector'],
                input_value=step['input_value']
            )
            
            if not success:
                print(f"Failed to replay step {step['step_number']}")
                # Continue anyway for now
        
        print("\nReplay completed")
        self.disconnect()
