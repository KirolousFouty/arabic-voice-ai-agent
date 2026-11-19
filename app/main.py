import asyncio
import json
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.workflow import invoke
from app.config import settings
from app.db.database import initialize_database
from app.schemas.models import ChatRequest, ChatResponse, ConfirmationRequest
from app.services.speech import synthesize, transcribe_wav
from app.services.telecom_tools import create_support_ticket
from app.services.vad import contains_speech_in_webm

# Replace this demo mapping with verified identity/JWT middleware in deployment.
sessions: dict[str, dict] = defaultdict(dict)
latencies: list[float] = []

@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    yield

app = FastAPI(title="Real-Time Arabic Voice AI Agent", lifespan=lifespan)
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir = Path.cwd() / "app" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def customer_for(authorization: str | None) -> str:
    if settings.allow_demo_auth and authorization == "Bearer demo-cust_demo": return "cust_demo"
    raise HTTPException(401, "يلزم رمز جلسة صالح.")

async def process(req: ChatRequest, customer_id: str) -> ChatResponse:
    started = time.perf_counter()
    result = await asyncio.wait_for(invoke(req.message, customer_id), timeout=settings.request_timeout_seconds)
    if result.get("pending_ticket"):
        sessions[req.session_id]["pending_ticket"] = result["pending_ticket"]
    history = sessions[req.session_id].setdefault("history", [])
    history.extend([{"role": "user", "text": req.message}, {"role": "assistant", "text": result["answer"]}])
    # Bounded in-memory history; use Redis with an explicit retention policy in production.
    del history[:-20]
    elapsed = (time.perf_counter() - started) * 1000
    latencies.append(elapsed)
    metrics = {**result.get("metrics", {}), "total_ms": round(elapsed, 1)}
    return ChatResponse(text=result["answer"], requires_confirmation=bool(result.get("pending_ticket")), tool_status=result.get("intent"), metrics=metrics)

@app.get("/")
async def index(): return FileResponse(static_dir / "index.html")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    return await process(req, customer_for(authorization))

@app.post("/api/confirm", response_model=ChatResponse)
async def confirm(req: ConfirmationRequest, authorization: str | None = Header(default=None)):
    customer_id = customer_for(authorization); pending = sessions[req.session_id].pop("pending_ticket", None)
    if not pending: raise HTTPException(409, "لا يوجد طلب إنشاء تذكرة بانتظار التأكيد.")
    if not req.confirmed: return ChatResponse(text="تم إلغاء إنشاء التذكرة.")
    start = time.perf_counter(); result = await create_support_ticket(customer_id, **pending)
    ms = round((time.perf_counter()-start)*1000, 1)
    return ChatResponse(text=f"تم إنشاء تذكرة الدعم رقم {result['ticket_id']} بنجاح.", tool_status="ticket_created", metrics={"tool_ms": ms, "total_ms": ms})

@app.get("/api/metrics")
async def metrics(authorization: str | None = Header(default=None)):
    customer_for(authorization)
    if not latencies: return {"count": 0}
    sorted_values = sorted(latencies)
    return {"count": len(latencies), "p50_ms": sorted_values[len(sorted_values)//2], "p95_ms": sorted_values[min(len(sorted_values)-1, int(len(sorted_values)*.95))]}

@app.websocket("/ws/voice")
async def voice(ws: WebSocket):
    # Browser sends JSON control messages and one complete WAV/WebM audio binary per turn.
    await ws.accept(); customer_id = "cust_demo"  # demo websocket identity; production: validate signed token before accept.
    session_id = ""
    try:
        while True:
            message = await ws.receive()
            if message.get("text"):
                control = json.loads(message["text"])
                if control.get("type") == "start":
                    session_id = str(control.get("session_id", ""))
                    await ws.send_json({"type": "status", "value": "listening"})
                elif control.get("type") == "cancel":
                    await ws.send_json({"type": "status", "value": "cancelled"})
            elif message.get("bytes"):
                await ws.send_json({"type": "status", "value": "transcribing"}); started = time.perf_counter()
                try:
                    if not await contains_speech_in_webm(message["bytes"]):
                        await ws.send_json({"type": "error", "message": "لم أسمع كلاماً واضحاً. حاول مرة أخرى."})
                        continue
                    transcript = await transcribe_wav(message["bytes"])
                    stt_ms = round((time.perf_counter()-started)*1000, 1)
                    await ws.send_json({"type": "transcript", "text": transcript, "final": True})
                    reply = await process(ChatRequest(message=transcript, session_id=session_id or "browser"), customer_id)
                    await ws.send_json({"type": "response", **reply.model_dump(), "metrics": {**reply.metrics, "stt_ms": stt_ms}})
                    tts_start = time.perf_counter(); wav = await synthesize(reply.text)
                    if wav: await ws.send_bytes(wav); await ws.send_json({"type": "tts_metrics", "tts_ms": round((time.perf_counter()-tts_start)*1000, 1)})
                except RuntimeError as exc: await ws.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect: pass
