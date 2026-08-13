"""Regras transparentes para transformar dados de mercado em alertas relevantes."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from datetime import datetime, timezone

import pandas as pd

from config import Settings, settings
from services.notifications.contracts import Alert, AlertSeverity
from services.technical_analysis import candles_to_dataframe, compute_indicators


class MarketAlertEngine:
    """Avalia preço, candles e macro sem fabricar eventos ou recomendações."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings
        self._ticks: deque[tuple[datetime, float]] = deque()

    def evaluate_tick(self, tick: dict) -> list[Alert]:
        """Detecta movimento material dentro da janela configurada de preço verificável."""
        try:
            price = float(tick["price"])
            timestamp = datetime.fromisoformat(str(tick["timestamp"]).replace("Z", "+00:00"))
            asset = str(tick["asset"]).upper()
        except (KeyError, TypeError, ValueError):
            return []
        if price <= 0:
            return []
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        self._ticks.append((timestamp, price))
        cutoff = timestamp.timestamp() - self._settings.ALERT_PRICE_WINDOW_SECONDS
        while self._ticks and self._ticks[0][0].timestamp() < cutoff:
            self._ticks.popleft()
        if len(self._ticks) < 2:
            return []

        base_time, base_price = self._ticks[0]
        change_pct = (price / base_price - 1) * 100
        threshold = abs(self._settings.ALERT_PRICE_MOVE_THRESHOLD_PCT)
        if abs(change_pct) < threshold:
            return []
        direction = "up" if change_pct > 0 else "down"
        severity = AlertSeverity.CRITICAL if abs(change_pct) >= threshold * 2 else AlertSeverity.WARNING
        minutes = max((timestamp - base_time).total_seconds() / 60, 1)
        movement = "alta" if direction == "up" else "queda"
        return [
            Alert(
                asset=asset,
                event_type=f"price_move_{direction}",
                severity=severity,
                title=f"Movimento de preço: {movement} de {change_pct:+.2f}%",
                message=(
                    f"{asset} variou {change_pct:+.2f}% em aproximadamente {minutes:.0f} min, "
                    f"de {base_price:,.2f} para {price:,.2f}. Hipótese: aceleração intradiária "
                    "acima do limiar monitorado. Condição de invalidação: retorno à faixa do preço-base."
                ),
                source=str(tick.get("source", "binance")),
                details={
                    "price": round(price, 8),
                    "base_price": round(base_price, 8),
                    "change_pct": round(change_pct, 4),
                    "window_minutes": round(minutes, 2),
                },
                cooldown_seconds=self._settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
            )
        ]

    def evaluate_candles(self, candles: Iterable[dict], asset: str = "BTCUSDT") -> list[Alert]:
        """Extrai sinais técnicos somente quando o histórico é suficiente para calculá-los."""
        df = candles_to_dataframe(list(candles))
        if len(df) < 30:
            return []
        indicators = compute_indicators(df)
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        asset = asset.upper()
        alerts: list[Alert] = []

        if indicators.rsi is not None and indicators.rsi >= self._settings.ALERT_RSI_OVERBOUGHT:
            alerts.append(self._rsi_alert(asset, indicators.rsi, "overbought"))
        elif indicators.rsi is not None and indicators.rsi <= self._settings.ALERT_RSI_OVERSOLD:
            alerts.append(self._rsi_alert(asset, indicators.rsi, "oversold"))

        previous_indicators = compute_indicators(df.iloc[:-1].copy())
        if all(
            value is not None
            for value in (indicators.macd, indicators.macd_signal, previous_indicators.macd, previous_indicators.macd_signal)
        ):
            crossed_up = previous_indicators.macd <= previous_indicators.macd_signal and indicators.macd > indicators.macd_signal
            crossed_down = previous_indicators.macd >= previous_indicators.macd_signal and indicators.macd < indicators.macd_signal
            if crossed_up or crossed_down:
                direction = "up" if crossed_up else "down"
                reading = "alta" if crossed_up else "baixa"
                alerts.append(
                    Alert(
                        asset=asset,
                        event_type=f"macd_cross_{direction}",
                        severity=AlertSeverity.INFO,
                        title=f"Cruzamento MACD de {reading}",
                        message=(
                            f"A linha MACD ({indicators.macd:.4f}) cruzou o sinal ({indicators.macd_signal:.4f}) "
                            f"no candle diário. Hipótese: mudança de momentum; confirmação depende do próximo "
                            "fechamento. Invalidação: cruzamento oposto."
                        ),
                        source="Binance candles 1d",
                        details={"macd": indicators.macd, "macd_signal": indicators.macd_signal},
                        cooldown_seconds=self._settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
                    )
                )

        rolling_high = float(df.iloc[-21:-1]["high"].max())
        rolling_low = float(df.iloc[-21:-1]["low"].min())
        close = float(latest["close"])
        previous_close = float(previous["close"])
        if close > rolling_high and previous_close <= rolling_high:
            alerts.append(self._breakout_alert(asset, close, rolling_high, "resistance"))
        elif close < rolling_low and previous_close >= rolling_low:
            alerts.append(self._breakout_alert(asset, close, rolling_low, "support"))

        average_volume = float(df.iloc[-21:-1]["volume"].mean())
        current_volume = float(latest["volume"])
        if average_volume > 0 and current_volume >= average_volume * self._settings.ALERT_VOLUME_SPIKE_MULTIPLIER:
            alerts.append(
                Alert(
                    asset=asset,
                    event_type="volume_spike",
                    severity=AlertSeverity.WARNING,
                    title="Volume acima do padrão recente",
                    message=(
                        f"O volume diário ({current_volume:,.2f}) está em {current_volume / average_volume:.2f}× "
                        "a média dos 20 candles anteriores. Hipótese: participação acima do padrão; "
                        "invalidação: normalização do volume nos próximos fechamentos."
                    ),
                    source="Binance candles 1d",
                    details={"current_volume": current_volume, "average_volume": average_volume},
                    cooldown_seconds=self._settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
                )
            )

        return alerts

    @staticmethod
    def classify_regime(candles: Iterable[dict]) -> dict[str, float | str] | None:
        """Classifica tendência e volatilidade a partir de fechamentos, sem inferência proprietária."""
        df = candles_to_dataframe(list(candles))
        if len(df) < 50:
            return None
        closes = df["close"].astype(float)
        sma20 = float(closes.rolling(20).mean().iloc[-1])
        sma50 = float(closes.rolling(50).mean().iloc[-1])
        close = float(closes.iloc[-1])
        volatility = float(closes.pct_change().rolling(20).std().iloc[-1])
        if volatility >= 0.04:
            regime = "alta volatilidade"
        elif close > sma20 > sma50:
            regime = "tendência de alta"
        elif close < sma20 < sma50:
            regime = "tendência de baixa"
        else:
            regime = "consolidação"
        return {
            "regime": regime,
            "close": close,
            "sma20": sma20,
            "sma50": sma50,
            "volatility_20d": volatility,
        }

    def evaluate_regime_change(
        self, asset: str, current: dict[str, float | str], previous: dict[str, object] | None
    ) -> list[Alert]:
        """Notifica mudança de regime, e não cada candle dentro de uma mesma condição."""
        previous_regime = previous.get("regime") if previous else None
        current_regime = str(current["regime"])
        if previous_regime is None or previous_regime == current_regime:
            return []
        return [
            Alert(
                asset=asset.upper(),
                event_type="market_regime_change",
                severity=AlertSeverity.WARNING,
                title=f"Regime de mercado alterado: {current_regime}",
                message=(
                    f"O regime técnico passou de '{previous_regime}' para '{current_regime}', com fechamento "
                    f"em {float(current['close']):,.2f}, SMA20 em {float(current['sma20']):,.2f}, "
                    f"SMA50 em {float(current['sma50']):,.2f} e volatilidade diária de 20 períodos em "
                    f"{float(current['volatility_20d']):.2%}. Hipótese: mudança de estrutura; "
                    "confirmação requer persistência nos próximos fechamentos. Invalidação: retorno ao regime anterior."
                ),
                source="Binance candles 1d",
                details={"value": float(current["close"]), "regime": current_regime, **current},
                cooldown_seconds=86_400,
            )
        ]

    def evaluate_selic(self, value: float, previous_value: float | None, reference_date: str) -> list[Alert]:
        """Comunica somente variações materiais na série oficial monitorada do BCB."""
        if previous_value is None:
            return []
        change = value - previous_value
        if abs(change) < self._settings.ALERT_SELIC_CHANGE_THRESHOLD:
            return []
        direction = "alta" if change > 0 else "queda"
        return [
            Alert(
                asset="SELIC",
                event_type=f"selic_change_{'up' if change > 0 else 'down'}",
                severity=AlertSeverity.WARNING,
                title=f"Série Selic: {direction} de {change:+.4f}",
                message=(
                    f"A série Selic monitorada apresentou {change:+.4f} na referência {reference_date}, "
                    f"de {previous_value:.6f} para {value:.6f}. Hipótese: alteração material na série diária; "
                    "confirmação requer a próxima divulgação oficial."
                ),
                source="Banco Central do Brasil — SGS série 11",
                details={"value": value, "previous_value": previous_value, "change": round(change, 6), "date": reference_date},
                cooldown_seconds=86_400,
            )
        ]

    def evaluate_probability_change(
        self,
        asset: str,
        current: dict[str, float],
        previous: dict[str, float] | None,
        *,
        model_name: str,
        balanced_accuracy: float,
    ) -> list[Alert]:
        """Alerta somente mudança probabilística material entre duas leituras confiáveis."""
        if not previous or not current:
            return []
        current_label, current_probability = max(current.items(), key=lambda item: item[1])
        previous_label, previous_probability = max(previous.items(), key=lambda item: item[1])
        change = current_probability - previous.get(current_label, 0.0)
        threshold = abs(self._settings.ALERT_PROBABILITY_CHANGE_THRESHOLD)
        if current_label == previous_label and abs(change) < threshold:
            return []
        direction = "aumentou" if change >= 0 else "diminuiu"
        return [
            Alert(
                asset=asset.upper(),
                event_type="reliable_probability_change",
                severity=AlertSeverity.INFO,
                title="Mudança probabilística material no modelo confiável",
                message=(
                    f"O cenário '{current_label}' passou de {previous.get(current_label, 0.0):.1%} para "
                    f"{current_probability:.1%} ({direction} {change:+.1%}). Modelo: {model_name}; "
                    f"acurácia balanceada de backtest: {balanced_accuracy:.2%}. Hipótese probabilística, não recomendação. "
                    "Invalidação: leitura seguinte desfaz a variação ou o modelo perde o critério de confiabilidade."
                ),
                source="MarketMind model registry",
                details={
                    "value": current_probability,
                    "previous_value": previous.get(current_label, 0.0),
                    "prediction": current_label,
                    "previous_prediction": previous_label,
                    "model_name": model_name,
                    "balanced_accuracy": balanced_accuracy,
                },
                cooldown_seconds=self._settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
            )
        ]

    def _rsi_alert(self, asset: str, rsi: float, state: str) -> Alert:
        extended = "sobrecompra" if state == "overbought" else "sobrevenda"
        threshold = self._settings.ALERT_RSI_OVERBOUGHT if state == "overbought" else self._settings.ALERT_RSI_OVERSOLD
        invalidation = "abaixo de 70" if state == "overbought" else "acima de 30"
        return Alert(
            asset=asset,
            event_type=f"rsi_{state}",
            severity=AlertSeverity.WARNING,
            title=f"RSI14 em {extended}",
            message=(
                f"RSI14 calculado em {rsi:.2f}, além do limiar de {threshold:.0f}. Hipótese: movimento "
                f"estendido no horizonte diário; não indica reversão garantida. Invalidação: RSI retorna {invalidation}."
            ),
            source="Binance candles 1d",
            details={"rsi14": rsi, "threshold": threshold},
            cooldown_seconds=self._settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
        )

    @staticmethod
    def _breakout_alert(asset: str, close: float, level: float, level_type: str) -> Alert:
        direction = "acima" if level_type == "resistance" else "abaixo"
        label = "resistência" if level_type == "resistance" else "suporte"
        return Alert(
            asset=asset,
            event_type=f"break_{level_type}",
            severity=AlertSeverity.WARNING,
            title=f"Fechamento {direction} da faixa de {label}",
            message=(
                f"Fechamento diário em {close:,.2f}, rompendo o nível de {label} de 20 períodos em {level:,.2f}. "
                "Hipótese: expansão da faixa; confirmação requer manutenção no próximo candle. "
                "Invalidação: retorno para dentro da faixa anterior."
            ),
            source="Binance candles 1d",
            details={"close": close, "level": level, "level_type": level_type},
            cooldown_seconds=86_400,
        )
