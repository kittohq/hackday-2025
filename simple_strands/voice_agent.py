"""
Simple Strands Agent with Voice Support
Demonstrates voice input/output with Strands
"""

import os
import json
import base64
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import httpx
from typing import Optional

# Try to import Strands
try:
    from strands import Agent, Tool
    from strands.tools import ToolResult
    STRANDS_AVAILABLE = True
except ImportError:
    # Fallback mock
    STRANDS_AVAILABLE = False

    class ToolResult:
        def __init__(self, success=True, data=None):
            self.success = success
            self.data = data

    class Tool:
        def __init__(self, name="", description="", func=None, parameters=None):
            self.name = name
            self.description = description
            self.func = func
            self.parameters = parameters or {}

    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Mock Agent')
            self.tools = {}

        def register_tool(self, tool):
            self.tools[tool.name] = tool

        async def process(self, message: str, context=None):
            # Simple responses
            msg_lower = message.lower()
            if "time" in msg_lower:
                response = f"The current time is {datetime.now().strftime('%I:%M %p')}"
            elif "date" in msg_lower:
                response = f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            elif "weather" in msg_lower:
                response = "It's 72°F and sunny"
            else:
                response = f"You said: '{message}'"

            return type('Response', (), {'content': response})()

# Create FastAPI app
app = FastAPI(title="Simple Voice Agent")

# Create Strands agent with voice tools
def create_voice_agent():
    """Create an agent with voice capabilities"""

    agent = Agent(
        name="Voice Time Assistant",
        system_prompt="""You are a helpful voice assistant.
        Respond to questions about time, date, and weather.
        Keep responses brief and natural for voice output."""
    )

    # Add a time tool
    async def get_time_tool(context=None):
        """Tool to get current time"""
        current_time = datetime.now()
        return ToolResult(
            success=True,
            data={
                "time": current_time.strftime("%I:%M %p"),
                "date": current_time.strftime("%B %d, %Y"),
                "day": current_time.strftime("%A")
            }
        )

    if STRANDS_AVAILABLE:
        time_tool = Tool(
            name="get_time",
            description="Get current time and date",
            func=get_time_tool
        )
        agent.register_tool(time_tool)

    return agent

