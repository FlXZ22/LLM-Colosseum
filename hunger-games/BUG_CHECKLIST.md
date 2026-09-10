## BUG_CHECKLIST

In this file we are going to put all the bugs and how to solve them, we will use ai to generate this each time we add a functionality!

> Gli esempi di codice qui sotto sono **schemi**, non soluzioni da incollare.
> Mostrano la forma del fix: la versione vera la scrivi tu.

Legenda stato: ✅ chiuso · 🟡 parziale · ⬜ aperto

---

# Revisione 2026-08-28 — aggiornata dopo i fix

Stato: Day 8-9 in corso. Codice **verificato con run reali** (seed 1, girato 2x):
il gioco gira fino alla fine, deterministico, e produce un log per-evento con
envelope `{seq, turn, type, data}`.

Chiusi finora: 1-21 (**21 su 21**). Nessun bug aperto.
Refactor passi 1-4 fatti (`balance.py`, `world.py`, SEARCH by `food`, roster).

## Riepilogo

| # | Stato | Gravità | File | Bug |
|---|-------|---------|------|-----|
| 1 | ✅ | 🔴 crash | `agents/agent.py` | `validate()` ritorna `reason` non assegnata |
| 2 | ✅ | 🔴 crash | `agents/agent.py` | typo `resason` nel ramo salute bassa |
| 3 | ✅ | 🔴 crash | `agents/agent.py` | `combat_value()` chiama `self.validate()` |
| 4 | ✅ | 🟠 logica | `engine/game.py` | evento `DEATH` registrato ogni turno per ogni agente |
| 5 | ✅ | 🟠 logica | `engine/game.py` | evento `HUNGER_TICK` senza il campo `agent` |
| 6 | ✅ | 🟠 logica | `engine/game.py` | gli agenti morti agiscono ancora |
| 7 | ✅ | 🟠 logica | `game.py` / `actions.py` | la stamina può andare negativa |
| 8 | ✅ | 🟠 logica | `engine/actions.py` | `is_legal` valida il target solo per `ATTACK` |
| 9 | ✅ | 🟠 logica | `main.py` | nessun tetto massimo di turni |
| 10 | ✅ | 🟡 pulizia | `engine/game.py` | strutture vecchie: `self.data`, `convert_jsonl` |
| 11 | ✅ | 🟡 pulizia | `engine/game.py` | due scrittori su file |
| 12 | ✅ | 🟠 logica | `game.py` / `main.py` | percorso log unico, passato a `Game(log_path)` |
| 13 | ✅ | 🟡 contratto | `engine/game.py` | envelope usa `action`, la EVENTS_GUIDE usa `type` |
| 14 | ✅ | 🟡 logica | `engine/game.py` | `HIDE`: successo e fallimento danno lo stesso stato |
| 15 | ✅ | 🟡 pulizia | `engine/game.py` | `run_turn` costruiva il dict `actions` inutilizzato |
| 16 | ✅ | 🔵 stile | vari | refusi: `avalible`, `atemptflee`, `atempthide` |
| 17 | ✅ | 🔵 robustezza | `main.py` | `int(seed_input)` senza `try/except` |
| 18 | ✅ | 🔵 divergenza | `engine/actions.py` | roadmap Day 8 = 6 azioni, codice = 7 (`HIDE`) |
| 19 | ✅ | 🔵 pulizia | `engine/game.py` | evento `DEATH` porta `alive` (sempre `false`) |
| 20 | ✅ | 🔵 logica | `engine/game.py` | `REST` registra i delta *prima* del clamp |
| 21 | ✅ | 🔵 design | `engine/game.py` | `FLEE` addebita stamina anche al target |

---

## ✅ CHIUSI

### Bug 1 — `validate()` ritornava `reason` non assegnata
`reason = None` come default prima degli `if`. Non crasha più su agente vivo.

### Bug 2 — typo `resason`
Corretto in `reason` nel ramo `elif self.health <= 0`.

