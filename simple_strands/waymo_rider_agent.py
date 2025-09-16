"""
Waymo Rider Experience Agent
Integrates Strands/OpenAI with Google Places API
Simulates destination-based place recommendations
"""

import os
import json
import requests
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, List, Optional
from datetime import datetime
import math

# API Keys - Set these as environment variables or in .env.example file

def load_env_file(filepath='.env.example'):
    """Load environment variables from .env.example file if exists"""
    if os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        value = value.strip().strip('"').strip("'")
                        if key and not os.environ.get(key):  # Don't override existing env vars
                            os.environ[key] = value

# Try to auto-load from .env.example if keys not in environment
if "OPENAI_API_KEY" not in os.environ:
    load_env_file()

# Get API keys from environment
if "OPENAI_API_KEY" not in os.environ:
    print("Warning: OPENAI_API_KEY not set. Create .env.example or set: export OPENAI_API_KEY='your-key'")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not set. Create .env.example or set: export GOOGLE_API_KEY='your-key'")

# Mock Waymo destinations (GPS coordinates)
WAYMO_DESTINATIONS = {
    "downtown": {"lat": 37.7749, "lng": -122.4194, "name": "Downtown SF"},
    "mission": {"lat": 37.7599, "lng": -122.4148, "name": "Mission District"},
    "marina": {"lat": 37.8030, "lng": -122.4360, "name": "Marina District"},
    "soma": {"lat": 37.7785, "lng": -122.3948, "name": "SOMA"},
    "castro": {"lat": 37.7609, "lng": -122.4350, "name": "Castro"},
    "haight": {"lat": 37.7699, "lng": -122.4469, "name": "Haight-Ashbury"}
}

@tool
def get_waymo_destination() -> Dict[str, float]:
    """
    Mock function to get current Waymo destination GPS coordinates.
    In production, this would interface with Waymo's API.

    Returns:
        Dict with lat, lng, and destination name
    """
    import random
    dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
    return WAYMO_DESTINATIONS[dest_key]

@tool
def search_places_near_destination(
    query: str,
    destination: Optional[Dict[str, float]] = None,
    radius: int = 1500
) -> List[Dict]:
    """
    Search for places near the Waymo destination using Google Places API.

    Args:
        query: What to search for (e.g., "coffee", "restaurant", "shopping")
        destination: GPS coordinates of destination (auto-fetched if None)
        radius: Search radius in meters

    Returns:
        List of places with details including reviews
    """

    # Get destination if not provided
    if destination is None:
        destination = get_waymo_destination()

    # NEW Google Places API endpoint
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours,places.reviews,places.location,places.editorialSummary"
    }

    # Map query to place type
    place_type = get_place_type(query)

    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": destination.get('lat'),
                    "longitude": destination.get('lng', destination.get('lon'))
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
                # Calculate distance from destination
                place_loc = place.get('location', {})
                if place_loc:
                    distance = calculate_distance(
                        destination.get('lat'),
                        destination.get('lng', destination.get('lon')),
                        place_loc.get('latitude'),
                        place_loc.get('longitude')
                    )
                else:
                    distance = 0

                places.append({
                    "name": place.get('displayName', {}).get('text', 'Unknown'),
                    "address": place.get('formattedAddress', 'No address'),
                    "rating": place.get('rating', 0),
                    "review_count": place.get('userRatingCount', 0),
                    "distance_meters": distance,
                    "distance_text": format_distance(distance),
                    "open_now": place.get('currentOpeningHours', {}).get('openNow'),
                    "summary": place.get('editorialSummary', {}).get('text', ''),
                    "reviews": place.get('reviews', [])[:3]  # Get top 3 reviews
                })

            # Sort by distance
            places.sort(key=lambda x: x['distance_meters'])
            return places
        else:
            print(f"Google Places API error: {response.status_code}")
            return []

    except Exception as e:
        print(f"Error calling Google Places: {e}")
        return []

def get_place_type(query: str) -> str:
    """Map query to Google Places API type"""
    query_lower = query.lower()

    type_map = {
        "coffee": "coffee_shop",
        "cafe": "cafe",
        "restaurant": "restaurant",
        "food": "restaurant",
        "breakfast": "breakfast_restaurant",
        "lunch": "restaurant",
        "dinner": "restaurant",
        "bar": "bar",
        "shopping": "shopping_mall",
        "grocery": "grocery_or_supermarket",
        "gas": "gas_station",
        "pharmacy": "pharmacy",
        "hotel": "lodging",
        "parking": "parking",
        "gym": "gym",
        "museum": "museum",
        "park": "park"
    }

    for key, value in type_map.items():
        if key in query_lower:
            return value

    return "restaurant"  # Default

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return int(R * c)

def format_distance(meters: int) -> str:
    """Format distance for display"""
    if meters < 100:
        return "right at your destination"
    elif meters < 500:
        return f"{meters} meters away"
    elif meters < 1000:
        return f"{meters} meters ({int(meters/60)} min walk)"
    else:
        km = meters / 1000
        walk_time = int(meters / 80)  # ~80m per minute walking
        return f"{km:.1f} km ({walk_time} min walk)"

