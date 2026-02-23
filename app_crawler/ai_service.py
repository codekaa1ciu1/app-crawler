"""AI service for analyzing DOM and making crawler decisions.

Adds support for OpenAI, Anthropic, and Qwen (configurable via env).
Qwen is called through a configurable HTTP endpoint `QWEN_API_URL` with
`QWEN_API_KEY` as Bearer token. The implementation attempts to handle
OpenAI-like and Qwen-like response shapes.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple


class AIService:
    """AI service for crawler intelligence."""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """Initialize AI service.
        
        Args:
            provider: 'openai' or 'anthropic'
            api_key: API key (or use environment variable)
        """
        self.provider = provider.lower()
        # logger for AI service (debug-level details only)
        self.logger = logging.getLogger("app_crawler.ai_service")
        
        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            # Allow overriding model via environment; default to a broadly-available model
            # Many accounts may not have `gpt-4` access; default to `gpt-3.5-turbo` for compatibility.
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-opus-20240229"
        elif self.provider == "qwen":
            # Qwen exposes an OpenAI-compatible API — use OpenAI SDK with api_base.
            import openai
            qwen_key = api_key or os.getenv("QWEN_API_KEY")
            qwen_base = os.getenv("QWEN_API_URL") or os.getenv("QWEN_API_BASE")
            if not qwen_base:
                # sensible default endpoint (can be overridden in env)
                qwen_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            # Instantiate OpenAI-compatible client pointing at Qwen base URL
            # Completely bypass proxy for external API calls
            import httpx
            http_client = httpx.Client(
                proxy=None,
                transport=httpx.HTTPTransport(
                    proxy=None,
                    retries=3
                )
            )
            client = openai.OpenAI(
                api_key=qwen_key,
                base_url=qwen_base,
                http_client=http_client
            )
            self.client = client
            # Keep Qwen connection details for debug/logging if needed
            self.qwen_key = qwen_key
            self.qwen_base = qwen_base
            self.model = os.getenv("QWEN_MODEL", "qwen-chat-1")
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def extract_actionable_elements(self, dom_tree: str, 
                                   context: str = "") -> List[Dict[str, Any]]:
        """Extract actionable elements from DOM tree using AI.
        
        Args:
            dom_tree: XML/JSON representation of DOM tree
            context: Additional context about the goal
            
        Returns:
            List of actionable element descriptions with selectors
        """
        prompt = f"""Analyze this mobile app DOM tree and identify all actionable UI elements.

DOM Tree:
{dom_tree}

Context: {context if context else "General exploration"}

For each actionable element, provide the following properties:
1. `type` - Element type (button, text field, switch, etc.)
2. `selector` - The locator string (e.g. an XPath or id value)
3. `selector_type` - One of: `id`, `xpath`, or `accessibility_id` (exactly these tokens)
4. `text` - Visible text or content description (if any)
5. `action` - Recommended action (click, input, swipe, etc.)
6. `priority` - One of: `high`, `medium`, `low`
7. `reasoning` - Short explanation of why this element is interesting

Guidelines:
- When producing an XPath for elements that have visible text, prefer using a `contains()` match on the text rather than an exact equality. Example: `//android.widget.TextView[contains(text(), "Sign in")]`.
- Use `selector_type:id` only when you are returning a platform-native id/resource-id value (do not wrap it in XPath). Use `selector_type:accessibility_id` for accessibility labels.
- Always include `selector_type` alongside `selector` so the crawler knows how to query the element.

