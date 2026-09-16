"""Configurazione letta dalle variabili d'ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Europe/Rome"
DEFAULT_GRAPH_VERSION = "v21.0"
DEFAULT_REPORT_DAYS = 7


class ConfigError(RuntimeError):
    """Configurazione mancante o non valida."""


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} deve essere un numero intero, trovato {value!r}") from exc


@dataclass(frozen=True)
class Config:
    """Tutti i parametri necessari per generare e inviare il report."""

    meta_access_token: str
    telegram_bot_token: str
    telegram_chat_id: str
    facebook_page_id: str | None = None
    instagram_account_id: str | None = None
    graph_version: str = DEFAULT_GRAPH_VERSION
    timezone: ZoneInfo = ZoneInfo(DEFAULT_TIMEZONE)
    report_days: int = DEFAULT_REPORT_DAYS
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        missing = [
            name
            for name in ("META_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
            if _env(name) is None
        ]
        if missing:
            raise ConfigError(
                "Variabili d'ambiente obbligatorie mancanti: " + ", ".join(missing)
            )

        facebook_page_id = _env("FACEBOOK_PAGE_ID")
        instagram_account_id = _env("INSTAGRAM_ACCOUNT_ID")
        if not facebook_page_id and not instagram_account_id:
            raise ConfigError(
                "Serve almeno uno tra FACEBOOK_PAGE_ID e INSTAGRAM_ACCOUNT_ID."
            )

        tz_name = _env("REPORT_TIMEZONE", DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE
        try:
            timezone = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise ConfigError(f"Fuso orario sconosciuto: {tz_name!r}") from exc

        report_days = _env_int("REPORT_DAYS", DEFAULT_REPORT_DAYS)
        if report_days < 1:
            raise ConfigError("REPORT_DAYS deve essere almeno 1.")

        return cls(
            meta_access_token=_env("META_ACCESS_TOKEN"),  # type: ignore[arg-type]
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),  # type: ignore[arg-type]
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),  # type: ignore[arg-type]
            facebook_page_id=facebook_page_id,
            instagram_account_id=instagram_account_id,
            graph_version=_env("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION) or DEFAULT_GRAPH_VERSION,
            timezone=timezone,
            report_days=report_days,
            dry_run=_env_bool("DRY_RUN"),
        )


def report_window(config: Config, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Finestra del report: gli ultimi `report_days` giorni *completi*.

    Lanciato il venerdi mattina con il default di 7 giorni, copre da venerdi
    scorso alle 00:00 a giovedi alle 23:59:59 (estremo destro escluso), cosi il
    giorno in corso -- ancora parziale -- non falsa le statistiche.
    """
    now = now.astimezone(config.timezone) if now else datetime.now(config.timezone)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=config.report_days)
    return start, end
