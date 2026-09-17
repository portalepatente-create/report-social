import pytest

from report_social import telegram
from report_social.telegram import TelegramError, send_message, split_message


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    def post(self, url, data=None, timeout=None):
        self.requests.append(data)
        return self._responses.pop(0)


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(telegram.time, "sleep", lambda _: None)


def test_messaggio_corto_resta_intero():
    assert split_message("ciao") == ["ciao"]


def test_split_preferisce_i_confini_dei_blocchi():
    blocchi = ["A" * 60, "B" * 60, "C" * 60]
    pezzi = split_message("\n\n".join(blocchi), limit=130)

    assert all(len(p) <= 130 for p in pezzi)
    assert pezzi[0] == "A" * 60 + "\n\n" + "B" * 60
    assert pezzi[1] == "C" * 60


def test_split_ripiega_sulle_righe():
    testo = "\n".join("riga %02d" % i for i in range(20))
    pezzi = split_message(testo, limit=40)

    assert all(len(p) <= 40 for p in pezzi)
    assert "".join(pezzi).replace("\n", "") == testo.replace("\n", "")


def test_split_spezza_una_riga_piu_lunga_del_limite():
    pezzi = split_message("X" * 250, limit=100)

    assert [len(p) for p in pezzi] == [100, 100, 50]


def test_send_message_invia_ogni_pezzo(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({"ok": True}), FakeResponse({"ok": True})])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    send_message("bot-token", "-100", "A" * 5000)

    assert len(session.requests) == 2
    assert session.requests[0]["chat_id"] == "-100"
    assert session.requests[0]["parse_mode"] == "HTML"


def test_send_message_solleva_su_rifiuto(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({"ok": False, "description": "chat not found"}, 400)])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    with pytest.raises(TelegramError, match="chat not found"):
        send_message("bot-token", "-100", "ciao")


def test_send_message_riprova_sugli_errori_del_server(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({}, 503), FakeResponse({"ok": True})])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    send_message("bot-token", "-100", "ciao")

    assert len(session.requests) == 2


def test_il_token_non_finisce_nel_corpo_della_richiesta(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({"ok": True})])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    send_message("segretissimo", "-100", "ciao")

    assert "segretissimo" not in str(session.requests[0])


def test_topic_incluso_solo_se_configurato(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({"ok": True})])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    send_message("bot-token", "-1001234567890", "ciao", "42")

    assert session.requests[0]["message_thread_id"] == "42"


def test_senza_topic_il_campo_non_viene_inviato(monkeypatch, no_sleep):
    session = FakeSession([FakeResponse({"ok": True})])
    monkeypatch.setattr(telegram.requests, "Session", lambda: session)

    send_message("bot-token", "-1001234567890", "ciao")

    assert "message_thread_id" not in session.requests[0]
