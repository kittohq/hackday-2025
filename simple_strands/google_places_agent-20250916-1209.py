"""
AWS Strands Agent with Google Places Integration
Demonstrates tool orchestration for location-based searches
"""

from strands import Agent, tool
from typing import Dict, List, Optional
import os
import json
from datetime import datetime

# Configure model provider
os.environ.setdefault("STRANDS_MODEL_PROVIDER", "openai")  # or "bedrock"

# Google Places Search Tool
@tool
def googlePlacesSearch(
    query: str,
    location: Dict[str, float],
    radius: int = 2000
) -> List[Dict]:
    """
    Search for places using Google Places API.

    Args:
        query: Search term (e.g., "cafe", "restaurant", "gas station")
        location: Dictionary with lat and lon coordinates
        radius: Search radius in meters (default 2000)

    Returns:
        List of places with details
    """

    # Check for Google API key
    google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if google_api_key:
        # Real Google Places API call would go here
        import requests

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "key": google_api_key,
            "location": f"{location['lat']},{location['lon']}",
            "radius": radius,
            "keyword": query
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            # Parse real results
            places = []
            for place in data.get("results", [])[:5]:
                places.append({
                    "name": place.get("name"),
                    "address": place.get("vicinity"),
                    "rating": place.get("rating", "N/A"),
                    "open_now": place.get("opening_hours", {}).get("open_now", None),
                    "distance_meters": calculate_distance(location, {
                        "lat": place["geometry"]["location"]["lat"],
                        "lon": place["geometry"]["location"]["lng"]
                    }),
                    "place_id": place.get("place_id")
                })

            return places
        except Exception as e:
            print(f"Google Places API error: {e}")
            # Fall through to mock data

    # Mock data for demo (when no API key)
    if "cafe" in query.lower() or "coffee" in query.lower():
        return [
            {
                "name": "Blue Bottle Coffee",
                "address": "300 Webster St, San Francisco, CA",
                "rating": 4.5,
                "open_now": True,
                "distance_meters": 800,
                "place_id": "ChIJ1234..."
            },
            {
                "name": "Ritual Coffee Roasters",
                "address": "432 Octavia St, San Francisco, CA",
                "rating": 4.3,
                "open_now": True,
                "distance_meters": 1200,
                "place_id": "ChIJ5678..."
            },
            {
                "name": "Starbucks",
                "address": "2727 Mission St, San Francisco, CA",
                "rating": 3.8,
                "open_now": True,
                "distance_meters": 500,
                "place_id": "ChIJ9012..."
            }
        ]
    elif "restaurant" in query.lower() or "food" in query.lower():
        return [
            {
                "name": "Tartine Bakery",
                "address": "600 Guerrero St, San Francisco, CA",
                "rating": 4.4,
                "open_now": True,
                "distance_meters": 900,
                "place_id": "ChIJ2345..."
            },
            {
                "name": "La Taqueria",
                "address": "2889 Mission St, San Francisco, CA",
                "rating": 4.6,
                "open_now": True,
                "distance_meters": 1500,
                "place_id": "ChIJ6789..."
            }
        ]
    elif "gas" in query.lower():
        return [
            {
                "name": "Shell Station",
                "address": "598 Bryant St, San Francisco, CA",
                "rating": 3.5,
                "open_now": True,
                "distance_meters": 600,
                "place_id": "ChIJ3456..."
            },
            {
                "name": "Chevron",
                "address": "1200 Van Ness Ave, San Francisco, CA",
                "rating": 3.7,
                "open_now": True,
                "distance_meters": 1100,
                "place_id": "ChIJ7890..."
            }
        ]
    else:
        return [
            {
                "name": f"Generic {query.title()}",
                "address": "Nearby location",
                "rating": 4.0,
                "open_now": True,
                "distance_meters": 1000,
                "place_id": "ChIJ0000..."
            }
        ]

# Helper function for distance calculation
def calculate_distance(loc1: Dict, loc2: Dict) -> int:
    """Simple distance calculation (mock)"""
    import math

    # Haversine formula (simplified)
    lat1, lon1 = loc1['lat'], loc1['lon']
    lat2, lon2 = loc2['lat'], loc2['lon']

    # Rough approximation for demo
    distance_km = math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111
    return int(distance_km * 1000)  # Convert to meters

# Format distance for display
@tool
def format_distance(distance_meters: int) -> str:
    """
    Format distance in meters to human-readable format.

    Args:
        distance_meters: Distance in meters

    Returns:
        Formatted string (e.g., "0.5 miles")
    """
    miles = distance_meters / 1609.34
    if miles < 0.1:
        return "just ahead"
    elif miles < 1:
        return f"{miles:.1f} miles"
    else:
        return f"{miles:.0f} miles"

