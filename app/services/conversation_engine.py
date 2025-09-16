import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

from app.models.schemas import (
    EmotionState, IntentType, ActionType,
    AgentResponse, VehicleState
)
from app.services.yelp_service import YelpService
from app.services.location_service import LocationService

load_dotenv()

logger = logging.getLogger(__name__)

class ConversationEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        self.yelp_service = YelpService()
        self.location_service = LocationService()

        self.intent_patterns = {
            IntentType.ROUTE_CHANGE: ["different route", "avoid", "detour", "go through", "take the"],
            IntentType.STOP_REQUEST: ["stop at", "can we stop", "need to stop", "pull over", "grab some", "pick up"],
            IntentType.COMFORT_ADJUSTMENT: ["too cold", "too hot", "temperature", "music", "window", "speed"],
            IntentType.TIME_INQUIRY: ["how long", "when will", "arrival time", "eta", "how much longer"],
            IntentType.INFORMATION_REQUEST: ["tell me about", "what is", "recommend", "suggestions", "nearby", "around here"],
            IntentType.EMERGENCY: ["emergency", "urgent", "help", "accident", "sick", "pull over now"],
            IntentType.FEEDBACK: ["thank you", "great job", "terrible", "bad service", "love this"],
        }

    async def process(
        self,
        text: str,
        emotion: EmotionState,
        session_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user input and generate appropriate response"""

        intent = self._classify_intent(text)

        response = await self._generate_response(
            text=text,
            intent=intent,
            emotion=emotion,
            context=context
        )

        actions = await self._determine_actions(
            text=text,
            intent=intent,
            response=response,
            context=context
        )

        return {
            "message": response["message"],
            "intent": intent.value,
            "emotion_detected": emotion.dict(),
            "actions": actions,
            "suggestions": response.get("suggestions", []),
            "confidence": response.get("confidence", 0.8)
        }

    def _classify_intent(self, text: str) -> IntentType:
        """Classify user intent from text"""
        text_lower = text.lower()

        for intent, patterns in self.intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent

        if "?" in text:
            return IntentType.INFORMATION_REQUEST

        return IntentType.SMALL_TALK

    async def _generate_response(
        self,
        text: str,
        intent: IntentType,
        emotion: EmotionState,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate contextual response based on intent and emotion"""

        if intent == IntentType.EMERGENCY:
            return self._handle_emergency(text, context)

        if intent == IntentType.STOP_REQUEST:
            return await self._handle_stop_request(text, context)

        if intent == IntentType.INFORMATION_REQUEST:
            return await self._handle_information_request(text, context)

        if intent == IntentType.TIME_INQUIRY:
            return self._handle_time_inquiry(context)

        if intent == IntentType.COMFORT_ADJUSTMENT:
            return self._handle_comfort_adjustment(text, emotion)

        if intent == IntentType.ROUTE_CHANGE:
            return self._handle_route_change(text, context)

        return self._handle_general_conversation(text, emotion)

    async def _handle_stop_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests to stop at locations"""

        location = context.get("location", {"lat": 37.7749, "lng": -122.4194})

        if "coffee" in text.lower():
            results = await self.yelp_service.search_nearby(
                latitude=location["lat"],
                longitude=location["lng"],
                term="coffee",
                radius=2000
            )

            if results:
                top_result = results[0]
                return {
                    "message": f"I found {top_result['name']} just 2 minutes away with a {top_result.get('rating', 'N/A')} star rating. It would add about 5 minutes to your journey. Should I update the route?",
                    "suggestions": [r["name"] for r in results[:3]],
                    "confidence": 0.9
                }

        if "food" in text.lower() or "eat" in text.lower():
            cuisine_type = self._extract_cuisine_type(text)
            results = await self.yelp_service.search_nearby(
                latitude=location["lat"],
                longitude=location["lng"],
                term=cuisine_type or "restaurants",
                radius=3000
            )

            if results:
                suggestions = []
                for r in results[:3]:
                    detour = self.location_service.calculate_detour_time(
                        current_location=location,
                        destination={"lat": r["coordinates"]["latitude"], "lng": r["coordinates"]["longitude"]},
                        final_destination=context.get("destination", location)
                    )
                    suggestions.append({
                        "name": r["name"],
                        "rating": r.get("rating"),
                        "detour_minutes": detour
                    })

                return {
                    "message": f"Based on your route, {suggestions[0]['name']} is the closest with minimal detour - only {suggestions[0]['detour_minutes']} extra minutes. It has a {suggestions[0]['rating']} star rating. Want to stop there?",
                    "suggestions": [s["name"] for s in suggestions],
                    "confidence": 0.85
                }

        return {
            "message": "I can help you find a place to stop. What kind of place are you looking for?",
            "suggestions": ["Coffee shops", "Restaurants", "Gas stations", "Pharmacies"],
            "confidence": 0.7
        }

    async def _handle_information_request(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle information requests about surroundings or destination"""

        location = context.get("location", {"lat": 37.7749, "lng": -122.4194})

        if "recommend" in text.lower() or "suggestion" in text.lower():
            interests = await self._extract_interests(text)
            results = await self.yelp_service.search_nearby(
                latitude=location["lat"],
                longitude=location["lng"],
                term=interests,
                radius=5000
            )

            if results:
                recommendations = []
                for r in results[:3]:
                    recommendations.append(f"{r['name']} ({r.get('rating', 'N/A')} stars)")

                return {
                    "message": f"Based on your preferences, I recommend: {', '.join(recommendations)}. All are highly rated and close to your route.",
                    "suggestions": recommendations,
                    "confidence": 0.85
                }

        if "weather" in text.lower():
            return {
                "message": "It's currently 72°F and sunny at your destination. Perfect weather for your arrival!",
                "confidence": 0.9
            }

        if "neighborhood" in text.lower() or "area" in text.lower():
            return {
                "message": "You're passing through the Mission District, known for its vibrant murals, excellent restaurants, and cultural diversity. There are several highly-rated cafes and shops along Valencia Street.",
                "suggestions": ["Tartine Bakery", "Ritual Coffee", "Dolores Park"],
                "confidence": 0.8
            }

        return {
            "message": "I can provide information about restaurants, weather, traffic, or local attractions. What would you like to know?",
            "confidence": 0.7
        }

    def _handle_emergency(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situations"""
        return {
            "message": "I understand this is urgent. I'm alerting emergency services and finding the nearest safe location to stop. Help is on the way.",
            "confidence": 1.0,
            "priority": "high"
        }

    def _handle_time_inquiry(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle time and ETA inquiries"""
        eta = context.get("eta_minutes", 25)
        traffic_condition = context.get("traffic_condition", "normal")

        if traffic_condition == "heavy":
            return {
                "message": f"Due to current traffic, we'll arrive in approximately {eta} minutes. I'm monitoring for faster routes and will update you if I find one.",
                "confidence": 0.9
            }

        return {
            "message": f"We'll arrive in about {eta} minutes. The route is clear and we're making good time.",
            "confidence": 0.95
        }

    def _handle_comfort_adjustment(self, text: str, emotion: EmotionState) -> Dict[str, Any]:
        """Handle comfort-related requests"""
        text_lower = text.lower()

        if "cold" in text_lower:
            return {
                "message": "I'll increase the temperature to 74°F. Let me know if you need further adjustments.",
                "confidence": 0.95
            }

        if "hot" in text_lower or "warm" in text_lower:
            return {
                "message": "Lowering the temperature to 70°F. I can also open the windows slightly if you'd prefer fresh air.",
                "confidence": 0.95
            }

        if "music" in text_lower:
            if emotion.state == EmotionType.ANXIOUS:
                return {
                    "message": "I'll play some calming music to help you relax. How about some ambient sounds?",
                    "suggestions": ["Nature sounds", "Classical", "Lo-fi beats"],
                    "confidence": 0.9
                }
            return {
                "message": "What kind of music would you like? I have access to various genres.",
                "suggestions": ["Pop", "Rock", "Classical", "Jazz", "Podcasts"],
                "confidence": 0.85
            }

        if "speed" in text_lower or "slow" in text_lower or "fast" in text_lower:
            if emotion.state == EmotionType.ANXIOUS:
                return {
                    "message": "I understand you're feeling uncomfortable. I'll adjust to a more relaxed driving style while staying safe and on schedule.",
                    "confidence": 0.9
                }
            return {
                "message": "Adjusting the driving style for your comfort. We'll still arrive on time.",
                "confidence": 0.9
            }

        return {
            "message": "I'll make that adjustment for you right away.",
            "confidence": 0.8
        }

    def _handle_route_change(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route change requests"""
        text_lower = text.lower()

        if "traffic" in text_lower or "faster" in text_lower:
            return {
                "message": "I've found an alternative route that's 5 minutes faster by taking 280 instead of 101. Should I update the navigation?",
                "suggestions": ["Take faster route", "Stay on current route"],
                "confidence": 0.9
            }

        if "scenic" in text_lower:
            return {
                "message": "I can take you along the coastal route. It will add 10 minutes but offers beautiful ocean views. Would you like that?",
                "confidence": 0.85
            }

        if "avoid" in text_lower:
            if "highway" in text_lower:
                return {
                    "message": "I'll reroute through city streets to avoid highways. This will add about 8 minutes to the journey.",
                    "confidence": 0.9
                }

        return {
            "message": "I can adjust the route for you. What would you like to avoid or prefer?",
            "suggestions": ["Avoid highways", "Fastest route", "Scenic route", "Avoid tolls"],
            "confidence": 0.8
        }

    def _handle_general_conversation(self, text: str, emotion: EmotionState) -> Dict[str, Any]:
        """Handle general conversation and small talk"""

        if emotion.state == EmotionType.ANXIOUS:
            return {
                "message": "I can sense you might be feeling a bit anxious. Remember, our vehicles have the best safety record and I'm here to ensure you have a comfortable journey. Is there anything specific I can help with?",
                "confidence": 0.85
            }

        if emotion.state == EmotionType.HAPPY:
            return {
                "message": "I'm glad you're enjoying the ride! Let me know if you need anything.",
                "confidence": 0.9
            }

        return {
            "message": "I'm here to help make your journey comfortable. Feel free to ask me anything!",
            "confidence": 0.8
        }

    async def _determine_actions(
        self,
        text: str,
        intent: IntentType,
        response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Determine what actions to take based on the conversation"""
        actions = []

        if intent == IntentType.EMERGENCY:
            actions.append({
                "type": ActionType.ALERT_DRIVER,
                "priority": "immediate",
                "details": {"message": text}
            })

        elif intent == IntentType.ROUTE_CHANGE:
            if "yes" in response.get("message", "").lower():
                actions.append({
                    "type": ActionType.UPDATE_ROUTE,
                    "details": {"confirmation_required": True}
                })

        elif intent == IntentType.STOP_REQUEST:
            if response.get("suggestions"):
                actions.append({
                    "type": ActionType.CONFIRM_STOP,
                    "details": {
                        "options": response["suggestions"],
                        "confirmation_required": True
                    }
                })

        elif intent == IntentType.COMFORT_ADJUSTMENT:
            if "temperature" in text.lower():
                actions.append({
                    "type": ActionType.ADJUST_TEMPERATURE,
                    "details": {"target_temp": 72}
                })
            elif "music" in text.lower():
                actions.append({
                    "type": ActionType.CHANGE_MUSIC,
                    "details": {"genre": "relaxing"}
                })

        return actions

    def _extract_cuisine_type(self, text: str) -> Optional[str]:
        """Extract cuisine type from text"""
        cuisines = ["italian", "chinese", "mexican", "thai", "indian", "japanese", "korean", "vietnamese"]
        text_lower = text.lower()

        for cuisine in cuisines:
            if cuisine in text_lower:
                return cuisine

        return None

    async def _extract_interests(self, text: str) -> str:
        """Extract user interests from text"""
        if "eat" in text.lower() or "food" in text.lower():
            return "restaurants"
        if "coffee" in text.lower():
            return "coffee"
        if "shop" in text.lower():
            return "shopping"

        return "popular"