Return a JSON array of elements in this format:
[
    {{
        "type": "button",
        "selector": "//android.widget.Button[contains(text(), 'Login')]",
        "selector_type": "xpath",
        "text": "Login",
        "action": "click",
        "priority": "high",
        "reasoning": "Main action button for authentication"
    }},
    ...
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        messages = [
            {"role": "system", "content": "You are an expert in mobile UI analysis. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]

        try:
            content = self._send_chat(messages, temperature=0.3, max_tokens=4096)
            elements = json.loads(content)
            return elements
        except Exception as e:
            print(f"Error extracting actionable elements: {e}")
            return []
    
    def suggest_input_value(self, element: Dict[str, Any], 
                          context: str = "") -> Tuple[Optional[str], str]:
        """Suggest input value for a text field using AI.
        
        Args:
            element: Element dictionary with type, text, etc.
            context: Additional context
            
        Returns:
            Tuple of (suggested_value, reasoning)
        """
        prompt = f"""This is a text input field in a mobile app. Suggest an appropriate value to input.

Element details:
Type: {element.get('type', 'text field')}
Text/Label: {element.get('text', 'N/A')}
Content Description: {element.get('content_desc', 'N/A')}
Placeholder: {element.get('hint', 'N/A')}

Context: {context if context else "General testing"}

Consider:
- If this is an email field, provide a test email
- If this is a password field, provide a test password
- If this is a search field, provide a relevant search query
- If this is a phone number, provide a valid format
- If this is a name field, provide a test name

Respond in JSON format:
{{
  "suggested_value": "the value to input",
  "reasoning": "explanation of why this value is appropriate"
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        messages = [
            {"role": "system", "content": "You are an expert in mobile app testing. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]

        try:
            content = self._send_chat(messages, temperature=0.5, max_tokens=1024)
            result = json.loads(content)
            return result.get("suggested_value"), result.get("reasoning", "")
        except Exception as e:
            print(f"Error suggesting input value: {e}")
            return None, f"Error: {str(e)}"
    
    def decide_next_action(self, current_state: Dict[str, Any],
                          explored_paths: List[str],
                          goal: str = "") -> Dict[str, Any]:
        """Decide on the next action to take in crawling.
        
        Args:
            current_state: Current app state with available elements
            explored_paths: List of already explored path signatures
            goal: Crawling goal or objective
            
        Returns:
            Dictionary with action decision and reasoning
        """
        prompt = f"""You are crawling a mobile application. Analyze the current state and decide the next action.

Current state:
Available elements: {json.dumps(current_state.get('elements', []), indent=2)}
Current screen: {current_state.get('activity', 'Unknown')}

Already explored paths: {len(explored_paths)} paths
Goal: {goal if goal else "Comprehensive exploration"}

Decide the next best action:
1. Choose an element to interact with (prioritize unexplored elements)
2. Determine the action type (click, input, swipe, back, etc.)
3. If input action, suggest what to input
4. Provide reasoning for your decision

If you cannot determine a good next action, set "needs_human_help" to true and explain why.

Respond in JSON format and include the selector type for the chosen element. Example:
{{
    "action": "click|input|swipe|back|stop",
    "element_selector": "//android.widget.Button[contains(text(), 'Login')]",
    "selector_type": "xpath",
    "input_value": "value if action is input",
    "reasoning": "explanation of decision",
    "needs_human_help": false,
    "question_for_human": "question if needs help"
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        messages = [
            {"role": "system", "content": "You are an expert mobile app crawler. Always respond with valid JSON only."},
            {"role": "user", "content": prompt}
        ]

        try:
            content = self._send_chat(messages, temperature=0.4, max_tokens=2048)
            # AI may sometimes return non-JSON or include unexpected text. Be
            # defensive: try to parse JSON, otherwise return a safe 'stop'
            try:
                decision = json.loads(content)
                return decision
            except Exception as parse_err:
                try:
                    self.logger.debug("Failed to parse AI decision JSON: %s", str(parse_err))
                    self.logger.debug("AI raw response: %s", content)
                except Exception:
                    pass
                return {
                    "action": "stop",
                    "reasoning": f"Unable to parse AI response: {str(parse_err)}",
                    "needs_human_help": True,
                    "question_for_human": f"AI returned an unparsable response. Raw: {str(content)[:500]}"
                }
        except Exception as e:
            print(f"Error deciding next action: {e}")
            return {
                "action": "stop",
                "reasoning": f"Error: {str(e)}",
                "needs_human_help": True,
                "question_for_human": f"AI encountered an error: {str(e)}. What should we do?"
            }

    def _send_chat(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: Optional[int] = None) -> str:
        """Unified chat caller for supported providers.

        Args:
            messages: List of {'role':.., 'content':..} messages (OpenAI-style)
            temperature: Sampling temperature
            max_tokens: Optional max tokens

        Returns:
            Text content from model
        """
        try:
            # OpenAI-compatible providers (OpenAI and Qwen via api_base)
            if self.provider == "openai":
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content

            if self.provider == "qwen":
                try:
                    self.logger.debug("QWEN provider selected; api_key=%s", getattr(self, 'qwen_key', None))
                    self.logger.debug("QWEN api_base=%s", getattr(self, 'qwen_base', None))
                except Exception:
                    pass

                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_body={"enable_thinking": False},
                )
                return resp.choices[0].message.content
            
            if self.provider == "anthropic":
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens or 2048,
                    messages=messages,
                    temperature=temperature,
                )
                if hasattr(resp, 'content'):
                    try:
                        return resp.content[0].text
                    except Exception:
                        return str(resp)
                return str(resp)

        except Exception as e:
            raise
