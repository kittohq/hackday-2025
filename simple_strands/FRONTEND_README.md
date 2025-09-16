# Waymo Rider Assistant - Web Interface

## 🚀 Quick Start

```bash
# Run the web app
python3 app.py

# Open in browser
http://localhost:5001
```

## ✨ Features

### Current
- **Clean, mobile-friendly UI** - Works great on phone/tablet
- **AI-powered intent understanding** - Natural language queries
- **Real Google Places data** - Live business info with ratings
- **Quick suggestion chips** - Tap common requests
- **Distance & walking time** - From your Waymo drop-off point
- **Open/closed status** - Real-time business hours

### Voice-Ready
- **Microphone button placeholder** - UI ready for voice integration
- **Visual feedback states** - Recording animation ready
- **Conversation flow** - Designed for voice interactions

## 🎨 UI Components

1. **Destination Header**
   - Shows current Waymo destination
   - GPS coordinates
   - Gradient purple design

2. **Chat Interface**
   - Message bubbles
   - Smooth animations
   - Auto-scroll

3. **Place Cards**
   - Business name
   - Distance & walking time
   - Star rating & review count
   - Open/closed status

4. **Input Area**
   - Text input with send button
   - Voice button (ready for integration)
   - Example chips for quick queries

## 🔧 Technical Stack

- **Backend**: Flask + Flask-CORS
- **Frontend**: Pure HTML/CSS/JS (no framework needed)
- **AI**: Strands SDK + OpenAI GPT-3.5
- **Data**: Google Places API (New)

## 🎤 Voice Integration (Coming Soon)

The UI is prepared for voice with:
- Recording button with pulse animation
- Visual states for listening/processing
- Conversation-style layout

To add voice:
1. Integrate Web Speech API or
2. Connect Gladia API for transcription
3. Add TTS for responses

## 📱 Mobile Optimized

- Responsive design
- Touch-friendly buttons
- Large tap targets
- Smooth scrolling

## 🎯 Example Queries

Try these natural language requests:
- "I'm starving"
- "Need my coffee fix"
- "Where can I grab a drink?"
- "Running low on gas"
- "I need to pick up my prescription"

## 🔑 Environment

Uses `.env.example` for API keys:
- `OPENAI_API_KEY` - For AI intent mapping
- `GOOGLE_API_KEY` - For Places API

## 🚦 API Endpoints

- `GET /` - Web interface
- `GET /api/destination` - Get current destination
- `POST /api/search` - Search for places

## 💡 Design Philosophy

- **No fuss** - Simple, clean, works
- **Voice-first thinking** - UI ready for speech
- **Mobile-friendly** - Designed for in-vehicle use
- **Fast responses** - One-shot classification