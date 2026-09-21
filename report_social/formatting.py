"""Composizione del messaggio Telegram (parse_mode HTML)."""

from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from .models import PlatformReport, PostStats

PLATFORM_EMOJI = {"Facebook": "📘", "Instagram": "📷"}
CAPTION_PREVIEW = 70
MAX_POSTS_LISTED = 10

GIORNI = ("lun", "mar", "mer", "gio", "ven", "sab", "dom")
SEPARATOR = " · "


def format_number(value: int | None) -> str:
    """1234567 -> '1.234.567' (separatore delle migliaia all'italiana)."""
    if value is None:
        return "n/d"
    return f"{value:,}".replace(",", ".")


def format_date(moment: datetime, timezone: ZoneInfo) -> str:
    local = moment.astimezone(timezone)
    return f"{GIORNI[local.weekday()]} {local:%d/%m}"


def _preview(caption: str) -> str:
    text = " ".join(caption.split())
    if not text:
        return "(senza testo)"
    if len(text) <= CAPTION_PREVIEW:
        return text
    return text[: CAPTION_PREVIEW - 1].rstrip() + "…"


def _post_line(post: PostStats, timezone: ZoneInfo) -> str:
    label = escape(_preview(post.caption))
    if post.permalink:
        label = f'<a href="{escape(post.permalink, quote=True)}">{label}</a>'

    pieces = [
        f"👍 {format_number(post.likes)}",
        f"💬 {format_number(post.comments)}",
    ]
    if post.shares:
        pieces.append(f"🔁 {format_number(post.shares)}")
    if post.saves:
        pieces.append(f"🔖 {format_number(post.saves)}")
    if post.reach:
        pieces.append(f"👀 {format_number(post.reach)}")
    if post.video_views:
        pieces.append(f"▶️ {format_number(post.video_views)}")

    details = SEPARATOR.join(pieces)
    line = f"• <b>{format_date(post.published_at, timezone)}</b> {label}\n  {details}"
    rate = post.engagement_rate
    if rate is not None:
        line += f" · ER {rate:.1f}%"
    return line


def _aggregate_section(report: PlatformReport) -> str:
    """Riga di riepilogo per le piattaforme senza elenco dei singoli post."""
    pieces = []
    if report.aggregate_impressions is not None:
        pieces.append(f"📈 {format_number(report.aggregate_impressions)} impression")
    if report.aggregate_reach is not None:
        pieces.append(f"👀 {format_number(report.aggregate_reach)} copertura")
    if report.aggregate_engagement is not None:
        pieces.append(f"👍 {format_number(report.aggregate_engagement)} interazioni")

    if not pieces:
        return "Dati non disponibili per questo periodo."
    return (
        SEPARATOR.join(pieces)
        + "\n<i>Dettaglio dei singoli post non disponibile per questa piattaforma.</i>"
    )


def _platform_section(report: PlatformReport, timezone: ZoneInfo) -> str:
    emoji = PLATFORM_EMOJI.get(report.platform, "📊")
    header = f"{emoji} <b>{escape(report.platform)}</b>"

    if report.error:
        return f"{header}\n⚠️ Dati non recuperati: {escape(report.error)}"

    if report.followers is not None:
        header += f" — {format_number(report.followers)} follower"

    if not report.posts_available:
        return f"{header}\n{_aggregate_section(report)}"

    if not report.posts:
        return f"{header}\nNessun post pubblicato in questo periodo."

    totals = [
        f"<b>{len(report.posts)}</b> post",
        f"👍 {format_number(report.total_likes)}",
        f"💬 {format_number(report.total_comments)}",
    ]
    if report.total_shares:
        totals.append(f"🔁 {format_number(report.total_shares)}")
    if report.total_saves:
        totals.append(f"🔖 {format_number(report.total_saves)}")
    if report.total_reach:
        totals.append(f"👀 {format_number(report.total_reach)} copertura")

    lines = [header, SEPARATOR.join(totals), ""]
    for post in report.posts[:MAX_POSTS_LISTED]:
        lines.append(_post_line(post, timezone))
    if len(report.posts) > MAX_POSTS_LISTED:
        lines.append(f"… e altri {len(report.posts) - MAX_POSTS_LISTED} post.")
    return "\n".join(lines)


def build_message(
    reports: list[PlatformReport],
    start: datetime,
    end: datetime,
    timezone: ZoneInfo,
) -> str:
    """Compone il testo completo del report settimanale."""
    last_day = end - timedelta(days=1)
    title = (
        "📊 <b>Report social settimanale</b>\n"
        f"<i>{start.astimezone(timezone):%d/%m/%Y} – "
        f"{last_day.astimezone(timezone):%d/%m/%Y}</i>"
    )

    blocks = [title]
    blocks.extend(_platform_section(report, timezone) for report in reports)

    published = [report for report in reports if not report.error]
    total_posts = sum(len(report.posts) for report in published if report.posts_available)
    total_interactions = sum(
        report.total_interactions if report.posts_available else (report.aggregate_engagement or 0)
        for report in published
    )
    if total_posts or total_interactions:
        blocks.append(
            f"✨ <b>Totale:</b> {format_number(total_posts)} post · "
            f"{format_number(total_interactions)} interazioni"
        )
        best = max(
            (report.best_post for report in published if report.best_post),
            key=lambda post: post.interactions,
            default=None,
        )
        if best is not None and best.interactions:
            blocks.append(
                f"🏆 <b>Post migliore</b> ({escape(best.platform)}): "
                f"{escape(_preview(best.caption))} — "
                f"{format_number(best.interactions)} interazioni"
            )

    return "\n\n".join(blocks)
