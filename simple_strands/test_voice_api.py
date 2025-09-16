#!/usr/bin/env python3
"""
Test the voice API endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_destination():
    """Test getting destination"""
    print("\n1. Testing /api/destination...")
    response = requests.get(f"{BASE_URL}/api/destination")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got destination: {data['name']}")
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        return None

def test_voice_endpoint(transcript="I need coffee"):
    """Test voice processing endpoint"""
    print(f"\n2. Testing /api/voice with: '{transcript}'")
    response = requests.post(
        f"{BASE_URL}/api/voice",
        json={"transcript": transcript},
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('response', '')[:100]}...")
        print(f"✅ Speech text: {data.get('speech_text', '')[:100]}...")
        if data.get('places'):
            print(f"✅ Found {len(data['places'])} places")
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        return None

def test_search_endpoint(query="Where can I get food?"):
    """Test search endpoint"""
    print(f"\n3. Testing /api/search with: '{query}'")
    response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": query},
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('response', '')[:100]}...")
        print(f"✅ Speech text: {data.get('speech_text', '')[:100]}...")
        if data.get('places'):
            print(f"✅ Found {len(data['places'])} places")
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Voice API Endpoints")
    print("=" * 50)

    # Test all endpoints
    destination = test_destination()

    if destination:
        # Test voice with different queries
        test_voice_endpoint("I need coffee")
        test_voice_endpoint("Where's the nearest pharmacy?")

        # Test search endpoint
        test_search_endpoint("I'm hungry")
        test_search_endpoint("Need gas")

    print("\n✅ All tests complete!")