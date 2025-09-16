"""
Hackathon-Ready Places Agent with Strands
Works with mock data for demo (no API needed!)
"""

import os
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, List
import math

# Set OpenAI key from environment
# export OPENAI_API_KEY="your-key-here"

@tool
def search_places(
    query: str,
    location: Dict[str, float],
    radius_meters: int = 2000
) -> List[Dict]:
    """
    Search for places near a location.

    Args:
        query: What to search for (coffee, restaurant, gas, etc.)
        location: Dict with 'lat' and 'lng' keys
        radius_meters: Search radius in meters

    Returns:
        List of places with details
    """

    # Calculate mock distances based on location
    base_lat = location.get('lat', 37.7749)
    base_lng = location.get('lng', location.get('lon', -122.4194))

    # Mock database of places
    places_db = {
        "coffee": [
            {"name": "Blue Bottle Coffee", "lat": base_lat + 0.002, "lng": base_lng + 0.001,
             "address": "300 Webster St", "rating": 4.5, "review_count": 523, "price": "$$"},
            {"name": "Ritual Coffee Roasters", "lat": base_lat + 0.004, "lng": base_lng - 0.002,
             "address": "432 Octavia St", "rating": 4.3, "review_count": 312, "price": "$$"},
            {"name": "Starbucks", "lat": base_lat - 0.001, "lng": base_lng + 0.001,
             "address": "2727 Mission St", "rating": 3.8, "review_count": 156, "price": "$"},
            {"name": "Philz Coffee", "lat": base_lat + 0.003, "lng": base_lng + 0.003,
             "address": "549 Castro St", "rating": 4.4, "review_count": 892, "price": "$$"}
        ],
        "restaurant": [
            {"name": "Tartine Bakery", "lat": base_lat + 0.002, "lng": base_lng - 0.003,
             "address": "600 Guerrero St", "rating": 4.4, "review_count": 3421, "price": "$$"},
            {"name": "La Taqueria", "lat": base_lat - 0.003, "lng": base_lng + 0.002,
             "address": "2889 Mission St", "rating": 4.6, "review_count": 2156, "price": "$"},
            {"name": "State Bird Provisions", "lat": base_lat + 0.005, "lng": base_lng - 0.001,
             "address": "1529 Fillmore St", "rating": 4.5, "review_count": 1832, "price": "$$$"}
        ],
        "gas": [
            {"name": "Shell Station", "lat": base_lat - 0.002, "lng": base_lng - 0.001,
             "address": "598 Bryant St", "rating": 3.5, "review_count": 89, "price": "$"},
            {"name": "Chevron", "lat": base_lat + 0.001, "lng": base_lng + 0.004,
             "address": "1200 Van Ness Ave", "rating": 3.7, "review_count": 124, "price": "$"}
        ]
    }

    # Find matching places
    query_lower = query.lower()
    results = []

    for category, places in places_db.items():
        if category in query_lower or query_lower in category:
            results.extend(places)
            break

    # If no category match, search all
    if not results:
        for places in places_db.values():
            for place in places:
                if query_lower in place['name'].lower():
                    results.append(place)

    # Default if still no results
    if not results:
        results = places_db.get("restaurant", [])

    # Calculate distances and filter by radius
    filtered_results = []
    for place in results:
        distance = calculate_distance(
            base_lat, base_lng,
            place['lat'], place['lng']
        )
        if distance <= radius_meters:
            place['distance_meters'] = distance
            place['distance_text'] = format_distance(distance)
            filtered_results.append(place)

    # Sort by distance
    filtered_results.sort(key=lambda x: x['distance_meters'])

    return filtered_results[:5]  # Return top 5

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """Calculate distance between two points in meters"""
    # Simplified distance calculation
    lat_diff = abs(lat2 - lat1)
    lng_diff = abs(lng2 - lng1)
    # Rough approximation: 1 degree ≈ 111km
    distance_km = math.sqrt(lat_diff**2 + lng_diff**2) * 111
    return int(distance_km * 1000)  # Convert to meters

def format_distance(meters: int) -> str:
    """Format distance for display"""
    miles = meters / 1609.34
    if miles < 0.1:
        return "just ahead"
    elif miles < 1:
        return f"{miles:.1f} miles"
    else:
        return f"{int(miles)} miles"

@tool
def format_places_response(places: List[Dict], add_stop: bool = True) -> str:
    """
    Format places into natural language response.

    Args:
        places: List of places from search
        add_stop: Whether to ask about adding a stop

    Returns:
        Natural language response
    """
    if not places:
        return "I couldn't find any places matching your request nearby."

    if len(places) == 1:
        p = places[0]
        response = f"I found {p['name']} {p['distance_text']} away with a {p['rating']} star rating."
        if add_stop:
            response += " Would you like me to add this as a stop?"
        return response

    # Multiple places
    response = f"I found {len(places)} options nearby:\n\n"

    for i, p in enumerate(places[:3], 1):
        response += f"{i}. {p['name']} - {p['distance_text']} away, {p['rating']}★ ({p['review_count']} reviews)\n"

    if add_stop:
        response += "\nWould you like me to add a stop at any of these?"

    return response

# Create OpenAI model (cheap!)
model = OpenAIModel(
    model_id="gpt-3.5-turbo",
    params={"temperature": 0.7, "max_tokens": 150}
)

# Create the Strands agent
agent = Agent(
    name="Places Assistant",
    model=model,
    tools=[search_places, format_places_response],
    system_prompt="""You are a helpful assistant for autonomous vehicle riders.
    When users ask about places, use search_places to find options.
    Always mention distance and ratings.
    Be conversational and helpful."""
)

def demo():
    """Run interactive demo"""
    print("\n🚗 Hackathon Places Agent (with Mock Data)")
    print("=" * 50)
    print("Using: Strands SDK + OpenAI + Mock Places Data")
    print("\nExample queries:")
    print("  - 'Find coffee nearby'")
    print("  - 'I need food'")
    print("  - 'Where's the nearest gas station?'")
    print("\nType 'quit' to exit\n")

    # Default location (San Francisco)
    location = {"lat": 37.7749, "lng": -122.4194}

    while True:
        user_input = input("👤 You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Safe travels!")
            break

        # Process with agent
        try:
            # For demo, manually orchestrate
            # In production, agent would handle this automatically

            # Determine search term
            search_term = "restaurant"  # default
            if "coffee" in user_input.lower():
                search_term = "coffee"
            elif "gas" in user_input.lower():
                search_term = "gas"
            elif "food" in user_input.lower() or "eat" in user_input.lower():
                search_term = "restaurant"

            # Search
            places = search_places(search_term, location, 2000)

            # Format response
            response = format_places_response(places)

            print(f"\n🤖 Agent: {response}\n")

        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    demo()