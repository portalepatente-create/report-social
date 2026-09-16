"""Doppi di test condivisi: nessuna chiamata di rete reale."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from report_social.graph_api import GraphAPIError  # noqa: E402


class FakeGraphClient:
    """GraphClient finto: risponde da una mappa `path -> payload`.

    Un payload puo essere un'eccezione, che viene sollevata come farebbe la API.
    """

    def __init__(self, responses: Mapping[str, Any]):
        self.responses = dict(responses)
        self.calls: list[tuple[str, dict]] = []

    def get(self, path: str, params: Mapping[str, Any] | None = None) -> dict:
        self.calls.append((path, dict(params or {})))
        try:
            payload = self.responses[path]
        except KeyError:
            raise GraphAPIError(f"path non previsto nel test: {path}") from None
        if isinstance(payload, Exception):
            raise payload
        return payload

    def get_all(self, path: str, params: Mapping[str, Any] | None = None) -> list[dict]:
        return list(self.get(path, params).get("data", []))


@pytest.fixture
def fake_client():
    return FakeGraphClient
