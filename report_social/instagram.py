"""Raccolta delle statistiche dei post di un account Instagram Business."""

from __future__ import annotations

import logging
from datetime import datetime

from .graph_api import GraphAPIError, GraphClient, fetch_insights, parse_timestamp
from .models import PlatformReport, PostStats

LOGGER = logging.getLogger(__name__)

PLATFORM = "Instagram"

MEDIA_FIELDS = ",".join(
    [
        "id",
        "caption",
        "media_type",
        "media_product_type",
        "permalink",
        "timestamp",
        "like_count",
        "comments_count",
    ]
)

# `views` ha sostituito `impressions`/`plays` per i contenuti pubblicati dopo
# luglio 2024; `fetch_insights` scarta da sola le metriche non supportate
# dall'account o dalla versione di API in uso.
MEDIA_METRICS = ("reach", "saved", "shares", "views")


def collect(client: GraphClient, account_id: str, start: datetime, end: datetime) -> PlatformReport:
    """Restituisce il report Instagram per la finestra [start, end)."""
    report = PlatformReport(platform=PLATFORM)
    try:
        raw_media = client.get_all(
            f"{account_id}/media",
            {
                "fields": MEDIA_FIELDS,
                "since": int(start.timestamp()),
                "until": int(end.timestamp()),
                "limit": 50,
            },
        )
        report.followers = _followers(client, account_id)
    except GraphAPIError as exc:
        LOGGER.error("Impossibile leggere i media dell'account %s: %s", account_id, exc)
        report.error = str(exc)
        return report

    for raw in raw_media:
        published_at = parse_timestamp(raw["timestamp"])
        if not start <= published_at < end:
            continue
        report.posts.append(_build_post(client, raw, published_at))

    report.posts.sort(key=lambda p: p.published_at)
    return report


def _build_post(client: GraphClient, raw: dict, published_at: datetime) -> PostStats:
    insights = fetch_insights(client, raw["id"], MEDIA_METRICS)
    views = insights.get("views", 0)
    is_video = raw.get("media_type") == "VIDEO" or raw.get("media_product_type") == "REELS"

    return PostStats(
        platform=PLATFORM,
        post_id=raw["id"],
        published_at=published_at,
        caption=raw.get("caption") or "",
        permalink=raw.get("permalink"),
        media_type=raw.get("media_product_type") or raw.get("media_type"),
        likes=int(raw.get("like_count") or 0),
        comments=int(raw.get("comments_count") or 0),
        shares=insights.get("shares", 0),
        saves=insights.get("saved", 0),
        reach=insights.get("reach", 0),
        impressions=views,
        video_views=views if is_video else 0,
    )


def _followers(client: GraphClient, account_id: str) -> int | None:
    try:
        payload = client.get(account_id, {"fields": "followers_count"})
    except GraphAPIError as exc:
        LOGGER.info("Numero di follower non disponibile per l'account %s: %s", account_id, exc)
        return None
    followers = payload.get("followers_count")
    return int(followers) if followers is not None else None
