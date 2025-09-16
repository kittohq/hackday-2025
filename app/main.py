from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime
import logging

from app.services.voice_service import VoiceService
from app.services.emotion_service import EmotionService
from app.services.conversation_engine import ConversationEngine
from app.services.redis_service import RedisService
from app.models.schemas import RiderRequest, VehicleState, EmotionState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dynamic Rider Experience Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

voice_service = VoiceService()
emotion_service = EmotionService()
conversation_engine = ConversationEngine()
redis_service = RedisService()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Dynamic Rider Experience Agent API", "status": "active"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)

    user_session = await redis_service.get_session(client_id)
    if not user_session:
        user_session = await redis_service.create_session(client_id)

    try:
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to Dynamic Rider Experience Agent",
            "session_id": client_id
        })

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "audio":
                transcription = await voice_service.transcribe(message["data"])

                emotion = await emotion_service.analyze(
                    audio_data=message["data"],
                    text=transcription
                )

                response = await conversation_engine.process(
                    text=transcription,
                    emotion=emotion,
                    session_id=client_id,
                    context=message.get("context", {})
                )

                await redis_service.add_to_history(client_id, {
                    "timestamp": datetime.now().isoformat(),
                    "user_input": transcription,
                    "emotion": emotion.dict(),
                    "agent_response": response
                })

                await websocket.send_json({
                    "type": "response",
                    "transcription": transcription,
                    "emotion": emotion.dict(),
                    "response": response,
                    "actions": response.get("actions", [])
                })

            elif message["type"] == "text":
                emotion = EmotionState(state="neutral", confidence=0.5)

                response = await conversation_engine.process(
                    text=message["data"],
                    emotion=emotion,
                    session_id=client_id,
                    context=message.get("context", {})
                )

                await websocket.send_json({
                    "type": "response",
                    "response": response,
                    "actions": response.get("actions", [])
                })

            elif message["type"] == "update_context":
                await redis_service.update_context(client_id, message["data"])
                await websocket.send_json({
                    "type": "context_updated",
                    "message": "Context updated successfully"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")
        manager.disconnect(websocket)

@app.post("/api/simulate_journey")
async def simulate_journey(journey_data: dict):
    """Simulate a journey with predefined scenarios"""
    scenarios = [
        {
            "trigger_time": 5,
            "event": "traffic_detected",
            "message": "I've detected heavy traffic ahead. We might be delayed by 10 minutes. Would you like me to find an alternative route?"
        },
        {
            "trigger_time": 15,
            "event": "comfort_check",
            "message": "We're halfway to your destination. How are you feeling? Is the temperature comfortable?"
        },
        {
            "trigger_time": 25,
            "event": "arrival_update",
            "message": "We'll be arriving in 5 minutes. I've found parking available near the entrance."
        }
    ]

    return {
        "journey_id": journey_data.get("journey_id"),
        "scenarios": scenarios,
        "estimated_duration": 30
    }

@app.get("/api/health")
async def health_check():
    services_status = {
        "voice_service": voice_service.is_connected(),
        "emotion_service": emotion_service.is_connected(),
        "redis": await redis_service.ping(),
        "conversation_engine": True
    }

    all_healthy = all(services_status.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_status,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)