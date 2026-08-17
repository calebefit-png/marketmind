"""Testes de proteção contra statements PostgreSQL grandes demais."""

import unittest

from services.market_batches import (
    MARKET_CANDLE_UPSERT_BATCH_SIZE,
    batches,
)


class MarketCandleBatchTests(unittest.TestCase):
    def test_splits_long_backfill_into_safe_postgres_batches(self) -> None:
        rows = [{"row": index} for index in range(MARKET_CANDLE_UPSERT_BATCH_SIZE * 2 + 13)]

        result = batches(rows)

        self.assertEqual([len(batch) for batch in result], [2_000, 2_000, 13])
        self.assertEqual(sum(len(batch) for batch in result), len(rows))

    def test_rejects_non_positive_batch_size(self) -> None:
        with self.assertRaises(ValueError):
            batches([{"row": 1}], batch_size=0)
