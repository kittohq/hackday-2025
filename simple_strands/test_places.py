"""
Test Google Places Agent with Strands
Non-interactive demo
"""

from strands import Agent, tool
from typing import Dict, List
import os

# Configure model
os.environ.setdefault("STRANDS_MODEL_PROVIDER", "openai")

@tool
def googlePlacesSearch(query: str, location: Dict[str, float], radius: int = 2000) -> List[Dict]:
    """Search for places using Google Places API"""

    # Mock results for demo
    if "coffee" in query.lower():
        return [
            {"name": "Blue Bottle Coffee", "address": "300 Webster St", "rating": 4.5,
             "distance_meters": 800, "open_now": True},
            {"name": "Ritual Coffee", "address": "432 Octavia St", "rating": 4.3,
             "distance_meters": 1200, "open_now": True},
            {"name": "Starbucks", "address": "2727 Mission St", "rating": 3.8,
             "distance_meters": 500, "open_now": True}
        ]
    return []

@tool
def format_distance(distance_meters: int) -> str:
    """Format distance to human-readable"""
    miles = distance_meters / 1609.34
    return f"{miles:.1f} miles" if miles < 1 else f"{miles:.0f} miles"

# Create agent
agent = Agent(
    tools=[googlePlacesSearch, format_distance],
    name="Places Assistant"
)

def test_agent():
    """Test the agent with sample queries"""
    print("\n🗺️ Google Places Strands Agent Test")
    print("=" * 50)

    # Test location
    location = {"lat": 37.7749, "lon": -122.4194}

    # Test queries
    test_queries = [
        "Find coffee shops nearby",
        "I need a cafe",
        "Where can I get coffee?"
    ]

    for query in test_queries:
        print(f"\n👤 Query: {query}")

        # Simulate what Strands would do:
        # 1. Parse intent (coffee search)
        # 2. Call tool
        results = googlePlacesSearch("coffee", location)

        # 3. Format response
        if results:
            response = f"Found {len(results)} options: "
            for i, place in enumerate(results[:3]):
                dist = format_distance(place['distance_meters'])
                response += f"{place['name']} ({dist}, {place['rating']}★)"
                if i < 2:
                    response += ", "

            print(f"🤖 Response: {response}")
        else:
            print("🤖 Response: No places found")

    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_agent()