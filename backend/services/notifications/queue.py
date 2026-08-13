"""Fila interna de entregas para que provedores lentos não bloqueiem o radar."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

from services.notifications.contracts import Alert, NotificationChannel
from services.notifications.notification_service import NotificationService

logger = logging.getLogger("marketmind.notification_queue")


@dataclass(frozen=True)
class NotificationJob:
    alert: Alert
    channels: tuple[NotificationChannel, ...]
    scope_key: str


class NotificationQueue:
    """Fila limitada, serial e tolerante a falhas para alertas já avaliados."""

    def __init__(
        self,
        notification_service: NotificationService,
        *,
        maxsize: int = 200,
        on_delivery: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        self._service = notification_service
        self._queue: asyncio.Queue[NotificationJob | None] = asyncio.Queue(maxsize=maxsize)
        self._task: asyncio.Task[None] | None = None
        self._on_delivery = on_delivery

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._consume(), name="marketmind-notification-queue")

    async def enqueue(
        self,
        alert: Alert,
        channels: Iterable[NotificationChannel],
        *,
        scope_key: str,
    ) -> bool:
        selected_channels = tuple(channels)
        if not selected_channels:
            return False
        job = NotificationJob(alert=alert, channels=selected_channels, scope_key=scope_key)
        try:
            self._queue.put_nowait(job)
        except asyncio.QueueFull:
            logger.warning("Fila de alertas cheia; evento descartado: %s", alert.dedup_key)
            return False
        return True

    async def stop(self) -> None:
        if self._task is None:
            return
        await self._queue.put(None)
        await self._task
        self._task = None

    async def _consume(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                if job is None:
                    return
                delivered = await self._service.send_alert(
                    job.alert, job.channels, scope_key=job.scope_key
                )
                if self._on_delivery is not None:
                    await self._on_delivery(delivered)
            except Exception as exc:
                # A persistência e a próxima mensagem continuam operacionais.
                logger.warning("Falha no consumo da fila de notificações: %s", type(exc).__name__)
                if self._on_delivery is not None:
                    await self._on_delivery(False)
            finally:
                self._queue.task_done()
