#!/usr/bin/env python3
"""
Test script to verify TTS and STT functionality
"""

import requests
import json
import sys

def test_voice_api():
    """Test the voice API endpoint"""
    url = "http://localhost:5004/api/voice"

    test_cases = [
        {"transcript": "I need coffee"},
        {"transcript": "Where can I get gas?"},
        {"transcript": "Find me a pharmacy nearby"}
    ]

    print("🎤 Testing Voice API Endpoints")
    print("=" * 50)

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test['transcript']}'")
        print("-" * 30)

        try:
            response = requests.post(url, json=test)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received")
                print(f"   Speech text: {data.get('speech_text', 'N/A')[:100]}...")
                print(f"   Places found: {len(data.get('places', []))}")

                # Verify that speech_text is present for TTS
                if 'speech_text' in data:
                    print(f"   ✅ TTS text ready: '{data['speech_text'][:50]}...'")
                else:
                    print(f"   ❌ No TTS text generated")

            else:
                print(f"❌ Error: Status code {response.status_code}")

        except Exception as e:
            print(f"❌ Failed: {str(e)}")

    print("\n" + "=" * 50)
    print("📍 To test in browser:")
    print("   1. Open http://localhost:5004")
    print("   2. Click the microphone button")
    print("   3. Speak your request")
    print("   4. Listen for the voice response")

def test_search_api():
    """Test the regular search API"""
    url = "http://localhost:5004/api/search"

    print("\n📝 Testing Search API (Quick Chips)")
    print("=" * 50)

    response = requests.post(url, json={"query": "coffee shops"})
    if response.status_code == 200:
        data = response.json()
        print("✅ Search API working")
        print(f"   Places found: {len(data.get('places', []))}")
        if 'speech_text' in data:
            print(f"   ✅ Speech text included: '{data['speech_text'][:50]}...'")
    else:
        print(f"❌ Search API failed: {response.status_code}")

def check_browser_compatibility():
    """Print browser compatibility info"""
    print("\n🌐 Browser Compatibility for Voice Features:")
    print("=" * 50)
    print("✅ Chrome/Chromium: Full support for Web Speech API")
    print("✅ Edge: Full support for Web Speech API")
    print("⚠️  Safari: Limited support (may need to enable in settings)")
    print("❌ Firefox: No Web Speech API support (STT won't work)")
    print("\nFor best experience, use Chrome or Edge browser.")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎤 WAYMO VOICE ASSISTANT - FEATURE TEST")
    print("=" * 60)

    try:
        # Test voice endpoint
        test_voice_api()

        # Test search endpoint
        test_search_api()

        # Show browser compatibility
        check_browser_compatibility()

        print("\n✅ All tests completed!")
        print("\n🚀 Voice features are ready for testing!")
        print("   Open http://localhost:5004 in Chrome/Edge browser")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("   Make sure app_voice.py is running on port 5004")
        sys.exit(1)