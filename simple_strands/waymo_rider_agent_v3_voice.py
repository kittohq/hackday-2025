"""
Waymo Rider Experience Agent V3 - Voice-Enabled Version
Uses Web Speech API for both STT and TTS (browser-based)
"""

import os
import json
import requests
import base64
import io
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from typing import Dict, List, Optional
from datetime import datetime
import math
import openai

# Load environment variables
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

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")
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

# Google Places categories
GOOGLE_PLACES_TYPES = {
    "coffee_shop": "Coffee shops, cafes",
    "restaurant": "Restaurants, dining",
    "bar": "Bars, pubs",
    "gas_station": "Gas stations",
    "pharmacy": "Pharmacies",
    "lodging": "Hotels",
    "parking": "Parking",
    "grocery_or_supermarket": "Grocery stores",
    "atm": "ATMs",
    "bank": "Banks"
}

# ===== VOICE PROCESSING TOOLS =====
# Note: Web Speech API is handled entirely in the browser JavaScript
# These tools provide formatting and response generation

@tool
def process_voice_transcript(transcript: str) -> Dict:
    """
    Process transcribed text from Web Speech API.

    Args:
        transcript: Text transcribed by Web Speech API in browser

    Returns:
        Processed intent and context
    """
    # Simple intent extraction
    transcript_lower = transcript.lower()

    intents = {
        "coffee": ["coffee", "cafe", "starbucks", "espresso"],
        "food": ["food", "eat", "hungry", "restaurant", "lunch", "dinner"],
        "pharmacy": ["pharmacy", "medicine", "drug", "prescription"],
        "gas": ["gas", "fuel", "petrol"],
        "atm": ["atm", "cash", "money", "withdraw"]
    }

    detected_intent = "general"
    for intent, keywords in intents.items():
        if any(kw in transcript_lower for kw in keywords):
            detected_intent = intent
            break

    return {
        "transcript": transcript,
        "intent": detected_intent,
        "confidence": 0.85
    }

@tool
def format_for_speech(text: str) -> str:
    """
    Format text for natural speech output via Web Speech API.

    Args:
        text: Text to format for speech

    Returns:
        Formatted text optimized for TTS
    """
    # Clean text for natural speech
    speech_text = clean_text_for_speech(text)

    # Add SSML-like hints (Web Speech API may interpret some)
    # Keep sentences short for better synthesis
    sentences = speech_text.split('. ')
    if len(sentences) > 3:
        # Summarize long responses
        speech_text = '. '.join(sentences[:3]) + '...'

    return speech_text

def clean_text_for_speech(text: str) -> str:
    """Clean text for natural speech output"""
    # Remove markdown formatting
    text = text.replace('**', '').replace('*', '')
    text = text.replace('##', '').replace('#', '')

    # Remove emojis (optional - some voices handle them well)
    import re
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)

    # Replace bullet points with pauses
    text = text.replace('\n-', '...')
    text = text.replace('\n•', '...')

    # Add pauses for natural speech
    text = text.replace('. ', '. ... ')

    return text.strip()

@tool
def create_voice_response(places: List[Dict], destination_name: str = "your destination") -> str:
    """
    Create a voice-optimized response for places.

    Args:
        places: List of places found
        destination_name: Name of the destination

    Returns:
        Voice-optimized response text
    """
    if not places:
        return "I couldn't find any places matching your request near your destination."

    # Voice-optimized formatting (shorter, clearer)
    if len(places) == 1:
        place = places[0]
        response = f"I found {place['name']}, {place['distance_text']} from {destination_name}. "
        response += f"It has {place['rating']} stars. "
        if place.get('open_now') is not None:
            status = "It's open now" if place['open_now'] else "It's currently closed"
            response += status
        return response

    # Multiple places - keep it concise
    response = f"I found {len(places)} options near {destination_name}. "

    for i, place in enumerate(places[:3], 1):
        if i == 1:
            response += f"The closest is {place['name']}, {place['distance_text']} away. "
        elif i == 2:
            response += f"Also nearby, {place['name']}, rated {place['rating']} stars. "
        elif i == 3:
            response += f"And {place['name']}. "

    response += "Would you like more details about any of these?"

    return response

# ===== EXISTING TOOLS (from V2) =====

@tool
def get_waymo_destination() -> Dict[str, float]:
    """Get current Waymo destination GPS coordinates."""
    import random
    dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
    return WAYMO_DESTINATIONS[dest_key]