### Bug 3 — `combat_value()` chiamava `self.validate()`
Rimossa. I "value" (`combat_value`, `flee_value`, `hide_value`) ora sono funzioni pure.

### Bug 4 — `DEATH` ogni turno
`_resolve()` confronta `alive` prima/dopo `validate()` e registra solo sulla
transizione vivo→morto. Verificato: 1 solo `DEATH` per partita nel log.

### Bug 5 — `HUNGER_TICK` senza `agent`
Aggiunto `agent=agent.name`. Verificato nel log.

### Bug 6 — agenti morti agiscono ancora
`run_turn` fa `if not agent.alive: continue`. Verificato: nessun evento dopo il
`DEATH` dell'agente.

### Bug 7 — stamina negativa
Doppia difesa: `Agent.clamp()` limita la stamina a `[0, max_stamina]`, e
`get_avalible_actions` non offre un'azione se `game.stamina_cost(agent, a) > agent.stamina`.
Introdotti `max_stamina` (stazza) separato da `stamina` (pool), la tabella
`STAMINA_COST`, `stamina_cost()` con moltiplicatore ×1.6 se `is_exhausted()`,
e `_spend_stamina()` come unico canale di spesa.

### Bug 10 / 11 — strutture vecchie e doppio scrittore
`self.data` / `"turns"` / `convert_jsonl` eliminati. Resta solo `self.events`
(l'unica verità) + `_append_to_jsonl` chiamato solo da `record`. Query per-turno
via `event_per_turn(n)`.

### Bug 15 — dict `actions` inutilizzato
Eliminato da `run_turn`.

### Bug 9 — nessun tetto massimo di turni
`main.py` ora ha un ciclo solo: `while vivi > 1 and game.turn < balance.MAX_TURNS`.
Finale a 3 rami (1 vivo → vincitore, 0 → doppia morte, >1 → "turn limit
reached, no winner"). Verificato: seed 5 e 7 finiscono in doppia morte.

### Bug 12 — log su un file solo
`Game(rng, seed, log_path)` riceve il percorso; `main.py` lo definisce una volta
(`runs/game_data.jsonl`) e tronca **quello stesso** file. `_append_to_jsonl` usa
`self.log_path`. Verificato: 2 run di fila = 83 righe, nessun file vagante.

### Bug 17 — `int(seed_input)` senza protezione
`main.py` legge la stringa, gestisce l'Invio vuoto (→ seed 0) e avvolge `int()`
in `try/except ValueError` dentro un `while True` con `break`.

### Passo 2 refactor — `world.py` come tabella
`locations` (lista di 4 stringhe) → `LOCATIONS` (dict con `food`/`danger`/
`cover` per stanza) + `LOCATIONS_NAME = list(LOCATIONS)`. `game.py`: import +
2 comprehension usano `LOCATIONS_NAME`. Le proprietà **non sono ancora usate**
(passo 3 le collega). Ordine del dict = ordine della vecchia lista, quindi
`rng.choice` invariato. Verificato: 6 seed identici alla baseline.
Trappola incontrata: un "sostituisci tutto" di `location` aveva rinominato
anche il campo evento `location=` in `LOCATIONS_NAME=` negli eventi ATTACK/
FLEE/HIDE — annullato a mano.

### Passo 1 refactor — `config/balance.py`
Tutti i numeri dell'**economia** (tick fame, costi stamina, guadagni REST, rese
SEARCH, danno ATTACK, soglie morte, esaurimento, MAX_TURNS, range stat) spostati
in `config/balance.py`. `game.py`, `agent.py`, `main.py` leggono da lì.
Comportamento invariato: stessi seed → stessi risultati di prima del refactor.
**Non** ancora spostati: i coefficienti dentro `combat_value` / `flee_value` /
`hide_value` (passo 1b, tema "bilanciamento combattimento" / Day 5).

### Bug 8 — `is_legal` valida il target solo per `ATTACK`
`is_legal` ora tratta `{"ATTACK", "FLEE", "HIDE"}` come azioni con target:
target `None` o fuori da `get_avalible_targets` → illegale; target valorizzato
su un'azione senza bersaglio → illegale. Verificato: il gioco gira, nessun
crash su FLEE/HIDE. (Quando arriverà l'LLM il target sarà una stringa, non un
oggetto `Agent` — vedi Bug 16 / nota convenzione nomi.)

### Bug 13 — chiave envelope `action` vs `type`
Envelope ora `{seq, turn, type, data}`. Parametro di `record` rinominato
`event_type` (la chiave è `"type"`, il parametro no, per non offuscare il
built-in). `game.py:146` è l'unico scrittore, nessun lettore usava `["action"]`.
Verificato nel log: 0 occorrenze di `"action"`. Resta da allineare `INFO.md`
(righe envelope + togliere dai known issues).

### Bug 19 — evento `DEATH` portava `alive`
Verificato: `_resolve()` fa `self.record("DEATH", agent=agent.name, cause=reason)`,
niente parametro `alive`. Già a posto.

### Bug 16 — refusi nei nomi
`get_avalible_actions`/`get_avalible_targets` → `get_available_*`, variabili
`avalible` → `available`, `_atemptflee` → `_attempt_flee`, `_atempthide` →
`_attempt_hide`. Toccati `game.py`, `actions.py`, `agent.py`. Nessun nome di
evento o campo `data` cambia → log identico alla baseline (6 seed verificati).
(`successor` non esisteva più, già `winner`.)

### Bug 20 — `REST` registrava i delta prima del clamp
Ora per health/hunger/stamina: `prima = agent.x`, applica, `clamp()`, poi
`delta = agent.x - prima`. L'evento REST riporta il guadagno *reale*. Lo stato
del gioco non cambia (il clamp c'era già), cambia solo il numero registrato:
verificato, il diff tocca solo i campi `*_delta` degli eventi REST, nessuna
cascata.

### Bug 21 — `FLEE` addebitava stamina al target
Scelta: niente inseguimento in V1. Tolte le 2 righe `_spend_stamina(target,
"FLEE")` e i campi `stamina_delta_target` dai record FLEE. Solo chi fugge si
stanca. Cambia il log a valanga (il target ora ha più stamina → sceglie
diverso): baseline 6-seed rigenerata dopo il fix.

---

### Bug 14 — `HIDE`: successo e fallimento sono identici
**File:** `engine/game.py`, `_attempt_hide()`
HIDE ora è azione **senza bersaglio** ("mi nascondo dalla stanza"). Riuscita =
`rng.random() < LOCATIONS[pos]["cover"]` (caves 0.9 quasi sempre, cornucopia 0.1
quasi mai). Successo → `agent.hidden = True`: `get_available_actions` /
`get_available_targets` filtrano `not n.hidden`, quindi per un turno gli altri
non ti "vedono" e non possono bersagliarti. Fallimento → `agent.hidden = False` +
`spotted=True` nel log. L'occultamento si azzera quando fai un'azione **rumorosa**
(MOVE/SEARCH/ATTACK/FLEE) — per mangiare devi uscire allo scoperto. Auto-limitato:
HIDE costa stamina e non sfama.
Verificato: sweep 80 seed, riuscita per stanza 12/18/67/82% (traccia il `cover`);
seed 4 t8 il nemico riceve il menù "da solo"; nessun deadlock (seed con hide-ok +
attacchi). Baseline 6-seed rigenerata.
**Rimandato al "batch 3":** HIDE fallito → `exposed` → il prossimo ATTACK contro
di te salta il confronto `combat_value()` (speculare del successo, fa pesare il
combattimento). `spotted=True` è l'aggancio.

### Bug 18 — 6 azioni nella roadmap, 7 nel codice
Deciso: **HIDE è la 7ª azione ufficiale** (ora ha un effetto meccanico vero, vedi
Bug 14). Da aggiornare in `INFO.md` / roadmap: elenco azioni = `MOVE, SEARCH,
REST, ATTACK, FLEE, HIDE, IGNORE`; HIDE senza bersaglio; nuovo campo evento
`spotted`; nuovo flag di stato `hidden`.

---

## Note di design (non bug)

- **Il combattimento non uccide quasi mai.** Un colpo = 50 danni, e dopo averlo
  preso sei a 50 esatti, ma per attaccare serve `health > 50` → un ferito non può
  insistere e il vincitore resta illeso. Nei run di prova entrambe le morti sono
  per fame. È il tema "bilanciamento combattimento" (Day 5), da rivedere quando
  vuoi che il combattimento pesi di più.

---

## Ordine consigliato (da qui in poi)

**Redesign in corso** (vedi "Note di design" e il piano a passi):
- passo 1 ✅ `balance.py` — costanti economia centralizzate
- passo 2 ✅ `world.py` — tabella `LOCATIONS` (food/danger/cover) + `LOCATIONS_NAME`
- passo 3 ✅ SEARCH usa `rng.random() < LOCATIONS[pos]["food"]`; tassi seguono il
  `food` (river ~0.75, caves ~0.15); 4/6 seed ora hanno un vincitore
- passo 4 ✅ roster: `Game(rng, seed, log_path, names)` costruisce
  `[Agent(n, rng) for n in names]` da `balance.AGENT_NAMES`; testo finale
  "no survivors left". Smoke test a 3 agenti ok. Baseline a 2 agenti.

- Bug 14 + Bug 18 ✅ HIDE ridisegnato: senza bersaglio, riuscita da `cover`,
  flag `hidden` che nasconde ai `get_available_*`, si azzera su azione rumorosa,
  campo evento `spotted`. Baseline 6-seed rigenerata.
- passo 5 ✅ seam del Controller: `agents/controller.py` (`Controller(rng)` con
  `choose_action(legal_actions)`); `Agent.controller`; `Game` chiama
  `agent.controller.choose_action(available)`; `Agent.choose_action` rimosso.
  6 seed identici al baseline. (Il target lo sceglie ancora `Game` — passo 6.)
  Nota: rinominare `Controller` → `RandomController` quando arriva `LLMController`.

- passo 1b ✅ coefficienti di `combat_value`/`flee_value`/`hide_value` → `balance.py`
  (`COMBAT_*`, `FLEE_*`, `HIDE_*`, `RANDOM_NOISE`, `RANDOM_ADD`).
- rework `combat_value` ✅ (2026-08-30): `capacity * readiness * noise`.
  `capacity` = somma pesata stat (0.50/0.35/0.15). `readiness` = PRODOTTO di
  `health/MAX · (1-hunger/DEATH) · stamina/max_stamina` → un fattore basso
  annienta. `noise` = `rng.uniform(0.9, 1.1)` (mai 0, mai negativo). Danno ancora
  fisso 50. Sweep: 9/80 morti "bassa salute" (prima ~0).
- HIDE cover+skill ✅ (2026-08-30): `skill = clamp01((hide_value()-10)/100)`,
  `chance = (skill + cover)/2`. Fa rivivere `hide_value`. Sweep riuscita:
  caves 82 / forest 53 / cornucopia 38 / river 33 %.
- `INFO.md` ✅ riallineato 2026-08-30 (envelope `type`, 7 azioni, HIDE senza
  bersaglio, `spotted`/`hidden`, tabella LOCATIONS, Controller, nuovo combat).
- Baseline 6-seed rigenerata 2026-08-30: 59/47/52/21/52/83.

- passo 6 ✅ seam della Perception (2026-08-30): `agents/perception.py` con la
  classe `Observation` (name, position, health, hunger, stamina, exhausted, room,
  others=[nomi], legal_actions, legal_targets) + la funzione modulo
  `observe(game, agent) -> Observation` (sola lettura, zero RNG).
  - 6a: file creato. 6b: `Game.choose_action` costruisce `obs` e la passa a
    `controller.choose_action(obs)`. 6c: la scelta del target è passata nel
    controller — `choose_action(obs) -> (action, target_name)`; `Game` risolve
    `target_name` → oggetto solo per `is_legal`, passa il nome a `execute_actions`.
  - Ordine estrazioni preservato (azione poi target) → 6 seed byte-identici in
    tutte e tre le fasi. Il controller ora riceve solo la scatola, mai `game`.

- Day 10 ✅ Tiny Inventory (2026-08-31): `engine/item.py` = dataclass `Item(frozen)`
  con campi `kind`/`name` (solo `food`/`medicine`/`weapon`) + `add_item` /
  `has_item` / `take_item` (trova+togli+return in un colpo, il primo del kind).
  `Agent.inventory = []`. `config/balance.py`: `LOOT_TABLE` (kind, name, peso) +
  `DROP_RATE = 0.35`. `game.py` SEARCH ramo `found`: dopo il record SEARCH,
  `if rng.random() < DROP_RATE` → `rng.choices(LOOT_TABLE, pesi, k=1)` → `Item` →
  `add_item` → evento `ITEM_DROP` (actor/kind/name/inventory_size). `_resolve`:
  su transizione vivo→morto registra sempre `DEATH`, poi se `inventory` non vuoto
  `ITEMS_LOST` (agent + items=[{kind,name}]) e svuota. Aggiunge estrazioni RNG →
  log divergente di proposito, baseline da rigenerare.
  Bug trovati e chiusi in sessione: `from dataclass` → `dataclasses`;
  `take_item` usava `i` non definito (var è `item`); `self.rng.random` senza `()`;
  typo `balace`/`invetory`/`Invetory` in 6 punti; virgola mancante in `record(...)`
  e in una riga di `LOOT_TABLE`; il `DEATH` era condizionato ad avere oggetti
  (regressione, l'evento spariva per chi moriva a mani vuote).
  Verificato (in luogo del test, che non c'è stato tempo di scrivere): take su
  vuoto → None; 2 medicine → ne toglie 1 sola; kind assente → None; `Item`
  frozen/hashable/eq; morte con 2 oggetti → DEATH poi ITEMS_LOST, inventory
  svuotato. 6 seed girano senza crash.
  Residuo: nessun test in `tests/` per l'inventario. `has_item` per ora inutile
  (serve al Day 11). Nota (verificata Day 14): l'evento è `ITEM_DROP` (singolare)
  e usa `agent=`, come `ITEMS_LOST`.

- Day 11 ✅ Medicine V1 (2026-08-31): `balance.MEDICINE_HEAL=40`,
  `STAMINA_COST["USE_ITEM"]=0`. `actions.py`: import `has_item`, `USE_ITEM` nei
  candidati sse `has_item(agent,"medicine")` (dopo l'if/else, prima del filtro
  affordable). `is_legal` invariato (USE_ITEM senza target → ramo else). `game.py`:
  import `take_item`, ramo `USE_ITEM` → `_use_medicine`: `take_item` (consuma
  PRIMA) → se None logga `ITEM_USED ok=False` e esce → altrimenti cura
  `MEDICINE_HEAL`, `clamp`, `wasted = delta==0`, `_spend_stamina`, evento
  `ITEM_USED` (health_before/after, wasted, stamina_delta).
  Bug in sessione: `appned`→`append`; import senza `take_item`; typo
  `wested`/`wasted` (prima incoerente → NameError, poi reso coerente sbagliato →
  campo evento errato); virgola mancante in `record(...)`; `stamina_cost` (calcola)
  invece di `_spend_stamina` (spende).
  Verificato: senza medicina USE_ITEM assente; 30→70 e consuma 1 sola; vita piena
  → `wasted=True`; medicina finita → `ok=False`. 6 seed ok.

- Day 12 ✅ Weapons V1 (2026-09-01): `balance.WEAPON_MODIFIERS` (rusted knife 8 /
  sharpened spear 14 / old katana 12), tutte e 3 già in `LOOT_TABLE`. `item.py`:
  `weapon_modifier(agent)` = `max` dei mod delle armi in inventario, **0 se
  nessuna, MAI la somma**; `best_weapon(agent)` = il `.name` dell'arma col mod più
  alto (o `None`) — serve solo per il log. `agent.py` `combat_value`: un solo
  termine **additivo** `+ weapon_modifier(self)` in fondo (non %), non tocca
  noise/readiness. `game.py` `_attack`: import `best_weapon`, campi
  `winner_weapon` / `loser_weapon` (nome o `null`) nell'evento ATTACK.
  Day 12 non aggiunge estrazioni RNG (`weapon_modifier`/`best_weapon` non usano
  rng); il log diverge solo per via di Day 10/11.
  Bug in sessione: `balance.WEAPON_MODIFIER` senza `S` (×3, AttributeError);
  `def best_weapons` plurale ma `game.py` chiama `best_weapon` singolare
  (ImportError all'avvio); `best_weapon` ritornava l'oggetto `Item` invece del
  `.name` → `json.dumps` non serializza un `Item` → crash nell'evento ATTACK.
  Verificato: 6 seed girano (exit 0, 44/52/37/21/52/64 righe); seed 11 t11 mostra
  `winner_weapon: "sharpened spear"` serializzato ok; test statistico (stat
  pareggiate, 2000 tiri × 40 seed): controllo senza arma 0.499, con knife 0.932,
  con spear 0.998; 3 armi in borsa → `weapon_modifier` = 14 (la migliore, non 34).
  Nota di design: con stat pari il mod additivo domina quasi sempre il rumore
  ±10% — magnitudo da rivedere in un futuro pass di bilanciamento (non blocca V1).
  Nit (risolto Day 14): l'evento in `game.py` è `ITEM_DROP` (singolare), i doc
  ora concordano.
- Baseline 6-seed rigenerata 2026-09-01: seeds 0,1,2,3,5,7 = 44/52/37/21/52/64
  (era 59/47/52/21/52/83; cambia per Day 10 + Day 11).

- Day 13 ✅ (meccanica) Perception vera (2026-09-01): in `perception.py` —
  `health_phrase`/`hunger_phrase`/`stamina_phrase` (4-5 bande, stamina sul
  rapporto `s/max_stamina`), `locations_phrase(pos)` (cover+food qualitativi,
  `danger` escluso: nessuna meccanica), `describe_other(agent, other)` (3 bande
  salute, niente fame, arma → "clutching something you can't make out", mai stat
  esatte / nomi oggetti / personalità). `Observation` ora porta le **frasi** al
  posto degli int + `turn` + `inventory` (tuoi, precisi) + metodo `to_prompt()`
  (testo per l'LLM, zero cifre, `turn` tenuto fuori dal testo).
  Bug in sessione: virgola mancante nel costruttore; `legal_actions` non
  qualificato in `to_prompt` (→ `self.`); `"/n"` invece di `"\n"`; `r["darger"]`
  (chiave è `danger`); `describe_other` prima a 4 bande e senza param `agent`;
  refusi `peckich`/`plentifull`/`scarse`.
  Verificato: 6 seed byte-identici alla baseline (RNG intatto); `to_prompt()` non
  contiene cifre né valori-stat reali; salute/arma di B assenti nel prompt di A.
  **Debito:** il file leak-test in `tests/` non è scritto (rimandato alla
  sessione-test del Day 14).

- Day 14 ✅ Test session — chiude Week 2 (2026-09-03). Pacchetto `tests/`:
  `__init__.py` (vuoto, per `unittest discover`); `harness.py` con `new_game` /
  `alive_agents` / `run_match(seed)` (match deterministico completo + record
  `RESULT`) / `actor_name(e)` (normalizza `agent` vs `actor`) / 6 helper
  `_check_*` che **raccolgono** le violazioni senza sollevare:
  `_check_log` (seq monotono da 1, chiavi envelope, serializzabile, turni
  ordinati), `_check_agents` (hunger ≥ 0, health ≤ MAX, stamina in range, vivo ⇒
  non oltre soglia morte, morto ⇒ ha evento DEATH, posizione valida),
  `_check_no_action_after_death` (nessun evento-azione con `actor == nome` dopo
  il turno di DEATH), `_check_termination` (turn ≤ MAX_TURNS; non finita con > 1
  vivo prima del tetto), `_check_items` (entrati = rimasti + usati[ok] + persi),
  `_check_events` (MOVE `from_ != to`; FLEE `success` ⇔ `escaped_to` non-None;
  nomi ATTACK/FLEE nel roster). `check_invariants(game, events)` = concatenazione
  delle 6 liste. `sweep(n=500)` avvolge ogni match in `try/except Exception as
  err` → `["Crash: " + repr(err)]`, ritorna `[(seed, violazioni), ...]`.
  `test_perception_leak.py` (debito Day 13, 4 test) + `test_integration.py`
  (6 test: `sweep(500)` pulito, `run_match(0)` × 2 log identici, un test per
  classe di invariante, meta-test "il checker becca davvero un evento corrotto").
  10 test totali, ~0.6 s, verdi.
  **Risultato: `sweep(1000)` = 0 seed rotti** → nessun file di regressione
  necessario. Il motore, per come lo si interroga oggi, non viola invarianti.
  Bug trovati in sessione (tutti nel codice dei test, scritti da Metis):
  `game.Agents`/`game.agent` invece di `game.agents`; `len(generatore)` (non ha
  `len`) → `sum(1 for ...)`; `"ITEM_LOST"` invece di `"ITEMS_LOST"` (→ 39/400
  falsi positivi); `except Exception:` senza `as err` + `repr(Exception)` (la
  classe, non l'istanza); `if not v:` invertito in `sweep`; `self.Subtest` →
  `self.subTest`; due metodi `check_*` senza prefisso `test_` (unittest li
  saltava in silenzio); `assertEqual([], ...)` dove serviva `assertNotEqual`;
  f-string non chiuse / variabili con refuso (`promblems`).

### Nota accettata — `clamp()` non è bilaterale (2026-09-03)
**File:** `agents/agent.py::clamp`. `hunger = max(0, hunger)` (solo floor),
`health = min(MAX_HEALTH, health)` (solo cap). Quindi nel turno in cui un agente
muore, `hunger` può leggere > 100 e `health` < 0 — lo stato di morte è corretto
(`validate()` decide bene), ma i valori numerici sfondano da un lato.
**Non è un bug**: `_check_agents` asserisce solo `hunger ≥ 0` e
`health ≤ MAX_HEALTH`. Se un giorno servisse loggare valori "puliti" alla morte,
aggiungere il secondo bound in `clamp()` (cambia solo i numeri negli eventi
HUNGER_TICK / DEATH dell'ultimo turno, nessuna cascata RNG).

Prossimo: passo 7 (ActionSpec registry) — interno, opzionale, non parte di Week 2.

Lavori residui (non bug di runtime):
1. "Batch 3" HIDE: fallimento → `exposed` → prossimo ATTACK salta `combat_value()`.
2. **Bug 8b / convenzione nomi**: quando arriva l'LLM il target sarà una stringa,
   non un oggetto `Agent` — `is_legal` e `execute_actions` vanno resi coerenti.
3. Danno ATTACK proporzionale al divario di `combat_value` (invece del fisso 50).
4. `danger` per stanza: definito, non ancora usato.
