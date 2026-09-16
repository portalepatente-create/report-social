from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from report_social.formatting import build_message, format_number
from report_social.models import PlatformReport, PostStats

TZ = ZoneInfo("Europe/Rome")
START = datetime(2026, 9, 11, tzinfo=TZ)
END = datetime(2026, 9, 18, tzinfo=TZ)


def _post(**overrides) -> PostStats:
    valori = {
        "platform": "Instagram",
        "post_id": "m1",
        "published_at": datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc),
        "caption": "Come funziona il quiz",
        "permalink": "https://instagram.com/p/abc",
        "likes": 210,
        "comments": 18,
        "reach": 5000,
    }
    valori.update(overrides)
    return PostStats(**valori)


def test_format_number_usa_il_punto_come_separatore():
    assert format_number(1234567) == "1.234.567"
    assert format_number(None) == "n/d"


def test_intestazione_mostra_il_periodo_coperto():
    messaggio = build_message([], START, END, TZ)
    assert "11/09/2026 – 17/09/2026" in messaggio  # il giorno in corso resta escluso


def test_sezione_con_post_riporta_totali_e_link():
    report = PlatformReport(platform="Instagram", posts=[_post()], followers=9876)

    messaggio = build_message([report], START, END, TZ)

    assert "9.876 follower" in messaggio
    assert "<b>1</b> post" in messaggio
    assert 'href="https://instagram.com/p/abc"' in messaggio
    assert "Totale:" in messaggio
    assert "228 interazioni" in messaggio


def test_piattaforma_senza_post():
    report = PlatformReport(platform="Facebook", followers=10)

    messaggio = build_message([report], START, END, TZ)

    assert "Nessun post pubblicato" in messaggio
    assert "Totale:" not in messaggio


def test_errore_di_piattaforma_e_visibile_nel_messaggio():
    report = PlatformReport(platform="Facebook", error="token scaduto")

    messaggio = build_message([report], START, END, TZ)

    assert "Dati non recuperati" in messaggio
    assert "token scaduto" in messaggio


def test_il_testo_dei_post_viene_scappato():
    report = PlatformReport(
        platform="Instagram", posts=[_post(caption="<b>offerta</b> & sconti", permalink=None)]
    )

    messaggio = build_message([report], START, END, TZ)

    assert "&lt;b&gt;offerta&lt;/b&gt; &amp; sconti" in messaggio


def test_elenco_lungo_viene_troncato():
    posts = [_post(post_id=f"m{i}", caption=f"post {i}") for i in range(14)]
    report = PlatformReport(platform="Instagram", posts=posts)

    messaggio = build_message([report], START, END, TZ)

    assert "e altri 4 post" in messaggio


def test_post_migliore_scelto_tra_le_piattaforme():
    ig = PlatformReport(platform="Instagram", posts=[_post(caption="reel", likes=10, comments=1)])
    fb = PlatformReport(
        platform="Facebook",
        posts=[_post(platform="Facebook", caption="vincitore", likes=900, comments=40)],
    )

    messaggio = build_message([ig, fb], START, END, TZ)

    assert "Post migliore" in messaggio
    assert "vincitore" in messaggio


def test_didascalia_vuota_ha_un_segnaposto():
    report = PlatformReport(platform="Instagram", posts=[_post(caption="", permalink=None)])

    assert "(senza testo)" in build_message([report], START, END, TZ)


def test_orario_convertito_nel_fuso_locale():
    # 23:30 UTC di giovedi = 01:30 di venerdi a Roma
    post = _post(published_at=datetime(2026, 9, 17, 23, 30, tzinfo=timezone.utc))
    report = PlatformReport(platform="Instagram", posts=[post])

    assert "ven 18/09" in build_message([report], START, END, TZ)
