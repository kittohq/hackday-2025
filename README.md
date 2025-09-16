# Waymo Rider Voice Assistant 🚗🎤

A voice-enabled AI assistant for Waymo riders that provides natural conversational interactions to find places near your destination using real-time Google Places data and Web Speech APIs.

## 🔧 Technologies & APIs Used

### Core AI & Processing
- **AWS Strands SDK** - Agent orchestration framework for tool-based AI
- **OpenAI API (GPT-3.5/4)** - Natural language understanding and intent classification
- **Google Places API** - Real-time business data for 5M+ locations worldwide

### Voice Technologies
- **Web Speech API** - Browser-native speech recognition (STT) - no API keys needed!
- **Web Speech Synthesis** - Browser-native text-to-speech (TTS) for natural responses
- **Gladia API** (Optional) - Advanced voice transcription for production deployments

### Additional Services
- **Google Maps Distance Matrix API** - Accurate walking/driving time calculations
- **Yelp Fusion API** (Legacy) - Alternative business data source
- **Redis** - Caching and preference learning
- **FastAPI/WebSocket** - Real-time bidirectional communication

## 🆕 Voice-Enabled Web Interface

The latest version (`app_voice.py`) provides a full voice conversational interface:

### Voice Features
- **Web Speech API**: Browser-native speech recognition (STT)
- **Natural Language Generation**: Conversational TTS responses
- **Dual Input Modes**: Voice or text input for flexibility
- **Real-time Transcription**: See what you're saying as you speak
- **Auto Speech Synthesis**: Responses are automatically spoken aloud

### Core V2 Features
- **Natural Language Understanding**: Say "I'm starving" instead of "restaurant"
- **Context-Aware Mapping**: "Need fuel" → coffee in morning, gas station at night
- **30+ Google Place Categories**: From coffee shops to tourist attractions
- **Strands Agent Philosophy**: Dedicated intent-mapping agent for accurate categorization
- **Real Google Places Data**: Live business info, ratings, reviews, and open/closed status

### Example Intent Mappings
```
"I need my morning caffeine fix" → coffee_shop
"Where can I grab a drink later?" → bar
"I'm exhausted, need somewhere to crash" → lodging
"Running low on fuel" → gas_station
"Need to pick up my prescription" → pharmacy
```

### Quick Start Voice Assistant:
```bash
# Run the voice-enabled web app
python3 simple_strands/app_voice.py
# Open http://localhost:5004 in Chrome/Edge
```

Test backend: `python3 simple_strands/waymo_rider_agent_v2.py test`

## 🎯 Key Features

### Voice Interface
- **Speech-to-Text**: Browser-native Web Speech API (no API keys needed)
- **Text-to-Speech**: Natural voice responses with Web Speech Synthesis
- **Visual Feedback**: Real-time transcription and voice status indicators
- **Fallback Options**: Text input for noisy environments

### Core Capabilities
- **Intent Classification**: AI understands natural language requests
- **Google Places Integration**: Real-time data on 5M+ businesses
- **Distance Calculations**: Accurate walking times from destination
- **Context-Aware**: Shows open/closed status, ratings, and reviews
- **Multi-Modal**: Voice, text, and visual responses

### Why Voice Assistant > Manual Search

1. **Hands-Free**: Just speak naturally - no typing or tapping
2. **Destination-Aware**: Automatically searches near your Waymo dropoff point
3. **Real Google Data**: Live info on 5M+ places with current open/closed status
4. **Natural Conversation**: Say "I need coffee" not "coffee shops near me"
5. **Safety First**: No phone handling while in motion
6. **Instant Results**: Voice response with top 3 options in seconds

## 🚀 Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Configuration
```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env:
# - OPENAI_API_KEY (for intent classification)
# - GOOGLE_API_KEY (for Google Places API)
```

### Running the Application

#### Option 1: Voice-Enabled Web App (Recommended)
```bash
# Start the voice assistant
python3 simple_strands/app_voice.py

# Open in Chrome or Edge browser
http://localhost:5004
```

#### Option 2: Command Line Testing
```bash
# Test intent mapping and places search
python3 simple_strands/waymo_rider_agent_v2.py test
```

#### Option 3: Original FastAPI Backend
```bash
# Start the backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Open the frontend
open frontend/index.html
# Or visit http://localhost:8000/frontend/index.html
```