@tool
def search_places_near_destination(
    query: str,
    destination: Optional[Dict[str, float]] = None,
    radius: int = 1500
) -> List[Dict]:
    """Search for places using Google Places API."""

    if destination is None:
        destination = get_waymo_destination()

    # Determine place type using the intent mapper
    place_type = map_to_google_place_type(query)

    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.currentOpeningHours,places.location"
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

        if response.status_code == 200:
            data = response.json()
            places = []

            for place in data.get('places', []):
                place_loc = place.get('location', {})
                if place_loc:
                    distance = calculate_distance(
                        destination.get('lat'),
                        destination.get('lng'),
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
                    "detected_category": place_type
                })

            places.sort(key=lambda x: x['distance_meters'])
            return places
        else:
            return []

    except Exception as e:
        print(f"Error calling Google Places: {e}")
        return []

def map_to_google_place_type(query: str) -> str:
    """Map query to Google Places type using simple keyword matching"""
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
        "drink": "bar",
        "gas": "gas_station",
        "pharmacy": "pharmacy",
        "medicine": "pharmacy",
        "hotel": "lodging",
        "sleep": "lodging",
        "park": "parking",
        "atm": "atm",
        "cash": "atm",
        "bank": "bank",
        "grocery": "grocery_or_supermarket",
        "store": "grocery_or_supermarket"
    }

    for key, value in type_map.items():
        if key in query_lower:
            return value

    return "restaurant"  # Default

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

# ===== VOICE-ENABLED AGENT =====

def create_voice_agent():
    """Create the voice-enabled Waymo agent"""

    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        params={
            "temperature": 0.7,
            "max_tokens": 150  # Keep responses short for voice
        }
    )

    agent = Agent(
        name="Waymo Voice Assistant",
        model=model,
        tools=[
            # Voice processing
            process_voice_transcript,
            format_for_speech,
            create_voice_response,
            # Location & Search
            get_waymo_destination,
            search_places_near_destination
        ],
        system_prompt="""You are a voice assistant for Waymo autonomous vehicle riders.

        VOICE INTERACTION RULES:
        1. Keep responses under 2 sentences for voice
        2. Use natural, conversational language
        3. Avoid technical terms and acronyms
        4. Lead with most important info (name, distance)
        5. Ask clarifying questions if unclear

        When presenting places:
        - Say the name and distance first
        - Mention rating if 4+ stars
        - Skip addresses unless asked
        - Use "a couple minutes walk" instead of exact meters

        Always be conversational and helpful."""
    )

    return agent

# ===== DEMO FUNCTIONS =====

def test_voice():
    """Test voice components"""
    print("\n🎤 Testing Voice Integration (Web Speech API)")
    print("=" * 50)

    # Test speech formatting
    print("\n1. Testing Speech Formatting...")
    test_text = "Hello! I found three coffee shops near your destination. The closest is Blue Bottle, just two minutes away."

    formatted = format_for_speech(test_text)
    print(f"✅ Original: {test_text}")
    print(f"✅ Formatted: {formatted}")

    # Test transcript processing
    print("\n2. Testing Transcript Processing...")
    test_transcripts = [
        "I need coffee",
        "Where can I get food?",
        "Find me a pharmacy"
    ]

    for transcript in test_transcripts:
        result = process_voice_transcript(transcript)
        print(f"   '{transcript}' -> Intent: {result['intent']}")

    # Test voice response formatting
    print("\n3. Testing Voice Response Formatting...")
    mock_places = [
        {
            "name": "Blue Bottle Coffee",
            "distance_meters": 200,
            "distance_text": "200 meters away",
            "rating": 4.5,
            "review_count": 100,
            "open_now": True
        },
        {
            "name": "Starbucks",
            "distance_meters": 500,
            "distance_text": "500 meters away",
            "rating": 3.8,
            "review_count": 50,
            "open_now": True
        }
    ]

    voice_response = create_voice_response(mock_places, "Mission District")
    print(f"   Voice Response: {voice_response[:100]}...")
    print(f"   Formatted for speech: {format_for_speech(voice_response)[:100]}...")

def demo_voice_interaction():
    """Demo the complete voice interaction flow"""
    print("\n🚗 Waymo Voice Assistant Demo")
    print("=" * 50)

    # Get destination
    destination = get_waymo_destination()
    print(f"📍 Your destination: {destination['name']}")

    # Simulate voice queries
    voice_queries = [
        "I need coffee",
        "Where can I get food?",
        "I need a pharmacy"
    ]

    for query in voice_queries:
        print(f"\n🎤 User says: '{query}'")

        # Search for places
        places = search_places_near_destination(query, destination)

        # Create voice response
        response = create_voice_response(places, destination['name'])
        print(f"🔊 Assistant: {response}")

        # Generate audio (optional)
        # audio = synthesize_speech(response)
        # print(f"   (Generated {len(audio)} bytes of audio)")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_voice()
        elif sys.argv[1] == "demo":
            demo_voice_interaction()
    else:
        demo_voice_interaction()