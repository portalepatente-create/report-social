# Report social settimanale su Telegram

Ogni **venerdì alle 8:00 (ora italiana)** raccoglie le statistiche dei post
pubblicati nei sette giorni precedenti su una Pagina Facebook e su un account
Instagram Business, e le invia come messaggio Telegram.

La finestra coperta va da **venerdì della settimana prima alle 00:00 a giovedì
alle 23:59**: il venerdì in corso resta fuori, perché sarebbe una giornata
parziale e falserebbe i confronti.

## Che aspetto ha il report

```
📊 Report social settimanale
11/09/2026 – 17/09/2026

📷 Instagram — 9.876 follower
2 post · 👍 302 · 💬 23 · 🔁 35 · 🔖 78 · 👀 6.640 copertura

• mar 15/09 Nuovo quiz patente B: 40 domande aggiornate al 2026
  👍 214 · 💬 18 · 🔁 31 · 🔖 66 · 👀 5.210 · ▶️ 8.140 · ER 6.3%
• gio 17/09 Le 5 domande in cui cascano tutti
  👍 88 · 💬 5 · 🔁 4 · 🔖 12 · 👀 1.430 · ER 7.6%

📘 Facebook — 4.321 follower
1 post · 👍 42 · 💬 7 · 🔁 6 · 👀 1.512 copertura

• sab 12/09 Guida sicura: il nostro corso gratuito di ottobre
  👍 42 · 💬 7 · 🔁 6 · 👀 1.512 · ER 3.6%

✨ Totale: 3 post · 493 interazioni

🏆 Post migliore (Instagram): Nuovo quiz patente B — 329 interazioni
```

Legenda: 👍 like/reazioni · 💬 commenti · 🔁 condivisioni · 🔖 salvataggi ·
👀 copertura (persone raggiunte) · ▶️ visualizzazioni video ·
**ER** = interazioni ÷ copertura, in percentuale.

## Cosa serve configurare

Tutto passa da cinque valori. Sono **segreti**: non vanno messi nel codice, ma
nei *Secrets* del repository.

| Variabile | Dove si trova |
|---|---|
| `META_ACCESS_TOKEN` | Token della Pagina Facebook (vedi sotto) |
| `FACEBOOK_PAGE_ID` | ID numerico della Pagina |
| `INSTAGRAM_ACCOUNT_ID` | ID dell'account Instagram Business collegato |
| `TELEGRAM_BOT_TOKEN` | Te lo dà @BotFather su Telegram |
| `TELEGRAM_CHAT_ID` | ID della chat dove ricevere il report |

Serve almeno uno tra `FACEBOOK_PAGE_ID` e `INSTAGRAM_ACCOUNT_ID`: se ne compili
solo uno, il report riguarderà solo quella piattaforma.

### 1. Il bot Telegram

1. Su Telegram apri una chat con **@BotFather** e manda `/newbot`.
2. Scegli nome e username: BotFather risponde con il token
   (`123456789:AAE...`) → è il tuo `TELEGRAM_BOT_TOKEN`.
3. Manda un messaggio qualsiasi al bot appena creato (un bot non può scriverti
   per primo se non gli hai mai parlato).
4. Per ricavare `TELEGRAM_CHAT_ID`, apri nel browser:
   `https://api.telegram.org/bot<IL_TUO_TOKEN>/getUpdates` e leggi
   `"chat":{"id": ...}`.

Se preferisci ricevere il report in un **gruppo**, aggiungi il bot al gruppo,
scrivi un messaggio lì e rileggi `getUpdates`: l'id del gruppo è negativo
(es. `-1001234567890`).

### 2. Il token di Meta

Le statistiche dei post non sono pubbliche: servono un'app Meta e un token
della Pagina.

