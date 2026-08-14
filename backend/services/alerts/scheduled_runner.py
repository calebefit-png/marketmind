"""Ponto de entrada para uma única varredura agendada do radar de alertas."""

from __future__ import annotations

import asyncio

from services.alerts.alert_worker import AlertWorker


async def main() -> None:
    await AlertWorker().run_once()


if __name__ == "__main__":
    asyncio.run(main())
