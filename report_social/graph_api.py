"""Client minimale per la Graph API di Meta (Facebook + Instagram)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Iterator, Mapping, Sequence

import requests

LOGGER = logging.getLogger(__name__)

BASE_URL = "https://graph.facebook.com"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 4
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_PAGES = 25


class GraphAPIError(RuntimeError):
    """Errore restituito dalla Graph API."""

    def __init__(self, message: str, *, code: int | None = None, status: int | None = None):
        super().__init__(message)
        self.code = code
        self.status = status


class GraphClient:
    """Wrapper su `requests` con retry, paginazione e token mai loggato."""

    def __init__(self, access_token: str, version: str, *, session: requests.Session | None = None):
        self._access_token = access_token
        self._version = version
        self._session = session or requests.Session()

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        url = f"{BASE_URL}/{self._version}/{path.lstrip('/')}"
        query: dict[str, Any] = dict(params or {})
        query["access_token"] = self._access_token
        return self._request(url, query)

    def get_all(self, path: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Come `get`, ma segue la paginazione e restituisce solo i record."""
        return list(self._iter_pages(path, params))

    def _iter_pages(
        self, path: str, params: Mapping[str, Any] | None
    ) -> Iterator[dict[str, Any]]:
        payload = self.get(path, params)
        pages = 0
        while True:
            yield from payload.get("data", [])
            pages += 1
            next_url = payload.get("paging", {}).get("next")
            if not next_url or pages >= MAX_PAGES:
                if next_url:
                    LOGGER.warning("Interrotta la paginazione di %s dopo %d pagine.", path, pages)
                return
            payload = self._request(next_url, None)

    def _request(self, url: str, params: Mapping[str, Any] | None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            if attempt:
                delay = 2**attempt
                LOGGER.info("Nuovo tentativo tra %ss (%d/%d).", delay, attempt + 1, MAX_RETRIES)
                time.sleep(delay)
            try:
                response = self._session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            except requests.RequestException as exc:
                last_error = exc
                continue

            if response.status_code in RETRYABLE_STATUS:
                last_error = GraphAPIError(
                    f"HTTP {response.status_code} da {_safe_url(url)}",
                    status=response.status_code,
                )
                continue

            try:
                payload = response.json()
            except ValueError as exc:
                raise GraphAPIError(
                    f"Risposta non JSON da {_safe_url(url)} (HTTP {response.status_code})"
                ) from exc

            error = payload.get("error")
            if error:
                raise GraphAPIError(
                    error.get("message", "errore sconosciuto"),
                    code=error.get("code"),
                    status=response.status_code,
                )
            if not response.ok:
                raise GraphAPIError(
                    f"HTTP {response.status_code} da {_safe_url(url)}",
                    status=response.status_code,
                )
            return payload

        raise GraphAPIError(f"Chiamata fallita dopo {MAX_RETRIES} tentativi: {last_error}")


def _safe_url(url: str) -> str:
    """URL senza query string, per non finire il token nei log."""
    return url.split("?", 1)[0]


def fetch_insights(
    client: GraphClient,
    object_id: str,
    metrics: Sequence[str],
    params: Mapping[str, Any] | None = None,
) -> dict[str, int]:
    """Legge le insight di un oggetto tollerando le metriche non supportate.

    Meta deprecata e rinomina metriche a ogni versione della Graph API, e basta
    una metrica non valida perche l'intera chiamata fallisca. Al primo errore
    ripieghiamo su una richiesta per metrica, cosi le altre arrivano comunque.
    """
    if not metrics:
        return {}
    try:
        payload = client.get(f"{object_id}/insights", {"metric": ",".join(metrics), **(params or {})})
    except GraphAPIError as exc:
        if len(metrics) == 1:
            LOGGER.info("Metrica %s non disponibile per %s: %s", metrics[0], object_id, exc)
            return {}
        LOGGER.info("Insight in blocco fallite per %s (%s); riprovo una per una.", object_id, exc)
        values: dict[str, int] = {}
        for metric in metrics:
            values.update(fetch_insights(client, object_id, [metric], params))
        return values

    return {
        entry["name"]: _insight_value(entry)
        for entry in payload.get("data", [])
        if "name" in entry
    }


def _insight_value(entry: Mapping[str, Any]) -> int:
    """Estrae il totale da una voce di insight (scalare o scomposta per tipo)."""
    values = entry.get("values") or []
    if not values:
        return 0
    total = 0
    for item in values:
        value = item.get("value", 0)
        if isinstance(value, Mapping):
            total += sum(int(v) for v in value.values() if isinstance(v, (int, float)))
        elif isinstance(value, (int, float)):
            total += int(value)
    return total


def parse_timestamp(raw: str) -> datetime:
    """Converte un timestamp Meta (`2026-09-11T08:30:00+0000`) in datetime aware."""
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S%z")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
