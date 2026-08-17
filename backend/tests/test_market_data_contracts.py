"""Testes sem banco para os contratos públicos da camada de dados de mercado."""

import ast
from pathlib import Path
import unittest

from schemas.market_data import MarketQuoteRead
from services.data_providers.contracts import DataStatus


class MarketDataContractTests(unittest.TestCase):
    def test_openapi_exposes_asset_catalog_detail_and_history_routes(self) -> None:
        route_file = Path(__file__).resolve().parents[1] / "api" / "routes" / "market.py"
        tree = ast.parse(route_file.read_text(encoding="utf-8"))
        paths = {
            decorator.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "get"
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
            and isinstance(decorator.args[0].value, str)
        }
        self.assertTrue({"/market/assets", "/market/assets/{symbol}", "/market/assets/{symbol}/history"}.issubset(paths))

    def test_unavailable_quote_never_requires_a_fabricated_price(self) -> None:
        quote = MarketQuoteRead(data_status=DataStatus.UNAVAILABLE.value)
        self.assertIsNone(quote.value)
        self.assertEqual(quote.data_status, "unavailable")
