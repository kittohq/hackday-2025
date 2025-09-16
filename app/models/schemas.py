from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EmotionType(str, Enum):
    ANXIOUS = "anxious"
    RELAXED = "relaxed"
    FRUSTRATED = "frustrated"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    IMPATIENT = "impatient"

class IntentType(str, Enum):
    ROUTE_CHANGE = "route_change"
    COMFORT_ADJUSTMENT = "comfort_adjustment"
    INFORMATION_REQUEST = "information_request"
    STOP_REQUEST = "stop_request"
    TIME_INQUIRY = "time_inquiry"
    EMERGENCY = "emergency"
    SMALL_TALK = "small_talk"
    FEEDBACK = "feedback"

class ActionType(str, Enum):
    UPDATE_ROUTE = "update_route"
    ADJUST_TEMPERATURE = "adjust_temperature"
    CHANGE_MUSIC = "change_music"
    PROVIDE_INFO = "provide_info"
    CONFIRM_STOP = "confirm_stop"
    ALERT_DRIVER = "alert_driver"
    NONE = "none"

class EmotionState(BaseModel):
    state: EmotionType
    confidence: float = Field(ge=0.0, le=1.0)
    intensity: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    details: Optional[Dict[str, Any]] = {}

class RiderRequest(BaseModel):
    text: str
    audio_data: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    context: Optional[Dict[str, Any]] = {}

class VehicleState(BaseModel):
    location: Dict[str, float]
    speed: float
    eta_minutes: int
    route_name: str
    temperature: float
    music_playing: Optional[str] = None
    windows_open: bool = False
    destination: str
    traffic_conditions: str = "normal"

class AgentResponse(BaseModel):
    message: str
    intent: IntentType
    emotion_detected: EmotionState
    actions: List[Dict[str, Any]] = []
    suggestions: Optional[List[str]] = []
    confidence: float = Field(ge=0.0, le=1.0)

class UserPreferences(BaseModel):
    preferred_temperature: float = 72.0
    music_genre: Optional[str] = "relaxing"
    driving_style: str = "normal"
    language: str = "en"
    notification_level: str = "normal"
    favorite_stops: List[str] = []

class JourneyContext(BaseModel):
    journey_id: str
    start_location: Dict[str, float]
    destination: Dict[str, float]
    start_time: datetime
    estimated_arrival: datetime
    current_state: VehicleState
    rider_preferences: UserPreferences
    conversation_history: List[Dict[str, Any]] = []

class LocalRecommendation(BaseModel):
    name: str
    type: str
    distance_miles: float
    rating: Optional[float] = None
    estimated_detour_minutes: int
    description: Optional[str] = None