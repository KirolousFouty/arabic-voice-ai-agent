FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg espeak-ng && rm -rf /var/lib/apt/lists/*
COPY . .
# Keep the default local image usable on CPU/ARM. Silero/PyTorch remains an
# optional extra (`pip install '.[speech]'`) because it is a multi-GB install.
RUN pip install --no-cache-dir '.[dev]' faster-whisper piper-tts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
