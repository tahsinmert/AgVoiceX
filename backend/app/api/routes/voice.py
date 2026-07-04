from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.voice_orchestrator import VoiceOrchestrator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
orchestrator = VoiceOrchestrator()

@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    try:
        await orchestrator.handle_connection(websocket)
    except WebSocketDisconnect:
        logger.info("Client disconnected from voice stream.")
    except Exception as e:
        logger.error(f"Error in voice stream endpoint: {e}")
