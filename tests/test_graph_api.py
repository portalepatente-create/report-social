from report_social.graph_api import GraphAPIError, fetch_insights, parse_timestamp
from conftest import FakeGraphClient


def test_insight_scalare_e_scomposta_per_tipo():
    client = FakeGraphClient(
        {
            "post_1/insights": {
                "data": [
                    {"name": "post_impressions", "values": [{"value": 1200}]},
                    {
                        "name": "post_reactions_by_type_total",
                        "values": [{"value": {"like": 30, "love": 12, "wow": 3}}],
                    },
                ]
            }
        }
    )

    values = fetch_insights(client, "post_1", ["post_impressions", "post_reactions_by_type_total"])

    assert values == {"post_impressions": 1200, "post_reactions_by_type_total": 45}


def test_ripiega_su_una_metrica_alla_volta_quando_una_non_e_supportata():
    calls = {"n": 0}
    ok = {"data": [{"name": "reach", "values": [{"value": 500}]}]}

    class Client(FakeGraphClient):
        def get(self, path, params=None):
            calls["n"] += 1
            metric = (params or {}).get("metric", "")
            if "," in metric:
                raise GraphAPIError("(#100) metric[1] deve essere valida", code=100)
            if metric == "impressions":
                raise GraphAPIError("metrica deprecata", code=100)
            return ok

    values = fetch_insights(Client({}), "media_1", ["reach", "impressions"])

    assert values == {"reach": 500}
    assert calls["n"] == 3  # blocco fallito + una chiamata per metrica


def test_nessuna_metrica_nessuna_chiamata():
    client = FakeGraphClient({})
    assert fetch_insights(client, "post_1", []) == {}
    assert client.calls == []


def test_parse_timestamp_normalizza_il_fuso():
    parsed = parse_timestamp("2026-09-11T08:30:00+0000")
    assert parsed.utcoffset().total_seconds() == 0
    assert parsed.hour == 8
