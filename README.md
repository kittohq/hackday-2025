# Dynamic Rider Experience Agent 🚗🤖

A conversational AI agent for autonomous vehicles that enhances the rider experience through natural voice interactions, emotion detection, and context-aware recommendations.

## 🆕 Version 2: AI-Powered Intent Understanding

The latest version (`waymo_rider_agent_v2.py`) uses AWS Strands SDK with OpenAI GPT-3.5 to intelligently understand natural language requests:

### V2 Features
- **Natural Language Understanding**: Say "I'm starving" instead of "restaurant"
- **Context-Aware Mapping**: "Need fuel" → coffee in morning, gas station at night
- **30+ Place Categories**: From coffee shops to tourist attractions
- **Strands Agent Philosophy**: Dedicated intent-mapping agent for accurate categorization
- **Real Google Places Data**: Live business info, ratings, and reviews

### Example Intent Mappings
```
"I need my morning caffeine fix" → coffee_shop
"Where can I grab a drink later?" → bar
"I'm exhausted, need somewhere to crash" → lodging
"Running low on fuel" → gas_station
"Need to pick up my prescription" → pharmacy
```

Test it: `python3 simple_strands/waymo_rider_agent_v2.py test`

## 🎯 Key Features

### Core Capabilities
- **Voice-to-Text**: Natural language input via Gladia API
- **Emotion Detection**: Real-time emotional state analysis via Minimax
- **Intent Classification**: Understanding rider requests and needs
- **Context-Aware Recommendations**: Yelp integration for local business suggestions
- **Personalization**: Redis caching for user preferences and patterns
- **Text-to-Speech**: Natural voice responses for conversational flow

### Why This Beats Manual Yelp Searches

1. **Context-Aware Routing**: Knows your exact route and suggests places with minimal detour
2. **Real-Time Traffic Integration**: Factors in current traffic when calculating detours
3. **Safety First**: No phone handling while in motion
4. **Emotional Intelligence**: Adapts responses based on rider's emotional state
5. **Proactive Suggestions**: "Traffic ahead will delay us 15 minutes. There's a coffee shop 1 minute away if you'd like to wait it out"
6. **Seamless Execution**: Direct route updates without app switching

## 🚀 Quick Start

### Prerequisites
```bash
# Install Redis (Mac)
brew install redis
brew services start redis

# Install Python dependencies
pip install -r requirements.txt
```

### Configuration
```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env:
# - GLADIA_API_KEY (for voice transcription)
# - MINIMAX_API_KEY (for emotion detection)
# - OPENAI_API_KEY (for conversation engine)
# - YELP_API_KEY (optional, for real Yelp data)
```

### Running the Application

#### Option 1: Waymo Agent with Google Places (Recommended)
```bash
# Version 2 with AI intent understanding
python3 simple_strands/waymo_rider_agent_v2.py

# Or Version 1 with keyword matching
python3 simple_strands/run_agent.py
```

#### Option 2: Original FastAPI Backend
```bash
# Start the backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Open the frontend
open frontend/index.html
# Or visit http://localhost:8000/frontend/index.html
```

## 🎮 Demo Scenarios

### 1. Anxious Rider
**User**: "I'm feeling nervous about the speed"
**Agent**: Detects anxiety, adjusts driving style, offers calming music

### 2. Hungry Traveler
**User**: "I'm hungry, any good Thai food nearby?"
**Agent**: Finds Thai restaurants along route with minimal detour

### 3. Time-Conscious
**User**: "I'm running late!"
**Agent**: Finds faster route, provides accurate ETA updates

### 4. Tourist Mode
**User**: "Tell me about this neighborhood"
**Agent**: Provides local history, attractions, recommendations

## 📁 Project Structure

```
hackday/
├── simple_strands/              # 🆕 Strands-based implementations
│   ├── waymo_rider_agent_v2.py # V2: AI intent mapping with Strands
│   ├── waymo_rider_agent.py    # V1: Keyword-based place search
│   ├── run_agent.py            # Python runner (auto-loads .env)
│   ├── test_waymo_agent.py     # Comprehensive test suite
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