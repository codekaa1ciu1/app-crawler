"""AI service for analyzing DOM and making crawler decisions."""
import os
import json
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
        
        if self.provider == "openai":
            import openai
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-opus-20240229"
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

For each actionable element, provide:
1. Element type (button, text field, switch, etc.)
2. Selector (xpath, id, or accessibility id)
3. Visible text or content description
4. Recommended action (click, input, swipe, etc.)
5. Priority (high, medium, low) based on importance
6. Reasoning for why this element is interesting

Return a JSON array of elements in this format:
[
  {{
    "type": "button",
    "selector": "//android.widget.Button[@text='Login']",
    "text": "Login",
    "action": "click",
    "priority": "high",
    "reasoning": "Main action button for authentication"
  }},
  ...
]

IMPORTANT: Return ONLY the JSON array, no other text."""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in mobile UI analysis. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                content = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                content = response.content[0].text
            
            # Parse JSON response
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

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in mobile app testing. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                content = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                content = response.content[0].text
            
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

Respond in JSON format:
{{
  "action": "click|input|swipe|back|stop",
  "element_selector": "xpath or selector",
  "input_value": "value if action is input",
  "reasoning": "explanation of decision",
  "needs_human_help": false,
  "question_for_human": "question if needs help"
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert mobile app crawler. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                content = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                content = response.content[0].text
            
            decision = json.loads(content)
            return decision
            
        except Exception as e:
            print(f"Error deciding next action: {e}")
            return {
                "action": "stop",
                "reasoning": f"Error: {str(e)}",
                "needs_human_help": True,
                "question_for_human": f"AI encountered an error: {str(e)}. What should we do?"
            }
