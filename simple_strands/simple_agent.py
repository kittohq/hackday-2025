"""
Simple Strands Agent - Time Query Example
Tests basic Strands functionality with optional voice
"""

import os
from datetime import datetime
import pytz
from typing import Optional

# Set your OpenAI API key from environment
# export OPENAI_API_KEY="your-key-here"
os.environ["STRANDS_MODEL_PROVIDER"] = "openai"

# Try Strands, fall back to mock
try:
    from strands import Agent
    STRANDS_AVAILABLE = True
    print("✅ Using real Strands SDK")
except ImportError:
    print("⚠️  Strands not installed, using mock")
    # Simple mock implementation
    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get('name', 'Mock Agent')
            self.system_prompt = kwargs.get('system_prompt', '')
            print(f"Initialized mock agent: {self.name}")

        def __call__(self, message: str) -> str:
            # Simple response logic
            if "time" in message.lower():
                return f"The current time is {datetime.now().strftime('%I:%M %p')}"
            elif "date" in message.lower():
                return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
            elif "weather" in message.lower():
                return "It's 72°F and sunny in San Francisco"
            else:
                return f"I heard: '{message}'. I can tell you the time, date, or weather."

    STRANDS_AVAILABLE = False

# Create a simple time agent
def create_time_agent():
    """Create a simple agent that responds to time queries"""

    # Import OpenAI model
    from strands.models.openai import OpenAIModel

    # Create model with cheapest OpenAI option
    model = OpenAIModel(
        model_id="gpt-3.5-turbo",  # Cheapest model
        params={
            "temperature": 0.7,
            "max_tokens": 150
        }
        # API key is picked up from environment automatically
    )

    agent = Agent(
        name="Time Assistant",
        model=model,  # Pass the model object
        system_prompt="""You are a helpful assistant that tells the time and date.
        Be friendly and concise. When asked about the time, provide it in a natural way.
        You can also provide the date, day of the week, and basic weather information."""
    )

    return agent

# Simple voice transcription (mock)
class SimpleVoiceTranscriber:
    """Simple voice handler with mock fallback"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.has_api = bool(api_key)

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio to text"""
        if self.has_api:
            # Would call real API here
            return "What time is it?"
        else:
            # Mock responses for demo
            import random
            phrases = [
                "What time is it?",
                "What's the current time?",
                "Can you tell me the time?",
                "What day is it?",
                "What's the weather like?"
            ]
            return random.choice(phrases)

# Simple TTS (mock)
class SimpleTTS:
    """Simple text-to-speech with mock fallback"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.has_api = bool(api_key)

    def synthesize(self, text: str) -> bytes:
        """Convert text to speech"""
        if self.has_api:
            # Would call real API here
            return b"[audio data]"
        else:
            # Mock audio data
            return f"[Mock audio: {text}]".encode()

# Main demo function
def demo_agent():
    """Run a simple demo of the agent"""
    print("\n🤖 Simple Strands Agent Demo")
    print("-" * 40)

    # Create agent
    agent = create_time_agent()

    # Test queries
    queries = [
        "What time is it?",
        "What's today's date?",
        "What day of the week is it?",
        "How's the weather?"
    ]

    for query in queries:
        print(f"\n👤 User: {query}")
        response = agent(query)
        print(f"🤖 Agent: {response}")

    # Test voice (mock)
    print("\n\n🎤 Voice Demo")
    print("-" * 40)

    voice = SimpleVoiceTranscriber()
    tts = SimpleTTS()

    # Simulate voice input
    print("🎤 [Simulating voice input...]")
    transcribed = voice.transcribe(b"[mock audio]")
    print(f"📝 Transcribed: {transcribed}")

    # Process with agent
    response = agent(transcribed)
    print(f"🤖 Agent: {response}")

    # Convert to speech
    audio = tts.synthesize(response)
    print(f"🔊 Audio response: {audio[:50]}...")

if __name__ == "__main__":
    demo_agent()
