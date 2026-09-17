from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from report_social.config import Config, ConfigError, report_window

BASE_ENV = {
    "META_ACCESS_TOKEN": "token",
    "TELEGRAM_BOT_TOKEN": "bot",
    "TELEGRAM_CHAT_ID": "-100",
    "FACEBOOK_PAGE_ID": "123",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "META_ACCESS_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "FACEBOOK_PAGE_ID",
        "INSTAGRAM_ACCOUNT_ID",
        "REPORT_TIMEZONE",
        "REPORT_DAYS",
        "META_GRAPH_VERSION",
        "DRY_RUN",
        "TELEGRAM_MESSAGE_THREAD_ID",
    ):
        monkeypatch.delenv(name, raising=False)


def _set(monkeypatch, **overrides):
    for key, value in {**BASE_ENV, **overrides}.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


def test_from_env_legge_i_valori_minimi(monkeypatch):
    _set(monkeypatch)
    config = Config.from_env()
    assert config.facebook_page_id == "123"
    assert config.instagram_account_id is None
    assert config.timezone == ZoneInfo("Europe/Rome")
    assert config.report_days == 7


def test_from_env_segnala_le_variabili_mancanti(monkeypatch):
    _set(monkeypatch, TELEGRAM_BOT_TOKEN=None)
    with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
        Config.from_env()


def test_from_env_richiede_almeno_una_piattaforma(monkeypatch):
    _set(monkeypatch, FACEBOOK_PAGE_ID=None)
    with pytest.raises(ConfigError, match="FACEBOOK_PAGE_ID"):
        Config.from_env()


def test_valori_vuoti_contano_come_mancanti(monkeypatch):
    _set(monkeypatch, INSTAGRAM_ACCOUNT_ID="   ", FACEBOOK_PAGE_ID=None)
    with pytest.raises(ConfigError):
        Config.from_env()


def test_report_days_non_numerico(monkeypatch):
    _set(monkeypatch, REPORT_DAYS="sette")
    with pytest.raises(ConfigError, match="numero intero"):
        Config.from_env()


def test_finestra_copre_i_sette_giorni_precedenti(monkeypatch):
    _set(monkeypatch)
    config = Config.from_env()
    venerdi = datetime(2026, 9, 18, 8, 0, tzinfo=ZoneInfo("Europe/Rome"))

    start, end = report_window(config, venerdi)

    assert start == datetime(2026, 9, 11, 0, 0, tzinfo=ZoneInfo("Europe/Rome"))
    assert end == datetime(2026, 9, 18, 0, 0, tzinfo=ZoneInfo("Europe/Rome"))
    assert (end - start).days == 7


def test_finestra_esclude_il_giorno_in_corso(monkeypatch):
    _set(monkeypatch)
    config = Config.from_env()
    venerdi = datetime(2026, 9, 18, 23, 59, tzinfo=ZoneInfo("Europe/Rome"))

    _, end = report_window(config, venerdi)

    assert end.day == 18 and end.hour == 0


def test_topic_del_supergruppo_opzionale(monkeypatch):
    _set(monkeypatch)
    assert Config.from_env().telegram_message_thread_id is None

    monkeypatch.setenv("TELEGRAM_MESSAGE_THREAD_ID", "42")
    assert Config.from_env().telegram_message_thread_id == "42"
