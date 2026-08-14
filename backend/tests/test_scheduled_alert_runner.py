import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from services.alerts.alert_worker import AlertWorker
from services.alerts.scheduled_runner import main


class ScheduledAlertRunnerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_single_run_processes_both_sources_and_ends_in_scheduled_state(self):
        worker = AlertWorker()
        worker._run_cycle = AsyncMock()
        worker._queue.start = AsyncMock()
        worker._queue.wait_until_idle = AsyncMock()
        worker._queue.stop = AsyncMock()
        worker._status.heartbeat = AsyncMock()
        worker._status.mark_scheduled = AsyncMock()

        with patch("services.alerts.alert_worker.init_db", new_callable=AsyncMock, return_value=True), patch(
            "services.alerts.alert_worker.dispose_db", new_callable=AsyncMock
        ) as mocked_dispose:
            await worker.run_once()

        self.assertEqual(worker._run_cycle.await_count, 2)
        worker._queue.start.assert_awaited_once_with()
        worker._queue.wait_until_idle.assert_awaited_once_with()
        worker._queue.stop.assert_awaited_once_with()
        worker._status.heartbeat.assert_awaited_once_with()
        worker._status.mark_scheduled.assert_awaited_once_with()
        mocked_dispose.assert_awaited_once_with()

    async def test_cli_entrypoint_runs_the_single_worker_cycle(self):
        with patch.object(AlertWorker, "run_once", new_callable=AsyncMock) as mocked_run_once:
            await main()

        mocked_run_once.assert_awaited_once_with()
