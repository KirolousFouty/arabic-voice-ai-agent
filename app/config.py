from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./telecom.db"
    redis_url: str = "redis://localhost:6379/0"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct"
    whisper_model: str = "small"
    piper_voice_path: str = "models/tts/ar_JO-kareem-medium.onnx"
    tts_engine: str = "piper"  # piper | espeak-ng | disabled
    allow_demo_auth: bool = True
    log_audio: bool = False
    request_timeout_seconds: int = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
