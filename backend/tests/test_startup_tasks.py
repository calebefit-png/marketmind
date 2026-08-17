import asyncio
import logging
import unittest

from services.startup_tasks import start_database_initialization


class StartupTasksTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_database_initializer_runs_without_blocking_startup(self):
        started = asyncio.Event()
        release = asyncio.Event()

        async def initializer() -> bool:
            started.set()
            await release.wait()
            return True

        task = start_database_initialization(initializer, logging.getLogger("marketmind.startup-test"))

        self.assertFalse(task.done())
        await started.wait()
        self.assertFalse(task.done())

        release.set()
        self.assertTrue(await task)

    async def test_initializer_failure_is_consumed_and_reported(self):
        async def initializer() -> bool:
            raise RuntimeError("database unavailable")

        logger = logging.getLogger("marketmind.startup-test.failure")
        with self.assertLogs(logger, level="ERROR") as captured:
            task = start_database_initialization(initializer, logger)
            await asyncio.sleep(0)
            await asyncio.sleep(0)

        self.assertTrue(task.done())
        self.assertIn("Falha inesperada ao inicializar o banco", "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
