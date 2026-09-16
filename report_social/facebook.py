"""Raccolta delle statistiche dei post di una Pagina Facebook."""

from __future__ import annotations

import logging
from datetime import datetime

from .graph_api import GraphAPIError, GraphClient, fetch_insights, parse_timestamp
from .models import PlatformReport, PostStats

LOGGER = logging.getLogger(__name__)

PLATFORM = "Facebook"

POST_FIELDS = ",".join(
    [
        "id",
        "message",
        "story",
        "created_time",
        "permalink_url",
        "shares",
        "likes.summary(true).limit(0)",
        "comments.summary(true).limit(0)",
        "attachments{media_type}",
    ]
)

POST_METRICS = (
    "post_impressions",
    "post_impressions_unique",
    "post_clicks",
    "post_reactions_by_type_total",
    "post_video_views",
)


def collect(client: GraphClient, page_id: str, start: datetime, end: datetime) -> PlatformReport:
    """Restituisce il report Facebook per la finestra [start, end)."""
    report = PlatformReport(platform=PLATFORM)
    try:
        raw_posts = client.get_all(
            f"{page_id}/published_posts",
            {
                "fields": POST_FIELDS,
                "since": int(start.timestamp()),
                "until": int(end.timestamp()),
                "limit": 50,
            },
        )
        report.followers = _followers(client, page_id)
    except GraphAPIError as exc:
        LOGGER.error("Impossibile leggere i post della Pagina %s: %s", page_id, exc)
        report.error = str(exc)
        return report

    for raw in raw_posts:
        published_at = parse_timestamp(raw["created_time"])
        # `since`/`until` sono inclusivi sul bordo destro: filtriamo a mano.
        if not start <= published_at < end:
            continue
        report.posts.append(_build_post(client, raw, published_at))

    report.posts.sort(key=lambda p: p.published_at)
    return report


def _build_post(client: GraphClient, raw: dict, published_at: datetime) -> PostStats:
    insights = fetch_insights(client, raw["id"], POST_METRICS)
    reactions = insights.get("post_reactions_by_type_total", 0)
    likes = reactions or _summary_count(raw.get("likes"))

    return PostStats(
        platform=PLATFORM,
        post_id=raw["id"],
        published_at=published_at,
        caption=raw.get("message") or raw.get("story") or "",
        permalink=raw.get("permalink_url"),
        media_type=_media_type(raw),
        likes=likes,
        comments=_summary_count(raw.get("comments")),
        shares=int((raw.get("shares") or {}).get("count", 0)),
        reach=insights.get("post_impressions_unique", 0),
        impressions=insights.get("post_impressions", 0),
        clicks=insights.get("post_clicks", 0),
        video_views=insights.get("post_video_views", 0),
    )


def _summary_count(edge: dict | None) -> int:
    return int(((edge or {}).get("summary") or {}).get("total_count", 0))


def _media_type(raw: dict) -> str | None:
    attachments = (raw.get("attachments") or {}).get("data") or []
    if not attachments:
        return None
    return attachments[0].get("media_type")


def _followers(client: GraphClient, page_id: str) -> int | None:
    try:
        payload = client.get(page_id, {"fields": "followers_count,fan_count"})
    except GraphAPIError as exc:
        LOGGER.info("Numero di follower non disponibile per la Pagina %s: %s", page_id, exc)
        return None
    followers = payload.get("followers_count") or payload.get("fan_count")
    return int(followers) if followers is not None else None
