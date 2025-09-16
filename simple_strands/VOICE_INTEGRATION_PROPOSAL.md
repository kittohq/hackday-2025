# Voice Integration Proposal for Waymo Rider Assistant
## Natural Speech Interaction with Strands Framework

---

## Executive Summary

This proposal outlines the integration of high-quality, cost-effective speech-to-text (STT) and text-to-speech (TTS) capabilities into the existing Waymo Rider Assistant built with AWS Strands SDK. The goal is to enable natural conversational interactions while maintaining the one-shot classification efficiency of our current architecture.

---

## 🎯 Requirements

### Functional Requirements
1. **Hands-free interaction** - Complete voice-only operation
2. **Natural conversation flow** - No wake words required in-vehicle
3. **Fast response time** - <2 seconds total latency
4. **Interrupt capability** - User can interrupt TTS playback
5. **Multi-language support** - At minimum English variants

### Technical Requirements
1. **Strands tool integration** - Voice as @tool decorators
2. **Streaming support** - Real-time audio processing
3. **Browser compatibility** - Works on mobile/desktop
4. **Cost efficiency** - <$0.01 per interaction
5. **Privacy-aware** - Option for on-device processing

---

## 🎤 Speech-to-Text (STT) Options

### 1. **OpenAI Whisper API** ⭐ RECOMMENDED
```python
@tool
def transcribe_speech(audio_data: bytes) -> str:
    """Transcribe user speech using OpenAI Whisper"""
    response = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_data
    )
    return response.text
```

**Pros:**
- $0.006/minute (very affordable)
- 99%+ accuracy
- Supports 98 languages
- Already using OpenAI for intent mapping
- No additional API keys needed

**Cons:**
- Not real-time streaming (batch processing)
- 25MB file size limit

**Integration:** Simple - same API client as GPT-3.5

### 2. **Web Speech API** (Browser-native)
```javascript
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    sendToStrands(transcript);
};
```

**Pros:**
- FREE - runs in browser
- Real-time streaming
- No API needed
- Privacy-friendly (on-device option)
- Zero latency

**Cons:**
- Browser compatibility issues
- Less accurate than cloud solutions
- Limited language support

**Integration:** Frontend-only, sends text to Strands

### 3. **Deepgram**
```python
@tool
def transcribe_with_deepgram(audio_stream: bytes) -> str:
    """Real-time transcription with Deepgram"""
    # $0.0043/minute for streaming
    return deepgram_client.transcribe(audio_stream)
```

**Pros:**
- Real-time streaming
- $0.0043/minute (cheapest)
- WebSocket support
- Good accuracy

**Cons:**
- Another API to manage
- Less ecosystem integration

### 4. **AssemblyAI**
- $0.00025/second ($0.015/minute)
- Real-time streaming
- Good for long conversations
- Speaker diarization included

---

## 🔊 Text-to-Speech (TTS) Options

### 1. **OpenAI TTS** ⭐ RECOMMENDED
```python
@tool
def synthesize_speech(text: str, voice: str = "nova") -> bytes:
    """Generate speech using OpenAI TTS"""
    response = openai.audio.speech.create(
        model="tts-1",  # or "tts-1-hd" for higher quality
        voice=voice,    # nova, alloy, echo, fable, onyx, shimmer
        input=text
    )
    return response.content
```

**Pricing:**
- Standard: $0.015 per 1K characters (~$0.002/response)
- HD: $0.030 per 1K characters (~$0.004/response)

**Pros:**
- 6 natural voices
- Very natural sounding
- Same API as STT/GPT
- Supports SSML-like speech control

**Cons:**
- Not real-time streaming
- Limited voice customization

### 2. **Web Speech API** (Browser-native)
```javascript
const utterance = new SpeechSynthesisUtterance(text);
utterance.voice = voices.find(v => v.name === 'Google US English');
utterance.rate = 1.1;
speechSynthesis.speak(utterance);
```

