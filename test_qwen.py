"""Test Qwen API connection."""
import os
from dotenv import load_dotenv
from app_crawler.ai_service import AIService

# Load environment variables
load_dotenv()

def test_qwen():
    """Test Qwen API connection."""
    print("Testing Qwen API connection...")

    try:
        ai = AIService(provider="qwen", api_key=os.getenv("QWEN_API_KEY"))
        print("✓ AIService initialized successfully")
        print(f"  Provider: {ai.provider}")
        print(f"  Model: {ai.model}")
        print(f"  Client base URL: {getattr(ai.client, '_base_url', 'unknown')}")

        # Test with a simple DOM
        test_dom = "<hierarchy><android.widget.Button text='Test Button'/></hierarchy>"
        print(f"\nSending test DOM: {test_dom}")

        elements = ai.extract_actionable_elements(dom_tree=test_dom, context="Test")
        print(f"✓ API call successful, returned {len(elements)} elements")

        if elements:
            print("Elements:", elements)
        else:
            print("⚠ No elements returned")

        # Ask the model who it is and print the response
        try:
            messages = [{"role": "user", "content": "Who are you?"}]
            print("\nAsking model: Who are you?")
            reply = ai._send_chat(messages, temperature=0.0, max_tokens=200)
            print("Model response:", reply)
        except Exception as e:
            print("Error asking model:", e)
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_qwen()