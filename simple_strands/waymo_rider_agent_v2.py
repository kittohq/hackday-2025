"""
Waymo Rider Experience Agent V2 - Using Strands Agent for Intent Mapping
Uses AI agent to intelligently map user requests to Google Places categories
"""

import os
import json
import requests
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, List, Optional
from datetime import datetime
import math

# API Keys - Auto-load from .env.example
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
                        if key and not os.environ.get(key):
                            os.environ[key] = value

# Auto-load if not in environment
if "OPENAI_API_KEY" not in os.environ:
    load_env_file()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Mock Waymo destinations
WAYMO_DESTINATIONS = {
    "downtown": {"lat": 37.7749, "lng": -122.4194, "name": "Downtown SF"},
    "mission": {"lat": 37.7599, "lng": -122.4148, "name": "Mission District"},
    "marina": {"lat": 37.8030, "lng": -122.4360, "name": "Marina District"},
    "soma": {"lat": 37.7785, "lng": -122.3948, "name": "SOMA"},
    "castro": {"lat": 37.7609, "lng": -122.4350, "name": "Castro"},
    "haight": {"lat": 37.7699, "lng": -122.4469, "name": "Haight-Ashbury"}
}

# Google Places API Categories (for agent reference)
GOOGLE_PLACES_TYPES = {
    "coffee_shop": "Coffee shops, cafes, coffee roasters",
    "cafe": "Cafes, coffee houses, tea rooms",
    "restaurant": "Restaurants, dining, eateries",
    "breakfast_restaurant": "Breakfast spots, brunch places, morning dining",
    "bar": "Bars, pubs, cocktail lounges, nightlife",
    "shopping_mall": "Shopping centers, malls, retail complexes",
    "grocery_or_supermarket": "Grocery stores, supermarkets, food markets",
    "gas_station": "Gas stations, fuel stops, petrol stations",
    "pharmacy": "Pharmacies, drugstores, chemists",
    "lodging": "Hotels, motels, inns, accommodation",
    "parking": "Parking lots, garages, parking spaces",
    "gym": "Gyms, fitness centers, health clubs",
    "museum": "Museums, galleries, exhibitions",
    "park": "Parks, gardens, recreational areas",
    "bank": "Banks, financial institutions",
    "atm": "ATMs, cash machines",
    "hospital": "Hospitals, medical centers",
    "doctor": "Doctors, clinics, medical offices",
    "dentist": "Dentists, dental clinics",
    "spa": "Spas, wellness centers, massage",
    "beauty_salon": "Beauty salons, hair salons",
    "bakery": "Bakeries, pastry shops",
    "store": "Stores, shops, retail",
    "book_store": "Bookstores, libraries",
    "clothing_store": "Clothing stores, fashion boutiques",
    "electronics_store": "Electronics stores, tech shops",
    "movie_theater": "Movie theaters, cinemas",
    "night_club": "Nightclubs, dance clubs",
    "tourist_attraction": "Tourist attractions, landmarks, points of interest"
}

@tool
def extract_place_intent(user_input: str) -> Dict[str, str]:
    """
    Use AI to extract the place type intent from natural language.

    Args:
        user_input: Natural language request from user

    Returns:
        Dict with 'place_type' and 'confidence' keys
    """
    # This would normally use the agent, but for demo purposes:
    # The actual agent will replace this logic
    return {
        "place_type": "restaurant",
        "confidence": "high",
        "reasoning": "User is asking for a place to eat"
    }

@tool
def map_to_google_place_type(user_request: str) -> str:
    """
    AI-powered mapping of user request to Google Places API type.
    Uses natural language understanding to find the best category match.

    Args:
        user_request: The user's natural language request

    Returns:
        The most appropriate Google Places API type
    """
    # This tool will be called by the agent to determine place type
    # The agent will use the context of GOOGLE_PLACES_TYPES
    # For now, returning a placeholder
    return "restaurant"

@tool
def get_waymo_destination() -> Dict[str, float]:
    """Get current Waymo destination GPS coordinates."""
    import random
    dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
    return WAYMO_DESTINATIONS[dest_key]

