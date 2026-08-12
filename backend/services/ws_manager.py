"""
services/ws_manager.py
Gerenciador de conexões WebSocket dos clientes do frontend.
Recebe ticks do BinanceStreamService e faz broadcast para todos os clientes.
"""

from __future__ import annotations

import logging

from fastapi import WebSocket

logger = logging.getLogger("marketmind.ws_manager")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("Cliente WS conectado. Total: %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("Cliente WS desconectado. Total: %d", len(self._connections))

    async def broadcast_json(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_json(payload)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


connection_manager = ConnectionManager()


async def on_binance_tick(payload: dict) -> None:
    """Callback registrado no BinanceStreamService para repassar ticks aos clientes."""
    await connection_manager.broadcast_json({"type": "price_tick", "data": payload})
