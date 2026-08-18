"""Testes do parser de registros de largura fixa COTAHIST."""

from datetime import datetime, timezone
import unittest

from services.data_providers.b3_cotahist import normalize_b3_currency, parse_cotahist_lines
from services.data_providers.contracts import DataStatus


def cotahist_line(
    *,
    symbol: str = "PETR4",
    market_type: str = "010",
    specification: str = "ON      NM",
) -> str:
    """Cria um registro mínimo com as colunas relevantes do layout COTAHIST."""
    chars = [" "] * 245

    def put(start: int, end: int, value: str) -> None:
        chars[start:end] = list(value.ljust(end - start)[: end - start])

    put(0, 2, "01")
    put(2, 10, "20240814")
    put(12, 24, symbol)
    put(24, 27, market_type)
    put(27, 39, "PETROBRAS PN")
    put(39, 49, specification)
    put(52, 56, "R$")
    put(56, 69, "0000000037500")
    put(69, 82, "0000000038200")
    put(82, 95, "0000000037100")
    put(108, 121, "0000000038000")
    put(147, 152, "00123")
    put(170, 188, "000000000123456789")
    return "".join(chars)


class B3CotahistParserTests(unittest.TestCase):
    def test_parses_requested_spot_market_symbol_as_closing_candle(self) -> None:
        points = parse_cotahist_lines([cotahist_line()], {"PETR4"})

        self.assertEqual(len(points), 1)
        point = points[0]
        self.assertEqual(point.asset.symbol, "PETR4")
        self.assertEqual(point.asset.exchange, "B3")
        self.assertEqual(point.asset.asset_class, "stock")
        self.assertEqual(point.asset.currency, "BRL")
        self.assertEqual(point.close, 380.0)
        self.assertEqual(point.volume, 1234567.89)
        self.assertEqual(point.trades, 123)
        self.assertEqual(point.data_status, DataStatus.CLOSING)
        self.assertEqual(point.time, datetime(2024, 8, 14, tzinfo=timezone.utc))

    def test_ignores_unrequested_symbols_and_non_spot_records(self) -> None:
        points = parse_cotahist_lines(
            [cotahist_line(symbol="VALE3"), cotahist_line(symbol="PETR4", market_type="012")],
            {"PETR4"},
        )
        self.assertEqual(points, [])

    def test_classifies_watchlist_fiis_and_etfs_when_cotahist_uses_generic_cota_specification(self) -> None:
        points = parse_cotahist_lines(
            [
                cotahist_line(symbol="HGLG11", specification="CI"),
                cotahist_line(symbol="BOVA11", specification="CI"),
                cotahist_line(symbol="OUTRO11", specification="CI"),
            ],
            {"HGLG11", "BOVA11", "OUTRO11"},
        )

        asset_classes = {point.asset.symbol: point.asset.asset_class for point in points}
        self.assertEqual(asset_classes["HGLG11"], "fii")
        self.assertEqual(asset_classes["BOVA11"], "etf")
        self.assertEqual(asset_classes["OUTRO11"], "fund_or_etf")

    def test_normalizes_b3_currency_markers_to_iso_codes(self) -> None:
        self.assertEqual(normalize_b3_currency("R$"), "BRL")
        self.assertEqual(normalize_b3_currency("US$"), "USD")
        self.assertEqual(normalize_b3_currency("BRL"), "BRL")
