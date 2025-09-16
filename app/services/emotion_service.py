import os
import httpx
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from app.models.schemas import EmotionState, EmotionType

load_dotenv()

logger = logging.getLogger(__name__)

class EmotionService:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimax.chat/v1"
        self.client = httpx.AsyncClient()
        self._connected = False
        self._initialize()

    def _initialize(self):
        if self.api_key:
            self._connected = True
            logger.info("Minimax Emotion Service initialized")
        else:
            logger.warning("Minimax API key not found - using mock mode")

    async def analyze(self, audio_data: Optional[str] = None, text: str = "") -> EmotionState:
        """
        Analyze emotion from audio and/or text
        """
        if not self.api_key:
            return self._mock_analyze(text)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "abab5.5-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an emotion analysis expert. Analyze the emotional state from the provided text and return: emotional state (anxious/relaxed/frustrated/happy/neutral/confused/impatient), confidence score (0-1), and intensity (0-1)."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the emotion in this text: '{text}'. Return JSON with: state, confidence, intensity"
                    }
                ],
                "temperature": 0.3
            }

            response = await self.client.post(
                f"{self.base_url}/text/chatcompletion",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                emotion_data = self._parse_emotion_response(result)
                return EmotionState(**emotion_data)
            else:
                logger.error(f"Minimax API error: {response.status_code}")
                return self._mock_analyze(text)

        except Exception as e:
            logger.error(f"Error in emotion analysis: {str(e)}")
            return self._mock_analyze(text)

    def _parse_emotion_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Minimax response to extract emotion data"""
        try:
            content = response["choices"][0]["message"]["content"]
            emotion_json = json.loads(content)

            return {
                "state": EmotionType(emotion_json.get("state", "neutral")),
                "confidence": float(emotion_json.get("confidence", 0.5)),
                "intensity": float(emotion_json.get("intensity", 0.5)),
                "details": emotion_json.get("details", {})
            }
        except:
            return {
                "state": EmotionType.NEUTRAL,
                "confidence": 0.5,
                "intensity": 0.5
            }

    def _mock_analyze(self, text: str) -> EmotionState:
        """Mock emotion analysis based on keywords"""
        text_lower = text.lower()

        emotion_keywords = {
            EmotionType.ANXIOUS: ["anxious", "nervous", "worried", "scared", "fear", "unsafe"],
            EmotionType.FRUSTRATED: ["frustrated", "annoyed", "angry", "stupid", "hate", "terrible"],
            EmotionType.HAPPY: ["happy", "great", "wonderful", "love", "perfect", "amazing"],
            EmotionType.RELAXED: ["relaxed", "calm", "comfortable", "peaceful", "nice"],
            EmotionType.CONFUSED: ["confused", "don't understand", "what", "why", "how"],
            EmotionType.IMPATIENT: ["hurry", "late", "faster", "quick", "rush", "slow"]
        }

        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return EmotionState(
                    state=emotion,
                    confidence=0.8,
                    intensity=0.7,
                    details={"source": "keyword_match"}
                )

        return EmotionState(
            state=EmotionType.NEUTRAL,
            confidence=0.6,
            intensity=0.5,
            details={"source": "default"}
        )

    def is_connected(self) -> bool:
        return self._connected

    async def close(self):
        await self.client.aclose()