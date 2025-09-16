import os
import httpx
import json
import base64
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.api_key = os.getenv("GLADIA_API_KEY")
        self.base_url = "https://api.gladia.io"
        self.client = httpx.AsyncClient()
        self._connected = False
        self._initialize()

    def _initialize(self):
        if self.api_key:
            self._connected = True
            logger.info("Gladia Voice Service initialized")
        else:
            logger.warning("Gladia API key not found - using mock mode")

    async def transcribe(self, audio_data: str) -> str:
        """
        Transcribe audio data to text using Gladia API
        audio_data: base64 encoded audio
        """
        if not self.api_key:
            return self._mock_transcribe(audio_data)

        try:
            headers = {
                "x-gladia-key": self.api_key,
                "Content-Type": "application/json"
            }

            response = await self.client.post(
                f"{self.base_url}/audio/text/audio-transcription",
                headers=headers,
                json={
                    "audio_url": f"data:audio/wav;base64,{audio_data}",
                    "language_behaviour": "automatic single language",
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("transcription", "")
            else:
                logger.error(f"Gladia API error: {response.status_code}")
                return self._mock_transcribe(audio_data)

        except Exception as e:
            logger.error(f"Error in voice transcription: {str(e)}")
            return self._mock_transcribe(audio_data)

    def _mock_transcribe(self, audio_data: str) -> str:
        """Mock transcription for testing without API"""
        mock_responses = [
            "Can you take a different route? This one has too much traffic.",
            "I'm feeling a bit anxious about the speed.",
            "Can we stop at a coffee shop nearby?",
            "What's the weather like at our destination?",
            "How much longer until we arrive?",
            "Can you turn up the temperature a bit?",
            "Play some relaxing music please.",
            "Tell me about this neighborhood.",
        ]

        import random
        return random.choice(mock_responses)

    async def transcribe_stream(self, audio_stream) -> str:
        """Handle real-time audio stream transcription"""
        if not self.api_key:
            return "Real-time transcription not available in mock mode"

        try:
            headers = {
                "x-gladia-key": self.api_key,
                "Content-Type": "application/json"
            }

            response = await self.client.post(
                f"{self.base_url}/live/audio/transcriptions",
                headers=headers,
                json={
                    "encoding": "wav",
                    "sample_rate": 16000,
                    "language_behaviour": "automatic single language",
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("transcription", "")
            else:
                return "Stream transcription failed"

        except Exception as e:
            logger.error(f"Error in stream transcription: {str(e)}")
            return "Stream transcription error"

    def is_connected(self) -> bool:
        return self._connected

    async def close(self):
        await self.client.aclose()