## 🎮 Demo Scenarios

### 1. Coffee Run
**Say**: "I need coffee" or "Where can I get caffeine?"
**Response**: Lists nearest coffee shops with ratings and walking distance

### 2. Hungry Traveler
**Say**: "I'm starving" or "Any good Thai food nearby?"
**Response**: Finds restaurants near destination, shows open/closed status

### 3. Quick Errands
**Say**: "I need to pick up medicine" or "Where's the nearest pharmacy?"
**Response**: Locates pharmacies with hours and distance

### 4. Tourist Mode
**Say**: "What's fun to do around here?" or "Any museums nearby?"
**Response**: Suggests attractions and landmarks near destination

## 📁 Project Structure

```
hackday-2025/
├── simple_strands/              # 🆕 Voice-enabled implementations
│   ├── app_voice.py            # Voice web app with STT/TTS
│   ├── waymo_rider_agent_v2.py # V2: AI intent mapping with Strands
│   ├── waymo_rider_agent.py    # V1: Keyword-based place search
│   ├── test_voice_features.py  # Voice feature testing
│   ├── VOICE_INTEGRATION_PROPOSAL.md # Voice architecture docs
│   └── DEVELOPER_GUIDE.md      # Architecture documentation
├── app/                         # Original FastAPI implementation
│   ├── main.py                 # FastAPI server & WebSocket handling
│   ├── models/
│   │   └── schemas.py           # Data models & enums
│   └── services/
│       ├── voice_service.py     # Gladia voice transcription
│       ├── emotion_service.py   # Minimax emotion detection
│       ├── conversation_engine.py # Intent classification & response
│       ├── yelp_service.py      # Yelp API integration
│       ├── location_service.py  # Distance & routing calculations
│       ├── redis_service.py     # Caching & preference learning
│       └── tts_service.py       # Text-to-speech synthesis
├── frontend/
│   └── index.html               # Interactive simulator UI
├── requirements.txt             # Python dependencies
└── .env.example                # Environment variables template
```

## 🔌 API Endpoints

### WebSocket: `/ws/{client_id}`
Real-time bidirectional communication for voice/text interactions

### REST Endpoints:
- `GET /` - API status
- `GET /api/health` - Service health check
- `POST /api/simulate_journey` - Trigger demo scenarios

## 💡 Technical Highlights

### Intent Classification
```python
IntentType:
- ROUTE_CHANGE      # "Take a different route"
- STOP_REQUEST      # "Stop at coffee shop"
- COMFORT_ADJUSTMENT # "Too cold in here"
- TIME_INQUIRY      # "When will we arrive?"
- INFORMATION_REQUEST # "Tell me about this area"
- EMERGENCY         # "Pull over now!"
```

### Emotion States
```python
EmotionType:
- ANXIOUS    # Slower driving, calming responses
- HAPPY      # Maintain positive experience
- FRUSTRATED # Address concerns quickly
- NEUTRAL    # Standard interaction
```

### Caching Strategy
- User preferences (30 days)
- Location recommendations (30 minutes)
- Conversation history (24 hours)
- Behavior patterns (90 days)

## 🎪 Demo Tips

### Best Demo Flow:
1. Start with voice input: "I'm heading to the airport but feeling anxious"
2. Show emotion detection affecting response tone
3. Request a coffee stop - show Yelp integration with detour time
4. Trigger traffic scenario - demonstrate proactive suggestions
5. Ask about the neighborhood - show contextual awareness

### Mock Mode
The system works without API keys using mock data:
- Simulated voice transcription
- Keyword-based emotion detection
- Pre-defined Yelp results
- Mock TTS responses

## 🏗️ Future Enhancements

- [ ] Multi-language support
- [ ] Integration with vehicle controls (temperature, music)
- [ ] Group ride coordination
- [ ] Payment integration for stops
- [ ] AR windshield display integration
- [ ] Predictive preference learning

## 📝 Notes for Judges

This system demonstrates:
1. **Real-world utility**: Solves actual rider pain points
2. **Technical integration**: Combines 4+ APIs seamlessly
3. **User experience**: Natural, conversational interface
4. **Scalability**: Redis caching for production readiness
5. **Innovation**: Emotion-aware autonomous vehicle interaction

## 🤝 Contributors

Built for [Hackathon Name] in 24 hours

## 📄 License

MIT