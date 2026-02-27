"""
WebSocket Connection Manager

Manages multiple WebSocket connections grouped by match_id.
Supports broadcasting to all connections watching the same match.
"""

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # match_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, match_id: str):
        await ws.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(ws)

    def disconnect(self, ws: WebSocket, match_id: str):
        if match_id in self.active_connections:
            self.active_connections[match_id] = [
                c for c in self.active_connections[match_id] if c != ws
            ]
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]

    async def broadcast(self, match_id: str, data: dict):
        if match_id not in self.active_connections:
            return
        disconnected = []
        for conn in self.active_connections[match_id]:
            try:
                await conn.send_json(data)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            self.disconnect(conn, match_id)

    def get_connection_count(self, match_id: str = None) -> int:
        if match_id:
            return len(self.active_connections.get(match_id, []))
        return sum(len(conns) for conns in self.active_connections.values())
