from datetime import datetime, timezone

from report_social import facebook, instagram
from report_social.graph_api import GraphAPIError
from conftest import FakeGraphClient

START = datetime(2026, 9, 11, tzinfo=timezone.utc)
END = datetime(2026, 9, 18, tzinfo=timezone.utc)


def test_facebook_legge_le_insight_aggregate_della_pagina():
    client = FakeGraphClient(
        {
            "page_1": {"followers_count": 4321},
            "page_1/insights": {
                "data": [
                    {
                        "name": "page_impressions",
                        "values": [{"value": 1000}, {"value": 1200}],
                    },
                    {
                        "name": "page_impressions_unique",
                        "values": [{"value": 800}, {"value": 900}],
                    },
                    {
                        "name": "page_post_engagements",
                        "values": [{"value": 60}, {"value": 40}],
                    },
                ]
            },
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.error is None
    assert report.followers == 4321
    assert report.posts_available is False
    assert report.posts == []
    assert report.aggregate_impressions == 2200
    assert report.aggregate_reach == 1700
    assert report.aggregate_engagement == 100


def test_facebook_metrica_non_disponibile_resta_a_none():
    client = FakeGraphClient(
        {
            "page_1": {"followers_count": 10},
            "page_1/insights": {
                "data": [
                    {"name": "page_impressions", "values": [{"value": 500}]},
                ]
            },
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.aggregate_impressions == 500
    assert report.aggregate_reach is None
    assert report.aggregate_engagement is None


def test_facebook_insight_fallite_degradano_senza_errore():
    # _followers e fetch_insights gestiscono da soli i propri errori: un
    # problema sulle insight aggregate non fa fallire l'intera raccolta,
    # semplicemente le metriche restano assenti (report.error resta None).
    client = FakeGraphClient(
        {
            "page_1": {"followers_count": 10},
            "page_1/insights": GraphAPIError("token scaduto", code=190),
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.error is None
    assert report.followers == 10
    assert report.aggregate_impressions is None
    assert report.aggregate_reach is None
    assert report.aggregate_engagement is None


def test_facebook_senza_follower_non_fallisce():
    client = FakeGraphClient(
        {
            "page_1": GraphAPIError("permesso mancante"),
            "page_1/insights": {"data": []},
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.followers is None
    assert report.error is None


def test_instagram_compone_le_statistiche_del_reel():
    client = FakeGraphClient(
        {
            "ig_1/media": {
                "data": [
                    {
                        "id": "media_1",
                        "caption": "Come funziona il quiz",
                        "media_type": "VIDEO",
                        "media_product_type": "REELS",
                        "permalink": "https://instagram.com/p/abc",
                        "timestamp": "2026-09-15T18:00:00+0000",
                        "like_count": 210,
                        "comments_count": 18,
                    }
                ]
            },
            "media_1/insights": {
                "data": [
                    {"name": "reach", "values": [{"value": 5000}]},
                    {"name": "saved", "values": [{"value": 65}]},
                    {"name": "shares", "values": [{"value": 32}]},
                    {"name": "views", "values": [{"value": 8100}]},
                ]
            },
            "ig_1": {"followers_count": 9876},
        }
    )

    report = instagram.collect(client, "ig_1", START, END)

    (post,) = report.posts
    assert post.likes == 210
    assert post.saves == 65
    assert post.shares == 32
    assert post.reach == 5000
    assert post.video_views == 8100
    assert post.interactions == 325
    assert round(post.engagement_rate, 2) == 6.5


def test_instagram_niente_video_views_per_le_foto():
    client = FakeGraphClient(
        {
            "ig_1/media": {
                "data": [
                    {
                        "id": "media_2",
                        "media_type": "IMAGE",
                        "media_product_type": "FEED",
                        "timestamp": "2026-09-14T09:00:00+0000",
                        "like_count": 12,
                        "comments_count": 0,
                    }
                ]
            },
            "media_2/insights": {"data": [{"name": "views", "values": [{"value": 300}]}]},
            "ig_1": {"followers_count": 100},
        }
    )

    (post,) = instagram.collect(client, "ig_1", START, END).posts

    assert post.video_views == 0
    assert post.impressions == 300
    assert post.engagement_rate is None  # reach sconosciuta -> niente percentuale


def test_instagram_riconosce_il_carosello_anche_se_e_in_feed():
    # media_product_type vale "FEED" sia per una foto singola sia per un
    # carosello: bisogna guardare anche media_type per distinguerli.
    client = FakeGraphClient(
        {
            "ig_1/media": {
                "data": [
                    {
                        "id": "media_3",
                        "media_type": "CAROUSEL_ALBUM",
                        "media_product_type": "FEED",
                        "timestamp": "2026-09-16T09:00:00+0000",
                        "like_count": 5,
                        "comments_count": 1,
                    }
                ]
            },
            "media_3/insights": {"data": []},
            "ig_1": {"followers_count": 1},
        }
    )

    (post,) = instagram.collect(client, "ig_1", START, END).posts

    assert post.media_type == "CAROUSEL"


def test_instagram_riconosce_il_reel_anche_se_media_type_e_video():
    client = FakeGraphClient(
        {
            "ig_1/media": {
                "data": [
                    {
                        "id": "media_4",
                        "media_type": "VIDEO",
                        "media_product_type": "REELS",
                        "timestamp": "2026-09-16T09:00:00+0000",
                        "like_count": 0,
                        "comments_count": 0,
                    }
                ]
            },
            "media_4/insights": {"data": []},
            "ig_1": {"followers_count": 1},
        }
    )

    (post,) = instagram.collect(client, "ig_1", START, END).posts

    assert post.media_type == "REEL"
