# Real-Time Arabic Voice AI Agent

A local-first Arabic assistant for a fictional telecom company. It supports Arabic text immediately and a half-duplex browser voice turn when local ASR/TTS assets are installed. All customer data is synthetic.

> Status: reliable turn-based (half-duplex) reference implementation. It does **not** claim simultaneous listening and speech playback. The browser records one turn, sends it over WebSocket, receives a final transcription and response, then plays returned audio. Cancellation is a control message; server-side cancellation of an in-flight Whisper/Ollama operation is a planned enhancement.

## Architecture

```text
Browser mic ──WebSocket/WebM──> FFmpeg decode → Silero VAD gate → faster-whisper (local)
                                      │ final Arabic transcript
                                      v
                          FastAPI → LangGraph routing → scoped telecom tools
                                      │                         │
                             local Qwen/Ollama*           PostgreSQL synthetic data
                                      │
                           Piper / eSpeak-NG → WAV → browser playback
```

`*` The initial routing uses deterministic Arabic intent classification for reliable security tests. Qwen2.5 is provisioned locally for a constrained Arabic phrasing/intent extension; it must never be given authority to select a customer or execute writes. This separation is deliberate: authorization and write confirmation remain code-enforced.

## Quick start

```bash
cp .env.example .env
make setup
make models              # requires local Ollama
make up
# open http://localhost:8000
make test
make eval
make down
```

For a lightweight non-Docker development run, set `DATABASE_URL=sqlite+aiosqlite:///./telecom.db` and run `uvicorn app.main:app --reload`. The API demo identity is `Authorization: Bearer demo-cust_demo`; this is intentionally development-only and is rejected if `ALLOW_DEMO_AUTH=false`.

## Supported workflows

- `ما هي باقتي؟` — subscription details
- `استهلاكي كام جيجا؟` — current usage
- `ما هي الباقات المتاحة؟` — available plans
- `ما حالة التذكرة T-XXXXXXXX؟` — status of a ticket belonging to the current account
- `أريد تقديم شكوى...` — creates a proposed ticket; a distinct confirmation request is mandatory
- Ticket status is tenant scoped. A guessed ticket ID from another account gets the same generic not-found response.

## Model setup and hardware

`faster-whisper` downloads its selected Whisper model on first use. `small` is a reasonable CPU baseline but Arabic quality varies by accent, microphone, and noise. For interactive use, an NVIDIA GPU with at least 8 GB VRAM is recommended; CPU-only operation works but typically has noticeably higher turn latency. Qwen2.5 7B needs roughly 6–8 GB RAM in quantized Ollama form (more headroom is recommended). Docker image includes FFmpeg for WebM decoding.

Piper has no pinned bundled Arabic voice here, by design: voice-weight licenses must be verified separately. Add a compatible `*.onnx` and JSON metadata at `PIPER_VOICE_PATH`. If none is available, set `TTS_ENGINE=espeak-ng` (open-source, much less natural Arabic) and add `espeak-ng` to your host/image, or set `disabled` for text-only. See [LICENSES.md](LICENSES.md).

## Security and privacy

- Tools receive `customer_id` only from authenticated server session context, never from user/model arguments.
- Ticket writes are two-step and expire when consumed; account modifications are not implemented.
- Requests have field validation and a timeout. Tool failures return Arabic-safe messages.
- Raw audio is processed in memory and not logged or stored by default (`LOG_AUDIO=false`). A bounded 20-message server-memory history maintains the current session only; it is lost on process restart and is not persisted. Redis-backed state needs an explicit retention policy before production.
- Deploy behind TLS, replace demo auth with JWT/session middleware, restrict CORS, rotate credentials, and configure retention before handling any real data.

## Metrics and evaluation

Each response returns STT, tool, TTS (when present), and total turn latency. `/api/metrics` reports process-local p50/p95 response time. `make eval` runs scripted workflow checks and writes `eval/results.json`; it is not a claim of production benchmark results. See [benchmark protocol](eval/BENCHMARKS.md). The repository ships no audio. Follow `eval/data/README.md` to add consented/licensed Arabic audio and calculate WER/CER before reporting ASR quality.

## Tests

`make test` uses deterministic routing and local SQLite. It covers subscriptions, confirmation-gated ticket creation, cross-account isolation, and an injection attempt. Real-model tests should be kept separately and skipped by default because they require downloaded local weights; no hosted model/API is used.

## Limitations and next steps

Egyptian Arabic depends strongly on the chosen Whisper/TTS model and should be measured against your own consented evaluation set. The current ASR display is final-only, not incremental; WebSocket transport is chunk-ready but browser audio is sent per completed turn. Add streaming Whisper segments, cached model instances, Redis-backed session state, verified bearer authentication for WebSockets, and cancellation propagation before calling this a production low-latency or full-duplex system.
