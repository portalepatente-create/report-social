from datetime import datetime, timezone

from report_social import facebook, instagram
from report_social.graph_api import GraphAPIError
from conftest import FakeGraphClient

START = datetime(2026, 9, 11, tzinfo=timezone.utc)
END = datetime(2026, 9, 18, tzinfo=timezone.utc)


def test_facebook_compone_le_statistiche_del_post():
    client = FakeGraphClient(
        {
            "page_1/published_posts": {
                "data": [
                    {
                        "id": "post_1",
                        "message": "Nuovo corso di guida sicura",
                        "created_time": "2026-09-12T10:00:00+0000",
                        "permalink_url": "https://facebook.com/post_1",
                        "shares": {"count": 6},
                        "likes": {"summary": {"total_count": 40}},
                        "comments": {"summary": {"total_count": 7}},
                        "attachments": {"data": [{"media_type": "photo"}]},
                    }
                ]
            },
            "post_1/insights": {
                "data": [
                    {"name": "post_impressions", "values": [{"value": 2000}]},
                    {"name": "post_impressions_unique", "values": [{"value": 1500}]},
                    {"name": "post_clicks", "values": [{"value": 90}]},
                    {
                        "name": "post_reactions_by_type_total",
                        "values": [{"value": {"like": 38, "love": 4}}],
                    },
                ]
            },
            "page_1": {"followers_count": 4321},
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.error is None
    assert report.followers == 4321
    (post,) = report.posts
    assert post.likes == 42  # le reazioni totali battono il conteggio dei soli "mi piace"
    assert post.comments == 7
    assert post.shares == 6
    assert post.reach == 1500
    assert post.impressions == 2000
    assert post.clicks == 90
    assert post.interactions == 55
    assert post.media_type == "photo"


def test_facebook_scarta_i_post_fuori_finestra():
    client = FakeGraphClient(
        {
            "page_1/published_posts": {
                "data": [
                    {
                        "id": "vecchio",
                        "message": "settimana scorsa",
                        "created_time": "2026-09-10T23:59:00+0000",
                    },
                    {
                        "id": "futuro",
                        "message": "oggi",
                        "created_time": "2026-09-18T07:00:00+0000",
                    },
                ]
            },
            "page_1": {"followers_count": 10},
        }
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.posts == []


def test_facebook_registra_l_errore_senza_sollevarlo():
    client = FakeGraphClient(
        {"page_1/published_posts": GraphAPIError("token scaduto", code=190)}
    )

    report = facebook.collect(client, "page_1", START, END)

    assert report.posts == []
    assert "token scaduto" in report.error


def test_facebook_senza_follower_non_fallisce():
    client = FakeGraphClient(
        {
            "page_1/published_posts": {"data": []},
            "page_1": GraphAPIError("permesso mancante"),
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
