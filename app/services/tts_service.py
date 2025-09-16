import os
import httpx
import base64
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TTSService:
    """Text-to-Speech service for agent responses"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gladia_api_key = os.getenv("GLADIA_API_KEY")
        self.client = httpx.AsyncClient()
        self._use_openai = bool(self.openai_api_key)
        self._use_gladia = bool(self.gladia_api_key) and not self._use_openai

        if self._use_openai:
            logger.info("TTS Service using OpenAI")
        elif self._use_gladia:
            logger.info("TTS Service using Gladia")
        else:
            logger.warning("No TTS API keys found - using mock mode")

    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        emotion: Optional[str] = None
    ) -> Optional[str]:
        """
        Convert text to speech
        Returns base64 encoded audio
        """
        if self._use_openai:
            return await self._synthesize_openai(text, voice)
        elif self._use_gladia:
            return await self._synthesize_gladia(text, emotion)
        else:
            return self._mock_synthesize(text)

    async def _synthesize_openai(self, text: str, voice: str = "alloy") -> Optional[str]:
        """Use OpenAI TTS API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }

            voice_map = {
                "calm": "alloy",
                "friendly": "nova",
                "professional": "onyx",
                "energetic": "shimmer",
                "warm": "echo",
                "neutral": "fable"
            }

            selected_voice = voice_map.get(voice, "alloy")

            response = await self.client.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": selected_voice,
                    "response_format": "mp3"
                }
            )

            if response.status_code == 200:
                audio_content = response.content
                return base64.b64encode(audio_content).decode('utf-8')
            else:
                logger.error(f"OpenAI TTS error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error in OpenAI TTS: {str(e)}")
            return None

    async def _synthesize_gladia(self, text: str, emotion: Optional[str] = None) -> Optional[str]:
        """Use Gladia TTS API"""
        try:
            headers = {
                "x-gladia-key": self.gladia_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "output_format": "mp3",
                "language": "en",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75
                }
            }

            if emotion:
                emotion_settings = {
                    "anxious": {"speed": 1.1, "pitch": 1.05},
                    "calm": {"speed": 0.95, "pitch": 0.98},
                    "happy": {"speed": 1.05, "pitch": 1.02},
                    "neutral": {"speed": 1.0, "pitch": 1.0}
                }

                if emotion in emotion_settings:
                    payload["voice_settings"].update(emotion_settings[emotion])

            response = await self.client.post(
                "https://api.gladia.io/audio/text/audio-transcription",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("audio_base64", "")
            else:
                logger.error(f"Gladia TTS error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error in Gladia TTS: {str(e)}")
            return None

    def _mock_synthesize(self, text: str) -> str:
        """Return mock audio data for testing"""
        mock_audio = f"MOCK_AUDIO_DATA_{len(text)}_BYTES"
        return base64.b64encode(mock_audio.encode()).decode('utf-8')

    async def get_voice_options(self) -> list:
        """Get available voice options"""
        if self._use_openai:
            return [
                {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
                {"id": "echo", "name": "Echo", "description": "Warm and conversational"},
                {"id": "fable", "name": "Fable", "description": "Expressive and dynamic"},
                {"id": "onyx", "name": "Onyx", "description": "Professional and authoritative"},
                {"id": "nova", "name": "Nova", "description": "Friendly and youthful"},
                {"id": "shimmer", "name": "Shimmer", "description": "Energetic and bright"}
            ]
        else:
            return [
                {"id": "default", "name": "Default", "description": "Standard voice"}
            ]

    def adjust_for_emotion(self, text: str, emotion: str) -> str:
        """Adjust text presentation based on emotion"""
        emotion_adjustments = {
            "anxious": f"<speak><prosody rate='slow' pitch='low'>{text}</prosody></speak>",
            "happy": f"<speak><prosody rate='medium' pitch='high'>{text}</prosody></speak>",
            "frustrated": f"<speak><prosody rate='slow' pitch='medium'>{text}</prosody></speak>",
            "neutral": text
        }

        return emotion_adjustments.get(emotion, text)

    async def close(self):
        await self.client.aclose()