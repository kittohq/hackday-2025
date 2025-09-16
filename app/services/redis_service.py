import os
import json
import redis
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

from app.models.schemas import UserPreferences, JourneyContext

load_dotenv()

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self._connected = True
            logger.info("Redis service connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)} - using in-memory cache")
            self._connected = False
            self._memory_cache = {}

    async def ping(self) -> bool:
        """Check if Redis is connected"""
        if not self._connected:
            return True

        try:
            self.redis_client.ping()
            return True
        except:
            return False

    async def create_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new user session"""
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "preferences": UserPreferences().dict(),
            "conversation_history": [],
            "journey_context": {}
        }

        if self._connected:
            self.redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=24),
                json.dumps(session_data)
            )
        else:
            self._memory_cache[f"session:{session_id}"] = session_data

        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if self._connected:
            data = self.redis_client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        else:
            return self._memory_cache.get(f"session:{session_id}")

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        if self._connected:
            self.redis_client.setex(
                f"session:{session_id}",
                timedelta(hours=24),
                json.dumps(data)
            )
        else:
            self._memory_cache[f"session:{session_id}"] = data

        return True

    async def add_to_history(
        self,
        session_id: str,
        interaction: Dict[str, Any]
    ) -> bool:
        """Add interaction to conversation history"""
        session = await self.get_session(session_id)

        if not session:
            session = await self.create_session(session_id)

        if "conversation_history" not in session:
            session["conversation_history"] = []

        session["conversation_history"].append(interaction)

        if len(session["conversation_history"]) > 50:
            session["conversation_history"] = session["conversation_history"][-50:]

        return await self.update_session(session_id, session)

    async def update_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        session = await self.get_session(session_id)

        if not session:
            session = await self.create_session(session_id)

        session["preferences"].update(preferences)

        if self._connected:
            self.redis_client.setex(
                f"preferences:{session_id}",
                timedelta(days=30),
                json.dumps(session["preferences"])
            )
        else:
            self._memory_cache[f"preferences:{session_id}"] = session["preferences"]

        return await self.update_session(session_id, session)

    async def get_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences with fallback to session"""
        if self._connected:
            prefs = self.redis_client.get(f"preferences:{session_id}")
            if prefs:
                return json.loads(prefs)
        else:
            prefs = self._memory_cache.get(f"preferences:{session_id}")
            if prefs:
                return prefs

        session = await self.get_session(session_id)
        return session["preferences"] if session else UserPreferences().dict()

    async def cache_recommendation(
        self,
        location_key: str,
        category: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        """Cache location-based recommendations"""
        cache_key = f"recommendations:{location_key}:{category}"

        if self._connected:
            self.redis_client.setex(
                cache_key,
                timedelta(minutes=30),
                json.dumps(results)
            )
        else:
            self._memory_cache[cache_key] = results

        return True

    async def get_cached_recommendations(
        self,
        location_key: str,
        category: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached recommendations"""
        cache_key = f"recommendations:{location_key}:{category}"

        if self._connected:
            data = self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        else:
            return self._memory_cache.get(cache_key)

    async def update_context(
        self,
        session_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """Update journey context"""
        session = await self.get_session(session_id)

        if not session:
            session = await self.create_session(session_id)

        session["journey_context"].update(context)

        return await self.update_session(session_id, session)

    async def track_user_feedback(
        self,
        session_id: str,
        business_id: str,
        rating: int,
        feedback_type: str
    ) -> bool:
        """Track user feedback for businesses"""
        feedback_key = f"feedback:{session_id}:{business_id}"

        feedback_data = {
            "business_id": business_id,
            "rating": rating,
            "type": feedback_type,
            "timestamp": datetime.now().isoformat()
        }

        if self._connected:
            self.redis_client.setex(
                feedback_key,
                timedelta(days=90),
                json.dumps(feedback_data)
            )
        else:
            self._memory_cache[feedback_key] = feedback_data

        return True

    async def get_user_feedback_history(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get user's feedback history"""
        pattern = f"feedback:{session_id}:*"
        feedback_list = []

        if self._connected:
            keys = self.redis_client.keys(pattern)
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    feedback_list.append(json.loads(data))
        else:
            for key in self._memory_cache:
                if key.startswith(f"feedback:{session_id}:"):
                    feedback_list.append(self._memory_cache[key])

        return feedback_list

    async def learn_preference_pattern(
        self,
        session_id: str,
        pattern_type: str,
        pattern_data: Dict[str, Any]
    ) -> bool:
        """Learn and store user preference patterns"""
        pattern_key = f"pattern:{session_id}:{pattern_type}"

        existing_pattern = None
        if self._connected:
            existing = self.redis_client.get(pattern_key)
            if existing:
                existing_pattern = json.loads(existing)
        else:
            existing_pattern = self._memory_cache.get(pattern_key)

        if existing_pattern:
            existing_pattern["occurrences"] = existing_pattern.get("occurrences", 0) + 1
            existing_pattern["last_seen"] = datetime.now().isoformat()
            existing_pattern["data"] = pattern_data
        else:
            existing_pattern = {
                "type": pattern_type,
                "occurrences": 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "data": pattern_data
            }

        if self._connected:
            self.redis_client.setex(
                pattern_key,
                timedelta(days=90),
                json.dumps(existing_pattern)
            )
        else:
            self._memory_cache[pattern_key] = existing_pattern

        return True