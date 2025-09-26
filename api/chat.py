from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Any, Dict, AsyncIterator
import logging
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import json

from .chat_agents.orchestrator import stream_chat_py


# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

app = FastAPI()

# Add CORS for frontend (allow * for dev; restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, set to your domain e.g. ["https://project-eve-mu.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    selectedChatModel: str
    requestHints: Dict[str, Any]

# Dynamic route path: / for Vercel (proxied root), /api/chat for local uvicorn (sub-path)
route_path = '/' if os.environ.get('VERCEL') else '/api/chat'

# Debug middleware to log incoming requests (remove in prod if sensitive)
@app.middleware("http")
async def debug_request(request: Request, call_next):
    if request.url.path == route_path and request.method == 'POST':
        body = await request.body()
        request._body = body  # Restore body for Pydantic (FastAPI consumes it)
        try:
            parsed_body = json.loads(body.decode('utf-8'))
            logging.info(f"Request body parsed: messages length={len(parsed_body.get('messages', []))}, model={parsed_body.get('selectedChatModel')}")
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in request body")
        logging.info(f"Request headers: {dict(request.headers)}")  # Log headers if needed
    response = await call_next(request)
    return response

async def safe_stream_chat_py(messages: List[Dict[str, Any]], selectedChatModel: str, requestHints: Dict[str, Any]) -> AsyncIterator[str]:
    try:
        logging.info(f"Starting stream_chat_py with model: {selectedChatModel}, messages count: {len(messages)}")
        async for chunk in stream_chat_py(messages, selectedChatModel, requestHints):
            yield chunk
        logging.info("stream_chat_py completed successfully")
    except Exception as e:
        logging.error(f"Error in stream_chat_py: {str(e)}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'text-end'})}\n\n"
        yield f"data: {json.dumps({'type': 'finish'})}\n\n"

@app.post(route_path)
async def chat_endpoint(chat_request: ChatRequest):
    logging.info(f"Chat endpoint hit with model: {chat_request.selectedChatModel}, messages count: {len(chat_request.messages)}")
    return StreamingResponse(
        safe_stream_chat_py(
            chat_request.messages,
            chat_request.selectedChatModel,
            chat_request.requestHints
        ),
        media_type="text/event-stream",
    )