1. Su [developers.facebook.com](https://developers.facebook.com/apps) crea
   un'app di tipo **Business**.
2. Apri il **Graph API Explorer**, seleziona l'app e chiedi questi permessi:
   `pages_read_engagement`, `pages_show_list`, `read_insights`,
   `instagram_basic`, `instagram_manage_insights`.
3. Genera il token, poi passa da *User Token* a **Page Token** scegliendo la tua
   Pagina: quello è `META_ACCESS_TOKEN`.
4. `FACEBOOK_PAGE_ID` compare nella stessa schermata; in alternativa lo trovi
   interrogando `me/accounts`.
5. `INSTAGRAM_ACCOUNT_ID` si ottiene con la chiamata
   `<FACEBOOK_PAGE_ID>?fields=instagram_business_account`.

> **Nota sulla scadenza.** I token generati dall'Explorer durano circa un'ora.
> Scambiane uno con un token di lunga durata (60 giorni) con
> `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<APP_SECRET>&fb_exchange_token=<TOKEN>`,
> poi usa quel token per generare un **Page Token**, che non scade finché non
> revochi i permessi o cambi password. Se il report smette di arrivare, la causa
> più probabile è il token: il messaggio lo dice esplicitamente
> ("⚠️ Dati non recuperati").

Requisiti lato account: la Pagina Facebook deve esistere e l'account Instagram
deve essere **Business o Creator** e collegato a quella Pagina. Un account
Instagram personale non espone alcuna statistica.

### 3. I Secrets del repository

Su GitHub: **Settings → Secrets and variables → Actions → New repository
secret**, uno per ciascuna delle cinque variabili della tabella.

Opzionalmente, nella scheda **Variables** puoi impostare `REPORT_TIMEZONE`
(default `Europe/Rome`), `REPORT_DAYS` (default `7`) e `META_GRAPH_VERSION`
(default `v21.0`).

## Come gira

`.github/workflows/weekly-report.yml` è schedulato alle **06:00 e alle 07:00
UTC ogni venerdì**. GitHub Actions accetta solo orari UTC, e le 8:00 italiane
cadono alle 06:00 UTC con l'ora legale e alle 07:00 UTC con l'ora solare: il
workflow parte a entrambi gli orari e il primo step lascia proseguire solo
l'esecuzione che corrisponde davvero alle 8:00 locali. Il cambio di ora legale
è quindi già gestito.

> GitHub non garantisce il minuto esatto: sotto carico la partenza può slittare
> di qualche minuto. Se l'orario deve essere preciso al minuto, serve uno
> scheduler esterno (cron su un server, Cloud Scheduler) che chiami lo stesso
> comando.

### Provarlo subito

Dalla scheda **Actions → Report social settimanale → Run workflow** puoi
lanciarlo a mano in qualsiasi momento; spuntando `dry_run` il report viene
scritto nei log senza essere inviato su Telegram.

### In locale

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env     # compila i valori
set -a && source .env && set +a

python -m report_social --dry-run    # stampa il report senza inviarlo
python -m report_social              # lo invia davvero
```

## Test

```bash
python -m pytest
```

I test coprono finestra temporale, parsing delle risposte Meta, formattazione
del messaggio e invio su Telegram; nessuno di essi tocca la rete.

## Struttura

| File | Ruolo |
|---|---|
| `report_social/config.py` | Lettura delle variabili d'ambiente e calcolo della settimana |
| `report_social/graph_api.py` | Client Graph API con retry, paginazione e insight tolleranti |
| `report_social/facebook.py` | Post e statistiche della Pagina Facebook |
| `report_social/instagram.py` | Post e statistiche dell'account Instagram |
| `report_social/formatting.py` | Composizione del messaggio Telegram |
| `report_social/telegram.py` | Invio, con suddivisione oltre i 4096 caratteri |
| `report_social/main.py` | Entrypoint `python -m report_social` |

## Limiti noti

- **Le Storie non sono incluse.** Meta le espone su un endpoint separato e con
  una finestra di sole 24 ore, quindi un report settimanale ne vedrebbe al più
  l'ultimo giorno.
- **Metriche in evoluzione.** Meta rinomina e deprecia metriche a ogni versione
  della Graph API (`views` ha sostituito `impressions` e `plays` per i contenuti
  pubblicati dopo luglio 2024). Il codice richiede le metriche una per una
  quando la richiesta cumulativa fallisce, così una metrica non più disponibile
  fa sparire una voce dal report invece di farlo fallire del tutto.
- **Se una piattaforma dà errore**, l'altra viene comunque riportata e il
  messaggio segnala il problema invece di non arrivare.
