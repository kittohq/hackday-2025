"""
Voice-Enabled Flask App for Waymo Rider Agent
Uses OpenAI Whisper for STT and Web Speech API for TTS
Single Strands agent with voice tools
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import os
import json
import random
import base64
import tempfile
import openai
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

# Initialize OpenAI client for Whisper
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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
    <title>Waymo Voice Assistant</title>
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

        .voice-status {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .status-text {
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-icon {
            font-size: 24px;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.2); }
            100% { transform: scale(1); }
        }

        .recording .status-icon {
            animation: pulse 1s infinite;
            color: #ff4444;
        }

        .speaking .status-icon {
            animation: pulse 1.5s infinite;
            color: #44ff44;
        }

        .chat-area {
            height: 400px;
            overflow-y: auto;
            padding: 25px;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
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
            margin-left: auto;
            display: block;
        }

        .assistant .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .voice-controls {
            padding: 30px;
            background: white;
            display: flex;
            flex-direction: column;
            gap: 20px;
            align-items: center;
        }

        .voice-button {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(102,126,234,0.4);
        }

        .voice-button:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 30px rgba(102,126,234,0.6);
        }

        .voice-button.recording {
            background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
            animation: glow 1.5s infinite;
        }

        @keyframes glow {
            0% { box-shadow: 0 0 20px rgba(255,68,68,0.6); }
            50% { box-shadow: 0 0 40px rgba(255,68,68,0.8); }
            100% { box-shadow: 0 0 20px rgba(255,68,68,0.6); }
        }

        .voice-button-icon {
            font-size: 48px;
        }

        .voice-button-text {
            font-size: 14px;
            font-weight: 600;
        }

        .text-input-section {
            margin: 20px 0;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }

        .input-wrapper {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .text-input {
            flex: 1;
            padding: 12px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            background: rgba(255,255,255,0.95);
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }

        .text-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102,126,234,0.3);
        }

        .send-button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .send-button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }

        .or-divider {
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin: 15px 0;
            font-size: 14px;
            font-weight: 500;
        }

        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }

        .chip {
            background: #f0f0f0;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }

        .chip:hover {
            background: #e0e0e0;
            border-color: #667eea;
            transform: translateY(-2px);
        }

        .audio-visualizer {
            width: 100%;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            padding: 10px;
        }

        .bar {
            width: 4px;
            background: #667eea;
            border-radius: 2px;
            transition: height 0.2s;
        }

        .recording .bar {
            background: #ff4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Waymo Voice Assistant</h1>
            <div class="voice-status">
                <div class="status-text">
                    <span class="status-icon" id="statusIcon">🎤</span>
                    <span id="statusText">Ready to listen</span>
                </div>
            </div>
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-bubble">
                    👋 Hi! I'm your Waymo voice assistant. Press the microphone button and tell me what you're looking for near your destination.
                </div>
            </div>
        </div>

        <div class="voice-controls">
            <div class="text-input-section">
                <div class="input-wrapper">
                    <input type="text" id="textInput" class="text-input" placeholder="Type your request here (e.g., 'I need coffee')"
                           onkeypress="if(event.key==='Enter') sendTextQuery()">
                    <button class="send-button" onclick="sendTextQuery()">Send</button>
                </div>
                <div class="or-divider">— OR —</div>
            </div>

            <button class="voice-button" id="voiceButton" onclick="toggleRecording()">
                <span class="voice-button-icon" id="voiceIcon">🎤</span>
                <span class="voice-button-text" id="voiceText">Tap to speak</span>
            </button>

            <div class="audio-visualizer" id="visualizer" style="display: none;">
                <div class="bar" style="height: 20px;"></div>
                <div class="bar" style="height: 40px;"></div>
                <div class="bar" style="height: 30px;"></div>
                <div class="bar" style="height: 50px;"></div>
                <div class="bar" style="height: 35px;"></div>
                <div class="bar" style="height: 45px;"></div>
                <div class="bar" style="height: 25px;"></div>
                <div class="bar" style="height: 40px;"></div>
                <div class="bar" style="height: 30px;"></div>
            </div>

            <div class="quick-actions">
                <div class="chip" onclick="sendVoiceQuery('I need coffee')">☕ Coffee</div>
                <div class="chip" onclick="sendVoiceQuery('Where can I get food?')">🍔 Food</div>
                <div class="chip" onclick="sendVoiceQuery('I need a pharmacy')">💊 Pharmacy</div>
                <div class="chip" onclick="sendVoiceQuery('Where is the nearest gas station?')">⛽ Gas</div>
            </div>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let currentDestination = null;
        let audioContext;
        let analyser;
        let animationId;

        // Initialize audio context
        function initAudio() {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        // Initialize speech synthesis
        const synth = window.speechSynthesis;
        let voices = [];

        function loadVoices() {
            voices = synth.getVoices();
            console.log('Available voices:', voices.length);
        }

        // Load voices when ready
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
        loadVoices();

        // Text-to-speech using Web Speech API
        function speak(text) {
            // Cancel any ongoing speech
            synth.cancel();

            const utterance = new SpeechSynthesisUtterance(text);

            // Select a good voice (prefer Google or Microsoft voices)
            const preferredVoice = voices.find(v =>
                v.name.includes('Google') ||
                v.name.includes('Microsoft') ||
                v.name.includes('Samantha') ||
                v.name.includes('Alex')
            ) || voices[0];

            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            utterance.rate = 1.1;  // Slightly faster
            utterance.pitch = 1.0;
            utterance.volume = 1.0;

            // Update UI during speech
            utterance.onstart = () => {
                updateStatus('speaking', '🔊', 'Speaking...');
                document.querySelector('.voice-status').classList.add('speaking');
            };

            utterance.onend = () => {
                updateStatus('ready', '🎤', 'Ready to listen');
                document.querySelector('.voice-status').classList.remove('speaking');
            };

            utterance.onerror = (event) => {
                console.error('Speech error:', event);
                updateStatus('ready', '🎤', 'Ready to listen');
            };

            synth.speak(utterance);
        }

        // Web Speech API for Speech Recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition;

        function createRecognition() {
            if (!SpeechRecognition) return null;

            const rec = new SpeechRecognition();
            rec.continuous = false;
            rec.interimResults = true;
            rec.lang = 'en-US';

            rec.onstart = () => {
                isRecording = true;
                updateStatus('recording', '🔴', 'Listening...');
                document.getElementById('voiceButton').classList.add('recording');
                document.getElementById('voiceIcon').textContent = '⏹️';
                document.getElementById('voiceText').textContent = 'Listening...';
                document.getElementById('visualizer').style.display = 'flex';
            };

            rec.onresult = (event) => {
                const last = event.results.length - 1;
                const transcript = event.results[last][0].transcript;

                if (event.results[last].isFinal) {
                    // Final transcript ready
                    console.log('Final transcript:', transcript);
                    sendTranscriptToServer(transcript);
                } else {
                    // Show interim results
                    updateStatus('recording', '🔴', `"${transcript}"`);
                }
            };

            rec.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                updateStatus('error', '❌', 'Error: ' + event.error);
                stopRecording();
            };

            rec.onend = () => {
                console.log('Recognition ended');
                stopRecording();
                // Reset recognition for next use
                isRecording = false;
            };

            return rec;
        }

        // Initialize recognition at startup
        if (SpeechRecognition) {
            recognition = createRecognition();
        }

        // Start/stop recording
        function toggleRecording() {
            if (!isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        }

        function startRecording() {
            if (!SpeechRecognition) {
                alert('Speech recognition not supported in this browser. Try Chrome or Edge.');
                return;
            }

            // Create fresh recognition instance for each recording
            recognition = createRecognition();
            if (!recognition) {
                alert('Failed to initialize speech recognition.');
                return;
            }

            try {
                recognition.start();

                // Animate visualizer bars randomly
                if (!animationId) {
                    animateVisualizer();
                }

            } catch (error) {
                console.error('Error starting recognition:', error);
                alert('Error accessing speech recognition.');
            }
        }

        function stopRecording() {
            if (recognition && isRecording) {
                recognition.stop();
                isRecording = false;

                // Stop visualization
                if (animationId) {
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }
                document.getElementById('visualizer').style.display = 'none';

                // Update UI
                document.getElementById('voiceButton').classList.remove('recording');
                document.getElementById('voiceIcon').textContent = '🎤';
                document.getElementById('voiceText').textContent = 'Tap to speak';
            }
        }

        // Animate visualizer bars
        function animateVisualizer() {
            const bars = document.querySelectorAll('.bar');

            function animate() {
                bars.forEach((bar) => {
                    const height = 10 + Math.random() * 40;
                    bar.style.height = height + 'px';
                });

                animationId = requestAnimationFrame(animate);
            }

            animate();
        }

        // Send transcript to server
        async function sendTranscriptToServer(transcript) {
            console.log('Sending transcript to server:', transcript);
            addMessage(transcript, 'user');
            updateStatus('processing', '⏳', 'Searching...');

            try {
                console.log('Making API request...');
                const response = await fetch('/api/voice', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ transcript: transcript })
                });

                console.log('Response status:', response.status);
                const data = await response.json();
                console.log('Response data:', data);

                if (data.response) {
                    addMessage(data.response, 'assistant');
                    // Always speak for voice responses (when speech_text is available)
                    if (data.speech_text) {
                        console.log('TTS: Speaking response:', data.speech_text);
                        speak(data.speech_text);
                    }
                }

                updateStatus('ready', '🎤', 'Ready to listen');

            } catch (error) {
                console.error('Error:', error);
                updateStatus('error', '❌', 'Error processing request');
                setTimeout(() => {
                    updateStatus('ready', '🎤', 'Ready to listen');
                }, 3000);
            }
        }

        // Send text query from input field
        async function sendTextQuery() {
            const input = document.getElementById('textInput');
            const text = input.value.trim();

            if (!text) return;

            input.value = '';
            sendVoiceQuery(text, false);  // false = don't use TTS for typed input
        }

        // Send text query as if it was spoken
        async function sendVoiceQuery(text, useTTS = true) {
            addMessage(text, 'user');
            updateStatus('processing', '⏳', 'Searching...');

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: text })
                });

                const data = await response.json();

                if (data.response) {
                    addMessage(data.response, 'assistant');
                    // Always speak for voice responses (when speech_text is available)
                    if (data.speech_text) {
                        console.log('TTS: Speaking response:', data.speech_text);
                        speak(data.speech_text);
                    }
                }

            } catch (error) {
                console.error('Error:', error);
                updateStatus('error', '❌', 'Error');
            }
        }

        // Update status display
        function updateStatus(state, icon, text) {
            document.getElementById('statusIcon').textContent = icon;
            document.getElementById('statusText').textContent = text;

            const statusEl = document.querySelector('.voice-status');
            statusEl.classList.remove('recording', 'speaking');
            if (state === 'recording' || state === 'speaking') {
                statusEl.classList.add(state);
            }
        }

        // Add message to chat
        function addMessage(text, sender) {
            const chatArea = document.getElementById('chatArea');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;

            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';

            // Format text with line breaks and proper display
            if (sender === 'assistant' && text.includes('\\n')) {
                bubbleDiv.innerHTML = text.replace(/\\n/g, '<br>');
            } else {
                bubbleDiv.textContent = text;
            }

            messageDiv.appendChild(bubbleDiv);
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        // Load destination on startup
        async function loadDestination() {
            try {
                const response = await fetch('/api/destination');
                const data = await response.json();
                currentDestination = data;
                console.log('Destination:', data);
            } catch (error) {
                console.error('Error loading destination:', error);
            }
        }

        // Initialize
        window.onload = () => {
            loadDestination();
            loadVoices();
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def generate_natural_speech(places, query, destination_name):
    """Generate natural, conversational TTS-optimized responses"""

    if not places:
        # Apologetic, helpful tone for no results
        responses = [
            f"I'm sorry, I couldn't find any places matching your request near {destination_name}.",
            f"Hmm, I didn't find anything like that around {destination_name}. Would you like to try a different search?",
            f"I couldn't locate any options near {destination_name}. Perhaps try searching for something else?"
        ]
        return random.choice(responses)

    # Single result - be specific and helpful
    if len(places) == 1:
        place = places[0]
        if place.get('open_now'):
            status = "and it's currently open"
        elif place.get('open_now') is False:
            status = "but it's closed right now"
        else:
            status = ""

        responses = [
            f"Great! I found {place['name']}, which is {place['distance_text']} from your destination. "
            f"It has a {place['rating']} star rating {status}.",

            f"I've located {place['name']} for you. It's just {place['distance_text']} away "
            f"with {place['rating']} stars from {place['review_count']} reviews {status}.",

            f"Perfect! {place['name']} is {place['distance_text']} from {destination_name}. "
            f"It's rated {place['rating']} stars {status}."
        ]
        return random.choice(responses)

    # Multiple results - be concise but informative
    closest = places[0]
    count = len(places)

    if "coffee" in query.lower():
        place_type = "coffee shops"
    elif "food" in query.lower() or "restaurant" in query.lower():
        place_type = "restaurants"
    elif "gas" in query.lower():
        place_type = "gas stations"
    elif "pharmacy" in query.lower():
        place_type = "pharmacies"
    else:
        place_type = "places"

    responses = [
        f"I found {count} {place_type} near {destination_name}. "
        f"The closest is {closest['name']}, just {closest['distance_text']} away "
        f"with a {closest['rating']} star rating.",

        f"Great news! There are {count} options nearby. "
        f"{closest['name']} is your closest choice at {closest['distance_text']}, "
        f"and it has {closest['rating']} stars.",

        f"I've located {count} {place_type} for you. "
        f"The nearest one is {closest['name']}, {closest['distance_text']} from your destination, "
        f"rated {closest['rating']} stars."
    ]

    # Add second option if available
    if len(places) > 1:
        second = places[1]
        addition = f" {second['name']} is also nearby at {second['distance_text']}."
        responses[0] += addition

    return random.choice(responses)

@app.route('/api/destination')
def get_destination():
    global current_destination
    dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
    current_destination = WAYMO_DESTINATIONS[dest_key]
    return jsonify(current_destination)

@app.route('/api/voice', methods=['POST'])
def process_voice():
    """Process voice input and return response"""
    global current_destination

    if not current_destination:
        dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
        current_destination = WAYMO_DESTINATIONS[dest_key]

    try:
        # Get transcribed text directly from Web Speech API
        data = request.json
        user_text = data.get('transcript', '')

        # Use intent mapper to determine place type
        result = intent_mapper(f"What Google Places category best matches: '{user_text}'? Reply with ONLY the category key.")
        place_type = str(result).strip().replace('"', '').replace("'", "")

        # Search for places
        places = search_places_with_ai(user_text, current_destination)

        # Create natural language voice response
        speech_text = generate_natural_speech(places, user_text, current_destination['name'])

        # For display, create a simpler formatted response without markdown
        if places:
            response = f"I found {len(places)} options near {current_destination['name']}:\n\n"
            for i, place in enumerate(places[:3], 1):
                response += f"{i}. {place['name']} - {place['distance_text']}\n"
                response += f"   ⭐ {place['rating']} stars ({place['review_count']} reviews)\n"
                if place.get('open_now') is not None:
                    status = "Open now" if place['open_now'] else "Currently closed"
                    response += f"   📍 {status}\n"
                response += "\n"
        else:
            response = speech_text

        return jsonify({
            'transcript': user_text,
            'response': response,
            'speech_text': speech_text,
            'places': places[:3] if places else []
        })

    except Exception as e:
        print(f"Voice processing error: {e}")
        return jsonify({
            'error': str(e),
            'response': "I'm having trouble understanding. Could you try again?"
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Process text search (for quick chips)"""
    global current_destination

    data = request.json
    query = data.get('query', '')

    if not current_destination:
        dest_key = random.choice(list(WAYMO_DESTINATIONS.keys()))
        current_destination = WAYMO_DESTINATIONS[dest_key]

    try:
        # Search for places
        places = search_places_with_ai(query, current_destination)

        # Create natural language voice response
        speech_text = generate_natural_speech(places, query, current_destination['name'])

        # For display, create a simpler formatted response
        if places:
            response = f"Found {len(places)} options near {current_destination['name']}:\n\n"
            for i, place in enumerate(places[:3], 1):
                response += f"{i}. {place['name']} ({place['distance_text']})\n"
                response += f"   ⭐ {place['rating']} stars\n\n"
        else:
            response = speech_text

        return jsonify({
            'places': places,
            'response': response,
            'speech_text': speech_text,
            'destination': current_destination['name']
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'response': "Error processing request"
        }), 500

if __name__ == '__main__':
    print("\n🎤 Waymo Voice Assistant")
    print("📍 Open http://localhost:5004 in your browser")
    print("🎤 Using Web Speech API for STT (browser-native)")
    print("🗣️ Using Web Speech API for TTS (browser-native)\n")
    app.run(debug=True, host='0.0.0.0', port=5004)