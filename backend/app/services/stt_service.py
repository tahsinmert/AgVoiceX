import tempfile
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, model_path: str = settings.stt_model_path):
        logger.info("Initializing MLX Whisper for Apple Silicon...")
        self.model_path = model_path
        logger.info("MLX Whisper ready.")

    async def transcribe(self, audio_bytes: bytes) -> str:
        tmp_path: str | None = None
        try:
            import mlx_whisper

            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
                
            # Transcribe natively using MLX
            result = mlx_whisper.transcribe(tmp_path, path_or_hf_repo=self.model_path)
            text = result["text"]
            
            logger.info(f"STT Transcribed (MLX): {text}")
            return text
        except Exception as e:
            logger.error(f"Error in MLX Whisper STT transcribe: {e}")
            raise RuntimeError("Speech-to-text failed. Check the audio format and local Whisper model.") from e
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
