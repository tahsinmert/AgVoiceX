import logging
from fastapi import WebSocket

from app.db.session import SessionLocal
from app.schemas.conversations import ConversationRequest
from app.services.conversations import ConversationService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)

class VoiceOrchestrator:
    def __init__(self):
        self.stt_service = STTService()
        self.tts_service = TTSService()

    async def handle_connection(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_json({"type": "ready"})
        logger.info("Voice connection accepted.")
        reservation_type = websocket.query_params.get("reservation_type") or ""
        scenario = websocket.query_params.get("scenario") or ""
        
        try:
            while True:
                # 1. Receive audio data from client
                data = await websocket.receive_bytes()
                logger.info(f"Received audio chunk: {len(data)} bytes")
                
                text = await self.stt_service.transcribe(data)
                
                if not text.strip():
                    continue
                
                logger.info(f"User said: {text}")
                
                with SessionLocal() as db:
                    response = await ConversationService(db).handle(
                        ConversationRequest(
                            message=text,
                            channel="voice",
                            metadata={"reservation_type": reservation_type, "scenario": scenario},
                        )
                    )
                
                await websocket.send_json(
                    {
                        "type": "transcript",
                        "text": text,
                        "reply": response.reply,
                        "intent": response.intent.intent,
                        "conversation_id": response.conversation_id,
                        "reservation_id": response.reservation_id,
                    }
                )

                async for audio_chunk in self.tts_service.generate_audio_stream(response.reply):
                    await websocket.send_bytes(audio_chunk)
                    
        except Exception as e:
            logger.error(f"Voice connection closed: {e}")
            await self._send_error(websocket, str(e))
        finally:
            logger.info("Voice connection ended.")

    @staticmethod
    async def _send_error(websocket: WebSocket, message: str) -> None:
        try:
            await websocket.send_json({"type": "error", "message": message})
        except Exception:
            logger.debug("Could not send voice error to websocket.", exc_info=True)
