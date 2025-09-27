from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional, AsyncIterator
import json
import time
import logging

# Import that works both locally (api.chat) and on Railway (chat)
try:
    from .chat_agents.orchestrator import stream_chat_py
except ImportError:
    from chat_agents.orchestrator import stream_chat_py

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow Vercel frontend to call Railway backend (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later: ["https://<your-vercel-app>.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Make fields permissive to avoid 422 while debugging
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    selectedChatModel: Optional[str] = None
    requestHints: Dict[str, Any] = Field(default_factory=dict)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    # TEMP: log headers + parsed body to confirm path/payload
    logger.info("x-from header: %s", request.headers.get("x-from"))
    logger.info("backendURL header: %s", request.headers.get("backendurl"))
    logger.info("payload keys: %s", list(chat_request.model_dump().keys()))

    # Friendly guard instead of hard 422 if model name missing
    if not chat_request.selectedChatModel:
        err = {"type": "error", "message": "selectedChatModel is required"}
        return StreamingResponse(
            iter([f"data: {json.dumps(err)}\n\n"]),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def event_stream() -> AsyncIterator[bytes]:
        start = time.time()
        try:
            async for chunk in stream_chat_py(
                chat_request.messages,
                chat_request.selectedChatModel,
                chat_request.requestHints,
            ):
                # Ensure each chunk is bytes; chunk should already be "data: {...}\n\n"
                yield chunk.encode("utf-8")
        except Exception as e:
            logger.exception("stream_chat_py failed")
            yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n".encode("utf-8")
        finally:
            duration_ms = int((time.time() - start) * 1000)
            yield f"data: {json.dumps({'type':'metrics','duration_ms':duration_ms})}\n\n".encode("utf-8")

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    # IMPORTANT: no trailing comma here
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
