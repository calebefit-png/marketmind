import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from services.alerts.alert_worker import AlertWorker
from services.alerts.scheduled_runner import main
from services.alerts.worker_status import WorkerStatusService


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

    async def test_heartbeat_normalizes_legacy_null_counters(self):
        record = SimpleNamespace(
            processed_events=None,
            sent_alerts=None,
            last_run=None,
            status=None,
            last_success=None,
        )

        class Session:
            async def get(self, *_args):
                return record

            async def commit(self):
                return None

        class SessionContext:
            async def __aenter__(self):
                return Session()

            async def __aexit__(self, *_args):
                return None

        with patch("services.alerts.worker_status.AsyncSessionLocal", return_value=SessionContext()):
            await WorkerStatusService().heartbeat(processed_increment=3, sent_increment=2)

        self.assertEqual(record.processed_events, 3)
        self.assertEqual(record.sent_alerts, 2)
        self.assertEqual(record.status, "online")
