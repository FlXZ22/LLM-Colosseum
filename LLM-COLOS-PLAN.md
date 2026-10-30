# ⚔️ LLM Colosseum — Il Piano

> Piano a 21 giorni (Day 8 → 28) di [progects-seven.vercel.app](https://progects-seven.vercel.app/), senza esercizi e confrontato con il codice.
> Codice verificato il **2026-10-22** · branch `day-20-part2` · commit `7a51ddb`

**Legenda:** ✅ fatto · 🟡 in parte · ⬜ da fare · 💡 miglioramento rispetto al sito

---

## Indice

1. [La regola d'oro](#1-la-regola-doro)
2. [Stato attuale](#2-stato-attuale)
3. [Da sistemare subito](#3-da-sistemare-subito)
4. [Settimana 2 — Motore e percezione](#4-settimana-2--motore-e-percezione-day-814)
5. [Settimana 3 — Personalità e LLM](#5-settimana-3--personalità-e-llm-day-1521)
6. [Settimana 4 — Società e client](#6-settimana-4--società-e-client-day-2228)
7. [Settimana 5 — Dopo V1](#7-settimana-5--dopo-v1)
8. [V1 è finita quando](#8-v1-è-finita-quando)
9. [Regole di lavoro](#9-regole-di-lavoro)

---

## 1. La regola d'oro

> **L'LLM sceglie. Il motore esegue.**
> Il modello riceve una descrizione e una lista di mosse legali, e ne restituisce **una**. Non tocca mai lo stato, non inventa azioni, non vede numeri nascosti.

| Livello | Fa | Non deve mai |
|---|---|---|
| Engine | Numeri, casualità, risultati, azioni legali | Chiedere all'LLM cosa succede |
| Perception | Trasforma i numeri in frasi | Rivelare statistiche esatte o segreti altrui |
| LLM controller | Sceglie un'azione dalla lista | Modificare lo stato o essere creduto senza validazione |
| Event log | Registro completo in JSONL | Dipendere da dati che stanno solo in memoria |
| Client | Legge il JSONL e racconta la storia | Importare l'engine |

**Il turno:** `Stato → Percezione → LLM sceglie → Engine valida ed esegue → Eventi → (nuovo stato)`

---

## 2. Stato attuale

| Settimana | Day | Stato |
|---|---|:---:|
| **2 · Motore** | 8 Azioni · 9 Eventi · 10 Inventario · 11 Medicine · 12 Armi · 13 Percezione | ✅ |
| | 14 Test e bug hunt | 🟡 i test oggi sono rossi |
| **3 · LLM** | 15 Personalità · 16 Memoria · 17 Intelligenza · 18 Controller · 19 Collegamento | 🟡 |
| | **20 Esperimento personalità** | 🎯 **sei qui** |
| | 21 Stabilità | ⬜ |
| **4 · Società** | 22 Talk · 23 Alleanze · 24 Tradimento · 25 Replay · 26 Streamlit · 27 Polish · 28 Finale | ⬜ |

**Da notare in git:**
- `hunger-games/BUG_CHECKLIST.md` è cancellato ma la cancellazione non è committata.
- `DEVLOG.md` si ferma al Day 15.

---

## 3. Da sistemare subito

💡 Queste correzioni vanno fatte **prima** dell'esperimento del Day 20. Altrimenti l'esperimento misura i bug invece delle personalità.

| # | Problema | Dove | Day |
|:-:|---|---|:-:|
| 1 | I test sono rossi: `Game(...)` viene chiamato senza `profiles`, quindi tutti i 500 seed crashano | `tests/harness.py:11` | 14 |
| 2 | Il controller non si può sostituire, quindi i test userebbero l'API vera | `agents/agent.py:22` | 14 |
| 3 | Il venv punta a mise `python/latest` (ora 3.15), ma i pacchetti sono installati per la 3.14. In più `json` in `requirements.txt` va tolto | `pyvenv.cfg`, `requirements.txt` | 14 |
| 4 | "X attacked you" non viene mai scritto: la riga sta dopo un `return` | `llm/memory.py:77` | 16 |
| 5 | Gli oggetti trovati non vengono mai ricordati (`item_drop` ≠ `item`) | `memory.py:117`, `balance.py` | 16 |
| 6 | `decay_value=0.8` nel profilo `medium` (forse doveva essere 0.08?) | `llm/memory.py:30` | 17 |
| 7 | L'intelligenza è ancora in combattimento, fuga e nascondersi | `agents/agent.py:48, 63, 72` | 17 |
| 8 | Il fallback casuale sta dentro il controller e può scegliere `ATTACK` | `agents/controller.py:74` | 19 |
| 9 | Il retry ripete lo stesso identico prompt | `controller.py` | 19 |
| 10 | La risposta completa dell'LLM finisce nel log degli eventi | `engine/game.py:60` | 21 |
| 11 | Ci sono due fonti per i nomi: `Agent-A/B` e Rocky/Flint/Mike | `config/balance.py:36` | 20 |

---

## 4. Settimana 2 — Motore e percezione (Day 8–14)

> **Obiettivo:** un gioco senza LLM, stabile e prevedibile.

| Day | Obiettivo | Finito quando | Stato |
|:-:|---|---|:-:|
| 8 | Un'unica funzione restituisce le azioni e i bersagli legali, senza cambiare niente | Stessa domanda → stessa lista, sempre | ✅ |
| 9 | Il motore registra fatti (eventi), non frasi | Senza `print()` la partita si capisce comunque dal JSONL | ✅ |
| 10 | Inventario di 3 tipi: food, medicine, weapon | Trovare, portare e perdere un oggetto sono tutti eventi | ✅ |
| 11 | La medicina cura in modo fisso e parziale | È il motore, non l'LLM, a decidere quanto si cura | ✅ |
| 12 | Un'arma è un bonus numerico; conta solo la migliore | L'evento `ATTACK` spiega chi ha vinto e perché | ✅ |
| 13 | L'agente vede frasi, non numeri | Nessun numero nascosto nel prompt (test anti-leak) | ✅ |
| 14 | Centinaia di seed senza violazioni | `sweep(500)` pulito e stesso seed = stesso log | 🟡 |

💡 **Day 14, riparazione:** il `Game` deve poter ricevere *quale* controller usare: casuale per i test, LLM per le partite vere. Così i test tornano offline e gratuiti.

---

## 5. Settimana 3 — Personalità e LLM (Day 15–21)

> **Obiettivo:** lo stesso modello interpreta personaggi diversi, e la differenza si può misurare.

### Day 15 · Personalità 🟡
- **Obiettivo:** tre profili che portano a **scelte** diverse, non solo a un tono diverso.
- **Già fatto:** 3 profili OCEAN come dati, `to_prompt()`.
- **Manca:**
  - tendenze legate alle azioni vere ("attacca a vista se non sta morendo");
  - il test a mano su 5 scenari;
  - togliere al Diplomat gli obiettivi sociali, che oggi il gioco non può esprimere (tornano al Day 22).
- **Finito quando:** ogni coppia di profili sceglie diversamente in almeno 2 scenari su 5.

### Day 16 · Memoria 🟡
- **Obiettivo:** poche memorie in prima persona, scelte per rilevanza.
- **Già fatto:** `Memory`, `remember`, `recall`, il limite di capacità, le memorie nella percezione.
- **Manca:** correggere i bug #4 e #5, decidere se `death` va ricordato, salvare nel log gli id delle memorie richiamate a ogni decisione.
- **Finito quando:** ogni decisione ha 3–4 memorie rilevanti, e tra queste c'è sempre chi hai davanti.

### Day 17 · Intelligenza → memoria 🟡
- **Obiettivo:** l'intelligenza cambia la qualità dei ricordi, non la forza.
- **Già fatto:** `MemoryProfile`, `degrade()` applicato quando la memoria viene letta.
- **Manca:** togliere l'intelligenza dal combattimento (#7), correggere il decay (#6), rendere il degrado probabilistico usando il RNG del gioco.
- **Finito quando:** due agenti ricordano lo stesso evento in modo diverso, e nessuno dei due combatte meglio per questo.

### Day 18 · LLM Controller 🟡
- **Obiettivo:** un adattatore che restituisce **una** azione legale oppure `None`, senza toccare lo stato.
- **Già fatto:** `Intent`, `prompt_builder`, `parse_intent`.
- **Manca:** togliere il fallback dal controller (#8), ripetere la lista delle azioni subito prima della risposta, 10 situazioni finte con un modello stub.
- **Finito quando:** con lo stub, 10 casi danno un `Intent` valido o `None`, senza rete.

### Day 19 · LLM ↔ Motore 🟡
- **Obiettivo:** **un solo** agente LLM finisce una partita intera.
- **Già fatto:** validazione con `is_legal`, il fallback è visibile nel log.
- **Manca:**
  - un solo agente LLM, l'altro casuale;
  - nel retry, il motivo del rifiuto (#9);
  - un fallback noioso (`REST`/`IGNORE`);
  - un evento `decision` con tier e latenza;
  - un budget massimo di chiamate.
- **Finito quando:** la partita finisce, gli invarianti passano, e il tasso di fallback si legge dal log.

### Day 20 · Esperimento personalità 🎯
- **Obiettivo:** capire se la personalità cambia davvero il comportamento.
- **Parte 1 — recupero** 💡: sistemare i problemi #1–#9 e #11.
- **Parte 2 — esperimento:**
  - 20 seed fissi, ogni profilo su ogni seed;
  - 💡 l'agente LLM gioca contro un avversario casuale sempre uguale;
  - intelligenza costante;
  - metriche decise prima: attacco, fuga, ricerca, uso delle medicine, prima azione all'incontro;
  - previsioni committate in git **prima** del primo run;
  - tassi calcolati solo sui turni in cui l'azione era disponibile, presi dal JSONL.
- **Attenzione:** con l'LLM nel loop, lo stesso seed non dà più la stessa partita. Usa una temperatura bassa e registra il modello.
- **Finito quando:** almeno 2 metriche differiscono nella direzione prevista, e hai un momento concreto del replay da mostrare.

### Day 21 · Stabilità ⬜
- **Obiettivo:** il loop regge partite lasciate girare da sole.
- **Cosa fare:**
  - un client finto che produce ogni tipo di errore;
  - errori distinti (parse, validazione, timeout, 429, 5xx, risposta vuota);
  - backoff solo per 429 e 5xx, con un budget unico;
  - prompt limitato richiamando meno memorie;
  - un riepilogo a fine partita;
  - 💡 `raw_text` spostato in un file di debug (#10);
  - 💡 una riga di intestazione nel JSONL (seed, roster, modello, `schema_version`).
- **Finito quando:** 5 partite senza intervento, fallback sotto il 5%, e il prompt al turno 60 è lungo come al turno 5.

---

## 6. Settimana 4 — Società e client (Day 22–28)

> **Obiettivo:** gli agenti parlano, si alleano e si tradiscono, e un estraneo capisce il replay.

### Day 22 · Comunicazione ⬜
- **Obiettivo:** un messaggio breve per volta, niente conversazioni.
- **Cosa fare:**
  - `TALK` disponibile solo se qualcuno è presente;
  - un campo `message` nell'`Intent`, con un limite di lunghezza imposto dal motore;
  - il destinatario lo salva come memoria;
  - un evento `TALK`.
- **Finito quando:** il destinatario ha il messaggio nella decisione successiva, e le chiamate per turno non aumentano.

### Day 23 · Alleanze ⬜
- **Obiettivo:** il sistema di alleanze più piccolo che si possa ancora rompere.
- **Cosa fare:**
  - `PROPOSE_ALLIANCE`, `ACCEPT`, `REJECT`, `LEAVE_ALLIANCE`;
  - un solo registro, con la coppia di nomi ordinata come chiave;
  - le proposte scadono;
  - niente `ATTACK` tra alleati;
  - un evento per ogni transizione;
  - la simmetria come invariante.
- **Finito quando:** uno sweep di 100 seed non trova alleanze asimmetriche.

### Day 24 · Tradimento ⬜
- **Obiettivo:** rompere un'alleanza lascia il segno nella memoria della vittima.
- **Cosa fare:**
  - attaccare un alleato scioglie l'alleanza e conta come tradimento;
  - anche l'ostilità entro 2 turni dall'uscita conta come tradimento;
  - la memoria della vittima ha salienza massima;
  - `SHARE_FOOD` con un evento `help`;
  - **nessun punteggio di fiducia**.
- **Finito quando:** chi è stato tradito al turno 12 lo ricorda al turno 40, e due personalità reagiscono in modo diverso.

### Day 25 · Lettore di replay ⬜
- **Obiettivo:** ricostruire la partita **solo** dal JSONL.
- **Cosa fare:**
  - `read_match(path)` senza import dall'engine;
  - controllo dell'intestazione;
  - snapshot per turno;
  - navigazione avanti e indietro;
  - un test che vieta gli import dall'engine.
- **Finito quando:** lo stato finale ricostruito coincide con quello dell'engine.

### Day 26 · Client Streamlit ⬜
- **Obiettivo:** chi non ha scritto il gioco capisce la partita.
- **Cosa fare:**
  - slider dei turni;
  - una scheda per agente;
  - agenti raggruppati per luogo;
  - feed degli eventi filtrato;
  - badge per le alleanze;
  - schermata del vincitore;
  - solo lettura, con `@st.cache_data`.
- 💡 Aggiungi `streamlit` a `requirements.txt`.
- **Finito quando:** un estraneo racconta la partita senza farti domande.

### Day 27 · Bello da guardare ⬜
- **Obiettivo:** far risaltare i momenti importanti senza toccare l'engine.
- **Cosa fare:**
  - un punteggio di importanza per turno;
  - "vai al prossimo momento importante";
  - stili diversi per morti e tradimenti;
  - grafo delle relazioni;
  - story mode con i 10 momenti principali.
- **Finito quando:** i 3 momenti chiave si trovano in meno di 10 secondi, e `git diff engine/` resta vuoto.

### Day 28 · Integrazione finale ⬜
- **Obiettivo:** una V1 completa e funzionante, **senza feature nuove**.
- **Cosa fare:**
  - test da un clone pulito;
  - matrice 5 seed × 3 combinazioni;
  - l'esperimento del Day 20 ripetuto sulle azioni sociali;
  - README;
  - una partita vetrina committata;
  - la lista della Settimana 5.
- **Finito quando:** un estraneo installa il progetto, guarda la partita vetrina e ne lancia una sua, con fallback sotto il 10%.

---

## 7. Settimana 5 — Dopo V1

Idee scritte qui apposta per **non** farle adesso:

- 🎮 Client in **Godot**, che legge lo stesso JSONL
- 🧑 **Umano contro LLM**, tramite un controller umano
- 🐺 **Creature** (witcher, mago), che usano finalmente la colonna `danger`
- 🎬 Intro cinematica con voce narrante
- ⚔️ Danno che scala con il margine di `combat_value`; HIDE fallito → stato `exposed`
- 🤖 **Più modelli a confronto**: è il vero obiettivo di ricerca

---

## 8. V1 è finita quando

- [ ] I test sono verdi e offline, e `sweep(500)` è pulito
- [ ] Il fallback è sotto il 5% (Day 21) e sotto il 10% sulla matrice finale (Day 28)
- [ ] Almeno 2 metriche mostrano differenze tra le personalità nella direzione prevista
- [ ] Il client non importa nulla dall'engine
- [ ] Ci sono il README e una partita vetrina nel repo

---

## 9. Regole di lavoro

- ✍️ **Nessun codice scritto dall'AI:** ogni riga la scrivi tu.
- 🌿 Un branch per ogni giorno, e una PR verso `main` a fine giornata.
- 📓 `DEVLOG.md` aggiornato lo stesso giorno.
- 🧪 Se un test è rosso, non si passa al giorno dopo.
- 🎲 Un solo RNG con seed, niente `random` globale.
- 💸 Prima lo stub, poi l'API vera.
