import unittest

from config import Settings
from services.alerts.alert_engine import MarketAlertEngine
from services.data_providers import provider_registry


def _engine() -> MarketAlertEngine:
    return MarketAlertEngine(Settings(ALERT_PROBABILITY_CHANGE_THRESHOLD=0.10))


class AlertEngineExtendedTestCase(unittest.IsolatedAsyncioTestCase):
    def test_probability_change_requires_prior_reading_and_material_delta(self):
        engine = _engine()
        self.assertEqual(engine.evaluate_probability_change("BTCUSDT", {"up": 0.7}, None, model_name="m", balanced_accuracy=0.7), [])
        self.assertEqual(engine.evaluate_probability_change("BTCUSDT", {"up": 0.75}, {"up": 0.7}, model_name="m", balanced_accuracy=0.7), [])
        alerts = engine.evaluate_probability_change("BTCUSDT", {"up": 0.85}, {"up": 0.7}, model_name="m", balanced_accuracy=0.7)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].event_type, "reliable_probability_change")

    def test_regime_change_requires_a_new_persisted_regime(self):
        engine = _engine()
        current = {"regime": "tendência de alta", "close": 100.0, "sma20": 95.0, "sma50": 90.0, "volatility_20d": 0.02}
        self.assertEqual(engine.evaluate_regime_change("BTCUSDT", current, None), [])
        self.assertEqual(engine.evaluate_regime_change("BTCUSDT", current, {"regime": "tendência de alta"}), [])
        alerts = engine.evaluate_regime_change("BTCUSDT", current, {"regime": "consolidação"})
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].details["regime"], "tendência de alta")

    async def test_provider_registry_is_explicit_about_unavailable_sources(self):
        statuses = {item.name: item for item in await provider_registry.statuses()}
        self.assertEqual(str(statuses["binance"].availability), "available")
        self.assertEqual(str(statuses["b3"].availability), "not_available")
        self.assertEqual(str(statuses["news"].availability), "not_available")
