import logging
import importlib.util

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.services.voice_orchestrator import VoiceOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)
orchestrator = VoiceOrchestrator()


@router.get("/capabilities")
def voice_capabilities() -> dict[str, str | bool]:
    stt_available = importlib.util.find_spec("mlx_whisper") is not None
    tts_available = importlib.util.find_spec("TTS") is not None
    return {
        "stt_available": stt_available,
        "tts_available": tts_available,
        "stt_model_path": settings.stt_model_path,
        "tts_model_name": settings.tts_model_name,
        "tts_device": settings.tts_device,
        "tts_language": settings.tts_language,
        "mode": "local",
    }


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    try:
        await orchestrator.handle_connection(websocket)
    except WebSocketDisconnect:
        logger.info("Client disconnected from voice stream.")
    except Exception as e:
        logger.error(f"Error in voice stream endpoint: {e}")