**Pros:**
- FREE
- Instant playback
- No API needed
- Works offline

**Cons:**
- Robotic voices
- Limited control
- Platform-dependent quality

### 3. **ElevenLabs**
- $0.30 per 1K characters (expensive but best quality)
- Most natural voices
- Voice cloning capability
- Real-time streaming

### 4. **Amazon Polly**
- $0.004 per 1K characters
- Neural voices available
- SSML support
- Good AWS integration

---

## 🏗️ Proposed Architecture with Strands

### Enhanced Strands Agent Structure

```python
# waymo_rider_agent_v3.py - Voice-Enabled Version

from strands import Agent, tool
import openai
import io
from pydub import AudioSegment

# Voice Processing Tools
@tool
def process_voice_input(audio_data: bytes) -> str:
    """
    Process voice input through STT pipeline.

    Args:
        audio_data: Raw audio bytes from browser

    Returns:
        Transcribed text
    """
    # Convert webm to wav if needed
    audio = AudioSegment.from_file(io.BytesIO(audio_data))
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")

    # Transcribe with Whisper
    transcript = openai.audio.transcriptions.create(
        model="whisper-1",
        file=("audio.wav", wav_io.getvalue())
    )

    return transcript.text

@tool
def generate_voice_response(
    text: str,
    voice_profile: str = "nova",
    speaking_rate: float = 1.0
) -> bytes:
    """
    Generate voice response with TTS.

    Args:
        text: Text to speak
        voice_profile: Voice selection
        speaking_rate: Speed adjustment

    Returns:
        Audio bytes for playback
    """
    # Clean text for speech (remove markdown, emojis)
    speech_text = clean_for_speech(text)

    # Generate audio
    response = openai.audio.speech.create(
        model="tts-1",  # Use tts-1-hd for premium
        voice=voice_profile,
        input=speech_text,
        speed=speaking_rate
    )

    return response.content

@tool
def create_ssml_response(places: List[Dict]) -> str:
    """
    Create speech-optimized response for places.

    Makes responses more natural for voice:
    - Emphasizes important info
    - Adds pauses
    - Simplifies complex data
    """
    if not places:
        return "I couldn't find any places matching your request."

    # Voice-optimized formatting
    response = f"I found {len(places)} options. "

    for i, place in enumerate(places[:3], 1):
        response += f"Option {i}: {place['name']}, "
        response += f"{place['distance_text']} away, "
        response += f"rated {place['rating']} stars. "

        if i < len(places[:3]):
            response += "... "  # Natural pause

    response += "Would you like to hear more details?"

    return response

# Enhanced Voice-Aware Agent
def create_voice_enabled_agent():
    """Create Strands agent with voice capabilities"""

    model = OpenAIModel(
        model_id="gpt-3.5-turbo",
        params={
            "temperature": 0.7,
            "max_tokens": 150  # Shorter for voice
        }
    )

    agent = Agent(
        name="Waymo Voice Assistant",
        model=model,
        tools=[
            process_voice_input,
            generate_voice_response,
            create_ssml_response,
            get_waymo_destination,
            search_places_with_ai,
            map_to_google_place_type
        ],
        system_prompt="""You are a voice assistant for Waymo riders.

        VOICE INTERACTION RULES:
        1. Keep responses concise - under 3 sentences
        2. Use natural, conversational language
        3. Avoid technical terms and acronyms
        4. Spell out numbers under 10
        5. Pause between listing items
        6. Ask clarifying questions if unclear
        7. Confirm before taking actions

        When presenting places:
        - Lead with most important info (name, distance)
        - Skip addresses unless asked
        - Round numbers for speech (4.7 → "four point seven")
        - Use landmarks when possible

        Always be:
        - Conversational, not robotic
        - Helpful but brief
        - Proactive with suggestions"""
    )

    return agent
```

### Frontend Voice Integration

