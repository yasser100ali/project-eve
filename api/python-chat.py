from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List

from backend.chat_agents.chat import stream_chat_py

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def _stream_response(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    messages: List[Dict[str, Any]] = payload.get("messages", [])
    selected_chat_model: str = payload.get("selectedChatModel", "default")
    request_hints: Dict[str, Any] = payload.get("requestHints", {})

    async for chunk in stream_chat_py(messages, selected_chat_model, request_hints):
        yield chunk.encode("utf-8")

async def _handle_post(body: bytes):
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON payload"}),
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
        },
        "body": _stream_response(payload),
    }

def handler(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Allow": "POST", "Content-Type": "application/json"},
            "body": json.dumps({"error": "Method Not Allowed"}),
        }

    body = request.body or b""
    return asyncio.run(_handle_post(body))
