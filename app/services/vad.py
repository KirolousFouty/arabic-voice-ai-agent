"""Silero VAD adapter used to gate audio chunks; safely falls back to browser turn boundaries."""
import asyncio
import subprocess
import tempfile


async def contains_speech(pcm_16khz: bytes) -> bool:
    """Return speech likelihood decision. Call after decoding WebM to 16kHz mono PCM."""
    def work():
        try:
            import torch
            from silero_vad import get_speech_timestamps, load_silero_vad
            samples = torch.frombuffer(memoryview(pcm_16khz), dtype=torch.int16).float() / 32768
            return bool(get_speech_timestamps(samples, load_silero_vad(), sampling_rate=16000))
        except ImportError: return True
    return await asyncio.to_thread(work)

async def contains_speech_in_webm(audio: bytes) -> bool:
    """Decode a browser chunk and apply Silero before costly ASR; requires FFmpeg."""
    def decode() -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".webm") as source, tempfile.NamedTemporaryFile(suffix=".pcm") as target:
            source.write(audio); source.flush()
            subprocess.run(["ffmpeg", "-y", "-i", source.name, "-ac", "1", "-ar", "16000", "-f", "s16le", target.name], check=True, capture_output=True)
            return target.read()
    try: return await contains_speech(await asyncio.to_thread(decode))
    except (FileNotFoundError, subprocess.CalledProcessError): return True
