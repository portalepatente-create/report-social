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
📈 8.400 impression · 👀 6.100 copertura · 👍 210 interazioni
Dettaglio dei singoli post non disponibile per questa piattaforma.

✨ Totale: 2 post · 512 interazioni

🏆 Post migliore (Instagram): Nuovo quiz patente B — 329 interazioni
```

Legenda: 👍 like/reazioni · 💬 commenti · 🔁 condivisioni · 🔖 salvataggi ·
👀 copertura (persone raggiunte) · 📈 impression · ▶️ visualizzazioni video ·
**ER** = interazioni ÷ copertura, in percentuale. Per Facebook vengono
mostrate solo le statistiche aggregate della settimana, non i singoli post —
il perché è spiegato in [Limiti noti](#limiti-noti).

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
| `TELEGRAM_MESSAGE_THREAD_ID` | *(facoltativo)* topic di un supergruppo forum |

Serve almeno uno tra `FACEBOOK_PAGE_ID` e `INSTAGRAM_ACCOUNT_ID`: se ne compili
solo uno, il report riguarderà solo quella piattaforma.

### 1. Il bot Telegram

1. Su Telegram apri una chat con **@BotFather** e manda `/newbot`.
2. Scegli nome e username: BotFather risponde con il token, nella forma
   `123456789:AAEabcDEF...` → è il tuo `TELEGRAM_BOT_TOKEN`.

Per ricavare `TELEGRAM_CHAT_ID` serve prima un messaggio che il bot possa
vedere, poi si legge l'elenco degli aggiornamenti.

**Se vuoi il report in chat privata**, scrivi `/start` al bot appena creato (un
bot non può scriverti per primo se non gli hai mai parlato).

**Se vuoi il report in un gruppo o supergruppo**, aggiungi il bot al gruppo e lì
manda `/start@nomedeltuobot`. Il comando con la menzione è importante: per
impostazione predefinita i bot nei gruppi hanno la *privacy mode* attiva e non
vedono i messaggi normali, quindi un "ciao" qualsiasi non produrrebbe alcun
aggiornamento e sembrerebbe che non funzioni nulla.

Poi apri nel browser:

```
https://api.telegram.org/bot123456789:AAEabcDEF.../getUpdates
```

> ⚠️ Sostituisci **tutto** `123456789:AAEabcDEF...` con il tuo token. La parola
> `bot` all'inizio va lasciata e il token le va attaccato, senza spazi e senza
> parentesi di alcun tipo. Se sbagli questa parte Telegram risponde
> `{"ok":false,"error_code":401,"description":"Unauthorized"}`: il 401 significa
> quasi sempre "token non valido", non "permesso negato".

Nella risposta cerca `"chat":{"id": ...}`: quel numero è `TELEGRAM_CHAT_ID`.
È **positivo** per una chat privata e **negativo** per gruppi e canali; i
supergruppi iniziano per `-100` (es. `-1001234567890`).

Se `getUpdates` restituisce `{"ok":true,"result":[]}`, il bot non ha ancora
ricevuto nulla: rimanda `/start` e ricarica. Gli aggiornamenti restano
disponibili circa 24 ore.

#### Supergruppi con i Topic

Se il supergruppo ha i **Topic** attivi (la modalità forum), senza altre
indicazioni il report finisce nel topic *General*. Per mandarlo in un topic
preciso, scrivi `/start@nomedeltuobot` dentro quel topic e cerca
`"message_thread_id"` nella risposta di `getUpdates`: quel valore va in
`TELEGRAM_MESSAGE_THREAD_ID` (è una *variabile*, non un secret: non è
un'informazione riservata).

Due avvertenze sui gruppi: se un gruppo normale viene promosso a supergruppo
**l'id cambia** e il report smette di arrivare, quindi conviene creare il
supergruppo prima di leggere l'id; e il bot deve restare nel gruppo, altrimenti
Telegram risponde `403 bot was kicked`.

### 2. Il token di Meta

Le statistiche dei post non sono pubbliche: servono un'app Meta e un token
che dia accesso alla Pagina. La via più affidabile per uno script automatico
come questo è un **Utente di sistema** del Business Manager: a differenza di
un token legato al tuo account personale, non dipende dalla tua sessione e
può essere generato per **non scadere mai**.

1. Su [developers.facebook.com/apps](https://developers.facebook.com/apps)
   crea un'app, scegliendo come casi d'uso **"Gestisci tutto sulla tua
   Pagina"** e **"Gestisci i messaggi e i contenuti su Instagram"** (con
   quest'ultimo scegli il percorso **"API setup with Facebook login"**, non
   quello con login Instagram diretto — solo il primo espone le statistiche).
2. Dentro l'app, per ciascuno dei due casi d'uso, apri **"Personalizza"** →
   **"Autorizzazioni e funzioni"** e assicurati che risultino **"Pronta per
   il test"** questi cinque permessi: `pages_read_engagement`,
   `pages_show_list`, `read_insights`, `instagram_basic`,
   `instagram_manage_insights`.
3. Su [business.facebook.com/settings](https://business.facebook.com/settings),
   verifica che la Pagina Facebook sia tra le **Pagine** del tuo Business
   Portfolio (Account → Pagine) e che l'app sia collegata a quella Pagina
   (Account → App → la tua app → scheda "Risorse collegate" → "Collega
   risorse" → tipo "Pagina").
4. Sempre nel Business Portfolio, vai su **Utenti → Utenti di sistema** →
   **"+ Aggiungi"**, crea un utente di sistema con ruolo **Amministratore**.
5. **Assegna quell'utente all'app**: Account → App → la tua app → scheda
   "Persone" → "Assegna persone" → seleziona l'utente di sistema, ruolo
   Amministratore (questo passaggio è facile da saltare, ma senza non si
   può generare un token: l'errore è "Nessuna autorizzazione disponibile").
6. Assegna anche la **Pagina** all'utente di sistema con accesso "Controllo
   completo" (dalla pagina della Pagina in Business Settings, o da quella
   dell'utente di sistema).
7. Sull'utente di sistema, clicca **"Genera nuovo token"**: scegli la tua
   app, scadenza **"Non scade mai"**, e spunta i cinque permessi del punto 2.
   Copialo subito — Meta lo mostra **una sola volta**.
8. Quel token dà accesso agli **oggetti** ma alcuni endpoint (come le insight
   della Pagina) richiedono specificamente un **Page Access Token**: nel
   Graph API Explorer, con il token del punto 7 nel campo "Token d'accesso",
   interroga `<FACEBOOK_PAGE_ID>?fields=access_token` — il valore che torna
   è il vero `META_ACCESS_TOKEN` da usare (eredita la scadenza "mai" del
   token da cui deriva).
9. `FACEBOOK_PAGE_ID` lo trovi nella stessa schermata di Business Settings
   della Pagina (sezione Account → Pagine).
10. `INSTAGRAM_ACCOUNT_ID` si ottiene interrogando, sempre nell'Explorer,
    `<FACEBOOK_PAGE_ID>?fields=instagram_business_account`.

Requisiti lato account: la Pagina Facebook deve esistere e l'account Instagram
deve essere **Business o Creator** e collegato a quella Pagina. Un account
Instagram personale non espone alcuna statistica.

Se il report smette di arrivare, la causa più probabile è il token: il
messaggio lo dice esplicitamente ("⚠️ Dati non recuperati").

### 3. I Secrets del repository

Su GitHub: **Settings → Secrets and variables → Actions → New repository
secret**, uno per ciascuna delle cinque variabili della tabella.

Opzionalmente, nella scheda **Variables** puoi impostare `REPORT_TIMEZONE`
(default `Europe/Rome`), `REPORT_DAYS` (default `7`), `META_GRAPH_VERSION`
(default `v21.0`) e `TELEGRAM_MESSAGE_THREAD_ID` (topic del supergruppo).

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

- **Facebook mostra solo statistiche aggregate, non i singoli post.** Leggere
  l'elenco dei post di una Pagina (`/posts`, `/published_posts`, `/feed`)
  richiede da Meta la funzionalità **"Page Public Content Access"**,
  approvabile solo con una vera revisione dell'app (App Review) — anche per le
  Pagine di cui si è amministratori. Finché non viene richiesta e approvata,
  il report mostra per Facebook solo copertura, impression e interazioni
  totali della settimana (lette dalle insight della Pagina, che restano
  accessibili con il solo permesso `read_insights`), senza il dettaglio per
  singolo post che invece è disponibile per Instagram. Per sbloccare anche il
  dettaglio dei post, va richiesta la revisione da developers.facebook.com →
  la propria app → **Autorizzazioni e funzionalità delle app** → **Page
  Public Content Access** → **Richiedi**; il processo prevede la verifica
  aziendale del Business Portfolio e spesso un video che dimostri l'uso reale.
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
