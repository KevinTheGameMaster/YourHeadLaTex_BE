from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter(tags=["websocket"])

# In-memory: doc_id -> list of active connections
connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/{doc_id}/{user_name}")
async def websocket_endpoint(websocket: WebSocket, doc_id: str, user_name: str):
    await websocket.accept()

    connections.setdefault(doc_id, []).append(websocket)

    await broadcast(doc_id, {"type": "user_joined", "user": user_name}, exclude=websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "edit":
                await broadcast(doc_id, {
                    "type": "edit",
                    "content": data["content"],
                    "user": user_name,
                    "cursor": data.get("cursor"),
                }, exclude=websocket)

    except WebSocketDisconnect:
        connections[doc_id].remove(websocket)
        await broadcast(doc_id, {"type": "user_left", "user": user_name})


async def broadcast(doc_id: str, message: dict, exclude: WebSocket = None):
    dead = []
    for ws in connections.get(doc_id, []):
        if ws is exclude:
            continue
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections[doc_id].remove(ws)