# Voice processing functions
class VoiceProcessor:
    """Handle voice input/output"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = httpx.AsyncClient() if self.api_key else None

    async def transcribe(self, audio_data: str) -> str:
        """Convert speech to text"""
        if not self.client:
            # Mock transcription
            import random
            return random.choice([
                "What time is it?",
                "What's the date today?",
                "Tell me the current time",
                "What day is it?"
            ])

        # Real transcription would go here
        # For now, return mock
        return "What time is it?"

    async def synthesize(self, text: str) -> str:
        """Convert text to speech"""
        if not self.client:
            # Return mock audio data
            return base64.b64encode(f"[Audio: {text}]".encode()).decode()

        try:
            # OpenAI TTS
            response = await self.client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": "alloy"
                }
            )

            if response.status_code == 200:
                return base64.b64encode(response.content).decode()
        except:
            pass

        return base64.b64encode(f"[Audio: {text}]".encode()).decode()

# Initialize components
agent = create_voice_agent()
voice_processor = VoiceProcessor()

@app.get("/")
async def home():
    """Serve the voice interface"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Simple Voice Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .chat-area {
            min-height: 300px;
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            background: #f9f9f9;
        }
        .message {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 10px;
        }
        .user {
            background: #667eea;
            color: white;
            text-align: right;
            margin-left: 20%;
        }
        .agent {
            background: #e0e0e0;
            margin-right: 20%;
        }
        .controls {
            display: flex;
            gap: 10px;
        }
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
        }
        #recordBtn {
            background: #667eea;
            color: white;
        }
        #recordBtn:hover {
            background: #5a67d8;
        }
        #recordBtn.recording {
            background: #e53e3e;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        #textBtn {
            background: #48bb78;
            color: white;
        }
        input {
            flex: 2;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
        }
        .status {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Simple Voice Agent</h1>
        <p class="subtitle">Using Strands SDK - Ask about time, date, or weather</p>

        <div class="chat-area" id="chat">
            <div style="text-align: center; color: #999; padding: 50px 0;">
                Click the microphone or type a message...
            </div>
        </div>

        <div class="controls">
            <input type="text" id="textInput" placeholder="Type a message..."
                   onkeypress="if(event.key==='Enter') sendText()">
            <button id="recordBtn" onclick="toggleRecording()">
                🎤 Hold to Talk
            </button>
            <button id="textBtn" onclick="sendText()">
                Send
            </button>
        </div>

        <div class="status" id="status">Ready</div>
    </div>

    <script>
        let ws = null;
        let isRecording = false;
        let mediaRecorder = null;
        let audioChunks = [];

        // Connect WebSocket
        function connect() {
            ws = new WebSocket('ws://localhost:8002/ws');

            ws.onopen = () => {
                document.getElementById('status').textContent = '🟢 Connected';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.transcription) {
                    addMessage(data.transcription, 'user');
                }

                if (data.response) {
                    addMessage(data.response, 'agent');
                }

                if (data.audio) {
                    playAudio(data.audio);
                }
            };

            ws.onerror = () => {
                document.getElementById('status').textContent = '🔴 Connection error';
                setTimeout(connect, 3000);
            };
        }

        // Add message to chat
        function addMessage(text, sender) {
            const chat = document.getElementById('chat');
            const message = document.createElement('div');
            message.className = 'message ' + sender;
            message.textContent = text;
            chat.appendChild(message);
            chat.scrollTop = chat.scrollHeight;
        }

        // Send text message
        function sendText() {
            const input = document.getElementById('textInput');
            const text = input.value.trim();

            if (text && ws) {
                addMessage(text, 'user');
                ws.send(JSON.stringify({
                    type: 'text',
                    data: text
                }));
                input.value = '';
            }
        }

        // Toggle recording
        async function toggleRecording() {
            const btn = document.getElementById('recordBtn');

            if (!isRecording) {
                // Start recording
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = (event) => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64Audio = reader.result.split(',')[1];
                            ws.send(JSON.stringify({
                                type: 'audio',
                                data: base64Audio
                            }));
                        };
                        reader.readAsDataURL(audioBlob);

                        stream.getTracks().forEach(track => track.stop());
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    btn.classList.add('recording');
                    btn.textContent = '⏹️ Stop';
                    document.getElementById('status').textContent = '🎤 Recording...';

                } catch (err) {
                    console.error('Microphone access denied:', err);
                    // Fallback to mock audio
                    simulateVoiceInput();
                }
            } else {
                // Stop recording
                if (mediaRecorder) {
                    mediaRecorder.stop();
                }
                isRecording = false;
                btn.classList.remove('recording');
                btn.textContent = '🎤 Hold to Talk';
                document.getElementById('status').textContent = '🟢 Connected';
            }
        }

        // Simulate voice input for demo
        function simulateVoiceInput() {
            const phrases = [
                "What time is it?",
                "What's today's date?",
                "What day of the week is it?",
                "How's the weather?"
            ];
            const text = phrases[Math.floor(Math.random() * phrases.length)];

            addMessage(text, 'user');
            ws.send(JSON.stringify({
                type: 'text',
                data: text
            }));
        }

        // Play audio response
        function playAudio(base64Audio) {
            // In a real implementation, decode and play
            console.log('Audio response received');
            document.getElementById('status').textContent = '🔊 Playing response...';
            setTimeout(() => {
                document.getElementById('status').textContent = '🟢 Connected';
            }, 1000);
        }

        // Initialize
        connect();
    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message['type'] == 'text':
                # Process text input
                text = message['data']

                # Get agent response
                response = await agent.process(text)
                response_text = response.content

                # Generate audio
                audio = await voice_processor.synthesize(response_text)

                await websocket.send_json({
                    'response': response_text,
                    'audio': audio
                })

            elif message['type'] == 'audio':
                # Process audio input
                audio_data = message['data']

                # Transcribe
                text = await voice_processor.transcribe(audio_data)

                # Get response
                response = await agent.process(text)
                response_text = response.content

                # Generate audio
                audio = await voice_processor.synthesize(response_text)

                await websocket.send_json({
                    'transcription': text,
                    'response': response_text,
                    'audio': audio
                })

    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Simple Voice Agent on http://localhost:8002")
    print("   Voice input: Click and hold the microphone button")
    print("   Text input: Type and press Enter")
    print(f"   Strands SDK: {'✅ Available' if STRANDS_AVAILABLE else '⚠️  Using mock'}")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8002)