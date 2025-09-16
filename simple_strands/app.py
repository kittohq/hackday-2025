"""
Simple Flask app for Waymo Rider Agent V2
Provides web interface with voice-ready UI
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import json
import random
from waymo_rider_agent_v2 import (
    search_places_with_ai,
    create_intent_mapping_agent,
    WAYMO_DESTINATIONS,
    GOOGLE_PLACES_TYPES,
    format_ai_response,
    load_env_file
)

# Load environment variables
load_env_file()

app = Flask(__name__)
CORS(app)

# Create the intent mapper once
intent_mapper = create_intent_mapping_agent()

# Store current destination
current_destination = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waymo Rider Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }

        .destination {
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }

        .destination-label {
            font-size: 12px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .destination-name {
            font-size: 20px;
            font-weight: bold;
            margin-top: 5px;
        }

        .coords {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 5px;
            font-family: monospace;
        }

        .chat-area {
            height: 500px;
            overflow-y: auto;
            padding: 25px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 25px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            text-align: right;
        }

        .message.assistant {
            text-align: left;
        }

        .message-bubble {
            display: inline-block;
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 18px;
            line-height: 1.5;
        }

        .user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .assistant .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .place-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin: 12px 0;
            border-left: 4px solid #667eea;
        }

        .place-name {
            font-weight: bold;
            color: #333;
            font-size: 16px;
            margin-bottom: 6px;
        }

        .place-details {
            font-size: 14px;
            color: #666;
            margin-top: 6px;
            line-height: 1.4;
        }

        .place-distance {
            color: #667eea;
            font-weight: 500;
        }

        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        #userInput {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        #userInput:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            padding: 12px 24px;
            border-radius: 25px;
            border: none;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }

        .btn-send {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .voice-controls {
            display: flex;
            gap: 10px;
            justify-content: center;
        }

        .btn-voice {
            background: #f8f9fa;
            border: 2px solid #667eea;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-voice.recording {
            background: #ff4444;
            border-color: #ff4444;
            color: white;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255,68,68,0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255,68,68,0); }
            100% { box-shadow: 0 0 0 0 rgba(255,68,68,0); }
        }

        .examples {
            padding: 0 20px 20px;
            background: white;
        }

        .example-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .chip {
            background: #f0f0f0;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
            user-select: none;
        }

        .chip:hover {
            background: #e0e0e0;
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(102,126,234,0.3);
        }

        .chip:active {
            transform: translateY(0);
            box-shadow: none;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .loading.active {
            display: block;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Waymo Rider Assistant</h1>
            <div class="destination">
                <div class="destination-label">Your Destination</div>
                <div class="destination-name" id="destName">Loading...</div>
                <div class="coords" id="destCoords"></div>
            </div>
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-bubble">
                    👋 Hello! I'm your Waymo assistant. I can help you find places near your destination. What are you looking for?
                </div>
            </div>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #666;">Understanding your request...</p>
        </div>

        <div class="examples">
            <div style="margin-bottom: 10px; color: #666; font-size: 14px; text-align: center;">
                Quick searches - tap to try:
            </div>
            <div class="example-chips">
                <div class="chip" onclick="sendExample('I need coffee')">☕ Coffee</div>
                <div class="chip" onclick="sendExample('Where can I get breakfast?')">🍳 Breakfast</div>
                <div class="chip" onclick="sendExample('I\\\'m starving')">🍔 Food</div>
                <div class="chip" onclick="sendExample('Need to fill up my tank')">⛽ Gas</div>
                <div class="chip" onclick="sendExample('Where\\\'s a pharmacy?')">💊 Pharmacy</div>
                <div class="chip" onclick="sendExample('I\\\'m exhausted, need a hotel')">🏨 Hotel</div>
                <div class="chip" onclick="sendExample('Where can I grab a drink?')">🍺 Bar</div>
                <div class="chip" onclick="sendExample('Need an ATM')">💳 ATM</div>
            </div>
        </div>

        <div class="input-area">
            <div class="input-wrapper">
                <input type="text" id="userInput" placeholder="Ask about places near your destination..."
                       onkeypress="if(event.key==='Enter') sendMessage()">
                <button class="btn btn-send" onclick="sendMessage()">Send</button>
            </div>
            <div class="voice-controls">
                <button class="btn btn-voice" id="voiceBtn" onclick="toggleVoice()">
                    🎤 <span id="voiceText">Hold to speak (coming soon)</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        let isRecording = false;
        let currentDestination = null;

        // Load destination on startup
        async function loadDestination() {
            try {
                const response = await fetch('/api/destination');
                const data = await response.json();
                currentDestination = data;
                document.getElementById('destName').textContent = data.name;
                document.getElementById('destCoords').textContent =
                    `📍 ${data.lat.toFixed(4)}, ${data.lng.toFixed(4)}`;
            } catch (error) {
                console.error('Error loading destination:', error);
            }
        }

        function sendExample(text) {
            // Set the input value
            const input = document.getElementById('userInput');
            input.value = text;

            // Flash the input to show it was filled
            input.style.borderColor = '#667eea';
            input.style.boxShadow = '0 0 10px rgba(102,126,234,0.3)';

            setTimeout(() => {
                input.style.borderColor = '';
                input.style.boxShadow = '';
            }, 300);

            // Send the message
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();

            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';

            // Show loading
            document.getElementById('loading').classList.add('active');

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: message })
                });

                const data = await response.json();

                // Hide loading
                document.getElementById('loading').classList.remove('active');

                // Add assistant response
                if (data.places && data.places.length > 0) {
                    addPlacesResponse(data);
                } else {
                    addMessage(data.response || "I couldn't find any places matching your request.", 'assistant');
                }
            } catch (error) {
                document.getElementById('loading').classList.remove('active');
                addMessage("Sorry, I encountered an error. Please try again.", 'assistant');
                console.error('Error:', error);
            }
        }

        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;

            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            bubbleDiv.textContent = text;

            messageDiv.appendChild(bubbleDiv);
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function addPlacesResponse(data) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';

            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';

            // Add intro text
            const intro = document.createElement('div');
            intro.textContent = `I found ${data.places.length} ${data.category.replace('_', ' ')}s near ${currentDestination.name}:`;
            intro.style.marginBottom = '10px';
            bubbleDiv.appendChild(intro);

            // Add place cards
            data.places.slice(0, 3).forEach(place => {
                const card = document.createElement('div');
                card.className = 'place-card';

                const name = document.createElement('div');
                name.className = 'place-name';
                name.textContent = place.name;

                const details = document.createElement('div');
                details.className = 'place-details';
                details.innerHTML = `
                    <span class="place-distance">${place.distance_text}</span> •
                    ⭐ ${place.rating} (${place.review_count} reviews)
                    ${place.open_now !== undefined ? (place.open_now ? ' • 🟢 Open' : ' • 🔴 Closed') : ''}
                `;

                card.appendChild(name);
                card.appendChild(details);
                bubbleDiv.appendChild(card);
            });

            messageDiv.appendChild(bubbleDiv);
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function toggleVoice() {
            const btn = document.getElementById('voiceBtn');
            const text = document.getElementById('voiceText');

            if (!isRecording) {
                btn.classList.add('recording');
                text.textContent = 'Recording... (coming soon)';
                isRecording = true;
                // Voice recording will be implemented here
                setTimeout(() => {
                    btn.classList.remove('recording');
                    text.textContent = 'Hold to speak (coming soon)';
                    isRecording = false;
                }, 2000);
            }
        }

        // Initialize on load
        window.onload = () => {
            loadDestination();
            document.getElementById('userInput').focus();

            // Add keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + K to focus input
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    document.getElementById('userInput').focus();
                }
            });
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/destination')
def get_destination():
    global current_destination
    # Get random destination
    dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
    current_destination = WAYMO_DESTINATIONS[dest_key]
    return jsonify(current_destination)

@app.route('/api/search', methods=['POST'])
def search():
    global current_destination

    data = request.json
    query = data.get('query', '')

    if not current_destination:
        dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
        current_destination = WAYMO_DESTINATIONS[dest_key]

    try:
        # Use AI to determine intent
        result = intent_mapper(f"What Google Places category best matches: '{query}'? Reply with ONLY the category key.")
        place_type = str(result).strip().replace('"', '').replace("'", "")

        # Validate category
        if place_type not in GOOGLE_PLACES_TYPES:
            for key in GOOGLE_PLACES_TYPES.keys():
                if key in place_type or place_type in key:
                    place_type = key
                    break
            else:
                place_type = "restaurant"

        # Search for places
        places = search_places_with_ai(query, current_destination)

        # Add detected category to places
        for place in places:
            place['detected_category'] = place_type

        return jsonify({
            'places': places,
            'category': place_type,
            'destination': current_destination['name'],
            'response': format_ai_response(query, places, current_destination['name'])
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'response': "I'm having trouble understanding. Could you try rephrasing?"
        }), 500

if __name__ == '__main__':
    print("\n🚀 Starting Waymo Rider Assistant Web Interface")
    print("📍 Open http://localhost:5001 in your browser")
    print("🎤 Voice support coming soon!\n")
    app.run(debug=True, host='0.0.0.0', port=5001)