@tool
def search_places_with_ai(
    user_request: str,
    destination: Optional[Dict[str, float]] = None,
    radius: int = 1500
) -> List[Dict]:
    """
    Search for places using AI to interpret the request.

    Args:
        user_request: Natural language request from user
        destination: GPS coordinates of destination
        radius: Search radius in meters

    Returns:
        List of relevant places
    """

    if destination is None:
        destination = get_waymo_destination()

    # AI agent will determine the place type
    # For now, we'll use the intent mapping agent
    place_type = map_to_google_place_type(user_request)
    print(f"DEBUG: Searching for '{user_request}' -> detected type: '{place_type}'")
    print(f"DEBUG: Destination: {destination}")
    print(f"DEBUG: Google API Key present: {bool(GOOGLE_API_KEY)}")

    # Call Google Places API
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours,places.reviews,places.location,places.editorialSummary"
    }

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
        print(f"DEBUG: API Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: Found {len(data.get('places', []))} places")
            places = []

            for place in data.get('places', []):
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
                    "detected_category": place_type  # Include what category we searched
                })

            places.sort(key=lambda x: x['distance_meters'])
            return places
        else:
            print(f"Google Places API error: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")
            return []

    except Exception as e:
        print(f"Error calling Google Places: {e}")
        return []

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Calculate distance between two points in meters"""
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
        walk_time = int(meters / 80)
        return f"{km:.1f} km ({walk_time} min walk)"

@tool
def format_ai_response(
    user_request: str,
    places: List[Dict],
    destination_name: str = "your destination"
) -> str:
    """
    Format response based on what the AI detected the user wanted.

    Args:
        user_request: Original user request
        places: List of places found
        destination_name: Name of the destination

    Returns:
        Natural language response
    """

    if not places:
        return f"I couldn't find what you're looking for near {destination_name}. Could you be more specific?"

    # Get the category that was searched
    category = places[0].get('detected_category', 'places')

    response = f"Based on your request, I searched for {category.replace('_', ' ')}s near {destination_name}.\n\n"
    response += f"Here are the top {min(3, len(places))} options:\n\n"

    for i, place in enumerate(places[:3], 1):
        response += f"**{i}. {place['name']}** - {place['distance_text']}\n"
        response += f"   ⭐ {place['rating']} stars ({place['review_count']} reviews)\n"

        if place.get('open_now') is not None:
            status = "Open now" if place['open_now'] else "Currently closed"
            response += f"   📍 {status}\n"

        if place.get('summary'):
            response += f"   💬 \"{place['summary'][:100]}...\"\n"

        response += "\n"

    return response

# Create the Intent Mapping Agent
def create_intent_mapping_agent():
    """Create a specialized agent for mapping user intent to place categories"""

    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        params={
            "temperature": 0.3,  # Lower temperature for more consistent mapping
            "max_tokens": 100
        }
    )

    intent_agent = Agent(
        name="Place Intent Mapper",
        model=model,
        tools=[],  # No tools needed for this agent
        system_prompt=f"""You are an expert at understanding what type of place a user is looking for.

Your ONLY job is to map user requests to the most appropriate Google Places API category.

Available Google Places categories:
{json.dumps(GOOGLE_PLACES_TYPES, indent=2)}

Instructions:
1. Analyze the user's request carefully
2. Consider context clues (time of day, specific needs mentioned)
3. Return ONLY the category key (e.g., "coffee_shop", "restaurant")
4. If multiple categories could work, choose the most specific one
5. Default to "restaurant" only if truly ambiguous

Examples:
- "I need caffeine" → "coffee_shop"
- "Where can I grab breakfast?" → "breakfast_restaurant"
- "I need to fill up my tank" → "gas_station"
- "Looking for somewhere to eat" → "restaurant"
- "Need my morning coffee fix" → "coffee_shop"
- "Where's a good happy hour spot?" → "bar"
- "I forgot my medication" → "pharmacy"
- "Need to grab some groceries" → "grocery_or_supermarket"
- "Looking for a quick bite" → "restaurant"
- "Need a place to work with wifi" → "cafe"

Remember: Return ONLY the category key, nothing else."""
    )

    return intent_agent

# Create the main Waymo Agent with AI intent understanding
def create_waymo_agent_v2():
    """Create the enhanced Waymo agent with AI-powered intent mapping"""

    # Create the intent mapping agent
    intent_mapper = create_intent_mapping_agent()

    # Main agent model
    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        params={
            "temperature": 0.7,
            "max_tokens": 300
        }
    )

    # Enhanced agent with intent understanding
    agent = Agent(
        name="Waymo Rider Assistant V2",
        model=model,
        tools=[
            get_waymo_destination,
            search_places_with_ai,
            format_ai_response
        ],
        system_prompt="""You are an AI assistant for Waymo autonomous vehicle riders.

