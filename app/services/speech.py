"""Optional local-only speech adapters. Audio remains in process and is never persisted."""
import asyncio
import subprocess
import tempfile
from pathlib import Path

from app.config import settings


async def transcribe_wav(audio: bytes) -> str:
    def work():
        try:
            from faster_whisper import WhisperModel
            with tempfile.NamedTemporaryFile(suffix=".webm") as input_file:
                input_file.write(audio); input_file.flush()
                # In production cache this model at application lifespan; kept lazy for CPU-only installs.
                model = WhisperModel(settings.whisper_model, device="auto", compute_type="int8")
                segments, _ = model.transcribe(input_file.name, language="ar", vad_filter=True)
                return " ".join(s.text.strip() for s in segments)
        except ImportError as exc: raise RuntimeError("ميزة التعرف على الكلام غير مثبّتة.") from exc
    return await asyncio.to_thread(work)

async def synthesize(text: str) -> bytes | None:
    if settings.tts_engine == "disabled": return None
    if settings.tts_engine == "espeak-ng":
        # Open-source fallback only; intelligibility/Arabic naturalness are substantially worse than Piper.
        def espeak():
            with tempfile.NamedTemporaryFile(suffix=".wav") as output:
                subprocess.run(["espeak-ng", "-v", "ar", "-w", output.name, text], check=True, capture_output=True)
                return Path(output.name).read_bytes()
        return await asyncio.to_thread(espeak)
    path = Path(settings.piper_voice_path)
    if not path.exists(): return None
    def work():
        import io
        import wave

        from piper import PiperVoice
        voice = PiperVoice.load(str(path)); buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            voice.synthesize_wav(text, wav)
        return buf.getvalue()
    return await asyncio.to_thread(work)
