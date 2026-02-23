"""Main crawler implementation using Appium with BFS strategy."""
import os
import time
import uuid
import base64
import logging
import traceback
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from collections import deque
import hashlib

from appium import webdriver
try:
    from appium.options.android import UiAutomator2Options
    from appium.options.ios import XCUITestOptions
except Exception:
    UiAutomator2Options = None
    XCUITestOptions = None
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
                 app_wait_activity: Optional[str] = None,  # Android only: appWaitActivity
                 bundle_id: Optional[str] = None,  # iOS only
                 device_name: str = "emulator",
                 appium_server: str = "http://localhost:4723",
                 ai_provider: str = "openai",
                 ai_api_key: Optional[str] = None,
                 db_path: str = "crawler_paths.db",
                 app_path: Optional[str] = None,
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
        self.app_wait_activity = app_wait_activity
        self.bundle_id = bundle_id or app_package
        self.device_name = device_name
        self.appium_server = appium_server
        self.screenshot_dir = screenshot_dir
        self.app = app_path  # Use app_package as fallback for app path if not provided
        # Create screenshot directory
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Initialize services
        self.db = CrawlerDatabase(db_path)
        self.ai = AIService(provider=ai_provider, api_key=ai_api_key)
        
        # Appium driver
        self.driver: Optional[webdriver.Remote] = None
        
        # Crawler state - enhanced for BFS
        self.current_path_id: Optional[str] = None
        self.step_count = 0
        self.explored_states = set()
        self.human_callback: Optional[Callable] = None
        
        # BFS-specific data structures - enhanced for directed graph
        self.action_queue = deque()  # Queue of actions to explore
        self.visited_states = set()  # Set of state hashes we've seen
        self.state_action_map = {}   # Maps state hash -> list of available actions
        
        # Directed Graph tracking
        self.current_node_id = None  # Current node in the graph
        self.previous_node_id = None  # Previous node for edge creation
        self.current_journey_path = []  # Current path of nodes for cycle detection
        self.current_edge_path = []   # Current path of edges for journey tracking
        # log all the prameters for debugging        
        print(f"Initialized AppCrawler with parameters:")
        print(f"  Platform: {self.platform}")
        print(f"  App Package: {self.app_package}")
        print(f"  App Activity: {self.app_activity}")
        print(f"  App Wait Activity: {self.app_wait_activity}")
        print(f"  Bundle ID: {self.bundle_id}")
        print(f"  Device Name: {self.device_name}")
        print(f"  Appium Server: {self.appium_server}")
        print(f"  AI Provider: {ai_provider}")
        print(f"  DB Path: {db_path}")
        print(f"  App Path: {app_path}")
        print(f"  Screenshot Directory: {screenshot_dir}")
        print(f"  AI API Key: {'set' if ai_api_key else 'not set'}")
    
    def connect(self):
        """Connect to Appium server and start app."""
        if self.platform == "android":
            # Use new Options API if available (Appium-Python-Client v5+)
            if UiAutomator2Options:
                opts = UiAutomator2Options()
                opts.platform_name = "Android"
                opts.platform_version = "14"
                opts.device_name = self.device_name
                # Set the app path or package name
                if self.app:
                    opts.app = os.path.abspath(self.app)
                else:
                    opts.app_package = self.app_package
                    if self.app_activity:
                        opts.app_activity = self.app_activity
                opts.auto_grant_permissions = True
                if self.app_wait_activity:
                    opts.app_wait_activity = self.app_wait_activity
                opts.automation_name = "UiAutomator2"
                opts.no_reset = False
                self.driver = webdriver.Remote(self.appium_server, options=opts)
                print(f"Connected to {self.platform} app: {self.app_package}")
                return
            else:
                desired_caps = {
                    "platformName": "Android",
                    "platformVersion": "14",
                    "deviceName": self.device_name,
                    "autoGrantPermissions": True,
                    "automationName": "UiAutomator2",
                    "noReset": False
                }
                # Set app path or package name
                if self.app:
                    desired_caps["app"] = os.path.abspath(self.app)
                else:
                    desired_caps["appPackage"] = self.app_package
                    if self.app_activity:
                        desired_caps["appActivity"] = self.app_activity
                if self.app_wait_activity:
                    desired_caps["appWaitActivity"] = self.app_wait_activity
                
                self.driver = webdriver.Remote(self.appium_server, desired_caps)
                print(f"Connected to {self.platform} app: {self.app_package}")
                return
        elif self.platform == "ios":
            if XCUITestOptions:
                opts = XCUITestOptions()
                opts.platformName = "iOS"
                opts.platformVersion = "15.0"
                opts.deviceName = self.device_name
                opts.bundleId = self.bundle_id
                opts.automationName = "XCUITest"
                opts.noReset = True
                self.driver = webdriver.Remote(self.appium_server, options=opts)
                print(f"Connected to {self.platform} app: {self.bundle_id}")
                return
            else:
                desired_caps = {
                    "platformName": "iOS",
                    "platformVersion": "15.0",
                    "deviceName": self.device_name,
                    "bundleId": self.bundle_id,
                    "automationName": "XCUITest",
                    "noReset": True,
                    "autoGrantPermissions": True
                }
                self.driver = webdriver.Remote(self.appium_server, desired_caps)
                print(f"Connected to {self.platform} app: {self.bundle_id}")
                return
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
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
            Relative path to screenshot file (for web portal serving)
        """
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"step_{step_number:04d}_{timestamp}.png"
        filepath = os.path.join(self.screenshot_dir, self.current_path_id, filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.driver.save_screenshot(filepath)
        
        # Return relative path for web portal serving
        relative_path = os.path.join(self.current_path_id, filename)
        return relative_path
    
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
        # Log the DOM tree being sent to AI
        try:
            self.logger.debug("Sending DOM tree to AI (length: %d chars)", len(page_source))
            # Also log the full DOM tree for debugging purposes
            self.logger.debug("DOM tree sent to AI:\n%s", page_source)
        except Exception:
            # Fallback to print if logger not configured
            try:
                print("Sending DOM tree to AI (length:", len(page_source), "chars)")
            except Exception:
                pass

        # Use AI to analyze DOM and extract actionable elements
        elements = self.ai.extract_actionable_elements(
            dom_tree=page_source,
            context=f"Crawling {self.app_package}"
        )
        
        return elements
    
    def _get_state_hash(self, page_source: str, activity: str) -> str:
        """Generate a hash for the current state to detect revisits."""
        # Create a normalized state representation
        state_content = f"{activity}_{len(page_source)}_{hash(page_source[:1000])}"
        return hashlib.md5(state_content.encode()).hexdigest()
    
    def _queue_actions_for_state(self, state_hash: str, elements: List[Dict[str, Any]], current_activity: str):
        """Queue all actionable elements from current state for immediate BFS exploration."""
        if not elements:
            return
        
        actionable_actions = []
        for element in elements:
            # Skip if element doesn't have a valid selector
            selector = element.get('selector', '').strip()
            if not selector:
                try:
                    self.logger.debug(f"⚠️  Skipping element with empty selector: {element.get('text', 'no text')}")
                except:
                    print(f"⚠️  Skipping element with empty selector: {element.get('text', 'no text')}")
                continue
                
            # Skip if element text is empty and selector is very short (likely invalid)
            element_text = element.get('text', '').strip()
            if not element_text and len(selector) < 5:
                try:
                    self.logger.debug(f"⚠️  Skipping element with short selector and no text: {selector}")
                except:
                    print(f"⚠️  Skipping element with short selector and no text: {selector}")
                continue
                
            # Create action entries for different interaction types
            action_entry = {
                'state_hash': state_hash,
                'activity': current_activity,
                'action_type': element.get('action_type', 'click'),
                'element_selector': selector,
                'selector_type': element.get('selector_type'),
                'element_text': element_text,
                'element_description': element.get('description', ''),
                'priority': element.get('priority', 5),  # Default priority
                'original_state': state_hash  # Track where this action originated
            }
            
            # Queue different types of interactions based on element type
            if element.get('element_type') == 'EditText':
                # For input fields, queue both click and input actions
                click_action = action_entry.copy()
                click_action['action_type'] = 'click'
                actionable_actions.append(click_action)
                
                input_action = action_entry.copy()
                input_action['action_type'] = 'input'
                input_action['input_value'] = f"test_input_{len(self.action_queue)}"
                actionable_actions.append(input_action)
            else:
                # For other elements, just queue click action
                actionable_actions.append(action_entry)
        
        # Sort actions by priority (lower number = higher priority)
        actionable_actions.sort(key=lambda x: x.get('priority', 5))
        
        # Store actions for immediate execution (element-by-element testing)
        self.state_action_map[state_hash] = actionable_actions
        
        try:
            self.logger.info(f"Prepared {len(actionable_actions)} actions for immediate testing on state {state_hash[:8]}...")
        except:
            print(f"Prepared {len(actionable_actions)} actions for immediate testing on state {state_hash[:8]}...")
        
        return actionable_actions
    
    def _create_or_get_graph_node(self, activity: str, page_source: str, screenshot_path: str) -> str:
        """Create or get existing graph node for current state.
        
        Args:
            activity: Current activity name
            page_source: Current page source/DOM
            screenshot_path: Path to screenshot
            
        Returns:
            Node ID
        """
        state_hash = self._get_state_hash(page_source, activity)
        element_count = page_source.count('<') if page_source else 0
        
        # Check if node already exists
        existing_node = self.db.get_node_by_hash(state_hash)
        if existing_node:
            return existing_node['node_id']
        
        # Create new node
        node_id = self.db.create_or_get_node(
            app_package=self.app_package,
            activity_name=activity,
            state_hash=state_hash,
            dom_snapshot=page_source,
            screenshot_path=screenshot_path,
            element_count=element_count,
            is_initial_state=(self.step_count == 0)
        )
        
        try:
            self.logger.info(f"📍 Created/found graph node: {node_id} (state: {state_hash[:8]}...)")
        except:
            print(f"📍 Created/found graph node: {node_id} (state: {state_hash[:8]}...)")
        
        return node_id
    
    def _create_graph_edge(self, from_node_id: str, to_node_id: Optional[str], 
                          action: Dict[str, Any], is_valid: bool) -> str:
        """Create graph edge representing action transition.
        
        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID (None if no state change)
            action: Action dictionary
            is_valid: Whether action caused valid state transition
            
        Returns:
            Edge ID
        """
        edge_id = self.db.create_edge(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            action_type=action.get('action_type', 'click'),
            element_selector=action.get('element_selector', ''),
            element_text=action.get('element_text', ''),
            element_attributes=action.get('element_attributes', {}),
            input_value=action.get('input_value', ''),
            is_valid=is_valid
        )
        
        try:
            validity = "✅ valid" if is_valid else "❌ invalid"
            self.logger.info(f"🔗 Created edge: {edge_id} ({validity} transition)")
        except:
            validity = "valid" if is_valid else "invalid"
            print(f"🔗 Created edge: {edge_id} ({validity} transition)")
        
        return edge_id
    
    def _detect_journey_cycle(self) -> Optional[str]:
        """Detect if current path forms a cycle and create journey record.
        
        Returns:
            Journey ID if cycle detected, None otherwise
        """
        if not self.current_journey_path or len(self.current_journey_path) < 2:
            return None
        
        current_node = self.current_node_id
        if current_node in self.current_journey_path:
            # Cycle detected!
            cycle_start_index = self.current_journey_path.index(current_node)
            cycle_nodes = self.current_journey_path[cycle_start_index:]
            cycle_edges = self.current_edge_path[cycle_start_index:]
            
            # Create journey record
            journey_id = self.db.create_journey(
                app_package=self.app_package,
                start_node_id=current_node,
                end_node_id=current_node,
                path_edges=cycle_edges,
                journey_type='cycle'
            )
            
            try:
                self.logger.info(f"🔄 CYCLE DETECTED! Journey: {journey_id} ({len(cycle_nodes)} nodes)")
            except:
                print(f"🔄 CYCLE DETECTED! Journey: {journey_id} ({len(cycle_nodes)} nodes)")
            
            return journey_id
        
        return None

    def _execute_all_actions_on_current_state(self, actions: List[Dict[str, Any]], starting_state_hash: str) -> List[Dict[str, Any]]:
        """Execute each actionable element on current screen and observe results.
        
        Args:
            actions: List of actions to execute on current state
            starting_state_hash: Hash of the starting state
        
        Returns:
            List of results for each action executed
        """
        results = []
        
        try:
            self.logger.info(f"🎯 Testing {len(actions)} elements on current screen systematically")
        except:
            print(f"🎯 Testing {len(actions)} elements on current screen systematically")
        
        for i, action in enumerate(actions):
            try:
                action_type = action.get('action_type', 'click')
                element_selector = action.get('element_selector', '').strip()
                element_text = action.get('element_text', '').strip()
                input_value = action.get('input_value')
                selector_type = action.get('selector_type')
                
                # Validate selector before proceeding
                if not element_selector and not element_text:
                    try:
                        self.logger.warning(f"❌ Skipping action {i+1}/{len(actions)}: No valid selector or text provided")
                    except:
                        print(f"❌ Skipping action {i+1}/{len(actions)}: No valid selector or text provided")
                    continue
                
                try:
                    self.logger.info(f"🔍 Action {i+1}/{len(actions)}: {action_type} on '{element_text or element_selector}'")
                except:
                    print(f"🔍 Action {i+1}/{len(actions)}: {action_type} on '{element_text or element_selector}'")
                
                # Capture state before action
                pre_action_source = self.get_page_source()
                pre_action_activity = self.get_current_activity()
                
                # Execute the action with enhanced text-based fallback
                try:
                    success = self.perform_action(
                        action=action_type,
                        element_selector=element_selector,
                        input_value=input_value,
                        selector_type=selector_type,
                        element_text=element_text  # Pass element text for fallback selection
                    )
                except Exception as action_error:
                    success = False
                    try:
                        self.logger.error(f"❌ Action execution error: {action_error}")
                    except:
                        print(f"❌ Action execution error: {action_error}")
                
                if not success:
                    try:
                        self.logger.warning(f"❌ Action failed: {action_type} on '{element_text}' ({element_selector})")
                    except:
                        print(f"❌ Action failed: {action_type} on '{element_text}' ({element_selector})")
                    
                    # Create invalid edge in graph (action doesn't work)
                    if hasattr(self, 'current_node_id') and self.current_node_id:
                        self._create_graph_edge(
                            from_node_id=self.current_node_id,
                            to_node_id=None,  # No state change
                            action=action,
                            is_valid=False
                        )
                    
                    results.append({
                        'action': action,
                        'success': False,
                        'error': 'Action execution failed',
                        'is_valid_path': False
                    })
                    continue
                
                # Wait for UI to settle
                time.sleep(2)
                
                # Capture state after action
                post_action_source = self.get_page_source()
                post_action_activity = self.get_current_activity()
                post_action_state_hash = self._get_state_hash(post_action_source, post_action_activity)
                
                # Analyze what happened and determine if path is valid
                state_changed = post_action_state_hash != starting_state_hash
                activity_changed = post_action_activity != pre_action_activity
                content_changed = len(post_action_source) != len(pre_action_source)
                
                # Determine if this is a valid path (causes UI change)
                is_valid_path = state_changed or activity_changed or content_changed
                
                # Create or get target node if state changed
                target_node_id = None
                if state_changed:
                    target_node_id = self._create_or_get_graph_node(
                        activity=post_action_activity,
                        page_source=post_action_source,
                        screenshot_path=self.take_screenshot(self.step_count + i + 1)
                    )
                
                # Create graph edge
                if hasattr(self, 'current_node_id') and self.current_node_id:
                    edge_id = self._create_graph_edge(
                        from_node_id=self.current_node_id,
                        to_node_id=target_node_id,  # None if no state change
                        action=action,
                        is_valid=is_valid_path
                    )
                    
                    # Track edge in current journey path
                    if is_valid_path and target_node_id:
                        self.current_edge_path.append(edge_id)
                        
                        # Check for cycle detection
                        cycle_journey = self._detect_journey_cycle()
                        if cycle_journey:
                            try:
                                self.logger.info(f"🎉 Completed journey cycle: {cycle_journey}")
                            except:
                                print(f"🎉 Completed journey cycle: {cycle_journey}")
                
                result = {
                    'action': action,
                    'success': True,
                    'state_changed': state_changed,
                    'activity_changed': activity_changed,
                    'content_changed': content_changed,
                    'is_valid_path': is_valid_path,
                    'new_state_hash': post_action_state_hash,
                    'new_activity': post_action_activity,
                    'target_node_id': target_node_id,
                    'observation': self._generate_action_observation(
                        action, state_changed, activity_changed, content_changed, is_valid_path
                    )
                }
                
                results.append(result)
                
                try:
                    self.logger.info(f"✅ Result: {result['observation']}")
                except:
                    print(f"✅ Result: {result['observation']}")
                
                # If we moved to a new state, mark it for future exploration
                if state_changed and post_action_state_hash not in self.visited_states:
                    try:
                        self.logger.info(f"🆕 Discovered new state: {post_action_activity} (hash: {post_action_state_hash[:8]}...)")
                    except:
                        print(f"🆕 Discovered new state: {post_action_activity} (hash: {post_action_state_hash[:8]}...)")
                    
                    # Add new states to queue for future exploration
                    self.action_queue.append({
                        'type': 'explore_new_state',
                        'state_hash': post_action_state_hash,
                        'activity': post_action_activity,
                        'discovered_from': starting_state_hash
                    })
                
                # Try to return to starting state if we moved away (for systematic testing)
                if state_changed and post_action_activity != pre_action_activity:
                    try:
                        # Attempt to go back
                        back_success = self.perform_action('back', '', None)
                        if back_success:
                            time.sleep(2)  # Wait for navigation
                            current_state_after_back = self._get_state_hash(
                                self.get_page_source(), self.get_current_activity()
                            )
                            if current_state_after_back == starting_state_hash:
                                try:
                                    self.logger.info("🔙 Successfully returned to starting state")
                                except:
                                    print("🔙 Successfully returned to starting state")
                            else:
                                try:
                                    self.logger.info("🔙 Back action performed, but in different state")
                                except:
                                    print("🔙 Back action performed, but in different state")
                        else:
                            try:
                                self.logger.info("🔙 Back action failed, staying in new state")
                            except:
                                print("🔙 Back action failed, staying in new state")
                    except Exception as e:
                        try:
                            self.logger.warning(f"🔙 Error attempting to return to starting state: {e}")
                        except:
                            print(f"🔙 Error attempting to return to starting state: {e}")
                
            except Exception as e:
                try:
                    self.logger.exception(f"❌ Exception testing element {i+1}: {e}")
                except:
                    print(f"❌ Exception testing element {i+1}: {e}")
                
                results.append({
                    'action': action,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def _generate_action_observation(self, action: Dict[str, Any], state_changed: bool, 
                                   activity_changed: bool, content_changed: bool, 
                                   is_valid_path: bool = True) -> str:
        """Generate human-readable observation of what happened after an action."""
        action_type = action.get('action_type', 'unknown')
        element_text = action.get('element_text', action.get('element_selector', 'unknown'))
        
        if not is_valid_path:
            return f"{action_type.title()} on '{element_text}' → ❌ invalid path (no change)"
        elif activity_changed:
            return f"{action_type.title()} on '{element_text}' → ✅ navigated to new screen"
        elif state_changed:
            return f"{action_type.title()} on '{element_text}' → ✅ UI state changed"
        elif content_changed:
            return f"{action_type.title()} on '{element_text}' → ✅ content updated" 
        else:
            return f"{action_type.title()} on '{element_text}' → ⚠️ no visible change"
    
    def _get_next_action_bfs(self) -> Optional[Dict[str, Any]]:
        """Get the next action to execute using BFS strategy (for backward compatibility).""" 
        if not self.action_queue:
            return None
            
        # Get the next action from the front of the queue (BFS order)
        return self.action_queue.popleft()
        
    def _should_explore_state(self, state_hash: str) -> bool:
        """Determine if we should explore this state based on enhanced BFS strategy."""
        # Don't explore states we've already fully explored
        if state_hash in self.visited_states:
            try:
                self.logger.debug(f"Skipping already visited state: {state_hash[:8]}")
            except:
                pass
            return False
        
        # Mark state as visited for systematic element testing
        self.visited_states.add(state_hash)
        return True
    
    def perform_action(self, action: str, element_selector: str,
                      input_value: Optional[str] = None,
                      selector_type: Optional[str] = None,
                      element_text: Optional[str] = None) -> bool:
        """Perform an action on an element with enhanced fallback selection.
        
        Args:
            action: Action type (click, input, swipe, back)
            element_selector: Element selector (xpath, id, etc.)
            input_value: Value for input actions
            selector_type: Type of selector provided
            element_text: Text content of element for fallback selection
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            raise RuntimeError("Not connected to Appium")
        
        # Validate selectors - prevent empty/invalid selector issues
        element_selector = (element_selector or '').strip()
        element_text = (element_text or '').strip()
        
        # Some actions don't require selectors (back, swipe)
        if action in ['back', 'swipe']:
            # These actions work without element selectors
            pass
        else:
            # Other actions must have either a valid selector or valid text for fallback
            if not element_selector and not element_text:
                try:
                    self.logger.warning("❌ perform_action: No valid selector or text provided")
                except:
                    print("❌ perform_action: No valid selector or text provided")
                return False
            
            # If selector is very short and no text, likely invalid
            if len(element_selector) < 3 and not element_text:
                try:
                    self.logger.warning(f"❌ perform_action: Selector too short and no text: '{element_selector}'")
                except:
                    print(f"❌ perform_action: Selector too short and no text: '{element_selector}'")
                return False
        
        try:
            # Handle actions that don't require elements first
            if action == "back":
                self.driver.back()
                try:
                    self.logger.info("✅ Executed back action")
                except Exception:
                    print("✅ Executed back action")
                return True
                
            elif action == "swipe":
                # Simple swipe up
                size = self.driver.get_window_size()
                self.driver.swipe(
                    size['width'] // 2, size['height'] * 3 // 4,
                    size['width'] // 2, size['height'] // 4,
                    duration=500
                )
                try:
                    self.logger.info("✅ Executed swipe action")
                except Exception:
                    print("✅ Executed swipe action")
                return True
            
            # Helper function to extract ID from resource ID format
            def extract_id_from_resource(selector, locator_type):
                """Extract just the ID part from Android resource ID format.
                
                Example: 'org.wikipedia:id/fragment_onboarding_forward_button' -> 'fragment_onboarding_forward_button'
                """
                try:
                    self.logger.debug(f"🔧 extract_id_from_resource called: selector='{selector}' locator_type='{locator_type}'")
                except:
                    print(f"🔧 extract_id_from_resource called: selector='{selector}' locator_type='{locator_type}'")
                    
                if locator_type == 'id' and ':id/' in selector:
                    extracted_id = selector.split(':id/')[-1]
                    try:
                        self.logger.debug(f"🔧 Extracted ID: '{selector}' -> '{extracted_id}'")
                    except:
                        print(f"🔧 Extracted ID: '{selector}' -> '{extracted_id}'")
                    return extracted_id
                    
                try:
                    self.logger.debug(f"🔧 No extraction needed: locator_type='{locator_type}' has_id_format={':id/' in selector}")
                except:
                    print(f"🔧 No extraction needed: locator_type='{locator_type}' has_id_format={':id/' in selector}")
                return selector
            
            # For element-based actions, proceed with element finding
            # Enhanced selector attempts with text-based fallbacks
            attempts = []

            if selector_type:
                # If AI provided a selector type, try a smart order: first try id,
                # then try the provided type, then fall back to xpath/accessibility.
                if selector_type != 'id':
                    id_selector = extract_id_from_resource(element_selector, 'id')
                    attempts.append(('id', id_selector))
                
                # Apply ID extraction for the main selector type if it's 'id'
                try:
                    self.logger.debug(f"🔧 About to extract ID for selector_type='{selector_type}' selector='{element_selector}'")
                except:
                    print(f"🔧 About to extract ID for selector_type='{selector_type}' selector='{element_selector}'")
                main_selector = extract_id_from_resource(element_selector, selector_type)
                try:
                    self.logger.debug(f"🔧 After extraction: main_selector='{main_selector}'")
                except:
                    print(f"🔧 After extraction: main_selector='{main_selector}'")
                attempts.append((selector_type, main_selector))
            else:
                # No selector_type provided: try id, xpath, accessibility id
                id_selector = extract_id_from_resource(element_selector, 'id')
                attempts.extend([('id', id_selector), ('xpath', element_selector), ('accessibility_id', element_selector)])

            # Always include common fallbacks if not already present
            if not any(a[0] == 'xpath' for a in attempts):
                attempts.append(('xpath', element_selector))
            if not any(a[0] == 'accessibility_id' for a in attempts):
                attempts.append(('accessibility_id', element_selector))
            
            # Add cleaned ID fallback if not already present and selector looks like resource ID
            if not any(a[0] == 'id' for a in attempts) and ':id/' in element_selector:
                clean_id = extract_id_from_resource(element_selector, 'id')
                attempts.append(('id', clean_id))
            
            # TEXT-BASED FALLBACKS - Add contains text xpath if element_text is available
            if element_text and element_text.strip():
                # Clean text for xpath (escape quotes if needed)
                clean_text = element_text.strip()
                if "'" in clean_text and '"' in clean_text:
                    # Use concat for mixed quotes - simplified approach
                    clean_text = clean_text.replace("'", '"') 
                
                # Add text-based fallback selectors
                text_xpath = f"//*[contains(text(),'{clean_text}')]"
                attempts.append(('text_xpath', text_xpath))
                
                # Also try partial text match (useful for truncated text)
                if len(clean_text) > 10:
                    partial_text = clean_text[:10]
                    partial_xpath = f"//*[contains(text(),'{partial_text}')]"
                    attempts.append(('partial_text_xpath', partial_xpath))
                
                # Try text matching on content-desc attribute
                content_desc_xpath = f"//*[@content-desc='{clean_text}']"
                attempts.append(('content_desc_xpath', content_desc_xpath))
                
                # Try text matching on various text attributes
                hint_xpath = f"//*[@hint='{clean_text}']"
                attempts.append(('hint_xpath', hint_xpath))

            last_exc = None
            found_element = None
            used_locator = None

            # Log the high-level attempt
            try:
                self.logger.debug("perform_action called: action=%s selector=%s selector_type=%s text='%s' input=%s", 
                                action, element_selector, selector_type, element_text, input_value)
            except Exception:
                print(f"perform_action: action={action} selector={element_selector} text='{element_text}' input={input_value}")

            for typ, sel in attempts:
                try:
                    try:
                        self.logger.debug("Trying locator %s with selector: %s", typ, sel)
                    except Exception:
                        pass

                    if typ == 'id':
                        found_element = self.driver.find_element(AppiumBy.ID, sel)
                    elif typ == 'xpath' or typ.endswith('_xpath'):
                        found_element = self.driver.find_element(AppiumBy.XPATH, sel)
                    elif typ in ('accessibility_id', 'accessibility', 'aid'):
                        found_element = self.driver.find_element(AppiumBy.ACCESSIBILITY_ID, sel)
                    else:
                        found_element = self.driver.find_element(AppiumBy.XPATH, sel)

                    if found_element:
                        used_locator = typ
                        try:
                            self.logger.debug("✅ Found element using %s: %s", typ, sel)
                        except Exception:
                            pass
                        break
                except Exception as e:
                    last_exc = e
                    try:
                        self.logger.debug("❌ Locator %s failed: %s", typ, e)
                    except Exception:
                        pass
                    continue

            if not found_element:
                try:
                    self.logger.warning("❌ Element not found for selector=%s text='%s' (tried %s)", 
                                      element_selector, element_text, [a[0] for a in attempts])
                except Exception:
                    print(f"❌ Element not found for selector={element_selector} text='{element_text}'")
                if last_exc:
                    raise last_exc
                return False

            # Perform the actual action and log success
            if action == "click":
                found_element.click()
                try:
                    self.logger.info("✅ Clicked element using %s selector: %s", used_locator, sel)
                except Exception:
                    print(f"✅ Clicked element using {used_locator} selector: {sel}")
                return True
                
            elif action == "input":
                found_element.clear()
                if input_value:
                    found_element.send_keys(input_value)
                try:
                    self.logger.info("✅ Input into element using %s selector: %s (value=%s)", used_locator, sel, input_value)
                except Exception:
                    print(f"✅ Input into element using {used_locator} selector: {sel} (value={input_value})")
                return True
                
            else:
                print(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"Error performing action {action}: {e}")
            return False
    
    def start_crawl(self, name: str, description: str = "",
                   max_steps: int = 500,
                   human_callback: Optional[Callable] = None):
        """Start a new crawl session or resume existing active path.
        
        Args:
            name: Name for this crawl path
            description: Description of crawl goal
            max_steps: Maximum number of steps
            human_callback: Callback function for human intervention
        """
        # Get or create active path for this app
        self.current_path_id = self.db.create_or_get_active_path(
            app_package=self.app_package,
            name=name,
            platform=self.platform,
            description=description
        )
        
        # Load existing steps and reconstruct explored states
        existing_steps = self.db.get_path_steps(self.current_path_id)
        self.step_count = len(existing_steps)
        self.explored_states = self._reconstruct_state_signatures(existing_steps)
        
        self.human_callback = human_callback

        # Configure per-run logger
        log_dir = os.path.join("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"crawl_{self.current_path_id}.log")

        logger = logging.getLogger("app_crawler")
        logger.setLevel(logging.DEBUG)

        # Avoid duplicate file handlers for same path
        found = False
        for h in list(logger.handlers):
            try:
                if isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '') == os.path.abspath(log_path):
                    found = True
            except Exception:
                pass

        if not found:
            fh = logging.FileHandler(log_path)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            logger.addHandler(fh)

        # Ensure console handler exists
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            sh = logging.StreamHandler()
            sh.setLevel(logging.INFO)
            sh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            logger.addHandler(sh)

        self.logger = logger
        
        if existing_steps:
            logger.info(f"Resuming crawl: {self.current_path_id} with {len(existing_steps)} existing steps")
        else:
            logger.info(f"Started new crawl: {self.current_path_id}")
        
        # Connect to app
        self.connect()
        
        # Initialize Enhanced BFS with directed graph tracking
        print("\n=== Enhanced BFS Crawler with Directed Graph Started ===")
        print("Strategy: Test every actionable element + Track as directed graph")
        try:
            self.logger.info("Initializing Enhanced BFS crawl strategy with directed graph tracking")
        except:
            print("Initializing Enhanced BFS crawl strategy with directed graph tracking")
        
        # Initialize directed graph tracking
        initial_state_source = self.get_page_source()
        initial_activity = self.get_current_activity()
        initial_screenshot = self.take_screenshot(0)
        
        # Create initial node in the graph
        self.current_node_id = self._create_or_get_graph_node(
            activity=initial_activity,
            page_source=initial_state_source,
            screenshot_path=initial_screenshot
        )
        
        # Initialize journey tracking
        self.current_journey_path = [self.current_node_id]
        self.current_edge_path = []
        
        try:
            self.logger.info(f"🏁 Starting from initial node: {self.current_node_id}")
        except:
            print(f"🏁 Starting from initial node: {self.current_node_id}")
        
        # BFS Crawl loop with systematic element testing and graph tracking
        discovered_states_to_explore = deque()  # Queue of states to explore
        
        while self.step_count < max_steps:
            print(f"\n--- Crawl Session {self.step_count + 1} ---")
            
            # Wait for page to load
            time.sleep(2)
            
            # Get current state
            page_source = self.get_page_source()
            activity = self.get_current_activity()
            screenshot_path = self.take_screenshot(self.step_count + 1)
            
            # Generate state hash for BFS tracking
            state_hash = self._get_state_hash(page_source, activity)
            
            try:
                self.logger.info(f"📱 Current state: {activity} (hash: {state_hash[:8]}...)")
                self.logger.info(f"🔍 Exploration queue: {len(discovered_states_to_explore)} states pending")
                self.logger.info(f"✅ Visited states: {len(self.visited_states)} total")
            except:
                print(f"📱 Current state: {activity} (hash: {state_hash[:8]}...)")
                print(f"🔍 Exploration queue: {len(discovered_states_to_explore)} states pending")
                print(f"✅ Visited states: {len(self.visited_states)} total")
            
            # Check if this state should be explored in our graph
            current_node_exploration_needed = False
            
            # Update current graph node if we've moved to a new state
            current_state_node = self._create_or_get_graph_node(
                activity=activity,
                page_source=page_source,
                screenshot_path=screenshot_path
            )
            
            # If we're in a different node, update our tracking
            if current_state_node != self.current_node_id:
                self.current_node_id = current_state_node
                self.current_journey_path.append(current_state_node)
                current_node_exploration_needed = True
                
                try:
                    self.logger.info(f"📍 Moved to graph node: {self.current_node_id}")
                except:
                    print(f"📍 Moved to graph node: {self.current_node_id}")
            
            # Check if this state needs exploration (legacy visited states + graph analysis)
            if self._should_explore_state(state_hash) or current_node_exploration_needed:
                # Extract all actionable elements on current screen
                elements = self.extract_elements()
                try:
                    self.logger.debug("Elements discovered: %s", json.dumps(elements[:10], default=str))
                except Exception:
                    self.logger.debug("Elements discovered (could not serialize)")

                if elements:
                    try:
                        self.logger.info(f"🎯 Found {len(elements)} actionable elements on this screen")
                        
                        # Debug: Log first few elements to see what AI is returning
                        for i, elem in enumerate(elements[:3]):
                            try:
                                selector = elem.get('selector', 'NO_SELECTOR')
                                text = elem.get('text', 'NO_TEXT')
                                action_type = elem.get('action_type', 'NO_ACTION_TYPE')
                                self.logger.debug(f"  Element {i+1}: action={action_type}, selector={selector}, text='{text}'")
                            except:
                                print(f"  Element {i+1}: {elem}")
                    except:
                        print(f"🎯 Found {len(elements)} actionable elements on this screen")
                    
                    # Prepare actions for systematic testing
                    actions_to_test = self._queue_actions_for_state(state_hash, elements, activity)
                    
                    # Execute each action systematically and observe results
                    if actions_to_test:
                        self.step_count += 1
                        action_results = self._execute_all_actions_on_current_state(actions_to_test, state_hash)
                        
                        # Record comprehensive step with all action results
                        self.db.add_path_step(
                            path_id=self.current_path_id,
                            step_number=self.step_count,
                            action_type="systematic_element_testing",
                            element_selector=f"tested_{len(actions_to_test)}_elements",
                            element_attributes={
                                'total_elements_tested': len(actions_to_test),
                                'successful_actions': len([r for r in action_results if r.get('success')]),
                                'state_changes_triggered': len([r for r in action_results if r.get('state_changed')]),
                                'new_states_discovered': len([r for r in action_results if r.get('state_changed')])
                            },
                            input_value=None,
                            screenshot_path=screenshot_path,
                            dom_snapshot=page_source[:5000],
                            ai_reasoning=f"Systematic testing of {len(actions_to_test)} elements on state {state_hash[:8]}"
                        )
                        
                        # Update last step number for resume capability
                        self.db.update_last_step_number(self.current_path_id, self.step_count)
                        
                        # Collect newly discovered states from graph edges for future exploration
                        new_states_found = 0
                        for result in action_results:
                            if result.get('state_changed') and result.get('target_node_id'):
                                new_node_id = result['target_node_id']
                                new_state_hash = result['new_state_hash']
                                new_activity = result['new_activity']
                                
                                # Add to exploration queue if node hasn't been fully explored
                                unexplored_from_node = self.db.get_unexplored_edges_from_node(new_node_id)
                                if new_state_hash not in self.visited_states or len(unexplored_from_node) > 0:
                                    discovered_states_to_explore.append({
                                        'state_hash': new_state_hash,
                                        'activity': new_activity,
                                        'node_id': new_node_id,
                                        'discovered_from': state_hash,
                                        'trigger_action': result['action']
                                    })
                                    new_states_found += 1
                        
                        try:
                            self.logger.info(f"🆕 Element testing complete: {new_states_found} new states discovered")
                        except:
                            print(f"🆕 Element testing complete: {new_states_found} new states discovered")
                
                else:
                    try:
                        self.logger.info("❌ No actionable elements found on current screen")
                    except:
                        print("❌ No actionable elements found on current screen")
            else:
                try:
                    self.logger.info(f"⏭️  State already explored: {activity}")
                except:
                    print(f"⏭️  State already explored: {activity}")
            
            # Move to next state from discovery queue and update graph tracking
            if discovered_states_to_explore and self.step_count < max_steps:
                next_state_info = discovered_states_to_explore.popleft()
                next_state_hash = next_state_info['state_hash']
                next_activity = next_state_info['activity']
                next_node_id = next_state_info.get('node_id')
                
                try:
                    self.logger.info(f"🧭 Navigating to node: {next_node_id} ({next_activity})")
                except:
                    print(f"🧭 Navigating to node: {next_node_id} ({next_activity})")
                
                # Try to navigate to the next state by re-executing the action that led there
                trigger_action = next_state_info.get('trigger_action', {})
                if trigger_action:
                    action_type = trigger_action.get('action_type', 'click')
                    element_selector = trigger_action.get('element_selector', '')
                    element_text = trigger_action.get('element_text', '')
                    input_value = trigger_action.get('input_value')
                    selector_type = trigger_action.get('selector_type')
                    
                    try:
                        self.logger.info(f"🎯 Re-executing navigation: {action_type} on '{element_text or element_selector}'")
                    except:
                        print(f"🎯 Re-executing navigation: {action_type} on '{element_text or element_selector}'")
                    
                    navigation_success = self.perform_action(
                        action=action_type,
                        element_selector=element_selector,
                        input_value=input_value,
                        selector_type=selector_type,
                        element_text=element_text  # Include text for fallback selection
                    )
                    
                    if not navigation_success:
                        try:
                            self.logger.warning("❌ Navigation action failed, continuing to next state")
                        except:
                            print("❌ Navigation action failed, continuing to next state")
                        continue
                        
                    # Wait for navigation to complete
                    time.sleep(2)
                    
                    # Update graph tracking after successful navigation
                    if next_node_id:
                        self.current_node_id = next_node_id
                        self.current_journey_path.append(next_node_id)
                        
                        try:
                            self.logger.info(f"✅ Successfully navigated to node: {next_node_id}")
                        except:
                            print(f"✅ Successfully navigated to node: {next_node_id}")
                    
                else:
                    try:
                        self.logger.info("🤔 No trigger action available, skipping to next state")
                    except:
                        print("🤔 No trigger action available, skipping to next state")
                    continue
            
            elif not discovered_states_to_explore:
                try:
                    self.logger.info("🎉 No more states to explore. Systematic exploration complete!")
                except:
                    print("🎉 No more states to explore. Systematic exploration complete!")
                break
            
            # Safety delay between state explorations
            time.sleep(1)
        
        # Get graph statistics for final report
        graph_stats = self.db.get_app_graph_stats(self.app_package)
        
        print(f"\n🎯 Enhanced BFS Crawl with Directed Graph completed!")
        print(f"📊 Total steps: {self.step_count}")
        print(f"🗺️  States explored: {len(self.visited_states)}")
        print(f"⏳ Pending states: {len(discovered_states_to_explore)}")
        print(f"📍 Graph nodes: {graph_stats.get('node_count', 0)}")
        print(f"🔗 Graph edges: {graph_stats.get('edge_count', 0)}")
        print(f"✅ Valid paths: {graph_stats.get('valid_edges', 0)}")
        print(f"❌ Invalid paths: {graph_stats.get('invalid_edges', 0)}")
        print(f"🔄 Journey cycles: {graph_stats.get('journey_cycles', 0)}")
        
        try:
            self.logger.info(
                "Enhanced BFS with Graph crawl completed. "
                "States: %d, Nodes: %d, Edges: %d, Valid: %d, Invalid: %d, Cycles: %d", 
                len(self.visited_states), graph_stats.get('node_count', 0),
                graph_stats.get('edge_count', 0), graph_stats.get('valid_edges', 0),
                graph_stats.get('invalid_edges', 0), graph_stats.get('journey_cycles', 0)
            )
        except:
            pass
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
            # Try to reuse selector_type if it was stored in element attributes
            selector_type = None
            try:
                selector_type = step.get('element_attributes', {}).get('selector_type')
            except Exception:
                selector_type = None

            success = self.perform_action(
                action=step['action_type'],
                element_selector=step['element_selector'],
                input_value=step['input_value'],
                selector_type=selector_type
            )
            
            if not success:
                print(f"Failed to replay step {step['step_number']}")
                # Continue anyway for now
        
        print("\nReplay completed")
        self.disconnect()
    
    def _reconstruct_state_signatures(self, existing_steps: List[Dict[str, Any]]) -> set:
        """Reconstruct explored state signatures from existing path steps for BFS resume.
        
        Args:
            existing_steps: List of step dictionaries from database
            
        Returns:
            Set of state signatures that were previously explored
        """
        explored_states = set()
        
        # For BFS, also reconstruct the visited states and action queue
        for step in existing_steps:
            # Try to reconstruct the same state signature used during crawling
            dom_snapshot = step.get('dom_snapshot', '')
            
            # Extract activity name from step context or use a fallback
            activity = "unknown_activity"  # Fallback
            
            # Create state hash for BFS tracking
            if dom_snapshot:
                state_hash = hashlib.md5(f"{activity}_{len(dom_snapshot)}_{hash(dom_snapshot[:1000])}".encode()).hexdigest()
                self.visited_states.add(state_hash)
            
            # Count elements from DOM snapshot (approximate)
            element_count = dom_snapshot.count('<') if dom_snapshot else 0
            
            # For backward compatibility with old signature format
            state_sig = f"{activity}_{element_count}"
            explored_states.add(state_sig)
        
        # Update step count based on existing steps for resume
        if existing_steps:
            max_step = max(step.get('step_number', 0) for step in existing_steps)
            self.step_count = max_step
            
            try:
                self.logger.info(f"BFS Resume: Loaded {len(explored_states)} state signatures, "
                               f"{len(self.visited_states)} visited states, "
                               f"starting from step {self.step_count + 1}")
            except:
                print(f"BFS Resume: Loaded {len(explored_states)} state signatures, "
                      f"{len(self.visited_states)} visited states, "
                      f"starting from step {self.step_count + 1}")
        
        return explored_states
