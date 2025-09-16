"""
Strands Agent that works WITHOUT API keys
Uses local logic for demo purposes
"""

import os
from datetime import datetime

# IMPORTANT: Tell Strands to use mock/local mode
os.environ["STRANDS_MODEL_PROVIDER"] = "mock"  # This prevents API calls

# Try importing Strands
try:
    from strands import Agent, tool
    print("✅ Using Strands SDK (in mock mode)")

    # Create tools that don't need API keys
    @tool
    def get_current_time() -> str:
        """Get the current time"""
        return datetime.now().strftime("%I:%M %p")

    @tool
    def get_current_date() -> str:
        """Get the current date"""
        return datetime.now().strftime("%A, %B %d, %Y")

    @tool
    def search_places(query: str, location: dict = None) -> list:
        """Search for places (mock data)"""
        if "coffee" in query.lower():
            return [
                {"name": "Blue Bottle Coffee", "distance": "0.5 miles"},
                {"name": "Starbucks", "distance": "0.3 miles"}
            ]
        return [{"name": f"Mock {query}", "distance": "1.0 miles"}]

    # Since we can't use real LLM without API keys,
    # we'll create a wrapper that provides mock responses
    class MockAgent:
        def __init__(self):
            self.tools = {
                "time": get_current_time,
                "date": get_current_date,
                "places": search_places
            }

        def __call__(self, query: str) -> str:
            """Process query with local logic (no API needed)"""
            query_lower = query.lower()

            # Time queries
            if any(word in query_lower for word in ["time", "clock"]):
                time = get_current_time()
                return f"The current time is {time}"

            # Date queries
            elif any(word in query_lower for word in ["date", "today", "day"]):
                date = get_current_date()
                return f"Today is {date}"

            # Place searches
            elif any(word in query_lower for word in ["coffee", "cafe", "starbucks"]):
                places = search_places("coffee")
                if places:
                    response = "I found these coffee shops nearby: "
                    for p in places[:2]:
                        response += f"{p['name']} ({p['distance']}), "
                    return response.rstrip(", ")
                return "No coffee shops found"

            # Weather (mock)
            elif "weather" in query_lower:
                return "It's currently 72°F and sunny"

            # Default
            else:
                return f"I understood: '{query}'. I can help with time, date, places, and weather."

    # Use mock agent
    agent = MockAgent()

except ImportError:
    print("⚠️  Strands not available, using pure mock")

    class MockAgent:
        def __call__(self, query: str) -> str:
            if "time" in query.lower():
                return f"The current time is {datetime.now().strftime('%I:%M %p')}"
            elif "date" in query.lower():
                return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            else:
                return "I can help with time and date queries"

    agent = MockAgent()

def demo():
    """Run demo without needing any API keys"""
    print("\n🤖 Strands Agent Demo (No API Keys Required!)")
    print("=" * 50)
    print("This demo works completely offline")
    print("\nExample queries:")
    print("  - What time is it?")
    print("  - What's today's date?")
    print("  - Find coffee shops")
    print("  - What's the weather?")
    print("\nType 'quit' to exit\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Process with mock agent (no API calls)
            response = agent(user_input)
            print(f"🤖 Agent: {response}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()

if __name__ == "__main__":
    demo()