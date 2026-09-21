"""Statistiche aggregate della Pagina Facebook (nessun dettaglio per singolo post).

Leggere l'elenco dei singoli post di una Pagina (`/posts`, `/published_posts`,
`/feed`) richiede da Meta la funzionalita "Page Public Content Access",
approvabile solo con una vera revisione dell'app (App Review) -- anche per le
Pagine di cui si e amministratori. Finche non viene richiesta e approvata,
qui leggiamo solo le insight aggregate della Pagina nel periodo, che restano
accessibili con il solo permesso `read_insights`.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .graph_api import GraphAPIError, GraphClient, fetch_insights
from .models import PlatformReport

LOGGER = logging.getLogger(__name__)

PLATFORM = "Facebook"

# Metriche "candidate": Meta le rinomina e le deprecia spesso a ogni versione
# della Graph API. fetch_insights scarta da sola quelle non piu supportate
# invece di far fallire l'intera chiamata.
PAGE_METRICS = (
    "page_impressions",
    "page_impressions_unique",
    "page_post_engagements",
)


def collect(client: GraphClient, page_id: str, start: datetime, end: datetime) -> PlatformReport:
    """Restituisce le statistiche aggregate della Pagina per la finestra [start, end).

    Sia `_followers` che `fetch_insights` gestiscono da sole i propri errori
    (li registrano nei log e restituiscono `None`/campi assenti), quindi qui
    non serve un try/except: la raccolta di Facebook non fallisce mai del
    tutto, degrada semplicemente ai singoli campi non disponibili.
    """
    report = PlatformReport(platform=PLATFORM, posts_available=False)
    report.followers = _followers(client, page_id)
    insights = fetch_insights(
        client,
        page_id,
        PAGE_METRICS,
        {
            "period": "day",
            "since": int(start.timestamp()),
            "until": int(end.timestamp()),
        },
    )
    report.aggregate_impressions = insights.get("page_impressions")
    report.aggregate_reach = insights.get("page_impressions_unique")
    report.aggregate_engagement = insights.get("page_post_engagements")
    return report


def _followers(client: GraphClient, page_id: str) -> int | None:
    try:
        payload = client.get(page_id, {"fields": "followers_count,fan_count"})
    except GraphAPIError as exc:
        LOGGER.info("Numero di follower non disponibile per la Pagina %s: %s", page_id, exc)
        return None
    followers = payload.get("followers_count") or payload.get("fan_count")
    return int(followers) if followers is not None else None
