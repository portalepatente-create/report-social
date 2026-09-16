"""Invio del report tramite Bot API di Telegram."""

from __future__ import annotations

import logging
import time

import requests

LOGGER = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 4096
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 4


class TelegramError(RuntimeError):
    """Errore restituito dalla Bot API di Telegram."""


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Spezza il testo sotto il limite di Telegram senza rompere i tag HTML.

    Taglia sulle righe vuote (i blocchi del report), poi sulle singole righe e
    infine, solo come ultima risorsa, a carattere.
    """
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(block) <= limit:
            current = block
        else:
            chunks.extend(_split_block(block, limit))
            current = chunks.pop() if chunks else ""
    if current:
        chunks.append(current)
    return chunks


def _split_block(block: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in block.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line
    if current:
        chunks.append(current)
    return chunks


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    """Invia il testo alla chat, spezzandolo se supera il limite di Telegram."""
    url = f"{API_BASE}/bot{bot_token}/sendMessage"
    session = requests.Session()
    for chunk in split_message(text):
        _post(
            session,
            url,
            {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )


def _post(session: requests.Session, url: str, payload: dict) -> None:
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        if attempt:
            delay = 2**attempt
            LOGGER.info("Nuovo tentativo di invio tra %ss (%d/%d).", delay, attempt + 1, MAX_RETRIES)
            time.sleep(delay)
        try:
            response = session.post(url, data=payload, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            last_error = exc
            continue

        if response.status_code >= 500 or response.status_code == 429:
            last_error = TelegramError(f"HTTP {response.status_code} da Telegram")
            continue

        try:
            body = response.json()
        except ValueError:
            body = {}
        if not body.get("ok", False):
            description = body.get("description") or f"HTTP {response.status_code}"
            raise TelegramError(f"Telegram ha rifiutato il messaggio: {description}")
        return

    raise TelegramError(f"Invio fallito dopo {MAX_RETRIES} tentativi: {last_error}")
