import logging
import asyncio
from pathlib import Path
import tempfile

from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(
        self,
        model_name: str = settings.tts_model_name,
        device: str = settings.tts_device,
        language: str = settings.tts_language,
        speaker: str = settings.tts_speaker,
        speaker_wav: str = settings.tts_speaker_wav,
    ):
        self.model_name = model_name
        self.device = device
        self.language = language
        self.speaker = speaker or None
        self.speaker_wav = speaker_wav or None
        self._tts = None

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        import torch

        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _client(self):
        if self._tts is None:
            from TTS.api import TTS

            device = self._resolve_device(self.device)
            logger.info("Loading Coqui TTS model %s on %s.", self.model_name, self.device)
            self._tts = TTS(model_name=self.model_name, progress_bar=False).to(device)
            logger.info("Coqui TTS model loaded.")
        return self._tts

    async def generate_audio_stream(self, text: str):
        """Generates an audio stream (WAV bytes) from text using Coqui TTS."""
        tmp_path: str | None = None
        try:
            loop = asyncio.get_event_loop()
            
            def synthesize():
                nonlocal tmp_path
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                kwargs = {
                    "text": text,
                    "file_path": tmp_path,
                    "language": self.language,
                }
                if self.speaker:
                    kwargs["speaker"] = self.speaker
                if self.speaker_wav:
                    kwargs["speaker_wav"] = self.speaker_wav

                self._client().tts_to_file(**kwargs)
                
                with open(tmp_path, "rb") as f:
                    return f.read()

            audio_bytes = await loop.run_in_executor(None, synthesize)
            yield audio_bytes
            
        except Exception as e:
            logger.error(f"Error in Coqui TTS generation: {e}")
            raise RuntimeError(
                "Text-to-speech failed. Configure TTS_SPEAKER or TTS_SPEAKER_WAV for the selected Coqui model."
            ) from e
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
