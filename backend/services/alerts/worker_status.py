"""Persistência do heartbeat do processo isolado de alertas."""

from __future__ import annotations

from datetime import datetime, timezone

from database import AsyncSessionLocal
from models.alert import WorkerHeartbeat


class WorkerStatusService:
    """Atualiza um registro pequeno e recuperável para a saúde do worker."""

    def __init__(self, worker_name: str = "market_alert_worker") -> None:
        self.worker_name = worker_name

    async def heartbeat(
        self,
        *,
        processed_increment: int = 0,
        sent_increment: int = 0,
        error: Exception | None = None,
    ) -> None:
        if AsyncSessionLocal is None:
            return
        now = datetime.now(tz=timezone.utc)
        async with AsyncSessionLocal() as session:
            record = await session.get(WorkerHeartbeat, self.worker_name)
            if record is None:
                record = WorkerHeartbeat(worker_name=self.worker_name)
                session.add(record)
            record.last_run = now
            record.processed_events += max(processed_increment, 0)
            record.sent_alerts += max(sent_increment, 0)
            if error is None:
                record.status = "online"
                record.last_success = now
            else:
                record.status = "degraded"
                record.last_error = type(error).__name__[:160]
                record.last_error_at = now
            await session.commit()

    async def mark_offline(self) -> None:
        if AsyncSessionLocal is None:
            return
        async with AsyncSessionLocal() as session:
            record = await session.get(WorkerHeartbeat, self.worker_name)
            if record is not None:
                record.status = "offline"
                await session.commit()

    async def mark_scheduled(self) -> None:
        """Marca uma execução pontual concluída, sem aparentar que existe processo residente."""
        if AsyncSessionLocal is None:
            return
        async with AsyncSessionLocal() as session:
            record = await session.get(WorkerHeartbeat, self.worker_name)
            if record is not None:
                record.status = "scheduled"
                await session.commit()

    async def snapshot(self) -> WorkerHeartbeat | None:
        if AsyncSessionLocal is None:
            return None
        async with AsyncSessionLocal() as session:
            return await session.get(WorkerHeartbeat, self.worker_name)