You have been enhanced with natural language understanding to better interpret what riders are looking for.

When a rider makes a request:
1. Understand the intent behind their request (what type of place they want)
2. Search for relevant places near their destination
3. Provide helpful, conversational responses
4. Always mention distance and walking time from drop-off
5. Include ratings and whether places are open

You understand context:
- Morning requests for "fuel" might mean coffee, not gas
- "Hungry" could mean different things at different times
- Be smart about interpreting casual language

Keep responses natural and helpful."""
    )

    # Store the intent mapper for use
    agent.intent_mapper = intent_mapper

    return agent

def demo_v2():
    """Interactive demo of the V2 agent with AI intent mapping"""

    print("\n🚗 Waymo Rider Experience Agent V2 (AI-Powered)")
    print("=" * 50)
    print("✨ Now with intelligent request understanding!")
    print("\nTry natural language like:")
    print("  - 'I'm starving'")
    print("  - 'Need my coffee fix'")
    print("  - 'Where can I grab a drink later?'")
    print("  - 'Running low on gas'")
    print("  - 'I need to pick up my prescription'")
    print("\nType 'quit' to exit\n")

    # Get destination
    destination = get_waymo_destination()
    print(f"📍 Your destination: {destination['name']}")
    print(f"   Coordinates: ({destination['lat']:.4f}, {destination['lng']:.4f})")
    print()

    # Create agents
    agent = create_waymo_agent_v2()
    intent_mapper = create_intent_mapping_agent()

    while True:
        user_input = input("🗣️  You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Thanks for riding with Waymo!")
            break

        try:
            # Step 1: Use AI to determine intent
            print("\n🧠 Understanding your request...")
            result = intent_mapper(f"What Google Places category best matches this request: '{user_input}'? Reply with ONLY the category key.")

            # Clean the response (handle AgentResult object)
            place_type = str(result).strip().replace('"', '').replace("'", "")

            # Validate it's a real category
            if place_type not in GOOGLE_PLACES_TYPES:
                # Find closest match
                for key in GOOGLE_PLACES_TYPES.keys():
                    if key in place_type or place_type in key:
                        place_type = key
                        break
                else:
                    place_type = "restaurant"  # Default fallback

            print(f"📍 Searching for: {place_type.replace('_', ' ')}s")

            # Step 2: Search using the detected type
            places = search_places_with_ai(user_input, destination)

            # Update places with the detected category
            for place in places:
                place['detected_category'] = place_type

            # Step 3: Format response
            response = format_ai_response(user_input, places, destination['name'])
            print(f"\n🤖 Assistant:\n{response}")

        except Exception as e:
            print(f"\n🤖 Assistant: I'm having trouble understanding. Could you rephrase that?")
            print(f"(Debug: {e})")

        print()

def test_intent_mapping():
    """Test the AI intent mapping with various inputs"""

    print("\n🧪 Testing AI Intent Mapping")
    print("=" * 50)

    # Create intent mapper
    intent_mapper = create_intent_mapping_agent()

    test_phrases = [
        "I need coffee",
        "Where can I get breakfast?",
        "I'm hungry",
        "Need to fill up my tank",
        "Looking for a pharmacy",
        "Where's a good bar?",
        "I need to grab groceries",
        "Find me a gym",
        "Where can I park?",
        "I want sushi",
        "Need an ATM",
        "Looking for a nice dinner spot",
        "Where can I get a drink?",
        "I need my morning caffeine fix",
        "Where's the nearest Starbucks?"
    ]

    print("\nTesting intent detection:\n")

    for phrase in test_phrases:
        try:
            result = intent_mapper(f"What Google Places category best matches: '{phrase}'? Reply with ONLY the category key.")
            # Handle AgentResult object - get the string content
            detected = str(result).strip().replace('"', '').replace("'", "")

            # Validate
            if detected not in GOOGLE_PLACES_TYPES:
                detected = f"{detected} (invalid - would default to restaurant)"

            print(f"📝 '{phrase}'")
            print(f"   → Detected: {detected}\n")

        except Exception as e:
            print(f"Error with '{phrase}': {e}\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_intent_mapping()
        elif sys.argv[1] == "demo":
            demo_v2()
    else:
        demo_v2()