"""Entrypoint: raccoglie le statistiche della settimana e le manda su Telegram."""

from __future__ import annotations

import argparse
import logging
import sys

from . import facebook, instagram
from .config import Config, ConfigError, report_window
from .formatting import build_message
from .graph_api import GraphClient
from .models import PlatformReport
from .telegram import TelegramError, send_message

LOGGER = logging.getLogger("report_social")


def build_report(config: Config) -> str:
    """Interroga Meta e restituisce il messaggio pronto per Telegram."""
    start, end = report_window(config)
    LOGGER.info("Finestra del report: %s -> %s", start.isoformat(), end.isoformat())

    client = GraphClient(config.meta_access_token, config.graph_version)
    reports: list[PlatformReport] = []

    if config.instagram_account_id:
        reports.append(instagram.collect(client, config.instagram_account_id, start, end))
    if config.facebook_page_id:
        reports.append(facebook.collect(client, config.facebook_page_id, start, end))

    for report in reports:
        LOGGER.info(
            "%s: %d post, %d interazioni%s",
            report.platform,
            len(report.posts),
            report.total_interactions,
            f" (errore: {report.error})" if report.error else "",
        )

    return build_message(reports, start, end, config.timezone)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report settimanale social su Telegram.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="stampa il report a schermo senza inviarlo su Telegram",
    )
    parser.add_argument("--verbose", action="store_true", help="log di dettaglio")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = Config.from_env()
    except ConfigError as exc:
        LOGGER.error("%s", exc)
        return 2

    message = build_report(config)

    if args.dry_run or config.dry_run:
        print(message)
        return 0

    try:
        send_message(config.telegram_bot_token, config.telegram_chat_id, message)
    except TelegramError as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Report inviato su Telegram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
