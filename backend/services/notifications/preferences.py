"""Preferências por perfil para priorização e roteamento dos alertas."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from config import settings
from database import AsyncSessionLocal
from models.alert import AlertPreference
from services.notifications.contracts import Alert, AlertSeverity, NotificationChannel

_SEVERITY_RANK = {AlertSeverity.INFO.value: 1, AlertSeverity.WARNING.value: 2, AlertSeverity.CRITICAL.value: 3}


@dataclass(frozen=True)
class PreferenceSnapshot:
    scope_key: str
    assets: tuple[str, ...]
    channels: tuple[NotificationChannel, ...]
    minimum_severity: AlertSeverity
    cooldown_seconds: int
    paused: bool

    def matches(self, alert: Alert) -> bool:
        if self.paused:
            return False
        if self.assets and "ALL" not in self.assets and alert.asset.upper() not in self.assets:
            return False
        return _SEVERITY_RANK[alert.severity.value] >= _SEVERITY_RANK[self.minimum_severity.value]


class AlertPreferenceService:
    """Armazena preferências sem conter e-mail, token ou chat ID de destinatários."""

    def _session_factory(self):
        if AsyncSessionLocal is None:
            raise RuntimeError("Banco de dados não configurado para preferências de alertas.")
        return AsyncSessionLocal

    async def get_or_create_owner(self) -> PreferenceSnapshot:
        return await self.get_or_create("owner")

    async def get_or_create(self, scope_key: str) -> PreferenceSnapshot:
        scope_key = self._validate_scope_key(scope_key)
        session_factory = self._session_factory()
        async with session_factory() as session:
            preference = await session.get(AlertPreference, scope_key)
            if preference is None:
                preference = AlertPreference(
                    scope_key=scope_key,
                    assets=["BTCUSDT", "SELIC"],
                    channels=settings.alert_channels_list,
                    minimum_severity=AlertSeverity.INFO.value,
                    cooldown_seconds=settings.ALERT_DEFAULT_COOLDOWN_SECONDS,
                    paused=False,
                )
                session.add(preference)
                await session.commit()
                await session.refresh(preference)
            return self._snapshot(preference)

    async def update(
        self,
        scope_key: str,
        *,
        assets: list[str],
        channels: list[str],
        minimum_severity: str,
        cooldown_seconds: int,
        paused: bool,
    ) -> PreferenceSnapshot:
        scope_key = self._validate_scope_key(scope_key)
        normalized_channels = self._normalize_channels(channels)
        severity = self._normalize_severity(minimum_severity)
        if cooldown_seconds < 60 or cooldown_seconds > 86_400:
            raise ValueError("cooldown_seconds deve estar entre 60 e 86400.")
        normalized_assets = tuple(dict.fromkeys(asset.strip().upper() for asset in assets if asset.strip()))
        if not normalized_assets:
            raise ValueError("Informe ao menos um ativo ou ALL.")

        session_factory = self._session_factory()
        async with session_factory() as session:
            preference = await session.get(AlertPreference, scope_key)
            if preference is None:
                preference = AlertPreference(scope_key=scope_key)
                session.add(preference)
            preference.assets = list(normalized_assets)
            preference.channels = [channel.value for channel in normalized_channels]
            preference.minimum_severity = severity.value
            preference.cooldown_seconds = cooldown_seconds
            preference.paused = paused
            await session.commit()
            await session.refresh(preference)
            return self._snapshot(preference)

    @staticmethod
    def _snapshot(preference: AlertPreference) -> PreferenceSnapshot:
        return PreferenceSnapshot(
            scope_key=preference.scope_key,
            assets=tuple(str(asset).upper() for asset in preference.assets),
            channels=AlertPreferenceService._normalize_channels(preference.channels),
            minimum_severity=AlertPreferenceService._normalize_severity(preference.minimum_severity),
            cooldown_seconds=preference.cooldown_seconds,
            paused=preference.paused,
        )

    @staticmethod
    def _normalize_channels(channels: list[str]) -> tuple[NotificationChannel, ...]:
        result: list[NotificationChannel] = []
        for channel in channels:
            try:
                parsed = NotificationChannel(str(channel).lower())
            except ValueError:
                continue
            if parsed not in result:
                result.append(parsed)
        if not result:
            raise ValueError("Informe pelo menos um canal reconhecido.")
        return tuple(result)

    @staticmethod
    def _normalize_severity(value: str) -> AlertSeverity:
        try:
            return AlertSeverity(value.upper())
        except ValueError as exc:
            raise ValueError("minimum_severity deve ser INFO, WARNING ou CRITICAL.") from exc

    @staticmethod
    def _validate_scope_key(scope_key: str) -> str:
        scope_key = scope_key.strip()
        if not scope_key or len(scope_key) > 80 or not scope_key.replace("-", "").replace("_", "").isalnum():
            raise ValueError("scope_key inválida.")
        return scope_key
