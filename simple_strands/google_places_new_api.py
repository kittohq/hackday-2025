"""
Google Places Agent using NEW Places API
Works with your Google Maps API key
"""

import os
import json
import requests
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, List

# Set API keys
# Load API keys from environment or .env file
# Set OPENAI_API_KEY and GOOGLE_API_KEY environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

@tool
def search_nearby_places(
    query: str,
    location: Dict[str, float],
    radius: int = 2000
) -> List[Dict]:
    """
    Search for places using NEW Google Places API (Nearby Search).

    Args:
        query: What to search for (e.g., "coffee", "restaurant")
        location: Dict with 'lat' and 'lng' keys
        radius: Search radius in meters

    Returns:
        List of places with details
    """

    # Use NEW Places API endpoint - requires Places API (New) to be enabled
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours"
    }

    body = {
        "includedTypes": [get_place_type(query)],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": location['lat'],
                    "longitude": location.get('lng', location.get('lon', -122.4194))
                },
                "radius": radius
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            data = response.json()
            places = []

            for place in data.get('places', []):
                places.append({
                    "name": place.get('displayName', {}).get('text', 'Unknown'),
                    "address": place.get('formattedAddress', 'No address'),
                    "rating": place.get('rating', 0),
                    "review_count": place.get('userRatingCount', 0),
                    "open_now": place.get('currentOpeningHours', {}).get('openNow', None)
                })

            return places
        else:
            print(f"Google Places API error: {response.status_code}")
            print(f"Response: {response.text}")
            # No fallback to mock - real data only
            return []

    except Exception as e:
        print(f"Error calling Google Places: {e}")
        return []  # No mock data - real only

def get_place_type(query: str) -> str:
    """Map query to NEW Google Places API type"""
    query_lower = query.lower()

    # NEW API uses different type names
    type_map = {
        "coffee": "coffee_shop",
        "cafe": "cafe",
        "restaurant": "restaurant",
        "food": "restaurant",
        "gas": "gas_station",
        "pharmacy": "pharmacy",
        "hotel": "lodging",
        "bank": "bank",
        "atm": "atm",
        "bar": "bar",
        "store": "store"
    }

    for key, value in type_map.items():
        if key in query_lower:
            return value

    return "restaurant"  # Default

# Removed mock data function - using real API only

@tool
def format_place_response(places: List[Dict]) -> str:
    """Format places into natural language response"""
    if not places:
        return "I couldn't find any places nearby."

    if len(places) == 1:
        p = places[0]
        return f"I found {p['name']} with a {p['rating']} star rating."

    response = f"I found {len(places)} options nearby: "
    details = []

    for p in places[:3]:
        details.append(f"{p['name']} ({p['rating']} stars)")

    response += ", ".join(details)
    response += ". Would you like directions to any of these?"

    return response

# Create OpenAI model
model = OpenAIModel(
    model_id="gpt-3.5-turbo",
    params={
        "temperature": 0.7,
        "max_tokens": 150
    }
)

# Create agent with tools
places_agent = Agent(
    name="Google Places Assistant",
    model=model,
    tools=[search_nearby_places, format_place_response],
    system_prompt="""You are a helpful assistant for finding places nearby.
    When users ask about places, use the search_nearby_places tool.
    Format responses naturally and suggest the top options."""
)

def test_new_api():
    """Test the new Google Places API"""
    print("\n🗺️ Testing NEW Google Places API")
    print("=" * 50)

    # Test location (San Francisco)
    location = {"lat": 37.7749, "lng": -122.4194}

    # Direct API test
    print("\n1️⃣ Direct API Test:")
    results = search_nearby_places("coffee", location, 1500)

    if results:
        print(f"✅ Found {len(results)} places:")
        for place in results:
            print(f"   - {place['name']} ({place['rating']} stars)")
    else:
        print("❌ No results (may be using mock data)")

    print("\n2️⃣ Agent Test:")
    queries = [
        "Find coffee shops nearby",
        "Where can I get food?",
        "I need a gas station"
    ]

    for query in queries:
        print(f"\n👤 You: {query}")
        try:
            # In real usage, agent would call the tool automatically
            # For demo, we'll simulate the flow
            if "coffee" in query.lower():
                places = search_nearby_places("coffee", location)
            elif "food" in query.lower():
                places = search_nearby_places("restaurant", location)
            elif "gas" in query.lower():
                places = search_nearby_places("gas", location)
            else:
                places = []

            response = format_place_response(places)
            print(f"🤖 Agent: {response}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_new_api()