```javascript
// Voice-enabled frontend additions

class VoiceInterface {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.audioContext = new AudioContext();

        // Voice Activity Detection
        this.setupVAD();
    }

    setupVAD() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const analyser = this.audioContext.createAnalyser();
                const microphone = this.audioContext.createMediaStreamSource(stream);
                microphone.connect(analyser);

                // Detect speech vs silence
                this.detectSpeech(analyser);
            });
    }

    async startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });

        this.mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        this.mediaRecorder.ondataavailable = (event) => {
            this.audioChunks.push(event.data);
        };

        this.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            await this.sendToBackend(audioBlob);
            this.audioChunks = [];
        };

        this.mediaRecorder.start();
        this.isRecording = true;
    }

    async sendToBackend(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);

        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Play TTS response
        if (result.audio) {
            this.playAudio(result.audio);
        }
    }

    playAudio(base64Audio) {
        const audio = new Audio('data:audio/mp3;base64,' + base64Audio);
        audio.play();

        // Update UI during playback
        audio.onplay = () => this.setUIState('speaking');
        audio.onended = () => this.setUIState('listening');
    }
}
```

---

## 💰 Cost Analysis

### Per Interaction Costs

| Component | OpenAI | Web API | Deepgram |
|-----------|--------|---------|----------|
| STT (30 sec) | $0.003 | FREE | $0.002 |
| Intent (GPT-3.5) | $0.001 | $0.001 | $0.001 |
| TTS (150 chars) | $0.002 | FREE | N/A |
| **Total** | **$0.006** | **$0.001** | **$0.003+TTS** |

### Monthly Costs (10K interactions/day)
- **OpenAI Stack**: ~$180/month
- **Hybrid (Web+OpenAI)**: ~$30/month
- **Pure Web API**: ~$30/month (GPT only)

**Recommendation**: Start with Hybrid approach
- Web Speech API for STT (when available)
- OpenAI Whisper as fallback
- OpenAI TTS for quality
- Total: ~$0.003 per interaction

---

## 🚀 Implementation Plan

### Phase 1: Backend Voice Tools (Week 1)
1. Add Whisper STT tool to Strands agent
2. Add OpenAI TTS tool
3. Create voice-optimized response formatter
4. Add audio file handling endpoints

### Phase 2: Frontend Integration (Week 1)
1. Add MediaRecorder for audio capture
2. Implement push-to-talk UI
3. Add audio playback for TTS
4. Voice activity detection (VAD)

### Phase 3: Optimization (Week 2)
1. Add streaming support
2. Implement interruption handling
3. Cache common TTS responses
4. Add voice selection UI

### Phase 4: Enhancement (Week 2)
1. Multi-language support
2. Speaker profiles
3. Emotion-aware TTS
4. Background noise handling

---

## 🎯 Strands-Specific Integration

### Voice as First-Class Tools

```python
# Voice tools become part of the agent's toolkit
voice_agent = Agent(
    name="Waymo Voice Assistant",
    tools=[
        # Voice I/O
        transcribe_speech,      # STT
        synthesize_speech,      # TTS
        detect_silence,         # VAD

        # Existing tools
        search_places_with_ai,
        format_rider_response,

        # New voice-aware tools
        create_voice_summary,   # Shorter responses
        spell_for_clarity,      # Spell complex names
        provide_voice_menu      # Voice UI navigation
    ]
)
```

### Voice-Aware Prompt Engineering

```python
VOICE_SYSTEM_PROMPT = """
You are a voice assistant in a Waymo autonomous vehicle.

VOICE-FIRST RULES:
1. Maximum 2 sentences per response
2. Use "first, second, third" not "1, 2, 3"
3. Pause indicators: "..." for breath pauses
4. Emphasize: *word* for emphasis
5. Clarify: Always confirm before actions
6. Fallback: "Could you repeat that?" if unclear

INTERACTION FLOW:
Listen → Understand → Confirm → Act → Respond

Example:
User: "I need coffee"
You: "I found three coffee shops nearby. *Closest* is Blue Bottle, just two minutes away. Would you like to hear all options?"
"""
```

