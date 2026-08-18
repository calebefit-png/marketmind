from datetime import date, datetime, timezone

import pytest

from services.reference_tickers import ReferenceTickerService


def test_parse_ptax_uses_official_sale_rate_and_timestamp() -> None:
    value, as_of = ReferenceTickerService.parse_ptax(
        {"cotacaoCompra": 5.2, "cotacaoVenda": 5.2014, "dataHoraCotacao": "2026-08-17 13:04:48.745527"}
    )

    assert value == 5.2014
    assert as_of == datetime(2026, 8, 17, 13, 4, 48, 745527)


def test_ptax_params_quotes_date_for_odata_service() -> None:
    assert ReferenceTickerService.ptax_params(date(2026, 8, 17)) == {
        "@dataCotacao": "'08-17-2026'",
        "$top": "100",
        "$format": "json",
    }


def test_parse_yahoo_uses_value_previous_close_currency_and_market_time() -> None:
    value, previous_close, currency, as_of = ReferenceTickerService.parse_yahoo(
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "regularMarketPrice": 166_783.56,
                            "chartPreviousClose": 167_875.0,
                            "currency": "BRL",
                            "regularMarketTime": 1_786_997_820,
                        }
                    }
                ]
            }
        }
    )

    assert value == 166_783.56
    assert previous_close == 167_875.0
    assert currency == "BRL"
    assert as_of == datetime.fromtimestamp(1_786_997_820, tz=timezone.utc)


def test_parse_yahoo_rejects_empty_result() -> None:
    with pytest.raises(ValueError, match="sem resultado"):
        ReferenceTickerService.parse_yahoo({"chart": {"result": []}})
