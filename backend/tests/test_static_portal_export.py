import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = REPOSITORY_ROOT / "backend" / "static"


class StaticPortalExportTestCase(unittest.TestCase):
    def test_core_portal_routes_are_exported_as_directory_indexes(self):
        expected_routes = (
            "index.html",
            "acoes/index.html",
            "fiis/index.html",
            "etfs/index.html",
            "bdrs/index.html",
            "cripto/index.html",
            "renda-fixa/index.html",
            "rankings/index.html",
            "rastreadores/index.html",
            "comparador/index.html",
            "carteira/index.html",
            "dividendos/index.html",
            "macro/index.html",
            "alerts/index.html",
        )

        missing_routes = [route for route in expected_routes if not (STATIC_DIR / route).is_file()]

        self.assertEqual(missing_routes, [])

    def test_static_home_contains_the_portal_identity(self):
        homepage = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

        self.assertIn("MarketMind", homepage)
        self.assertIn("Mercado em contexto, não em ruído", homepage)
        self.assertNotIn("github_pat_", homepage)


if __name__ == "__main__":
    unittest.main()
