from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any, Dict, Optional, AsyncIterator
import json
import time
import logging

# api/chat.py
try:
    # When run as a package: `uvicorn api.chat:app` (local)
    from .chat_agents.orchestrator import stream_chat_py
except ImportError:
    # When run as a top-level module from inside api/: `uvicorn chat:app` (Railway)
    from chat_agents.orchestrator import stream_chat_py
    
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# --- Allow Vercel frontend to call Render backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # or lock to your vercel domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    selectedChatModel: str
    requestHints: Optional[Dict[str, Any]] = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    # Create the async generator that will *yield* SSE events
    async def event_stream() -> AsyncIterator[bytes]:
        start = time.time()
        try:
            async for chunk in stream_chat_py(
                chat_request.messages,
                chat_request.selectedChatModel,
                chat_request.requestHints,
            ):
                # Ensure each chunk is bytes
                yield chunk.encode("utf-8")
        finally:
            duration_ms = int((time.time() - start) * 1000)
            # Send a final metrics event (your frontend can listen for it)
            metrics = {"type": "metrics", "duration_ms": duration_ms}
            yield f"data: {json.dumps(metrics)}\n\n".encode("utf-8")

    # SSE-friendly headers (and disable proxy buffering hints)
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # helps some proxies avoid buffering SSE
    }

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)