@tool
def summarize_reviews(places: List[Dict]) -> str:
    """
    Summarize reviews for top places using OpenAI.

    Args:
        places: List of places with review data

    Returns:
        Natural language summary of reviews
    """
    if not places:
        return "No places found to summarize."

    # Build review summary prompt
    review_text = ""
    for i, place in enumerate(places[:3], 1):
        review_text += f"\n{i}. {place['name']} ({place['rating']}★, {place['review_count']} reviews):\n"

        if place.get('summary'):
            review_text += f"   Summary: {place['summary']}\n"

        if place.get('reviews'):
            review_text += "   Recent reviews:\n"
            for review in place['reviews'][:2]:
                if isinstance(review, dict):
                    text = review.get('text', {}).get('text', '') if isinstance(review.get('text'), dict) else review.get('text', '')
                    if text:
                        review_text += f"   - \"{text[:100]}...\"\n"

    return review_text

@tool
def format_rider_response(
    query: str,
    places: List[Dict],
    destination_name: str = "your destination"
) -> str:
    """
    Format the complete response for the Waymo rider.

    Args:
        query: What the rider asked for
        places: List of places found
        destination_name: Name of the destination

    Returns:
        Natural, conversational response
    """
    if not places:
        return f"I couldn't find any {query} near {destination_name}."

    # Build response
    response = f"Near {destination_name}, I found {len(places)} great options for {query}:\n\n"

    # Top recommendations
    for i, place in enumerate(places[:3], 1):
        response += f"**{i}. {place['name']}** - {place['distance_text']}\n"
        response += f"   ⭐ {place['rating']} stars ({place['review_count']} reviews)\n"

        if place.get('open_now') is not None:
            status = "Open now" if place['open_now'] else "Currently closed"
            response += f"   📍 {status}\n"

        if place.get('summary'):
            response += f"   💬 \"{place['summary'][:100]}...\"\n"

        response += "\n"

    # Add quick summary
    if places[0]['distance_meters'] < 200:
        response += f"The closest, {places[0]['name']}, is practically at your destination! "
    elif places[0]['distance_meters'] < 500:
        response += f"{places[0]['name']} is just a quick {int(places[0]['distance_meters']/60)}-minute walk from where you'll be dropped off. "

    # Highest rated
    highest_rated = max(places[:3], key=lambda x: x['rating'])
    if highest_rated['rating'] >= 4.5:
        response += f"{highest_rated['name']} has exceptional reviews at {highest_rated['rating']} stars."

    return response

# Create the Strands agent with all tools
def create_waymo_rider_agent():
    """Create the integrated Waymo rider experience agent"""

    # OpenAI model configuration
    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        params={
            "temperature": 0.7,
            "max_tokens": 300
        }
    )

    # Create agent with all tools
    agent = Agent(
        name="Waymo Rider Assistant",
        model=model,
        tools=[
            get_waymo_destination,
            search_places_near_destination,
            summarize_reviews,
            format_rider_response
        ],
        system_prompt="""You are an AI assistant for Waymo autonomous vehicle riders.

        When a rider asks about places near their destination:
        1. Use get_waymo_destination to get their destination coordinates
        2. Use search_places_near_destination to find relevant places
        3. Use format_rider_response to create a helpful response
        4. Focus on distance from destination, ratings, and reviews
        5. Be conversational and helpful, like a knowledgeable local friend

        Always mention:
        - Distance/walking time from their drop-off point
        - Ratings and review highlights
        - Whether places are currently open

        Keep responses concise but informative for in-vehicle display."""
    )

    return agent

def demo():
    """Interactive demo of the Waymo rider experience"""
    print("\n🚗 Waymo Rider Experience Agent")
    print("=" * 50)
    print("Powered by: Strands + OpenAI + Google Places API")
    print("\nSimulating ride to destination...")

    # Get mock destination
    destination = get_waymo_destination()
    print(f"📍 Your destination: {destination['name']}")
    print(f"   Coordinates: ({destination['lat']:.4f}, {destination['lng']:.4f})")

    print("\n💡 Ask about places near your destination!")
    print("Examples:")
    print("  - 'What coffee shops are near my destination?'")
    print("  - 'Find good restaurants nearby'")
    print("  - 'I need a pharmacy near where I'm going'")
    print("  - 'What's good for breakfast near my stop?'")
    print("\nType 'quit' to exit\n")

    # Create agent
    agent = create_waymo_rider_agent()

    while True:
        user_input = input("🗣️  You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Thanks for riding with Waymo! Safe travels!")
            break

        try:
            # Extract what they're looking for
            query_terms = user_input.lower()

            # Search for places
            print("\n🔍 Searching near your destination...")
            places = search_places_near_destination(query_terms, destination)

            if places:
                # Format response
                response = format_rider_response(
                    query_terms,
                    places,
                    destination['name']
                )
                print(f"\n🤖 Assistant:\n{response}")
            else:
                print(f"\n🤖 Assistant: I couldn't find any matching places near {destination['name']}.")

        except Exception as e:
            print(f"\n🤖 Assistant: I can help you find places near your destination. What are you looking for?")
            print(f"(Error: {e})")

        print()

def test_automated():
    """Automated test of the Waymo rider experience"""
    print("\n🚗 Waymo Rider Experience Agent - Automated Test")
    print("=" * 50)

    # Get mock destination
    destination = get_waymo_destination()
    print(f"📍 Destination: {destination['name']}")

    # Test queries
    test_queries = [
        "coffee shops",
        "restaurants",
        "breakfast"
    ]

    for query in test_queries:
        print(f"\n🗣️  Rider asks: 'What {query} are near my destination?'")
        print("🔍 Searching...")

        places = search_places_near_destination(query, destination)

        if places:
            response = format_rider_response(query, places, destination['name'])
            print(f"\n{response}")
        else:
            print(f"No {query} found near destination.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_automated()
    else:
        demo()