---

## 🔧 Technical Considerations

### Browser Compatibility
- Chrome/Edge: Full support
- Safari: Requires permissions
- Firefox: Limited WebRTC support

### Latency Optimization
1. **Parallel processing**: STT + Intent mapping simultaneously
2. **Response streaming**: Start TTS before full response
3. **Preload common phrases**: Cache TTS for frequent responses
4. **Edge caching**: CDN for audio assets

### Privacy & Security
1. **On-device option**: Web Speech API for privacy
2. **Audio encryption**: TLS for all audio streams
3. **No audio storage**: Process and discard
4. **User consent**: Clear microphone permissions

---

## 📊 Success Metrics

### Technical KPIs
- **End-to-end latency**: <2 seconds
- **STT accuracy**: >95%
- **TTS naturalness**: 4.5/5 MOS score
- **Interaction success rate**: >90%

### User Experience KPIs
- **Hands-free completion**: >80% of tasks
- **User satisfaction**: >4.5/5
- **Retry rate**: <10%
- **Interruption handling**: <500ms

---

## 🎤 Voice UI/UX Guidelines

### Conversation Design
1. **Implicit confirmation**: "Finding coffee shops..." (shows understanding)
2. **Progressive disclosure**: Start with top result, offer more
3. **Error recovery**: "I didn't catch that. Could you say it again?"
4. **Context awareness**: Remember previous queries
5. **Multimodal feedback**: Visual + audio confirmation

### Voice Feedback States
```javascript
// Visual states during voice interaction
states = {
    idle: "🎤 Tap to speak",
    listening: "🔴 Listening...",
    processing: "🤔 Understanding...",
    speaking: "🔊 Speaking...",
    error: "❌ Couldn't hear you"
}
```

---

## 💡 Recommendations

### Immediate Implementation (MVP)
1. **Use OpenAI Whisper + TTS** - Single API, good quality
2. **Push-to-talk UI** - Simpler than always-on
3. **Hybrid fallback** - Web API with OpenAI backup
4. **Basic voice commands** - Focus on place search

### Future Enhancements
1. **Wake word detection** - "Hey Waymo"
2. **Continuous conversation** - Multi-turn dialog
3. **Personalized voices** - User preferences
4. **Multilingual support** - Spanish, Mandarin priority

### Cost Optimization Strategy
1. **Start with pay-per-use** - OpenAI usage-based
2. **Cache common responses** - Reduce TTS calls
3. **Batch process when possible** - Combine requests
4. **Monitor usage patterns** - Optimize high-frequency paths

---

## 🚦 Go/No-Go Decision Criteria

### Go with Voice Integration if:
- ✅ Latency consistently <2 seconds
- ✅ Cost per interaction <$0.01
- ✅ STT accuracy >95% in vehicle environment
- ✅ User testing shows preference over touch

### Consider Alternatives if:
- ❌ Browser compatibility <80% of users
- ❌ Noise cancellation inadequate
- ❌ Privacy concerns from users
- ❌ Cost exceeds budget constraints

---

## 📝 Conclusion

The recommended approach for integrating voice into the Waymo Rider Assistant is:

1. **OpenAI Whisper + TTS** for quality and simplicity
2. **Strands tools** for clean integration
3. **Hybrid fallback** with Web APIs for cost optimization
4. **Push-to-talk** for MVP, continuous listening later

This provides:
- **High quality** voice interaction
- **Low cost** (~$0.006 per interaction)
- **Simple integration** with existing Strands architecture
- **Scalable** to millions of rides

The voice-enabled agent maintains the elegance of the one-shot classification approach while adding natural conversation capabilities that enhance the rider experience.