# Get opening hours details
@tool
def get_opening_hours(place_id: str) -> Dict:
    """
    Get detailed opening hours for a place.

    Args:
        place_id: Google Places ID

    Returns:
        Dictionary with opening hours
    """
    # Mock implementation
    return {
        "open_now": True,
        "closes_at": "8:00 PM",
        "opens_at": "7:00 AM",
        "days": ["Mon-Fri: 7:00 AM - 8:00 PM", "Sat-Sun: 8:00 AM - 7:00 PM"]
    }

# Create the Strands agent with Google Places tools
places_agent = Agent(
    tools=[googlePlacesSearch, format_distance, get_opening_hours],
    name="Places Assistant",
    description="An intelligent assistant for finding nearby places using Google Places",
    system_prompt="""You are a helpful assistant for autonomous vehicle riders.

    When users ask about places nearby:
    1. Use googlePlacesSearch to find relevant places
    2. Format distances using format_distance
    3. Provide clear, concise recommendations
    4. Always mention the top 3 options with distances and ratings
    5. If relevant, mention opening hours
    6. Ask if they'd like to add a stop

    Keep responses natural and conversational for voice output."""
)

def demo():
    """Interactive demo of the Google Places agent"""
    print("\n🗺️ Google Places Agent with AWS Strands")
    print("=" * 50)

    # Check API configuration
    if os.getenv("GOOGLE_PLACES_API_KEY"):
        print("✅ Google Places API key found")
    else:
        print("⚠️  No Google Places API key - using mock data")
        print("   Set GOOGLE_PLACES_API_KEY for real results")

    if os.getenv("OPENAI_API_KEY"):
        print("✅ OpenAI API key found")
    elif os.getenv("AWS_ACCESS_KEY_ID"):
        print("✅ AWS credentials found")
    else:
        print("⚠️  No LLM API configured - using fallback responses")

    print("\nExample requests:")
    print("  - 'Find a coffee shop nearby'")
    print("  - 'I need to stop for gas'")
    print("  - 'What restaurants are around here?'")
    print("  - 'Find the nearest Starbucks'")
    print("\nType 'quit' to exit\n")

    # Default location (San Francisco)
    current_location = {"lat": 37.7749, "lon": -122.4194}

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Process with Strands agent
            try:
                # In production, Strands would:
                # 1. Parse intent
                # 2. Call googlePlacesSearch with extracted parameters
                # 3. Format the response

                # For demo without API key, we'll simulate the flow
                if any(word in user_input.lower() for word in ['coffee', 'cafe', 'starbucks']):
                    # Simulate Strands calling our tool
                    results = googlePlacesSearch("cafe", current_location, 2000)

                    # Format response as Strands would
                    if results:
                        top_3 = results[:3]
                        response = f"There are {len(top_3)} good options nearby: "

                        details = []
                        for place in top_3:
                            dist = format_distance(place['distance_meters'])
                            status = "open now" if place.get('open_now', False) else "currently closed"
                            details.append(f"{place['name']} is {dist} ahead ({place['rating']} stars, {status})")

                        response += ". ".join(details)
                        response += ". Would you like me to add a stop at any of these?"
                    else:
                        response = "I couldn't find any coffee shops nearby."

                elif any(word in user_input.lower() for word in ['restaurant', 'food', 'eat']):
                    results = googlePlacesSearch("restaurant", current_location, 2000)

                    if results:
                        top = results[0]
                        dist = format_distance(top['distance_meters'])
                        response = f"I found {top['name']}, {dist} away with a {top['rating']} star rating. "
                        response += f"There are also {len(results)-1} other options nearby. Should I show you more?"
                    else:
                        response = "No restaurants found nearby."

                elif "gas" in user_input.lower():
                    results = googlePlacesSearch("gas station", current_location, 3000)

                    if results:
                        nearest = results[0]
                        dist = format_distance(nearest['distance_meters'])
                        response = f"The nearest gas station is {nearest['name']}, {dist} away. "
                        response += "Would you like me to add this as a stop?"
                    else:
                        response = "No gas stations found within range."

                else:
                    # Try to use the actual Strands agent if configured
                    try:
                        response = places_agent(user_input)
                    except:
                        response = "I can help you find coffee shops, restaurants, gas stations, and other places nearby. What are you looking for?"

                print(f"🤖 Agent: {response}")

            except Exception as e:
                print(f"🤖 Agent: I can help find places nearby. Try asking about coffee, restaurants, or gas stations.")

            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()

if __name__ == "__main__":
    demo()