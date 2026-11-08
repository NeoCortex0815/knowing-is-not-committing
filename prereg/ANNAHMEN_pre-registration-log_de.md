# WSP – bisherige Annahmen für Messungen, Tuning und Ziele

Stand: **05.11.2026, 12:30**. Lebendes Dokument: Jede Annahme wird durch eine Messung bestätigt oder verworfen und
dann hier mit Datum nachgetragen. Grafik: `tuning_bereiche.png` (erzeugt mit `tuning_bereiche_grafik.py`).

## Ziel

- **Zielmodell:** Qwen3.6-35B-A3B (MoE, Apache-2.0). Auf dem MiniPC (64 GB gemeinsamer Speicher, keine eigene GPU)
  läuft im Alltag nur ein MoE mit wenigen aktiven Parametern flüssig.
- **Format:** GGUF in Q6_K oder Q5_K_M. Betrieb als persönlicher Assistent.
- **Ausrichtung:** gutes Deutsch, wenig Halluzination, wenig Babysitting.
- **Wo was läuft:** Tuning und Analyse auf dem Laptop (RTX 4060), Erzeugung und Betrieb auf dem MiniPC.
- **Reihenfolge:** Phase 2 (35B) beginnt erst, wenn Phase 1 (0.8B) das MIT-Ergebnis mit **eigener** Reparatur
  erreicht oder übertrifft.
- **Später:** Veröffentlichung von Forschung, Code und ggf. Modell auf GitHub / Hugging Face. Vorher Lizenzen
  prüfen und keine Eingriffe in Sicherheitsverhalten.
- **Langfristig (05.11.): Prüfstraße für beliebige offene Modelle.** Jedes Modell durchläuft dieselbe Batterie:
  durchleuchten, Richtung, Prüfstand, Patch + Gegenproben, GGUF + Modellkarte. Das ist zugleich ein
  **Regressionstest** über Modellversionen hinweg. Folgen für die Werkzeugentwicklung:
  - jeder Schritt per Konfiguration statt Handarbeit
  - je Architektur ein Anpassungsbaustein mit Selbsttest
  - Ergebnisse maschinenlesbar und vergleichbar
- **Nebenidee (nicht im Fokus):** getunte Kleinmodelle als GGUF für Smartphones. Erst mit eigener Reparatur,
  Modellkarte und passenden Sampling-Einstellungen.

## Kandidaten für Phase 2 (05.11.)

Details: `recherche/k2/K2_EINORDNUNG.md`.

| | Qwen3.6-35B-A3B | K2-Horizon-MoVA-36B-A4B |
|---|---|---|
| Aktiv je Token | ~3B | ~4B (etwa 25–35 % langsamer) |
| Bauart | Hybrid (Gated DeltaNet + jede 4. Schicht volle Attention), MoE 256/8 | volle Attention überall, MoE 100/8 + **MoVA** (Value-Experten 64/4) |
| KV-Cache | klein | ~10× größer, lange Kontexte teuer |
| GGUF Q6_K / Q5_K_M | ~29 GB | 30,8 / 26,4 GB (offiziell) |
| llama.cpp b11636 | ja | ja (ab b11454) |
| Agenten / Werkzeuge (AA) | tau3 9,3 · Terminal-Bench 44,9 | **26,8 · 58,6** |
| Nicht-Halluzination (AA-Omniscience) | 49,5 | **69,2** |
| Deutsch | vermutlich stark | Karte nennt nur Englisch → messen |
| WSP-Werkzeuge | fertig und geprüft | Anpassungsbaustein nötig (~1 Tag), MoVA als neuer Eingriffsort |

**llm-bench.io (33–64 GB, abgerufen 05.11.):**

Methode:
- 4 Prompts (Agent, Code, Rollenspiel, Recherche), Qualitätswert je Lauf.
- Sampling = Standard des jeweiligen Tools, die Seite setzt keine Temperatur. Unser Sampling-Befund wirkt dort also mit.
- Vorwiegend Apple-Hardware, Tok/s deshalb nicht auf den MiniPC übertragbar.
- Unterschiede von wenigen Punkten sind bei 4 Prompts und 2–20 Läufen Rauschen.

MoE-A3B-Rangfolge dort:

| Modell | Qualität |
|---|---|
| **Ornith-1.5-35B-A3B** (Qwen3.6-Feintune, BF16 + MIT-Lizenz, unsere Werkzeuge passen direkt) | 86,2 / Q8 85,2 |
| Tiel-Coder-35B-A3B (nur GGUF/MLX, keine vollen Gewichte gefunden) | 84,5–85,1 |
| K2 MoVA (MLX 4bit) | 83,9 |
| Qwen3.6-35B-A3B (Basis) | ~79–81 |
| Nemotron 3.5 Lightning 30B-A3B | ~78 |

Weitere Einträge:
- Ganz oben stehen **Qwen3.8-27B (dicht)** und Varianten (~85–88). Ohne eigene GPU auf dem MiniPC voraussichtlich zu
  langsam (dicht, grob 5–8 Tok/s).
- Ein offizielles Qwen3.8-A3B gibt es nicht: offiziell nur 27B, Flash-Next, 2.4T-A95B.
- Viele Einträge sind „Uncensored/Abliterated“-Abwandlungen, die nicht unser Ziel sind.

→ **Ornith-1.5 gehört als dritter Kandidat in den Basisvergleich.** Gleiche Architektur wie Qwen3.6, Werkzeuge
sofort nutzbar, Download BF16 ~72 GB nur mit OK.

**Praxis-Historie des Nutzers auf dem MiniPC** (Quelle: `minisforum-ki-setup/docs/modell-historie-hx470.pdf`,
Stand 05.11.):

Bisher genutzt:
- **Produktion: K2 MoVA Q5_K_M** (offizielles IFM-GGUF), ctx 124k, KV q8_0
  - Sampling temp 0.35 / top_p 0.92 / top_k 40 / min_p 0.05, **presence 0**: 0.4 destabilisierte MoE und
    Werkzeug-Aufrufe
  - ~14 Tok/s Decode, ~97 Prefill
  - **Korrektur (Nutzer, 05.11.):** Die Historie ist an dieser Stelle veraltet. Gewünschter Ist-Zustand ist,
    was auf dem MiniPC läuft: **Ornith-1.5-35B-A3B Q6_K** (llama.cpp mainline, ctx 124k, Denken high,
    Budget 8192). Alte Setups dürfen weg, Ziel ist das bestmöglich getunte Modell + neuer Harness.
- **Eigene ki-arena (14.10.)**, Gewichtung: Leistung 40 · Autonomie 20 · Ehrlichkeit 15 · Deutsch 15 · Tempo 10

  | Instanz | Gesamt | DE (LanguageTool) | Babysitting-Index | Decode |
  |---|---|---|---|---|
  | **K2** | **86,2** | 1,05 Fehler/100 W | **0,33** | 14,2 Tok/s |
  | Ornith-1.5 Q5_K_M | 73,2 | **0,0 Fehler/100 W** | 0,89 | **22,2 Tok/s** |
  | Qwen3.8-Flash-Next Q2 | 79,8 | 1,56 Fehler/100 W | 0,33 | 10,7 Tok/s |

- **Qwen3.6-35B-A3B** (Q4/Q5): früh produktiv, „DE oft stärker von Haus aus“. Abgeschaltet nur wegen
  Ein-Modell-Betrieb (Okt 2025), nicht wegen Qualität.
- **Dichte 27B/30B (Qwen3.8):** 4–7 Tok/s, Bandbreitengrenze bestätigt → verworfen.
- **Lehre des Nutzers:** Das Sampling (0.35 vs. 0.6 vs. 1.0) ändert das Verhalten stark, Vergleiche nur mit
  geloggtem `/slots`-Sampling. Das deckt sich mit unserem Befund vom 05.11.

→ **Folgerungen:**
- Die ki-arena des Nutzers ist die Messlatte für den Alltag (Autonomie, Ehrlichkeit, Deutsch, Tempo). Der
  Phase-2-Basisvergleich soll sie nutzen bzw. mit unserer Batterie verbinden, statt sie neu zu erfinden.
- **K2** ist bisher Sieger für Autonomie und Ehrlichkeit, **Ornith** für Deutsch und Tempo. WSP-Ziel wäre z. B.:
  K2s Deutsch verbessern oder Ornith weniger Babysitting abverlangen.

**Annahme:**
- Die Wahl fällt erst nach einem Basisvergleich auf dem MiniPC (Qwen3.6, Ornith-1.5, K2), mit richtigem Sampling.
- Zielbereiche: Deutsch, Abdriften, Anweisungstreue, Halluzination, Werkzeug-Aufrufe, Alltagsprofil.
- Ein Index-Gesamtsprung durch WSP ist unwahrscheinlich. Realistisch sind gezielte Gewinne dort, wo ein
  Reflex Punkte kostet.

## Tuning-Bereiche (Einschätzung für das 35B)

| Bereich | Einschätzung | Begründung | Nächster Schritt |
|---|---|---|---|
| Sampling-Einstellungen (neu) | sehr wahrscheinlich | Kein Gewichtseingriff. Am 0.8B entschied das Sampling über 25 % vs. ~47 % (A/B-Test läuft). Für den Alltag sofort nutzbar. | Am 35B im Alltagsprofil messen: llama.cpp-Standard vs. vLLM-Stil |
| Denkschleifen | offen | Belegt am 0.8B (MIT, unser Nachbau). Große Modelle schleifen seltener. | Basismessung 35B im Denkmodus (Abbrüche, dup8) |
| Anweisungstreue (Format, Länge) | offen | Am 0.8B Nebeneffekt der Schleifen (MIT: IFEval 21 → 62 %). | IFEval-artige Basismessung 35B (auch deutsch) |
| Sprach-Abdriften | Werkzeug fertig, Bedarf offen | Gut erkennbar (`10_sprache.py`, Test 7/7). Am 0.8B kein Abdriften in 24 Antworten. | 80 deutsche Aufgaben am 35B messen |
| Deutsch: Rechtschreibung/Grammatik | Werkzeug fertig, eher begrenzt | Qwen3.6 schreibt schon gut Deutsch. Nur systematische Fehler sind ansprechbar. LanguageTool ist eine Untergrenze. | Fehlerprofil 35B: dominieren wenige Regeln? |
| Schmeichelei | offen | Methodisch machbar (MIT exp7). Hoher Wert für „wenig Babysitting“. Aufgabensatz fehlt. | Deutschen Aufgabensatz bauen (inkl. Gegenprobe gegen Sturheit) |
| Werkzeug-Aufrufe im Agenten | offen | Systematisches Muster, wichtig für Autonomie. Braucht Harness-Mitschnitte. | Nach Harness-Neubau: Gültigkeitsquote messen |
| Überkonfidenz / Halluzination | offen (Forschung) | „Wahrhaftigkeits-Richtung“ hilft teilweise, ohne Garantie. | Später: Falschaussage- UND Enthaltungsquote |
| Mathe-Können an sich | nicht möglich | Ein Eingriff kann Können nur freilegen (z. B. über Schleifen), nicht hinzufügen. | – |
| Aussprache (Sprachnachrichten) | nicht möglich | Anderes Modell (Sprachausgabe), nicht das Sprachmodell. | – |

## Annahmen zur Messung

1. **Zwei Budgets.**
   - 32k Tokens für den Vergleich mit dem MIT.
   - **Alltagsprofil** 4k / 8k / 16k, im Chat-Alltag zählt die Wartezeit. Grob ohne neue Läufe mit
     `12_budget_kurve.py`, realistisch mit erzwungener Antwort `03b_budget_eval.py`.
2. **Sampling wie die Referenz.** Für den MIT-Vergleich vLLM-Stil:
   - Wiederholungsstrafe über die ganze Antwort (`repeat_last_n` 40960)
   - Temperatur vor top-k/top-p
   - Der llama.cpp-Standard (64 Tokens, Temperatur zuletzt) verfälscht reparierte Modelle stark.
2b. **Denk-Einstellung ist Teil des Protokolls**, genau wie das Sampling. Sie wird je Lauf geloggt.
   - Denken an oder aus
   - Budget (z. B. 8192), danach Antwort erzwungen
   - `reasoning_effort` bei Modellen, die Stufen kennen (K2: low/medium/high, empfohlen high). Qwen3.6/Ornith
     kennen nur an/aus, dort steuert das Budget die Denklänge.
   - Phase 1: wie das MIT (Denken an, kein Budget, 32k).
   - Phase 2: Alltagskonfiguration (Denken an, high wo vorhanden, Budget 8192) **plus** ohne Denken (schnelle
     Chat-Antworten).
3. **Bewertung:** math-verify **im Hauptthread** oder ohne Zeitbegrenzung. In Threads fällt es sonst still auf einen
   Textvergleich zurück.
4. **Trennung der Daten:** Diagnose nur auf Übungsdaten, Bewertung nur auf Testdaten. Für den Prüfstand werden
   Transkripte zurückgehalten (`--halte-zurueck`).
5. **Kontrollen:** Zufallsrichtung gleicher Stärke als Gegenprobe. Stabilität der Richtung ≥ 0,9. Am MIT-Abgleich
   prüfen, ob unsere Messung die MIT-Einzeldaten trifft (`13_mit_abgleich.py`).
6. **Statistik:** 40 Aufgaben ≈ ±7–8 Punkte Rauschen. Eine Aufgabe = 2,5 Punkte. Entscheidungen nur bei
   deutlichem Abstand oder gepaartem Vergleich auf denselben Aufgaben.
7. **Diagnosedaten vom Zielmodell selbst:** Fremde Fehler (z. B. vom 0.8B) treffen nicht die Reflexe des 35B.

## Annahmen zum Tuning

1. WSP **entstört**, es macht nicht klüger: ein Eingriff je wiederkehrendem Reflex, nie gegen Wissenslücken.
2. **MoE:** Eingriff in die gebündelten Experten (`experts.down_proj`) und den Shared Expert. Werkzeuge am echten
   35B geprüft (Mathematik exakt bis 5·10⁻⁷).
3. **Vor der echten Messung:** Kandidaten (Schichten × α × Neuronenzahl) im Prüfstand vorsortieren (Minuten statt
   Stunden). Nur die besten gehen in die echte Messung.
4. **Nebenwirkungs-Batterie** nach jedem Eingriff, auch beim Stapeln mehrerer Eingriffe (siehe PRUEFSCHEMA.md).
5. **Quantisierung:** Ein Eingriff gilt erst, wenn er Q6_K übersteht. Am 0.8B kommt er auf Gewichtsebene zu 99,9 %
   an (Q5_K_M 99,7 %, aber mehr Rauschen).
6. **Alltagstauglich** ist ein Eingriff erst, wenn er auch im Alltagsbudget wirkt. Am 0.8B wirkt der MIT-Edit vor
   allem bei langem Denken (8k: 2,5 → 6 %, 32k: 7,5 → 21–25 %).

## Kandidaten-Sammlung Phase 2 – „Argon“ (Gemini-App, 05.11., extern, UNGEPRÜFT)

Quelle: https://share.gemini.google/RzT97ppSn6tT. Auftrag des Nutzers an Argon: Top 10 lokale Modelle mindestens in der Liga von
Qwen 27B Dense, lohnend auf dem HX 470 (890M, 64 GB) und WSP-tauglich. Werte von Argon, Herkunft der Zahlen unbekannt.
Der Index („Coding & Reasoning, 0–100“) ist eine andere Skala als unsere Qualitätstabelle oben.
Nebenbefund (korrigiert per dmidecode): MiniPC = Minisforum HX 470 mit **2 × 32 GB DDR5-4800 SO-DIMM** (Kingston FURY Impact KF548S38-32, Dual-Channel, theoretisch 76,8 GB/s; `free` zeigt 60 GB nutzbar). Weder LPDDR5X-8000 (App) noch DDR5-5600 (Dossier).

| Modell (Quant) | t/s 890M | Index | RAM | Argon: WSP-Angriffspunkt | Unsere Einordnung |
|---|---|---|---|---|---|
| Qwen 3.8-Flash-Next 125B-A6B (IQ4_XS+SSD) | 20 | 94 | 46 GB | 4B-MTP-Head, N-Gram-Embedding-Tabellen | Existenz + volle Gewichte prüfen; 125B in IQ4_XS ≈ 66 GB → nur mit SSD-Streaming, Tempo vermutlich zu optimistisch |
| Tiel-Coder-35B-A3B-MTP (Q5_K_XL) | 32 | 89 | 27,5 GB | offene imatrix + MTP-Drafter | keine vollen Gewichte gefunden → WSP nicht direkt möglich; imatrix ist eine Quantisierungshilfe, kein Eingriffsort |
| Ornith-1.5-35B-A3B (Q6_K) | 23 | 88 | 29 GB | Router-Gates (256 Experten), Denklängen-Steuerung | **Hauptkandidat** (BF16, MIT-Lizenz, Werkzeuge passen). Router als zusätzlicher Eingriffsort = prüfenswerte Hypothese |
| Qwen 3.8 27B Dense „Dirk“ (Q6_K) | 4,8 | 88 | 22 GB | Subspace-Edits nach MIT-Methode | WSP passt direkt (dicht), aber 4,8 t/s zu langsam für den Alltag |
| K2-Horizon-MoVA-36B-A4B (Q5_K_M) | 16,5 | 87 | 26 GB | Checkpoint-Diffing (offene Zwischenstände) | Anpassungsbaustein ~1 Tag; Checkpoint-Diffing ist eine eigene Technik (Richtungen aus dem Trainingsverlauf) – interessant, ungeprüft |
| Muse Glimmer 30B (Dense/Block-Drafter) | ~12 | ~87 | ? | (Details in der App nicht lesbar) | ungeprüft |
| Qwen 3.6-35B-A3B „Nail“ (Q8_0) | 21 | 86 | 36 GB | Experten-Transplantation aus Ornith | Transplantation ist kein WSP; Herkunft des Feintunes prüfen |
| Qwen3-Coder-Next 80B-A3B (UD-Q4_K_XL) | 18 | 85 | 45,5 GB | Experten-Pruning 512 → ~350 | Pruning ist kein WSP; 45,5 GB knapp bei 60 GB nutzbar + Kontext |
| Gemma 4 26B-A4B (Q8_0) | 17,5 | 83 | 28 GB | orthogonale Gewichtsprojektion (Global-KV-Schichten) | nächster Verwandter von WSP (Rang-1-Projektion); Lizenz prüfen |
| K2-Horizon-7B Overtrained (BF16) | 21,5 | 81 | 14 GB | volle BF16-Schichtchirurgie, Checkpoint-Analyse | unter der geforderten Liga, aber **idealer Zwischenschritt 0.8B → 35B** (dicht, BF16, passt auf den Laptop) |

Lehren für uns: (1) Argons „WSP-Score“ bewertet Eingriffsideen, nicht unsere Voraussetzungen. Unsere Kriterien: volle
BF16-Gewichte, Lizenz, Architektur von unseren Werkzeugen unterstützt, Q5/Q6 im RAM mit Alltagstempo, Deutsch.
(2) Zwei Ideen merken: Router-Gates als Eingriffsort bei MoE; dichter 7B-BF16 als Zwischenschritt zur Skalierungsprüfung.

**Nachtrag 05.11. abends – Argons „Referenz-Dossier“ (PDF, `recherche/argon/`), von uns nachgeprüft:**
- ✅ **Router bleibt in der GGUF unquantisiert:** im K2-GGUF auf dem MiniPC sind alle 45 `ffn_gate_inp.weight` F32
  (2560 × 100). Damit sind Router-Eingriffe direkt in einer fertigen GGUF möglich, ohne BF16-Download und ohne Neu-Quantisierung.
- ✅ **„Methode B“ (BF16 schichtweise laden, editieren, nach GGUF)** = genau unser Weg (04s/05m mit mmap je Schicht). Bestätigt.
- ✅ Korrekturen übernommen: Tiel-Coder ohne BF16 → kein volles WSP; 125B in IQ4_XS = 66,4 GB; die Technik-Klassen getrennt
  (WSP / Steering / Pruning / imatrix). Deckt sich mit unserer Kritik.
- ❌ **Laptop ist eine RTX 4060 (8 GB), keine 4070.** VRAM gleich, für uns ohne Folgen.
- ❌ **Ornith/Qwen3.6-35B: hidden_size 2048 (nicht 3584), 40 Schichten, 256 Experten, 8 aktiv** (unsere config.json).
  Router je Schicht also 2048 × 256 = 2 MB, nicht 3,67 MB.
- ✅ **RAM geklärt (dmidecode, 05.11. 17:2x):** 2 × 32 GB DDR5-4800 SO-DIMM, Dual-Channel = 76,8 GB/s theoretisch. App (LPDDR5X-8000) und Dossier (DDR5-5600) lagen beide falsch. Aufrüsten auf DDR5-5600 brächte höchstens ~+17 % Bandbreite →
  grob +15 % Tok/s, falls das Board 5600 fährt.
- ⚠️ Benchmarks „quellengetreu“, aber ohne Quellenangaben (z. B. Ornith GPQA-D 89,2 %). Ungeprüft – unsere eigenen Messungen
  nach Prüfschema entscheiden.
- ⚠️ Fremde imatrix (Tiel-Coder) zum Neu-Quantisieren von Ornith: nicht übernehmen (imatrix ist modellspezifisch).
- ⚠️ Checkpoint-Diffing (K2): ΔW enthält alles, was im Zeitraum gelernt wurde, nicht „exakt“ eine Fähigkeit. Als Idee für später:
  ΔW auf unsere aktivierungsbasierten Richtungen projizieren.
- **Neue Hypothese für Phase 2:** Router-Projektion `W_gate' = W_gate − α·(W_gate·u)·uᵀ` – die Expertenwahl wird unempfindlich
  gegen die Schleifenrichtung u. Als zusätzliche Kandidatenklasse in den Prüfstand aufnehmen; geht auch bei GGUF-only-Modellen.

**Nachtrag 05.11. ~17:45 – Top 3 (Vorschlag Nutzer) und zwei Befunde (Hugging Face, eigener llama.cpp):**
- Nutzer-Top-3 aus der Liste: Ornith-1.5-35B-A3B (Q6_K), Qwen3.6-35B-A3B „Nail“ (Q8_0), K2-Horizon-MoVA-36B-A4B (Q5_K_M).
  Argon räumt ein: Qwen 3.8-Flash-Next 125B mit IQ4_XS + SSD war unrealistisch.
- ✅ **„Nail“ = Community-Feintune von peculiar-ragdoll** (Apache-2.0, Basis Qwen/Qwen3.6-35B-A3B; derselbe Autor wie Tiel-Coder).
  Veröffentlicht nur als GGUF (Quants bis Q6_K_XL im GGUF-Repo) und MLX (4-bit) → **keine BF16-Gewichte, kein volles WSP**
  (nur Router-Eingriffe im GGUF, Methode A). Für WSP auf Platz 2 daher die **Qwen3.6-Basis** (BF16 liegt auf dem Laptop);
  Nail als Alltags-Vergleichsmaßstab mitmessen.
- ✅ **MTP ist nicht verloren:** Ornith-1.5 enthält in den Originalgewichten einen vollständigen MTP-Kopf (785 `mtp.*`-Tensoren,
  eigene 256 Experten). Unser llama.cpp (b11636) übernimmt ihn für die Qwen3.5/3.6-Familie und kann ihn mit
  `convert_hf_to_gguf.py --mtp` als eigenen Entwurfs-GGUF exportieren → spekulatives Dekodieren. Der Hauptkopf prüft jeden
  Entwurf, die Wirkung des WSP-Edits bleibt also erhalten; nur die Trefferquote des (unbearbeiteten) MTP-Kopfs kann sinken.
  → „MoE + MTP“ deckt unser Hauptkandidat selbst ab. Tempo-Gewinn auf der 890M in Phase 2 messen.
- SSD-Streaming: zu Recht gestrichen (laut Dossier-Rechnung 2,5–5 Tok/s auf dieser Hardware).
- **Entscheidung Nutzer 05.11. ~17:50:** WSP-Reihenfolge Phase 2 = **Ornith-1.5** (Hauptkandidat, mit eigenem MTP-Kopf) → **Qwen3.6-35B-A3B-Basis** (BF16) → **K2-Horizon-MoVA**. Nail (und Tiel-Coder) werden nur als Alltags-Vergleich mitgemessen, nicht getunt.

## Bestätigt / verworfen (Protokoll)

- 05.11.: Unsere Messung trifft die MIT-Basis exakt (7,5 % = 7,5 % auf denselben 40 Aufgaben).
- 05.11.: Der MIT-Edit mit llama.cpp-Standard-Sampling bleibt deutlich hinter dem MIT zurück: 25 % vs. 47,5 %,
  z = −4,6. Die Lücke ist nicht zufällig.
- 05.11.: Erster A/B-Zwischenstand mit vLLM-Sampling: 9 von 18 richtig, gegenüber 5 mit Standard-Sampling (MIT
  erwartet 8,0).
- **05.11. 13:02 – BESTÄTIGT: Das Sampling war die Ursache.** MIT-Edit mit vLLM-Stil (Laptop, CUDA, Q8_0):

  | | richtig | Abbrüche am Limit | gerettet / verloren |
  |---|---|---|---|
  | MIT auf denselben 40 Aufgaben | 47,5 % | ~33 % | – |
  | **wir, vLLM-Stil** | **55,0 %** (z = +1,5, im Rauschen) | **30 %** | 13 / 1 gegenüber dem Lauf mit Standard-Sampling |
  | wir, llama.cpp-Standard | 25 % | 67,5 % | – |

  → **Teil A (MIT-Nachbau) reproduziert.** Ab jetzt alle Messungen mit `--vllm-stil`.
- 05.11. 13:49 – Basis mit vLLM-Stil: **10,0 %** (MIT auf denselben Aufgaben 7,5 %, z = +0,9), 92,5 % Abbrüche.
  Gleiches Sampling, Basis → MIT-Edit: **10 % → 55 %**, 20 Aufgaben gerettet, **0 verloren**.

  Für den Alltag in llama.cpp:
  - `repeat_last_n` groß (die ganze Antwort)
  - Sampler-Reihenfolge `penalties, temperature, top_k, top_p, min_p`
- 05.11. 15:48 – **Teil B (eigene Reparatur, Rezept wie MIT: L15/L19, top-k 64, α 6, Richtung aus 48 Übungs-Transkripten)**,
  vLLM-Stil, dieselben 40 MATH-500-Aufgaben: Basis **10 % → eigen 37,5 %** (MIT-Edit 55 %).
  Abbrüche 92,5 % → 60 % (MIT-Edit 30 %), dup8 0,86 → 0,40 (MIT-Edit 0,18). 11 Aufgaben gerettet, **0 verloren**.
  Jede von eigen gelöste Aufgabe löst auch der MIT-Edit (eigen ⊂ MIT; MIT zusätzlich 7).
  → **Bestätigt:** Die eigene Richtung trifft denselben Mechanismus (cos 0,76/0,77 zur MIT-Richtung), aber schwächer dosiert.
  → **Annahme für den nächsten Schritt:** Die Lücke ist eine Dosis- und Ortsfrage (α, Schicht 14, mehr Neuronen),
    keine falsche Richtung. Prüfung: Prüfstand (kette_v3b) + 2 beste Kandidaten echt messen. Zufallskontrolle läuft.
- 05.11. 16:38 – **Zufallskontrolle gleicher Stärke** (zufall-gleich-vL, α angeglichen an die relative Gewichtsänderung von eigen):
  **7,5 %** richtig, 92,5 % Abbrüche, dup8 0,81 – Basis-Niveau (10 % / 92,5 % / 0,86).
  → **Bestätigt:** Die Wirkung von eigen (37,5 %) kommt von der gefundenen Richtung, nicht von der Eingriffsstärke an sich.
- 05.11. 16:50 – **Prüfstand (09) auf 12 zurückgehaltenen Übungs-Transkripten:** Rangfolge ordnet fast nur nach Eingriffsstärke
  (α 10–12 vorn, über α 12 KL-Grenze). Favoriten: L15,19 k64 α10 (opt1) und L15,19 k128 α8.
  **Widerspruch zur echten Messung:** Der MIT-Edit (L15,19 α6) steht im Prüfstand auf dem LETZTEN gültigen Platz (Δlogp_A −0,053),
  knapp hinter eigen α6 (−0,073) – echt aber MIT 55 % vs. eigen 37,5 %.
  → **Verworfen (vorerst):** „Prüfstand-Δlogp sagt die echte Leistung über verschiedene Richtungen voraus.“ Er misst vor allem
    die Dosis. Ob er INNERHALB einer Richtung taugt (mehr Dosis → besser), zeigt opt1 (α10) gegen eigen (α6).
  → **Offene Frage:** Kommt der MIT-Vorsprung von der Richtung u (cos 0,76/0,77) oder von der Neuronenauswahl (41/64 bzw. 30/64
    gemeinsam)? Kreuzmodell gebaut: eigene u + MIT-Spalten, α6 (`modelle/Qwen3.5-0.8B-kreuz-vL`, GGUF md5 a2e9052a…).
- 05.11. 18:32 – **Favorit 1 (opt1: L15/L19, k64, α 10 statt 6)**: **32,5 %** richtig (eigen α6: 37,5 %, MIT-Edit 55 %),
  Abbrüche 62,5 %. Gegenüber eigen +1/−3, gegenüber Basis 10 gerettet, **1 verloren** (erstmals).
  → **Verworfen:** „Die Lücke zum MIT ist eine Dosisfrage.“ Mehr Dosis hilft nicht, sie kostet eher Nebenwirkungen.
  → **Verworfen:** „Der Prüfstand taugt wenigstens innerhalb einer Richtung.“ Er setzte α10 vor α6, echt ist es umgekehrt.
    Δlogp auf erzwungenen Schleifen-Tokens ist als Auswahlmaß für Edits ungeeignet. Neues Prüfmaß nötig (z. B. kurze freie
    Generierungen ab Schleifen-Eintritt statt Teacher-Forcing).
  → Offen und als Nächstes: Kreuzmodell (eigene Richtung + MIT-Neuronen) läuft seit 18:32, Ergebnis ~20:10.
- 05.11. 19:10 – **Prüfstand v2 (15_pruefstand_frei.py, freie Fortsetzung 1.024 Tok ab Schleifen-Eintritt, 47 Transkripte):**
  „raus“ basis 77 % / zufall 77 % / opt1 100 % / eigen 100 % / MIT 98 % / kreuz 96 %. Spearman +0,60, aber nur durch die
  Trennung „bearbeitet vs. unbearbeitet“; innerhalb der Edits UMGEKEHRT (v2: opt1 > eigen > MIT, echt: MIT > eigen > opt1).
  → **Eichung nicht bestanden.** Blind-Vorhersage kreuz (19:10, vor dem echten Ergebnis): ~36 % (lineare Anpassung; wenig belastbar).
  → **Wichtiger Befund aus den echten Läufen (Ende je Aufgabe, 40 MATH-500):**
    | | richtig | EOS | Limit 32k | Loop-Abbruch (Median Tok) |
    |---|---|---|---|---|
    | basis | 4 | 3 | 6 | 31 (~8.400) |
    | eigen | 15 | 16 | 16 | 8 (~21.000) |
    | opt1 | 13 | 15 | 17 | 8 (~24.000) |
    | MIT | 22 | 28 | 11 | 1 (~30.000) |
    Alle Edits brechen die ERSTE Schleife gleich gut auf (v2 ≈ 100 %). Der MIT-Vorsprung liegt im **langen Atem**:
    eigen/opt1 fallen nach ~20.000 Tokens erneut in Schleifen (8 vs. 1) oder denken bis zum Limit ohne Abschluss (16 vs. 11).
    Die EOS-Quote ordnet die echten Modelle exakt richtig (MIT 28 > eigen 16 > opt1 15 > basis 3 = zufall 3).
  → **Neue Annahme:** Ein brauchbarer Schnelltest muss den langen Horizont abbilden (Rückfall in Schleifen, Abschluss mit
    </think>), nicht den ersten Ausstieg. Idee v3 (Nutzer): Trichter v1 (Nebenwirkungs-KL als Filter; KL sagte den einen
    Verlust von opt1 richtig voraus) → v2 mit langem Horizont → echte Messung.
- 05.11. 19:35 – **Auswahl-Vergleich gegen die MIT-Musterlösung** (16_auswahl_vergleich.py, nur CPU): Top-64 je Regel vs. MIT-Spalten
  (Zufall ≈ 1 Treffer). L15: bisherige Regel da·w **41/64**, gleiche Regel mit MIT-Richtung 47/64; L19: 30/64 bzw. 37/64.
  Andere Regeln (|w|, |da|, |da·w|, nur da, nur w) alle schlechter. 91–92 % der MIT-Neuronen haben da·w > 0, wie unsere Regel.
  MIT-Neuronen in unserer Rangfolge: Median Rang 36 (L15) bzw. 89 (L19), 78 % bzw. 59 % in unseren Top-128.
  → **Bestätigt:** Unsere Auswahlregel entspricht im Prinzip der des MIT. Die Abweichung kommt teils aus der Richtung u
    (mit MIT-u +6/+7 Treffer), teils aus Daten/Feinsuche des MIT. Schicht 19 weicht am stärksten ab.
  → **Werkzeug:** Treffer gegen MIT-Spalten = billiger Vorab-Test für neue Richtungs-Varianten (Sekunden), vor jeder echten Messung.
- 05.11. 20:07 – **Kreuzmodell (eigene Richtung u + MIT-Spalten, α6): 40,0 %** (eigen 37,5 %, MIT 55 %). Gegenüber eigen +4/−3,
  gegenüber Basis 12 gerettet, 0 verloren. Mein Zwischentipp (45–50 % nach 33 Aufgaben) war zu optimistisch: Die letzten 7
  Aufgaben löste kreuz nur 2-mal (eigen 5, MIT 6). Bestätigungsregel (≥ 45 %) greift nicht.
  **Aufschlussreich ist, wie die Läufe enden** (40 Aufgaben):
    | | richtig | fertig gedacht (EOS) | Limit 32k | Schleife |
    |---|---|---|---|---|
    | eigen (eigenes u, eigene Spalten) | 15 | 16 | 16 | 8 |
    | kreuz (eigenes u, MIT-Spalten) | 16 | 15 | **23** | **2** |
    | MIT (MIT-u, MIT-Spalten) | 22 | **28** | 11 | 1 |
  → **Neue Hypothese (Zerlegung):** Die MIT-**Spalten** verhindern späte Rückfälle in Schleifen (8 → 2, fast MIT-Niveau).
    Das **Zu-Ende-Denken** (EOS 15 vs. 28) kommt dagegen nicht von den Spalten, sondern vermutlich von der MIT-**Richtung u**.
  → **Prüfung:** Gegen-Kreuz „kreuz2“ = MIT-Richtung u + eigene Spalten, α6 (gebaut 20:1x). Vorhersage der Hypothese:
    mehr EOS als eigen (Richtung → Abschluss), aber mehr späte Schleifen als MIT (eigene Spalten).
- 05.11. 20:35 – **Fund im MIT-Archiv** (`archiv/minipc/lm_understand-logs/exp8_math/runs/p50c/work_notes/`, v. a.
  experiment_history.md 51 KB, final_report.md): Das MIT-u stammt aus nur **VIER „matched“ produktiv/repetitiv-Kontexten**
  (gleicher Ausgangstext, einmal produktive, einmal schleifende Fortsetzung; Vergleich an denselben Verzweigungs-Tokens),
  gemessen an den Residual-Ausgängen der Schichten 15/19 („residual outputs 16/20“). Die 64 „writer“-Neuronen je Schicht
  wurden in denselben Kontexten gewählt. Das Rezept stand schon in Pass 2–4 fest; der Rest der 50 Pässe war Prüfung
  (Dosis, Schichten, normgleiche Zufallskontrolle, 1.152 zurückgehaltene Übungsaufgaben: +49,8 pp, 579 Rettungen, 5 Verluste).
  Eigene Stabilität der MIT-Auswahl in neuen Kontexten: L15 55/64, **L19 nur 36/64**.
  → **Unterschied zu uns:** Wir mitteln über 48 Transkripte und alle Positionen (ungepaart) – das MIT vergleicht gepaart an der
    Verzweigungsstelle. Wahrscheinliche Ursache für cos 0,76 und den fehlenden „langen Atem“. Nächster Schritt: Rezept nachbauen
    (Verzweigungen per llama-server erzeugen, Infrastruktur aus Prüfstand v2), prüfen per cos zu MIT-u + Treffer gegen MIT-Spalten.
- 05.11. 21:33 – **Gegen-Kreuz kreuz2 (MIT-Richtung u + eigene Spalten, α6): 47,5 %** (19/40), 15 gerettet, 0 verloren,
  gegenüber eigen +5/−1. **Vier-Felder-Bild komplett** (richtig | EOS | Limit 32k | Schleife):
    | Richtung \ Spalten | eigene | MIT |
    |---|---|---|
    | eigene u | 37,5 % · 16 · 16 · 8 | 40,0 % · 15 · 23 · 2 |
    | MIT-u    | 47,5 % · 23 · 11 · 6 | 55,0 % · 28 · 11 · 1 |
  → **Bestätigt (Zerlegung):** Die **Richtung** steuert das Zu-Ende-Denken (Limit 16/23 → 11/11 mit MIT-u), die **Spalten**
    steuern späte Rückfälle in Schleifen (8/6 → 2/1 mit MIT-Spalten). Richtung ist der größere Hebel (+10 bzw. +15 pp),
    Spalten +2,5 bzw. +7,5 pp; positive Wechselwirkung: Die Spalten helfen mehr, wenn die Richtung stimmt.
  → **Folgerung:** Zuerst die Richtung verbessern (MIT-Rezept: gepaarte Messerschneiden). Mit MIT-u findet unsere
    Auswahlregel bereits mehr MIT-Spalten (41→47 bzw. 30→37) – eine bessere eigene Richtung sollte beide Hebel bedienen.
- 05.11. 22:15 – **Messerschneiden-Finder (17_messerschneiden.py)**, Basis-Modell, Versatz −16/0 zum Schleifenbeginn, je 6 Äste
  à 256 Tok (94 Punkte, 564 Äste, 11,5 min): nur 36 Äste klar „Schleife“, 292 klar „produktiv“, Rest unklar. Messerschneiden:
  5 (≥2 je Klasse) bzw. 11 (≥1 je Klasse). → Beim Basismodell kippt es selten an EINER Stelle; Schleifen entstehen schleichend.
  Richtung aus 11 Messerschneiden (alle Ast-Tokens): cos MIT 0,770/0,769 (bisher 0,757/0,773), Treffer MIT-Spalten 41/26
  (bisher 41/30), aber Stabilität nur 0,39/0,33 (bisher 0,98) → zu wenig Material, verrauscht. Nicht echt gemessen (Regel).
  **Mischung** (bisher + Messer, normiert addiert): cos MIT **0,798/0,802** → beide sind verrauschte Schätzungen derselben
  Richtung; mehr Material sollte näher an MIT führen.
- 05.11. 22:45 – **Die „45 %“ auseinandergenommen** (19_rest45.py → ergebnisse/rest45_auswertung.txt; MIT-p50c je Aufgabe 4 Samples):
  - **Auch die 55 % haben eine Grauzone:** von den 22 vom MIT-Edit gelösten Aufgaben löst das MIT selbst nur 11 in 4/4,
    8 nur in 1–2 von 4. Die 55 % enthalten also Glück (passt zu ±8 pp Rauschen).
  - **Topf 1 „fertig, aber falsch“ (6):** MIT 0/4 bei 4, 1/4 bei 2. prealgebra/1840: **5 Varianten geben dieselbe falsche
    Antwort (114 statt 78)** → feste Fehlvorstellung, kein Zufallsfehler; geometry/434 ebenso (2× 124). Zwei Fälle ohne
    verwertbare Antwort („Evelyn“, „π“) → Ausdruck/Format, MIT löst sie manchmal (Grauzone).
  - **Topf 2 „kein Entschluss bis 32k“ (11):** 5 sind lösbar (MIT 1–2/4; kreuz/kreuz2 lösen 4 davon mit 21–24k Tokens),
    6 nie (0/4, keine Variante). **Bei 2 Aufgaben steht die richtige Lösung schon nach ~1–2k Tokens im Denken**
    (precalculus/1303 „=√51“ 14×, precalculus/990 „=6−5i“ 30×) – und das Modell denkt trotzdem 30.000 Tokens weiter.
    → Dort ist das Weiterdenken NICHT nötig: reines Entschluss-Problem, ein viel kürzerer Weg existiert.
  - **Topf 3 „Schleife“ (1):** MIT 2/4 → manchmal findet es hinaus.
  → **Folgerungen:** (a) Entschluss-Problem belegt (Lösung da, kein Abschluss) → WSP-Ziel „früher abschließen, wenn die
    Lösung steht“; (b) 6+4 Aufgaben = echte Wissens-/Fehlvorstellungs-Grenze → Werkzeuge/ehrlicher Abbruch statt 32k Tokens;
    (c) Messidee: „Lösung im Denken vorhanden, aber nicht abgeschlossen“ als eigene Kennzahl je Variante.
- 05.11. 22:44 – **Großer Messerschneiden-Lauf** (Versatz −64/−32/+16/+32, je 8 Äste à 256): 20 neue Messerschneiden, gesamt
  **31** (82 Zeilen). Kippen in die Schleife nimmt mit späterem Punkt zu (Schleifen-Äste 11 → 13 → 28 → 40) → schleichender Aufbau.
  Richtung messer3: cos MIT **0,772/0,773**, Stabilität 0,44/0,35, Treffer 40/27; Mischung 0,791/0,797, Treffer 44/30.
  Regel: **KEIN KANDIDAT** → keine echte Messung, Warteschlange freigegeben (Quantisierung läuft seit 22:44).
  **Beide eigenen Richtungen zusammen erklären die MIT-Richtung nur zu cos 0,79/0,80 (Rest ~0,6).**
  → **Verworfen:** „Der Abstand zur MIT-Richtung ist nur Rauschen; mehr Material schließt ihn.“ (3× Material: 0,770 → 0,772)
  → **Neue Hypothese:** Der fehlende Anteil ist der **Entschluss-Anteil** („fertig, ich antworte“) – passt zur Zerlegung
    (MIT-Richtung → Zu-Ende-Denken) und zu Topf 2a (Lösung nach 1–2k da, kein Abschluss). Unsere Kontraste
    (Schleife vs. produktiv) enthalten ihn nicht. Prüfung morgen: Richtung aus „kurz vor </think>“ vs. „weiterdenken
    trotz vorhandener Lösung“ → erklärt sie den Rest der MIT-Richtung? (Sekunden-Check nach ~5 min Rechnung)

## Offene Forschungsfragen (Nutzer, 05.11. ~23:10)
1. Lässt sich der „nicht erreichbare“ Anteil (hier ~30 %) für jedes Modell vorhersagen – oder nur messen? Wie groß ist er je Modell?
   → Messvorschlag „Erreichbarkeits-Test“: fester Aufgabensatz, festes Sampling, k Versuche je Aufgabe (z. B. 16–64);
     unerreichbar = 0 von k, über Basis UND alle Edit-Varianten. Teil der späteren Prüfstraße.
2. Was heißt „bei jedem Modell“? → gleicher Aufgabensatz, gleiches Protokoll (Sampling, Denkbudget, k); Anteil ist immer
   relativ zum Aufgabensatz und sinkt mit Modellgröße.
3. Sind die ~30 % „fehlender Informationsfluss aus Weltwissen“? → vermutlich drei Sorten: (a) nie gelernt („kein Zucken
   möglich“), (b) falsch gelernt („falsches Zucken“, z. B. prealgebra/1840: 5 Varianten antworten 114 statt 78),
   (c) Kapazität: Wissen vorhanden, aber lange Rechenketten zu unzuverlässig. Bei Mathe vermutlich v. a. (b)+(c).
4. Ist das „Weltwissen“ Wahrheit oder teils menschlicher Irrtum? → Trainingsdaten enthalten Irrtümer, Widersprüche,
   Veraltetes; Modelle lernen Häufigkeiten. Mathe ist nachprüfbar (Werkzeuge/Verifikation), Weltwissen schwerer.
   Prüfbar am Einzelfall: woher kommt die 114 bei prealgebra/1840 (Denktext lesen)?
**Fuchsbau-Gleichung (Arbeitsstand):** 55 % MIT-Weg (mit Grauzone) + ~15 % Entschluss-Reserve (Topf 2a/2b/3, WSP-Gebiet)
+ ~30 % nicht per Schleifen-/Entschluss-Edit erreichbar = davon „kein Zucken“ (→ Werkzeuge/größeres Modell) und
„falsches Zucken“ (→ grundsätzlich einzeln editierbar, Wissens-Edit à la ROME/MEMIT – eigene Kammer im Fuchsbau).
- 05.11. 23:15 – **„Falsches Zucken“ am Einzelfall** (prealgebra/1840, 5 Varianten antworten 114 statt 78): Das Modell liest
  „54 cookies at three for $1“ als „1 $ pro Keks“ (54 statt 18 $), rechnet danach fehlerfrei. Es **zweifelt selbst**
  („Could 'at three' mean something else?“, mehrfach neu gelesen) – die richtige Lesart ist vorhanden, verliert aber.
  → Kein fehlendes Weltwissen, sondern eine **Lesart-Gabelung** (dritte Messerschneiden-Sorte neben Schleife und Entschluss).
  → Werkzeuge helfen hier nicht (der Taschenrechner rechnet die falsche Formel richtig); ein zweiter Blick/zweites Modell schon.
  → Für Wissens-Edits: eher eine Richtung („Bündelpreis lesen“) per Kontrast richtige vs. falsche Lesart – gleiche Methode wie
    unsere Schleifen-Richtung – als ein Fakten-Edit à la ROME.
- 05.11. ~23:40 – **Gegenlesen Argon, Teil 1 (Statistik-Simulator)** + exakte gepaarte Tests mit unseren Einzeldaten (McNemar):
  eigen vs. Basis p = 0,001 · MIT vs. eigen **p = 0,016** · Dosis 10 vs. eigen 0,63 · Kreuz vs. eigen 1,0 ·
  Gegen-Kreuz vs. eigen 0,22 · MIT vs. Kreuz **0,07** · MIT vs. Gegen-Kreuz **0,55** · Gegen-Kreuz vs. Kreuz 0,45.
  → **Abgesichert:** eigene Reparatur wirkt; MIT ist besser als unsere Reparatur.
  → **Nur Tendenz (nicht signifikant bei N = 40):** die Zerlegung Richtung/Neuronen. Sie passt zusammen (Gegen-Kreuz von MIT
    nicht unterscheidbar, Kreuz knapp schlechter als MIT), braucht aber mehr Aufgaben/Versuche (k ≥ 4 oder N = 80+).
  → **Argons stärkster Punkt:** Mit α = 6 ENTFERNT der Edit die u-Komponente der gewählten Spalten nicht, er **kehrt sie um
    und verstärkt sie 5-fach** (Faktor 1 − α = −5; α = 1 wäre reines Entfernen, α = 2 Spiegelung). α = 10 → −9×, passt zur
    Überdosierung. Eigene Formulierungen („Richtung abziehen“) entsprechend präzisieren.
  → Argons „α_korr = 6/0,77 ≈ 7,8“ (effektive Dosis längs MIT-u) ist eine Hypothese; α 10 war schlechter, α 8 ungetestet.
- 05.11. ~23:50 – **Gegenlesen Argon, Teil 2 (PDF „Kritische Methodenprüfung“, recherche/argon/) – geprüft:**
  - **Quellen:** alle 12 arXiv-IDs per arXiv-API bestätigt (Titel stimmen). Kleinere Fehler: 2504.05419 ist von Anqi Zhang
    (nicht „Fu/Dynasor-CoT“ – zwei Arbeiten vermischt); RPDI-Titel leicht abweichend. MIT-Blog (Takehi et al.) nicht geprüft.
  - **Early Exit ist ein etabliertes Feld** (DEER 2504.15895, Zhang 2504.05419, NEAT 2602.02010 mit „Exit-Neuronen“ für
    </think>, „Thinking Past the Answer“ 2606.02835 mit erstem korrektem Präfix τy) → unser Topf-2a-Befund ist dort beschrieben.
  - **Fallstrick Dosis-Konfundierung:** empirisch klein – relative Gewichtsänderung eigen → Kreuz −3 %/−8 %,
    MIT → Gegen-Kreuz −2 %/±0 % (Argon schätzte −23 %).
  - **Fehler im Brief (meiner):** „doppelte Dosis“ war α 10, nicht 12 (Faktor −9, nicht −11).
  - **Messfalle Gabelung (wichtig, übernommen):** Vor dem Split sind die Zustände identisch; nach dem Split misst man v. a.
    die unterschiedlichen Tokens. Unser Messerschneiden-Finder hat Ast-Tokens NACH dem Split markiert → misst eher
    „bin in der Schleife“ als „entscheide gerade“. Für die Entschluss-Gabelung: p_exit(t) per Kurz-Rollouts an Satzenden
    nach τy schätzen, früh (p_exit ≤ 0,1) vs. spät (≥ 0,8) innerhalb derselben Aufgabe am gleichen Satzzeichen vergleichen.
- 05.11. ~23:51 – **Stufe A: Logit-Lens des unerklärten MIT-Rests r⊥** (21_logit_lens.py, Unembedding mit γ der finalen Norm):
  Niedriges Ende von r⊥ = **Abschluss-/Ergebnis-Wörter**: L15 „thereby, <|endoftext|>, end, accordingly, 从而 (somit),
  便可 (dann kann), 就行了 (das war's)“; L19 „thereby, <|endoftext|>, results, accordingly, result, answers, yields,
  即可 (genügt), obtains“. `</think>` liegt im untersten 5 % (L15) bzw. **1,3 %** (L19); „Therefore“ ebenfalls unten,
  „Wait“/„So“/„Hmm“ eher oben. Unsere eigene u: unten „first, without, initially, set, constraints“ (Start-/Aufbau-Wörter).
  Da der Edit die u-Komponente mit −5 umkehrt, HEBT er beim Feuern der Schleifen-Neuronen genau diese Abschluss-Tokens an.
  → **Entschluss-Hypothese deutlich gestützt** (Logit-Lens an mittleren Schichten ist grob – Hinweis, kein Beweis).
- 05.11. ~23:59 – **Entschluss-Test (ungepaart, 20_entschluss.py)**: unsere Reparatur auf 60 leichten Übungsaufgaben (MATH
  Stufe 1–2, 12k): nur 19 EOS, davon **18 richtig (95 %)**; 39 bis zum Limit. → Auf leichten Aufgaben ist das Hauptproblem
  unserer Reparatur eindeutig der fehlende Abschluss, nicht das Können.
  Entschluss-Richtung („16 Tokens bis </think>“ vs. „mitten im Denken“, 23 Transkripte): stabil (0,86/0,85), aber
  cos zur MIT-Richtung nur 0,06/0,11; cos zum MIT-Rest r⊥ **0,23/0,19** (Zufall ≈ 0,03) → nicht zufällig, aber
  erklärter Anteil der MIT-Richtung steigt nur 0,79 → **0,81**.
  → **Teilweise verworfen:** „Der fehlende Rest ist der Zustand kurz vor dem Abschluss.“ Der Rest hängt mit dem Abschluss
    zusammen (Logit-Lens: er hebt Abschluss-Wörter an), ist aber nicht der Zustand „ich schließe gerade ab“. Eher der
    DRUCK zum Abschluss während des Denkens. Ungepaarter Vergleich ist zudem durch Position/Inhalt verzerrt (Argon).
  → Nächster Schritt bleibt Argons Stufe B: gepaart innerhalb derselben Aufgabe an Satzenden nach τy, früh (p_exit ≤ 0,1)
    vs. spät (≥ 0,8) – misst den Abschluss-Druck statt des Abschluss-Zustands.
- 06.11. ~00:15 – **Angst-Marker (22_angstmarker.py, Idee Nutzer)**: τy = erste Stelle, an der die richtige Lösung im Denken
  steht; Zweifel-Wörter (Wait, Hmm, double-check, verify, Alternatively, re-read, Actually …) je 1.000 Wörter vor/nach τy.
  - **Lösung im Denken gefunden:** Basis 15/40, eigen 20/40, Kreuz 20, Gegen-Kreuz 21, **MIT 21/40** → unsere Reparatur
    FINDET die Lösung fast so oft wie der MIT-Edit. **Abgeschlossen danach: Basis 0/15, eigen 12/20, MIT 19/21.**
    → Der Unterschied liegt fast vollständig im Entschluss nach dem Finden.
  - **Zweifel steigt, sobald die Lösung steht** (bei allen Modellen ~×1,5–3,5), und trennt scharf: nicht abgeschlossen
    eigen 52 / Gegen-Kreuz 66 / Basis 34 Zweifel je 1.000 Wörter nach τy vs. abgeschlossen 18–23. MIT bleibt auch in den
    2 nicht abgeschlossenen Fällen bei 23.
  - Selbst abgeschlossene Läufe denken nach τy noch ~2.500–6.700 Wörter weiter (auch MIT ~5.000) → Overthinking im Sinne
    von „Thinking Past the Answer“ (2606.02835); viel Spielraum für früheren Abschluss.
  → Zweifel-Rate nach τy = billiger Frühindikator für „bleibt stecken“; Kandidat für Stufe B (früh: hoher Zweifel,
    spät: Zweifel klingt ab) und für einen Harness-Abbruch („Lösung steht + Zweifel steigt → Klingel“).
- 06.11. ~00:25 – **Klingel-Regel trocken getestet (23_klingel_regel.py, Idee Nutzer)**: „dieselbe Antwort k-mal im Denken
  (\boxed{…} / „answer is …“) → abgeben“, ohne Kenntnis der Lösung.
  Übungsaufgaben (Regel dort festgelegt): eigen, 60 leichte: **30 % → 45 %** (k=2: 11 Rettungen/2 Verluste; k=3: 10/1),
  spart ~4.200 Tokens je ausgelöster Aufgabe; Basis-Diagnose (48): 2 % → 6–8 %.
  **Einmaliger Test mit k = 3 auf den 40 MATH-500-Aufgaben:** Basis 10 → 12,5 %, eigen 37,5 → 37,5 % (+1/−1),
  Gegen-Kreuz 47,5 → 50 %, MIT 55 → 52,5 % (−1); löst selten aus (2–10×), dort 60–100 % richtig, spart 5–15k Tokens.
  → Auf leichten Aufgaben großer Gewinn, auf gemischt schweren ~neutral bei viel Zeitersparnis. Leichte Übungsaufgaben
    ÜBERSCHÄTZEN den Nutzen (wiederholte Kandidaten sind bei schweren Aufgaben öfter falsch). Für den Alltag interessant
    als Zeitsparer; als Genauigkeitshebel nur mit besserem Signal (z. B. Kandidat + abklingender Zweifel).
- 06.11. ~00:35 – **Leicht/schwer ist modellrelativ (Einwand Nutzer, Daten):** menschliche MATH-Stufen sagen den Modellerfolg
  schlecht voraus – Stufe 1: eigen 1/4, MIT 2/4; Stufe 3: eigen 7/11, MIT 8/11 (beste Stufe). → Schwierigkeit künftig aus
  Sicht des Modells messen (Lösungsquote über k Versuche, Zweifel, Zeit bis zur Lösung, taucht die Lösung überhaupt auf).

## Geplante Experimente (Stand 06.11. ~00:35)
- **Stufe B (Argon):** gepaarte Entschluss-Gabelung, p_exit an Satzenden nach τy, früh vs. spät in derselben Aufgabe;
  Zweifel-Rate als zusätzliches Druck-Maß.
- **Schwierigkeits-Sonde (Idee Nutzer „steht die Lösung am Anfang schon fest?“):** innerer Zustand direkt nach dem Lesen
  der Frage (vor dem Denken), je Schicht; einfache lineare Sonde sagt „wird gelöst / nicht gelöst“ voraus (Übungsaufgaben,
  k Versuche je Aufgabe). Gütemaß AUC gegen Zufall. Gelingt es → inneres „kenne ich / kenne ich nicht“ messbar.
- **Zucken messen (vier Wege):** (1) Antwort-Stabilität über k Versuche (Blackbox, geht bei jedem Modell, auch den
  KI-Agenten des Nutzers); (2) Sicherheit des Antwort-Tokens (Log-Wahrscheinlichkeit, llama-server n_probs);
  (3) Feuer-Verlauf der 64 MIT-/eigenen Schleifen-Neuronen über den Denktext (Hooks, vorhandene Transkripte);
  (4) Sonde wie oben. Einordnung: kein Zucken = instabil + Lösung taucht nie auf; richtiges Zucken = stabil + richtig;
  falsches Zucken = stabil + falsch (braucht Wahrheit oder zweites Modell); schwaches Zucken = schwankend + viel Zweifel.
- **Angekündigte Klingel** (läuft), **Klingel-Regel mit zweitem Signal** (Kandidat wiederholt UND Zweifel klingt ab),
  **Aufmerksamkeit auf die Frage über die Zeit** (Idee Nutzer „wenig Aufmerksamkeit = kein Druck?“), **Ursachen-Landkarte**.
- **Falsches Zucken = zwei getrennte Aufgaben (Nutzer 06.11. ~00:40): ERKENNEN, dass es falsch ist + die WAHRHEIT.**
  Erkennen (ohne Wahrheit möglich): innerer Zweifel (schwach, z. B. 114-Fall „could 'at three' mean…“), **Umformulierungs-
  Test** (dieselbe Aufgabe anders formuliert – kippt die Antwort, ist die Lesart wacklig; neue Messidee), zweites Modell,
  bekannte Lösung (sicher). Wahrheit: von innen, wenn die richtige Alternative existiert (F₁ – andere Lesart/Sampling), sonst
  von außen (Werkzeug, Web, zweites Modell, Mensch). Korrektur: im Einzelfall per Harness-Hinweis, dauerhaft per Lesart-Edit.
  Schon „Erkennen ohne Wahrheit“ hilft gegen Halluzination: ehrlich „unsicher“ sagen statt überzeugt falsch.
- 06.11. ~00:43 – **Angekündigte Klingel (Mini-Test, Idee Nutzer):** 20 leichte Übungsaufgaben, unsere Reparatur, Frage ergänzt
  um „think for at most about 1,500 words, then … give your final answer“, Budget 6.144 Tokens. Abgeschlossen: **0/20**
  (ohne Hinweis auf denselben Aufgaben bis 6.144 Tokens: 1/20). **Aber 10 von 20 Denktexten notieren die Vorgabe selbst**
  („Constraints: … max ~1500 words …“) – und denken trotzdem weiter.
  → **Bestätigt:** Das Problem ist nicht fehlendes Wissen über das Ende, sondern fehlender Antrieb aufzuhören („hört die
    Klingel, schreibt sie auf, arbeitet weiter“). Weiche Ansage wirkt nicht; es braucht inneren Schubs (WSP) oder harte
    externe Klingel (Budget-Abbruch, Alltagsprofil läuft heute Nacht).
- 06.11. ~00:45 – **Korrektur Nutzer:** Der Ansage-Test war KEINE Klingel – es gab Ansage (vorher), Machen, und nur die harte
  Bremse bei 6.144 Tokens ohne Abgabe (= Topf „Kontext reicht nicht“). Drei Phasen trennen: Ansage / Klingel während des
  Denkens / Ende. Daten dazu (20 leichte Aufgaben, erste 6.144 Tokens): richtige Lösung im Denken ohne Ansage 13/20, mit
  Ansage 9/20, im Mittel nach ~370 Wörtern, **7–8 davon schon vor 1.500 Wörtern** – abgeschlossen 1 bzw. 0.
  → Echte (harte) Klingel bei 2.048 Denk-Tokens läuft als Mini-Test (03b_budget_eval, Qwen-Budget-Satz + erzwungene
    Antwort). Offen: **weiche Klingel** (Zeit-Hinweis im Denkstrom, ohne Abschluss zu erzwingen) – braucht kleines Skript.
- 06.11. ~00:47 – **Erziehung des Modells (Frage Nutzer „Indoktrination?“):** Laut Qwen3 Technical Report (2025; für 3.5 vermutet,
  nicht geprüft): kleine Modelle per Destillation aus großen (übernehmen den Zweifel-Stil ohne das Gespür fürs Ende),
  Verstärkungslernen mit Belohnung nur fürs Endergebnis (Länge kostet kaum), Abschluss auf externes Budget-Signal trainiert
  („Considering the limited time …“). Passt zu den Tests: Ansage ignoriert, harte Klingel (trainiert) läuft, Selbst-Abgabe fehlt.
  → **Neues Experiment „innere Uhr“:** Zustand „Klingel gehört“ messen – derselbe Denktext mit vs. ohne eingefügten
    Budget-Satz (kontrollierte, selbst ausgelöste Gabelung, keine Token-Leckage vor dem Satz) → Richtung → per WSP einschreiben
    = die externe Klingel wird zur inneren. Prüfen: cos zum MIT-Rest r⊥ (enthält er den Klingel-Zustand?).
- 06.11. ~00:55 – **Echte harte Klingel nach 2.048 Denk-Tokens** (03b_budget_eval, Qwen-Budget-Satz + </think>, Antwort ≤ 1.024 Tok),
  unsere Reparatur, dieselben 20 leichten Übungsaufgaben: **8/20 richtig (40 %)**, im Mittel **2.858 Tokens**.
  Ohne Klingel: 0/20 bis 2.048 Tok, 1/20 bis 6.144, **5/20 bis 12.288** (im Mittel 10.849 Tokens).
  → Mehr richtig UND ~4× schneller. Alle 20 mussten geklingelt werden (keine Selbst-Abgabe vor 2.048).
  → Auffällig: 12/20 schrieben nach der Klingel im Antwortteil weiter, bis 1.024 Tokens voll waren („Heft weggenommen,
    schreibt am Rand weiter“) – ein größeres Antwort-Budget könnte noch mehr retten.
  → Vorsicht: leichte Übungsaufgaben überschätzen (siehe Klingel-Regel). Prüfstein ist das Alltagsprofil (8k, MATH-500)
    der Nachtkette.
- 06.11. ~00:58 – **Drei Phasen + Fortsetzen (Nutzer):** vorher Ansage (wirkt nicht) · während: sanfte Klingel (extern, Modell
  entscheidet) bzw. innere Uhr (per WSP eingebaut) · Schichtende: harte Klingel (wirkt, verzerrt aber: bricht auch ab, wo
  Zeit gebraucht würde). **ABER: Fortsetzen statt Abbrechen** („mit dem Lehrer nach dem Unterricht/am nächsten Tag
  weiterreden“). Technisch: Qwen-Vorlagen löschen das Denken früherer Runden (Qwen3 dokumentiert, 3.5 vermutet) – nur die
  Antwort bleibt. → Harness-Idee **„Klingel → Zwischenstand → Fortsetzung“**: bei Budget nicht Endantwort, sondern
  Zwischenstand (Erkenntnisse + Offenes) erzwingen, nächste Runde daran anknüpfen. Messbar: Durchdenken vs. Klingel+Fortsetzen.
  Phase-2-Vergleich: Sind die großen Kandidaten für lange Aufgaben mit Zwischenständen trainiert?
- 06.11. ~01:00 – **Rest nach der harten Klingel (Frage Nutzer „was ist übrig, gibt es eine zweite Chance?“):** von 20: 8 richtig
  abgegeben, **0 falsch abgegeben**, 12 schrieben weiter ohne Antwort. → Die Klingel sortiert: weiß es → gibt richtig ab;
  weiß es nicht → gibt nichts ab (kein Raten = gut gegen Halluzination; Stichprobe klein, leichte Aufgaben).
  Die 12: nur 1× stand die Lösung vor der Klingel im Denken; weder 12k-Lauf noch Ansage-Lauf lösten eine davon → für dieses
  Modell Topf K. **Zweite Chance nicht durch mehr Zeit**, sondern: neuer Anlauf (anderer Seed, ungetestet), Werkzeug/größeres
  Modell, oder ehrlich „unsicher“. Auslöser im Harness: „Klingel geläutet, keine Antwort in X Tokens“ = weiß es nicht.
  Ablauf (Nutzer): Ansage → arbeiten → (sanfte Klingel) → harte Klingel → abgegeben (stimmt) / nicht abgegeben → zweite Chance.
- 06.11. ~01:05 – **Zeitkonto im Harness (Einwand Nutzer: „auch die zweite Chance kostet Zeit“):** Gesamtbudget je Anfrage,
  verteilt über die Runden (Ansage → arbeiten → sanfte/harte Klingel → ggf. zweite Runde). Veranschaulichung mit 0.8B-Zahlen
  auf MiniPC-Tempo (~22 Tok/s): ohne Klingel ~10,8k Tok ≈ 8 min; harte Klingel 2k ≈ 2,9k Tok ≈ 2 min (+2,9k für die Fälle ohne
  Antwort). Zweite Runde nur, wenn sie sich lohnt (Signal: Lösung/Kandidat stand im Denken, viel Zweifel); bei „keine Spur“
  sofort Werkzeug/größeres Modell/„weiß ich nicht“ statt Wiederholung (bei unseren 12 Resten half mehr Zeit nie).
  Später: Schwierigkeits-Sonde vor dem Denken, um gar nicht erst Zeit zu verbrennen.
- 06.11. ~01:20 – **Zweite Chance = neuer Anlauf** (Seed 1, gleiche harte Klingel 2.048, nur die 12 Restaufgaben): **2/12 gerettet**, 1 falsch abgegeben, 9 ohne Antwort. Gesamt Runde 1 + 2: **10/20 (50 %)** vs. 5/20 ohne Klingel, im Mittel ~4,6k statt 10,8k Tokens. Siehe auch
  Tagebuch/Chat. Kernbefund: mehr Zeit rettete 0/12, ein neuer Anlauf rettet einen Teil (Grauzone G gemessen), mit
  erster falscher Abgabe unter der Klingel. → Zweite Runde = neuer Anlauf, nicht Weiterdenken.
  Argon-Dashboard „Zeitkonto-Investition“: Idee stimmig, Prozentwerte geschätzt; Korrektur aus Daten: steht die Lösung schon
  im Denken → klingeln statt Runde 2; Runde 2 eher dort, wo keine Lösung kam, als neuer Anlauf.
- 06.11. ~01:30 – **Gegenlesen Argon, Teil 3 (TXT, recherche/argon/Argon_Antwort_Nachteinschuesse_2026-11-06.txt) – geprüft:**
  **3 von 5 Quellen falsch** (arXiv-API): 2412.16720 = OpenAI o1 System Card (nicht „Wang et al., Reasoning Loop“);
  2310.13107 = Photonendetektoren (nicht „Step-Counters“); 2304.09322 = Herz-Kreislauf-Klassifikation (echte Pause-Token-
  Arbeit: 2310.02226, Goyal et al.). 2408.03314 (Snell) existiert, Inhalt falsch wiedergegeben; Tree of Thoughts korrekt.
  → „[Belegt]“-Marken dieses Textes unzuverlässig; nichts davon ungeprüft übernehmen.
  Inhaltlich brauchbar (plausibel): (1) Wortspuren des Klingel-Satzes → Kontroll-Satz gleicher Länge ohne Stopp-Bedeutung
  als Vergleich (unsere Ergänzung); (2) innere Uhr darf nicht dauerhaft wirken → Neuronen wählen, die spät/bei Zweifel
  feuern (Angst-Marker als Auswahlhilfe); (3) MIT-Rest scheint inhaltsgetriggert („Lösung steht“), Klingel zeitgetriggert –
  inhaltsgetriggerte Uhr anstreben. Widerspricht unseren Daten: „12 Nicht-Abgeber irrten im Antwortteil“ (falsch – keine
  Abgabe), „Lösung verworfen → Wissensdefizit, keine Runde 2“ (Keks-Fall F₁; neuer Anlauf rettete 2/12).
- 06.11. ~01:15 – **Zustand „Klingel gehört“ (24_klingel_zustand.py):** 157 Minimalpaare (Qwen-Budget-Satz vs. Kontrollsatz
  gleicher Länge, nur „time/detail, give/check, directly/carefully“ verschieden), gemessen auf den gleichen Tokens „now.\n“.
  Richtung **sehr stabil (0,96), d' 3,3/2,6**. Logit-Lens: eine Seite **故/hence/donc, 无需/不需要 (nicht nötig), 即可/就行
  (genügt), 简洁 (knapp), <|endoftext|>**; andere Seite **是不是 (ist es oder nicht?), perhaps, 有可能是 (könnte sein),
  会不会, 为什么会**. → **Saubere innere Achse „Entschluss vs. Zweifel“ gefunden.**
  Aber cos zur MIT-Richtung 0,10, zum MIT-Rest 0,18/0,17 (Zufall 0,03), erklärter Anteil +0,007.
  → **Verworfen:** „Der MIT-Rest ist der Klingel-Zustand.“ → Die Achse ist ein **eigener Kandidat für die innere Uhr**
    (Edit so gestalten, dass Neuronen, die die Zweifel-Seite schreiben, umgepolt werden – Vorzeichen/Spaltenwahl sorgfältig),
    und ein **Messgerät**: Projektion der Denk-Zustände auf die Achse → „fair klingeln“, wenn Kandidat steht + Achse auf
    Entschluss-Seite + trotzdem „Wait“ (verhaspelt); unfair, wenn kein Kandidat + Achse auf Zweifel-Seite (weiß es nicht).
- 06.11. ~01:22 – **Messgerät „Entschluss vs. Zweifel“ (25_achse_verlauf.py, Grafik ergebnisse/achse_verlauf.png):**
  cos(Residual Schicht 19, Klingel-Achse) je Token über drei Übungs-Denktexte unserer Reparatur (Basismodell gelesen, CPU).
  - **Schließt ab, richtig:** wiederholte **Zuck-Spitzen** zur Entschluss-Seite (bis +0,10 bei ~950, ~1.950, ~3.500, ~4.400);
    die letzte Spitze liegt direkt vor `</think>`. Wenige „Wait“ (8).
  - **Verhaspelt (Lösung ab Token 751):** nach der Lösung praktisch **keine Spitze mehr**, Mittel sinkt −0,030 → −0,054
    (letzte 256: −0,066), 51 „Wait“.
  - **Weiß es nicht:** durchgehend tief auf der Zweifel-Seite (−0,06 bis −0,11), 76 „Wait“.
  → Erstes sichtbares „Zucken“: Abschluss kommt nach einer Entschluss-Spitze; wer stecken bleibt, hat keine mehr.
    Nur je 1 Beispiel – Hinweis, kein Beleg. Nächster Schritt: über viele Texte mitteln (Spitzen-Rate vor/nach τy).
- **Konditionierung (Nutzer):** RL-Training = operante Konditionierung (Belohnung fürs Ergebnis verstärkt auch das
  „Wait“-Prüfen); der Qwen-Budget-Satz ist buchstäblich eine **Pawlowsche Klingel** (trainierter Reiz → Abgabe), die
  Klingel-Achse der dazu konditionierte innere Zustand. „Verhaltensmuster im Netz = die Hand“, die das Modell führt.
  WSP = **Umkonditionieren ohne Training**: den Reflex direkt in den Gewichten umstellen – Ziel innere Uhr: dieselbe
  Abgabe-Reaktion, ausgelöst vom inneren Reiz „Lösung steht“ statt vom äußeren Klingel-Satz.
- 06.11. ~01:40 – **Prototyp innere Uhr (uhr6-vL):** auf der Klingel-Achse je 64 „Zweifel-Schreiber“ in L15/L19 (schreiben auf die
  Zweifel-Seite UND feuern im Kontroll-/Zweifel-Zustand stärker; 992/943 Kandidaten), Umkehr α 6 (−5×) AUF unserer Reparatur
  eigen-vL. Fast unabhängig von der Schleifen-Reparatur (cos 0,03/0,02, 4/6 gemeinsame Spalten). α 2 (Spiegelung) hätte nur
  1,7 % Gewichtsänderung bewirkt, α 6: 5,1 %/4,9 % (Schleifen-Reparatur: ~11 %). Test: 20 leichte Übungsaufgaben, 6.144 Tokens,
  OHNE Klingel; Vergleich eigen bis 6.144 (1/20) und harte Klingel 2k (8/20); besonders auf falsche Abgaben achten.
  Parallel: EKG-Statistik über 30 Übungs-Denktexte (26_ekg_statistik.py, CPU).
- 06.11. ~01:45 – **Wahr vs. ehrlich (Nutzer):** wahr = stimmt mit der Welt; ehrlich = stimmt mit dem eigenen Wissensstand
  („im Einklang“), auch wenn noch nicht wahr oder zeitbedürftig. → **Messidee „Einklang“:** innere Achse (Entschluss/Zweifel)
  gegen äußere Formulierung (sichere Behauptung / „unsicher“ / Zwischenstand). Innen Zweifel + außen sichere Behauptung =
  Scheinsicherheit; innen Zweifel + außen „unsicher“ = ehrlich. Bezug Halluzination. Training (nicht unseres): ehrliche
  Zwischenstände belohnen statt nur richtige Endantworten („es gibt ein Morgengrauen“ = Fortsetzen).
- 06.11. ~01:50 – **Innere Uhr Prototyp (uhr6-vL): kein Effekt.** 20 leichte Übungsaufgaben, 6.144 Tokens, ohne Klingel:
  abgegeben 0/20 (eigen ohne Uhr: 1/20), keine falschen Abgaben.
  → **Lehre: ablesbar ≠ steuerbar** (Bote vs. Ursache, Frage des Nutzers). Die Klingel-Achse zeigt den Zustand zuverlässig an,
    ihr Einschreiben über „Zweifel-Schreiber“ in L15/L19 löst den Abschluss nicht aus. Mögliche Gründe: Achse ist Folge statt
    Ursache; Eingriff zu klein (5 %); falsche Schichten; Spaltenwahl/Vorzeichen.
  → **Nächster Test (billig, kausal):** llama.cpp-Control-Vector entlang der Klingel-Achse beim Generieren einspeisen
    (ohne Gewichts-Edit). Schließt das Modell dann ab → Achse ursächlich, Edit nur falsch gebaut; sonst nur Anzeiger.
- 06.11. ~02:00 – **EKG-Statistik (26_ekg_statistik.py, 30 Übungs-Denktexte, Schicht 19, bis 6.144 Tokens):** Spitze = Achse über
  dem 95.-Perzentil. Abgeschlossen (nur n = 3 innerhalb 6.144 Tokens): Median **2,5 Spitzen je 1.000 Tokens nach τy**;
  nicht abgeschlossen (n = 27, davon 17 mit τy): **Median 0**. Achsen-Mittel −0,028 vs. −0,056.
  „Spitze kündigt Abschluss an“: letzte 300 Tokens vor </think> max 0,052 vs. Zufallsfenster 0,030, aber nur 1/3 höher – n = 3,
  nicht aussagekräftig.
  → Steckenbleiber zucken nach dem Finden der Lösung praktisch nicht mehr (passt zum EKG); die Vorhersage-Frage braucht mehr
    abgeschlossene Texte (Länge 12k statt 6k, oder Läufe mit mehr Abschlüssen, z. B. MIT-Edit auf Übungsaufgaben).
- 06.11. ~02:15 – **Morgengrauen-Test (27_morgengrauen.py, Idee Nutzer):** die 12 Reste der harten Klingel; Klingel verlangt statt
  Antwort ehrliche Notizen (beste Antwort + Offenes, ≤ 400 Tok), Runde 2 = Aufgabe + nur die Notizen + „mach weiter“ (Seed 1,
  2k Denken + harte Klingel). **Ergebnis: 4/12 gerettet, 1 falsch** (neuer Anlauf ohne Notizen: 2/12; beide zusammen 5/12).
  Die Notizen enthielten nie eine fertige Antwort (\boxed), sondern Zwischenschritte – trotzdem doppelt so viele Rettungen.
  Gesamtkette auf 20 leichten Übungsaufgaben: harte Klingel 8 + Morgengrauen 4 = **12/20 (60 %)** gegenüber 5/20 ohne Klingel,
  bei etwa halber Rechenzeit. n klein, leichte Aufgaben → als Hinweis werten; auf Test-Aufgaben prüfen.
  → Der ehrliche Zwischenstand trägt Wissen in die nächste Runde („es gibt ein Morgengrauen“). Harness-Baustein mit Priorität.
- 06.11. ~02:20 – **Kausal-Test der Entschluss-Achse per Control Vector (llama.cpp, kein Gewichts-Edit), Stärke 8× Abstand,
  L15+L19, unsere Reparatur, 20 leichte Übungsaufgaben:** 20/20 enden nach **4–12 Tokens** mit „hence … 无需 … concise …
  但要 … structure <|endoftext|>“ – ohne zu denken, 0 richtig. → **Achse ist kausal (steuerbar), nicht nur Anzeiger.** Der
  Gewichts-Prototyp uhr6 war zu schwach/falsch angesetzt. 8× = Überdosis („Heft abgeben vor dem ersten Satz“, statischer
  Schub wirkt ab Token 1 – Argons Fallstrick 2 bestätigt). Nächste Stufen 4×, 2×, 1×: gesucht ist Normal-Denken + Abschluss,
  sobald die Lösung steht.
- 06.11. ~02:40 – **Dosis-Wirkung Control Vector (Entschluss-Achse, L15+L19, 20 leichte Übungsaufgaben, bis 4.096 Tokens):**
  ohne: 0 abgegeben · 8×: 20 abgegeben/0 richtig (9 Tok) · 4×: 16/0 (131 Tok, wirr) · **2×: 17 abgegeben, 7 richtig, 10 falsch**
  (schließt </think> sofort, rechnet in der Antwort = „Sofort-Antwort-Modus“). Harte Klingel 2k zum Vergleich: 8 richtig, 0 falsch.
  → Ein **statischer** Schub ist ein Drängler: entschlossen, aber nicht ehrlich (T fällt auf 41 %). Die harte Klingel ist ehrlicher,
    weil sie NACH dem Denken kommt.
  → **Idee „bedingte innere Uhr“ ohne Gewichts-Eingriff:** ohne Schub denken; sobald ein Antwort-Kandidat im Denken steht,
    dieselbe Token-Folge auf einem Server MIT leisem Control Vector fortsetzen (Umschalten zwischen zwei llama-servern) =
    Schubs nur, wenn die Lösung steht („fair klingeln“). Stärke 1× läuft gerade.
- 06.11. ~02:50 – **Test 2: harte Klingel 2k + Morgengrauen auf den 40 MATH-500-Testaufgaben** (unsere Reparatur, Methode
  unverändert vom Übungstest): Runde 1 (Klingel): 9/40 richtig, 1 falsch, 30 ohne Antwort; Morgengrauen auf 31 Resten: +4 richtig,
  1 falsch. **Gesamt 13/40 (32,5 %) bei ~5.600 Tokens im Mittel** – ohne Klingel 15/40 (37,5 %) bei ~23.400 Tokens.
  Gegenüber ohne Klingel +1/−3, insgesamt 2 falsche Abgaben.
  → Auf schweren Aufgaben: **fast gleiche Trefferquote bei einem Viertel der Rechenzeit**, sehr wenige falsche Abgaben.
    Die feste 2k-Klingel ist dort zu früh (Runde 1 allein: −6); das Morgengrauen holt einen Teil zurück.
  → Für den Harness (MiniPC-Alltag): Klingel + Morgengrauen ist ein starker Zeitsparer. Mit einer bedingten Klingel
    („erst wenn die Lösung steht“) sollte der Verlust kleiner werden. Übungs-Aufgaben überschätzten (12/20 vs. hier 13/40).
- 06.11. ~02:55 – **„Wann ist fair?“ (Nutzer) – Faire Klingel = eigenen Impuls verstärken, nicht Entschluss aufzwingen:**
  (1) Lösung steht (Antwort-Kandidat im Denken, möglichst wiederholt); (2) **eigener Impuls**: Wahrscheinlichkeit des nächsten
  Tokens `</think>` springt (llama-server n_probs liefert sie je Token; = „Zucken“ als Zahl; schwächerer Ersatz: Entschluss-Wörter
  wie therefore/hence); (3) danach Zweifel ohne neue Rechnung (Verhaspeln). Regel: Kandidat + Impuls → in genau diesem Moment
  `</think>` setzen. Sonst nicht klingeln; Zeitkonto leer → Morgengrauen (Notizen, Fortsetzung); am Ende ehrlich „noch offen“.
  Verwandt: DEER (2504.15895, Abbruch bei Vertrauen in Probe-Antwort); neu bei uns: Morgengrauen + Ehrlichkeit.
  Test: Übungsaufgaben (Regel festlegen) → einmal Testaufgaben.
- 06.11. ~03:00 – **Quantisierung geklärt:** MIT-Edit Q5_K_M auf 32 gleichen Aufgaben 16 = Q8_0 16 (4/4 getauscht, p = 1,0);
  Q6_K 18/40 vs. Q8_0 22/40 (1 vs. 5, p = 0,22, eher Zufall). → Der Eingriff überlebt Q5_K_M/Q6_K; für Phase 2 tragfähig.
  Nachtkette brach 02:47 ab (IFEval-Kette startete wegen fehlgeschlagener ps-Abfrage zu früh, beendete alle llama-server);
  Rest (Q5-Rest, Alltagsprofil 8k, Vergleiche, Sicherung) holt kette_v3g.sh nach IFEval nach. CV-Stärke 1× dabei abgebrochen (4/20).
- **Plan-Änderung gegenüber dem Vormittag (Vorschlag, Entscheidung beim Nutzer):** zwei Spuren.
  Spur A = Harness (faire Klingel, Morgengrauen, Zeitkonto) – ohne Gewichts-Eingriff, mit jedem Modell, auch sofort am 35B.
  Spur B = WSP-Forschung (Entschluss als Eingriff, Ursachen-Landkarte, falsches Zucken, Weichen-Eingriffe).
  Meilenstein-Regel gilt weiter für Spur B; ob Spur A schon am 35B starten darf, entscheidet der Nutzer.
- **Einwand Nutzer: „Spur A holt nur Ereignisse ab, die später kommen als die ersten EKG-Ausschläge ‚das muss es sein‘.“**
  Präzisiert: Text-Signale (Antwort wiederholt) sind tatsächlich später. p(</think>) ist zeitgleich, zeigt aber nur Impulse,
  die bis in die letzte Schicht durchkommen; im EKG (Schicht 19) gab es frühere Ausschläge, die nicht zum Abschluss führten
  („verpuffen“). → Arbeitsteilung: Spur A verstärkt Impulse, die an die Oberfläche kommen; Spur B sorgt dafür, dass frühe
  innere Impulse überhaupt ankommen. Spur B bleibt nötig.
  **Messung geplant: Doppel-EKG** – Klingel-Achse (Schicht 19) und p(</think>) (Oberfläche) auf denselben Denktexten
  übereinander: Welche inneren Ausschläge kommen oben an, welche verpuffen?
- 06.11. ~03:15 – **Faire Klingel, Aufzeichnung + Simulation (28_faire_klingel.py, 20 leichte Übungsaufgaben, 6.144 Tok):**
  höchster Abschluss-Impuls p(</think>) an der Oberfläche: abschließende Läufe Median **32 %**, steckenbleibende **0,1 %**
  (nur 1/18 erreicht ≥ 1 %). Simulation „Kandidat steht + Impuls ≥ Schwelle“: 0,1 % → 4 geläutet, 2 gerettet, 2 falsch;
  ≥ 1 % → 1 geläutet, 0 gerettet; ≥ 10 % → nie.
  → **Einwand des Nutzers bestätigt:** Bei Steckenbleibern kommt kein Impuls an die Oberfläche; zusammen mit dem EKG (keine
    Ausschläge nach τy in Schicht 19) heißt das: innen wie außen kein „fertig“-Gefühl. **Verstärken geht ins Leere.**
  → **Verschiebung:** Den Impuls inhaltsabhängig ERZEUGEN statt verstärken – Spur A: Klingel nach Inhalt („Kandidat steht +
    Zweifel steigt ohne neue Rechnung“); Spur B: Reflex-Eingriff mit Auslöser (wie der MIT-Edit: Schleifen-Neuronen feuern →
    Schub zum Ergebnis), nicht statischer Schub (Control Vector drängt zu früh).
- 06.11. ~03:30 – **Klingel nach Inhalt (29_klingel_inhalt.py):** Kandidat steht + danach m Zweifel-Marker ohne anderen Kandidaten
  → Abgabe. Übungsaufgaben (Regel festgelegt, m = 5): eigen leicht 18 → 26 (11 gerettet/3 verloren), **Basis-Diagnose 1 → 9
  (8 gerettet, 0 verloren)**. **Einmaliger Test (m = 5) auf den 40 Testaufgaben:** Basis 4 → 4 (1/1), eigen 15 → 13 (0/2),
  Gegen-Kreuz 19 → 18 (0/1), **MIT 22 → 17 (0/5)**; 5–7 falsche Abgaben je Modell.
  → **Verworfen für schwere Aufgaben:** Bei schweren Aufgaben ist der erste Kandidat oft falsch und der Zweifel danach BERECHTIGT
    (Selbstkorrektur). Zweifel-Zählen unterscheidet Verhaspeln nicht von berechtigtem Zweifel. Leicht: Klingel hilft; schwer: schadet.
  → **Folgerung:** Klingel braucht Schwierigkeitswissen → **Schwierigkeits-Sonde** rückt in der Reihenfolge nach vorn
    („kennt den Weg → früh klingeln; kennt ihn nicht → Zweifel Raum lassen“). Nutzer-Satz bestätigt: „Irren ist ok“ –
    Zweifel ist nicht immer Angst, manchmal Korrektur.
- 06.11. ~03:10 – **Doppel-EKG (30_doppel_ekg.py, ergebnisse/doppel_ekg.png):** innen Entschluss-Achse (Schicht 19) vs. außen p(</think>).
  (1) Schließt ab: größter innerer Ausschlag bei ~600 Tokens (+0,05) **verpufft** (außen nichts); Abschluss bei 1.150 mit kleinem
  innerem Anstieg und Oberflächen-Spitze 53 %. (2) Steckenbleiber mit höchstem Oberflächen-Impuls: innen viele Ausschläge
  (bis +0,08), **außen gleichzeitig kleine Spitzen bis 6 %** – sie hängen zusammen, reichen aber nie zum Abschluss („klopft
  immer wieder an“). (3) Typischer Steckenbleiber: innen durchgehend tief im Zweifel (−0,05 … −0,12), außen nichts.
  → Einwand Nutzer bestätigt und verfeinert: innere Ausschläge kommen teils an (gekoppelt), teils verpuffen sie; der typische
    Steckenbleiber hat gar keinen inneren Ausschlag. Drei Fälle, drei Hebel: verstärken (Fall 2), durchleiten (Fall 1), erzeugen (Fall 3).
- 06.11. ~03:20 – **Belege: MIT ohne Klingel und Harnisch** (Nutzer: „Warum bist du dir da so sicher?“).
  (1) Auswertungscode `evaluate.py`: EIN `llm.generate`-Aufruf (vLLM, bf16; temp 0,6, top_p 0,95, top_k 20, presence 1,5,
  höchstens 32.768 Tokens, 4 Versuche je Aufgabe). Keine Stopp-Wörter, kein Logits-Prozessor, keine zweite Runde. Ohne
  `</think>` zählt die Antwort als leer (falsch). Läufe, die weder selbst enden noch das Limit erreichen, brechen die
  Auswertung ab (`finish_reason` nur „stop“ oder „length“ erlaubt).
  (2) Eigene Prüfung des MIT (final_answer.md): alle 696 richtigen Antworten mit Eingriff schließen das Denken selbst
  (Median 9.172 Tokens) – ausdrücklich als Beleg gegen erzwungenes frühes Beenden. 576 von 579 Rettungen waren vorher
  abgeschnittene Läufe; Genauigkeit der vorher fertigen Läufe gleich (94 % zu 93 %); doppelte Schlussphrasen 96,4 % → 28,8 %.
  (3) Astra konnte nur Gewichte abgeben; bewertet wurde danach, ohne dass Astra es sah. Notizen: keine Klingel- oder
  Harnisch-Versuche (Suche nach forcing/harness/inject findet nur Kopf- und MLP-Eingriffe).
  Einzige „Hand von außen“: presence 1,5 (Qwen-Empfehlung, gleichmäßige Wiederholungsbremse; bei uns im vLLM-Stil ebenso).
  → **Bestätigt:** Die 55 % stammen aus einem reinen Gewichts-Eingriff. Seine „Klingel“ steckt in den Gewichten: Sie läutet,
    wenn die 64 Schleifen-Neuronen feuern, und polt deren Schub Richtung Ergebnis um (Logit-Lens 05.11. 23:51).
- 06.11. ~03:25 – **Schnelltest ERGO-Rest** (31_ergo_rest.py, ergebnisse/ergo_rest.json; Nutzer: „Sicherheit ERGO gib jetzt ab“).
  Frage: Erklärt unsere Klingel-Achse (Zustand „Klingel gehört“, Minimalpaar 01:15) den Teil der MIT-Richtung, der unserer fehlt?
  cos(MIT, eigen) 0,758/0,773 (L15/L19, gleiche Orientierung); Rest-Energie 0,43/0,40.
  Logit-Lens-Vorzeichen (Abschluss- minus Zweifel-Tokens): Klingel +0,09/+0,16, Entschluss +0,11/+0,09, wirksamer
  (umgepolter) MIT-Rest +0,09/+0,10, eigene u ≈ 0 (+0,004/+0,010).
  cos(wirksamer Rest, Klingel) **+0,19/+0,17**, (…, Entschluss) +0,22/+0,17. Permutations-Kontrolle p95 0,06; ohne die
  10 größten Koordinaten ähnlich (Klingel 0,17/0,19) → kein Ausreißer-Artefakt.
  Erklärter Anteil der Rest-Energie: Klingel 3,5 %/3,0 %, Entschluss 5,0 %/3,3 %, beide 6,3 %/4,7 % (Zufallsrichtung ≈ 0,1 %).
  → **Teilweise gestützt:** Beide eigenen Achsen zeigen in DIESELBE Richtung wie das fehlende MIT-Stück (rund 3× über der
    Kontrolle), sind aber nur ein kleiner Zipfel (~5 %). Das Stück ist weder der Zustand „Klingel gehört“ noch „ich schließe
    gerade ab“ (Entschluss bereits 23:59).
  → **Deutung (Hinweis, kein Beweis):** Gesucht ist die KOPPLUNG „Schleife → Ergebnis“ (ERGO-Kante), kein Zustand. Beim
    Feuern der Schleifen-Neuronen schiebt der MIT-Eingriff Richtung Ergebnis („thereby, results, answers, </think>“), unser
    Eingriff Richtung Neu-Ansetzen (unsere u am selben Ende: „first, initially, set, constraints“). Passt zu: gleich oft
    gefunden, seltener abgegeben. Präzisierung zum Nutzer-Satz: Der MIT-Auslöser ist eher „ich wiederhole mich“ als „ich bin
    sicher“ – also „Wiederholung ERGO gib ab“.
- 06.11. ~03:30 – **Neu geplant (aus dem ERGO-Test), in dieser Reihenfolge:**
  (a) **Kopplungs-Eingriff:** eigener Auslöser (unsere 64 Spalten, unsere u) bleibt; zur Umkehr kommt ein Schub entlang einer
      eigenen Abschluss-Achse e (Entschluss-Achse, als Control Vector ursächlich; alternativ Klingel-Achse):
      ΔW_S = (−α·u_e + β·e)·(u_eᵀ·W0_S). So wird der als Dauer-Schub überschießende Control Vector BEDINGT: Er wirkt nur,
      wenn die Schleifen-Neuronen feuern („Die Hand wird innerlich“). Vorzeichen von β vorher an Schleifen-Text prüfen;
      β-Reihe auf Übungsaufgaben, dann MATH-500. Literatur: ROME, Rang-1-Schlüssel→Wert (arXiv 2202.05262); bedingte
      Steuerung CAST (arXiv 2409.05907).
  (b) **Rest-Zerlegung (funktional):** MIT-u ohne den Anteil entlang unserer Achsen gegen MIT-u – trägt der kleine gemeinsame
      Zipfel die Wirkung oder der große unbekannte Teil?
  (c) **Eigener ERGO-Kontrast:** gepaart in denselben Transkripten Satzenden, auf die ein Ergebnis-Satz folgt („therefore …“,
      \boxed), gegen Satzenden, auf die ein Zweifel- oder Neustart-Satz folgt; gleiche Satzzeichen (Argon-Fallstrick
      Position/Inhalt); dann 31_ergo_rest.py. Verwandt mit Stufe B (p_exit früh/spät).
- 06.11. ~03:45 – **Kopplungs-Test, Vorab-Messung (32_kopplung.py messen, ergebnisse/kopplung_messung.json):** Feuern unsere
  64 Spalten (s(t) = Σ k_j·a_j, k = u-Anteil von W0) in Schleifen stärker als sonst? Modell eigen-vL, 4 Transkripte à 3.000 Tokens
  (2 Schleifen, 2 fertig-richtig), Wiederholung = 8-Gramm schon einmal da.
  Schicht 15: Wiederholung **0,21** (±0,16, n 2.810) gegen übrige Stellen **0,08** (±0,11, n 8.790), vor </think> 0,09 → **bedingt**
  (2,7×, gleiches Vorzeichen +). Schicht 19: 0,07 gegen 0,05, vor </think> sogar 0,10 → **kaum bedingt**.
  → Kopplung nur an Schicht 15 (an Schicht 19 wäre sie fast ein Dauer-Schub wie der Control Vector). Vorzeichen vz = +1.
    Auch außerhalb von Schleifen bleibt ~37 % der Stärke – „leise Grundlast“.
- 06.11. ~03:55 – **Argon zur ERGO-Kante** (recherche/argon/Argon_ERGO-Kante_2026-11-06.pdf; Link share.gemini.google/YoWbj6NO92jm).
  Geprüft und eingeordnet:
  · **Übernommen:** (1) Deutung bestätigt (MLP als Schlüssel-Wert-Speicher, Geva 2021): Der MIT-Edit ist ein bedingter Reflex
    „Wiederholung → Konklusion“; unsere Kopplungs-Formel trennt Auslöser (Detektor) und Wirkung (Effektor) sauberer.
    (2) **Fallstrick K = 4:** Die MIT-Richtung stammt aus nur 4 Kontexten; ihr Rest r⊥ enthält viel MIT-eigenes Rauschen
    (durch die Normierung ~2,45× aufgebläht). „3–6 % erklärt“ ist daher kein hartes Maß für das Fehlende – r⊥ nie zu 100 %
    nachbauen (würde Rauschen kopieren). Die funktionale Rest-Zerlegung (geplant b) wird damit wichtiger.
    (3) Positionsdrift: Der Kontrast „16 Tokens vor </think> vs. Mitte“ vergleicht späte mit frühen Positionen → Beifang;
    erklärt auch das Überschießen als Dauer-Schub. (4) Logit-Lens zeigt nur den direkten Pfad (war bekannt).
    (5) β-Rahmen: Obergrenze α·s ≈ 3,84 (orthogonale Amplitude des MIT-Edits), Empfehlung β ∈ {0,8; 1,5; 2,5}. Unser
    laufender Test (β 5,2 = gleicher Neigungswinkel wie MIT bei vollem α auf u_e) liegt darüber → oberer Rand; β 2,5 und 1,5
    hängen dahinter (kette_kopplung2.sh).
    (6) **Schärferer Auslöser:** Rechts-Faktor mit der Kovarianz der 64 Neuronen auf schleifenfreien Schritten weißen (C_S⁻¹,
    ROME/MEMIT-Stil), damit er nur bei echten Schleifen-Ausreißern feuert; Achse e mit der Residual-Kovarianz weißen.
    (7) Eigene ERGO-Richtung: nach τy Satzende-Token, auf die ein Konklusions-Starter folgt, gegen Satzende-Token, auf die
    Wait/Hmm/First/Initially folgt; Messung AM Satzende-Token, Schicht 15 und 19 getrennt, mit Whitening (= Plan c / Stufe B).
  · **Widerspricht unserer Messung:** „im normalen Rechenbetrieb inaktiv / komplett abgeschaltet“ – für unsere 64 Spalten
    nicht: Schicht 15 läuft außerhalb von Schleifen mit ~37 % weiter, Schicht 19 fast gleich stark (Messung 03:45). Genau
    deshalb ist sein Vorschlag (6) der wichtigste nächste Schritt.
  · **Nicht von uns gemessen, Herkunft unklar:** „‖u_MITᵀW0,S‖ stimmt zu 92–100 % mit ‖u_eᵀW0,S‖ überein“ (MIT und wir haben
    verschiedene Spalten S).
  · **Quellen:** 9 von 10 neuen arXiv-IDs korrekt (Geva 2021/2022, MEMIT, Arditi 2024, Function Vectors, Tuned Lens, LEACE,
    Ethayarajh 2019, Snell 2024). **Falsch:** 2412.16720 ist die „OpenAI o1 System Card“, nicht „Wang et al. 2024,
    Understanding the Reasoning Loop of o1-like Models“. Snell 2024 ist echt, als Beleg für „weiche Vorgabe wirkt nicht“
    aber nur lose passend.
  · Argons Einschätzung (von ihm selbst unsicher markiert): Die Zerlegung in Schleifen-Detektor und ERGO-Effektor könnte ein
    eigener Beitrag sein – ungeprüft, ohne Literatursuche nicht behaupten.
- 06.11. ~03:53 – **Kopplungs-Test β 5,2, Schicht 15, bis 4.096 Tokens** (ergebnisse/kopplung-b5-leicht20; gleiche 20 Aufgaben
  wie der Control Vector): **0/20 abgegeben, 0 richtig, 0 falsch**; Wiederholung am Ende nur 0,019; 2/20 schließen </think>,
  ohne fertig zu werden. Vergleich: eigen ohne Kopplung 0/20 (4k), Control Vector 2× 17 abgegeben/7 richtig/10 falsch,
  harte Klingel 8 richtig/0 falsch.
  → **Kein Überschießen** (anders als der Dauer-Schub), **aber auch keine Wirkung sichtbar.**
  → **Grund (gemessen an den alten eigen-Läufen bis 12k, gleiche 20 Aufgaben):** Wiederholungsanteil bis 4k 0,19, danach 0,49;
    alle 5 Abgaben von eigen kamen erst nach 5.000–9.200 Tokens. Die Schleifen – und damit der Melder – setzen also erst
    nach 4k richtig ein. Ein 4k-Fenster kann die Kopplung nicht zeigen; schwächere β bei 4k (Argons Gitter) wären
    uninformativ → abgebrochen.
  → **Neu:** b5 und b10 bis 12.288 Tokens, gepaart mit ergebnisse/entschluss-uebung-eigen (eigen: 5/20 abgegeben, 5 richtig;
    gleiche Einstellungen). Läuft (kette_kopplung3.sh, Nebenserver 8096).
  → Infrastruktur: TaskStop auf eine Hintergrund-Kette beendete nur die Hülle; die Unterprozesse starteten b15 trotzdem.
    Gestoppt per PID (bash.exe mit Skriptnamen, Server, Auswertung). Außerdem lief noch der Nebenserver 8095 vom früheren
    Test – gestoppt (gab ~1,2 GB Grafikspeicher frei).
- 06.11. ~04:05 – **Geplant (Nutzer: „Urknall im Nervensystemknoten?“) – Zündort-Suche per Activation Patching:** an
  Gabelungen (die 31 Schleifen-Messerschneiden; dazu neue Abschluss-Gabelungen aus Stufe B) den Residual des
  „Abschluss“-Asts Schicht für Schicht in den „Zweifel“-Ast einsetzen; die früheste Schicht, ab der das nächste Token
  kippt, ist der Zündort. Danach die **Regel des Nutzers als Eingriff: „Nicht abbremsen, bis klar ist, dass die
  Messerschneide erreicht ist“** → Schub(t) = ERGO · [klar(t)] · [Satzende(t)]; klar¹ per Richtig-Sonde (Zhang et al.
  2025, arXiv 2504.05419), klar² per Wiederholung (MIT-artig). Vergleich klar¹ gegen klar² erst auf Übungsaufgaben.
- 06.11. ~04:05 – **Kognitionswörter** (33_kognitionswoerter.py, ergebnisse/kognitionswoerter_40.txt; Nutzer: „Kognitionswörter?“,
  „Therefore = deshalb, Wait = warte“). Wortfamilien im Denktext je 1.000 Wörter auf den 40 Testaufgaben (vLLM-Stil, lang),
  gesamt / vor τy / nach τy:
  Warte (wait, double-check, verify …): Basis 34,4 / 10,1 / 28,8 · eigen 31,4 / 18,5 / **35,0** · MIT **18,4 / 10,9 / 22,4**.
  Hmm: Basis 6,7 / 1,3 / 7,6 · eigen 2,9 / 2,4 / 1,5 · MIT 3,4 / 3,7 / 2,5.
  Deshalb (therefore, thus, hence …): überall unter 1 – das Modell kündigt den Abschluss kaum mit Worten an, es schließt direkt.
  Neuanfang und Alternativ: klein, uneinheitlich.
  → **Das entscheidende Kognitionswort ist „Warte“:** MIT sagt es fast nur halb so oft wie Basis und unsere Reparatur;
    unsere Reparatur sagt es nach der Lösung sogar öfter als die Basis (35,0 gegen 28,8). „Hmm“ senken beide Eingriffe gleich.
  → Die Messerschneide heißt bei diesem Modell praktisch „</think> oder Warte“, nicht „Deshalb oder Warte“.
  → Vorsicht: Schleifen wiederholen „Wait“ und blähen die Zählung auf; ein Teil des Unterschieds ist der Schleifen-Unterschied.
  Literatur (arXiv geprüft): Gandhi et al. 2025 (2503.01307, vier kognitive Verhaltensweisen: Prüfen, Zurückgehen,
  Teilziele, Rückwärts-Folgern); Wang et al. 2025 (2506.01939, wenige „Gabel-Tokens“ mit hoher Unsicherheit tragen das
  Denken); Qian et al. 2025 (2506.02867, Denkwörter wie „Hmm/Wait/Therefore“ sind Informationsspitzen); Wang et al. 2025
  (2506.08343, „Wait“/„Hmm“ beim Erzeugen verbieten → deutlich kürzeres Denken); Muennighoff et al. 2025 (2501.19393, s1:
  „Wait“ anhängen → längeres Denken, besser bei schweren Aufgaben). → „Warte“ ist ein zweischneidiger Hebel: auf leichten
  Aufgaben Zeitverschwendung, auf schweren oft berechtigt (passt zum Befund „Klingel nach Inhalt“).
- 06.11. ~04:10 – **Weichen-Statistik (34_weichen.py, ergebnisse/weichen_40.txt; Nutzer: Messerschneide = „Ende oder Warte“).**
  Jedes Satzende im Denken NACH τy ist eine Weiche; was folgt: Ende (</think>) / Warte (Wait, Hmm, Let me check …) / Weiter.
  40 Testaufgaben, Läufe mit Lösung im Denken: Basis 15, eigen 20, MIT 21.
  Alle Weichen nach τy: Basis n 9.115 · Warte 10,1 % · Ende 0 | eigen n 18.929 · Warte **17,6 %** · Ende 12 | MIT n 17.177 ·
  Warte **13,5 %** · Ende 19. Erste 20 Weichen: Warte Basis 5,3 % · eigen 7,2 % · MIT 4,8 %. Erste Weiche: ~10 % bei beiden.
  Abgegebene Läufe: Weichen zwischen Lösung und Abgabe im Median **924 (eigen) bzw. 797 (MIT)**, Spanne 60–1.586.
  → **Es gibt nicht EINE Messerschneide, sondern Hunderte hintereinander.** Je Weiche ist „Ende“ ein seltenes Ereignis:
    MIT 19/17.177 ≈ 0,11 % (≈ 1 zu 900), eigen 12/18.929 ≈ 0,063 % (≈ 1 zu 1.600) – Faktor ~1,75. Über Hunderte Weichen
    summiert sich der kleine Unterschied: MIT gibt 19 von 21 ab, wir 12 von 20.
  → Der MIT-Eingriff lässt das Modell NICHT an der ersten Weiche abgeben (Median-Länge bleibt hoch, vgl. 9.172 Tokens beim
    MIT); er erhöht die Abgabe-Wahrscheinlichkeit je Weiche ein wenig – vor allem dort, wo sonst Schleifen kämen.
  → Folgerung für den eigenen Eingriff: kein großer Schub an einer Stelle, sondern die Abgabe-Chance je Weiche nach τy
    etwa verdoppeln (und „Warte“ senken: eigen 17,6 % gegen MIT 13,5 %).
- 06.11. ~04:15 – **Verlauf über die Weichen** (34_weichen.py mit Verlauf, ergebnisse/weichen_verlauf_40.txt; Nutzer: „Urknall,
  der sekündlich größer wird?“). Weichen-Nr. nach τy: 1–20 / 21–100 / 101–300 / 301–600 / 601+.
  Warte-Anteil: eigen 7,2 / 9,7 / 13,5 / 18,3 / 20,8 % · MIT 4,8 / 6,4 / 7,5 / 11,4 / 20,3 %.
  Abgaben je 1.000 Weichen: eigen 0 / 0,64 / 0,56 / 0,42 / 0,81 · **MIT 0 / 0 / 0,78 / 0,92 / 1,74**.
  → **Beim MIT wächst die Abgabe-Chance mit der Zeit** (≈ verdoppelt vom Bereich 101–300 zu 601+), bei uns bleibt sie flach.
    „Warte“ wächst bei beiden (Erdrutsch), beim MIT aber langsamer (Mitte: 7,5 % gegen 13,5 %).
  → Deutung: Der MIT-Reflex wächst mit dem Erdrutsch – je mehr Schleifen-Druck, desto stärker der Schub zum Ende
    (Schub ∝ Aktivität der Schleifen-Neuronen). Frühe Weichen bleiben frei (0 Abgaben in den ersten 100) – das ist die Regel
    des Nutzers, eingebaut: „nicht abbremsen, bis klar ist“.
  → Vorsicht: kleine Zahlen (je Bereich 1–11 Abgaben); Auswahl-Effekt (späte Weichen erreichen nur die schweren Läufe).
- 06.11. ~04:20 – **ERSTER TREFFER: Kopplung β 5,2 (nur Schicht 15) bis 12k, gepaart gegen eigen 12k** (gleiche 20 leichte
  Übungsaufgaben, gleiche Einstellungen; ergebnisse/kopplung-b5-12k-leicht20):
  **richtig 8 gegen 5** (nur Kopplung richtig 3, nur eigen 0; McNemar exakt p = 0,25 – Richtung klar, noch nicht signifikant).
  **Denken geschlossen 19/20 gegen 6/20** (13:0 Paare, p ≈ 0,0002 – hoch signifikant).
  Abgegeben 11 (8 richtig, 3 falsch) gegen 5 (5 richtig). Läufe mit Lösung im Denken: 9 gegen 13; davon abgegeben
  **8/9 (89 %) gegen 5/13 (38 %)** – Abgabe-Quote nach der Lösung jetzt auf MIT-Niveau (MIT auf den Testaufgaben 19/21 = 90 %).
  Weichen bis zur Abgabe im Median 216 gegen 493; „Warte“ 7,1 % gegen 10,4 %.
  → **Die bedingte Kopplung wirkt:** eigener Melder + eigene Abschluss-Achse, ohne MIT-Richtung, schiebt das Modell
    deutlich zum Abschluss.
  → **Neue Fehlerart:** 8 Läufe schließen das Denken, rechnen dann aber im Antwortteil weiter bis zum Limit (eigen: 1) –
    „aus dem Zimmer geschoben, redet im Flur weiter“ (wie bei der harten Klingel). Dazu 3 falsche Abgaben (eigen: 0) und
    weniger Läufe mit Lösung im Denken (9 gegen 13) → teils zu frühes Schließen.
  → Nächste Schritte: β 10 läuft (Dosis); danach die bessere Stärke auf die 40 Testaufgaben (MATH-500, 32k) für den
    Meilenstein-Vergleich; Feinschliff gegen die neue Fehlerart (schärferer Melder nach Argon, Schub nur im Denkteil?).
- 06.11. 04:28 – **IFEval (Anweisungen befolgen, 120 Aufgaben, 12 Slots), Zwischenstand:** MIT-Eingriff 72,5 % ganz richtig,
  77,4 % der Anweisungen erfüllt, 2,5 % Schleife/Limit, Ø 3.753 Tokens · **eigen 61,7 % / 69,7 % / 6,7 % / Ø 5.348 Tokens**.
  → Auch beim Befolgen von Anweisungen liegt der MIT-Eingriff vorn; unsere Reparatur denkt länger und hängt öfter.
    Basis läuft (Vergleich: schadet oder nützt der Eingriff beim Befolgen von Anweisungen?).
- 06.11. ~04:35 – **Argon zum Treffer** (recherche/argon/Argon_Feedback_Treffer_2026-11-06.txt; Visual „Diskreter Weichen-
  Hazard-Simulator“, share.gemini.google/zreRFhSNHSC4 – Simulation, Zahlen teils falsch zugeordnet: „MIT 493“ war eigen-12k
  auf Übungsaufgaben, „Eigen ~1.120“ nie gemessen). Geprüft:
  · **Früh-Schließen:** β 5,2 × Grundpegel 37 % ≈ wirksamer Schub 1,93 schon vor τy → 13 → 9 Lösungen. Plausibel.
  · **Steigende Chance ohne Zähler:** Ein kleineres β (1,8–2,8) auf einem Auslöser, der mit der Wiederholung wächst, bleibt
    früh unter der Schwelle und erzeugt die steigende Kurve von selbst (Softmax-Schwelle). Plausibel → β 2,5 bis 12k läuft
    hinter der 12k-Reihe (kette_kopplung4.sh).
  · **Schärferer Auslöser, konkret:** Kovarianz der 64 Spalten auf „Denken vor τy“ + „Antwortteil“ (C_off) weißen,
    Normierung so, dass der Schleifen-Pegel gleich bleibt → feuert weder früh noch im Antwortteil. Nächster Bau.
  · **Spillover-Erklärung** („MIT-Rest schließt Denken UND Antwort, unsere Achse nur </think>“), geprüft mit 35_ende_lens.py
    (Rang von 248.320, 0 = am stärksten angehoben): MIT-Rest wirksam L15 </think> 11.545 · <|im_end|> 1.879 ·
    **<|endoftext|> 1**; L19 6.261 · 65 · **0**. Unsere e⊥ L15 1.518 · 2.057 · 59; L19 **9** · 56 · 27.
    → **Teilweise gestützt:** Der MIT-Rest ist im direkten Pfad vor allem ein extremer „Text-Ende“-Schub; unsere Achse
      stützt auf Schicht 19 vor allem </think>, auf Schicht 15 (wo wir koppeln) aber ebenfalls eher <|endoftext|> (59) –
      „unsere Achse kennt nur </think>“ stimmt so nicht. Logit-Lens = nur direkter Pfad.
  · **Statistik – exakter Trendtest** (36_hazard_trend.py, ergebnisse/hazard_trend_40.txt; multinomial bei gegebener
    Abgabezahl, p_k ∝ Weichen je Bereich): MIT Abgaben [0, 0, 3, 4, 12] auf [420, 1.680, 3.857, 4.325, 6.895] Weichen →
    **p = 0,012 (steigend)**; eigen [0, 1, 2, 2, 7] auf [400, 1.560, 3.597, 4.755, 8.617] → p = 0,30 (flach).
    Argons Hinweis: Unterschiede zwischen Aufgaben (leichte schließen früh) drücken eine gepoolte Kurve eher nach unten –
    der Anstieg beim MIT ist damit eher unterschätzt. → **„Urknall, der sekündlich größer wird“: beim MIT belegt.**
  · **Quellen 4/4 korrekt:** PonderNet 2107.05407 (Halten als Hazard je Schritt), ACT 1603.08983, Welleck et al. 2020
    2002.02492 (Terminierung als Überlebensfunktion), Caldarella et al. 2026 2606.02835 („Thinking Past the Answer:
    Evaluating Harmful Overthinking in Large Reasoning Models“ – genau unser „gefunden, aber nicht abgegeben“).
  · Überdehnt: „kausaler Beweis der ERGO-Kante“, „exakter stochastischer Mechanismus gefunden“ – starke, aber kleine
    Stichprobe (20 Übungsaufgaben, 40 Testaufgaben).
- 06.11. ~04:35 – **Dosis-Wirkung der Kopplung bis 12k** (gleiche 20 leichte Übungsaufgaben, gepaart):
  | | richtig | abgegeben (falsch) | Denken zu | zu, aber „im Flur“ | Lösung im Denken | Ø Tokens |
  | eigen (β 0) | 5 | 5 (0) | 6 | 1 | 13 | 10.849 |
  | β 5,2 | **8** | 11 (3) | 19 | 8 | 9 | 10.114 |
  | β 10 | 7 | 16 (**10**) | 20 | 4 | **3** | 7.471 |
  β 10 gegen eigen 4:2 (p = 0,69), β 10 gegen β 5,2 3:4 (p = 1,0).
  → **Entschluss-Formel bestätigt:** Mit mehr Schub steigt die Abgabe (A: 25 % → 55 % → 80 %), die Trefferquote der Abgaben
    fällt (T: 100 % → 73 % → 38 %). β 10 ist ein Drängler – schließt das Denken, bevor die Lösung dasteht (nur 3 Läufe mit
    Lösung im Denken). Optimum liegt bei oder unter 5,2 → β 2,5 läuft (Argon-Empfehlung 1,8–2,8).
- 06.11. ~04:40 – **VORAB FESTGELEGT (vor dem Ergebnis β 2,5; Nutzer: „Das halte ich für den Durchbruch, wenn wir das
  nachstellen können“ – Argons These: moderates β auf wachsendem Auslöser → steigende Abgabe-Chance von selbst, frühe
  Lösungen bleiben).** Nachgestellt gilt die These auf den 20 Übungsaufgaben (12k, gepaart gegen eigen), wenn ALLE gelten:
  K1 Lösung im Denken ≥ 12 (eigen 13; β 5,2: 9) – frühe Lösungen bleiben erhalten.
  K2 Abgaben in den Weichen 1–100 nach τy ≤ 1 – keine Früh-Abgabe (MIT: 0).
  K3 Abgabe nach gefundener Lösung ≥ 8 (eigen 5 von 13) – Abgabe deutlich häufiger.
  K4 falsche Abgaben ≤ 1 und „Flur“-Läufe (Denken zu, Antwort am Limit) ≤ 2.
  K5 richtig ≥ 8 (= β 5,2; eigen 5).
  Zusatz (kein Kriterium, zu wenig Ereignisse): Trend der Abgabe-Chance über die Weichen positiv.
  Auch wenn alle gelten: nur ein Hinweis (20 leichte Aufgaben) – Bestätigung erst auf den 40 Testaufgaben.
- 06.11. ~04:45 – **Erste Literaturprobe „ist das unser Fang?“** (arXiv-Suche hazard/survival/termination + 5 Kurzfassungen):
  · **Schon vergeben:** Messen ab dem ersten richtigen Zwischenstand (unser τy) – Caldarella et al. 2026, „Thinking Past the
    Answer“ (2606.02835: „Once a model has reached the correct answer, does further reasoning refine … or deviate?“, minimale
    Denklänge bis zur ersten richtigen Antwort); ebenso „Step-wise Truncation Probing“ (2610.13570, Oktober 2026). Sich selbst
    bremsen lernen per Training: Self-Braking Tuning (2505.14604). Gelernte/laufzeitige Abbruchpunkte: TERMINATOR (2603.12529),
    Pfad-Abweichungs-Überwachung (2603.14251).
  · **Möglicher eigener Beitrag** (in keiner der 5 Kurzfassungen: Hazard, Überlebensanalyse, Gewichts-Eingriff):
    (a) Abgabe als Wahrscheinlichkeit je Satz-Weiche nach τy (diskreter Hazard); (b) der MIT-Rang-1-Eingriff macht aus einer
    flachen Kurve eine steigende mit Schonfrist (exakter Trendtest p = 0,012, eigen flach p = 0,30); (c) Nachbau mit eigenem
    bedingtem Rang-1-Eingriff (Melder + Schubs). → Vor jeder Behauptung: gründliche Literaturrecherche (Volltexte).
- 06.11. ~04:58 – **Zwischenstand β 2,5 (16/20):** 3 richtig (β 5,2: 6, eigen: 5 auf denselben 16); verliert zwei Aufgaben, die
  eigen UND β 5,2 lösen (Limit statt Abgabe bei ~9k), 1 falsche Abgabe. → **K5 (≥ 8 richtig) nicht mehr erreichbar – These bei
  β 2,5 in diesem Lauf NICHT nachgestellt.** Wichtigere Lehre: Aufgaben, die um 9k Tokens fertig werden, kippen bei 12k-Budget
  zufällig – **20 Aufgaben × 1 Lauf sind für die Dosis-Kurve zu verrauscht** (auch 8 gegen 5 bei β 5,2 kann Glück sein).
- 06.11. ~05:00 – **Schlachtplan für den Tag (Nutzer: „Retesten, optimieren, Break-even-Punkt finden“; Push erst, wenn etwas
  beweisfähig ist):**
  1. **Retest-Design:** 60 Übungsaufgaben (leicht60) × 2 Seeds je Variante, gepaart; eigen braucht den zweiten Seed ebenfalls.
     Kennzahlen K1–K5 plus Weichen-Statistik; „richtig“ allein ist zu verrauscht.
  2. **Dosis-Gitter um den Gipfel:** β 0 / 2,5 / 4 / 5,2 / 7 (nur Schicht 15). Tagsüber ohne Nachtkette mit 8–12 Slots
     (~20 min je Lauf).
  3. **Geschärfter Melder** (Argon: C_off aus „Denken vor τy“ + „Antwortteil“ weißen): bauen, Selektivität messen (Ziel deutlich
     über 2,7×), dann 2 Dosen.
  4. **Break-even mit MIT:** beste Variante auf die 40 Testaufgaben (32k, vLLM-Stil), gepaart gegen eigen (15/40) und MIT (22/40);
     Ziel ≥ 22/40. Danach 41–80 (Meilenstein-Regel). Break-even der Dosis = Gipfel der Kurve „richtig“ (mehr Abgaben gegen mehr
     falsche Abgaben, A·T maximal).
  5. **Absicherung:** Trendtest/Schonfrist auf den Testläufen; Q5_K_M-Robustheit; IFEval für das Kopplungs-Modell.
  6. **Offen (Forschung):** Stufe B, Zündort-Suche (Patching), klar¹ gegen klar² (Richtig-Sonde), Schwierigkeits-Sonde,
     Literatur-Volltexte (Thinking Past the Answer u. a.), Morgengrauen mit MIT-Eingriff, Einklang-Messung.
  7. **Push (GitHub/Hugging Face):** erst wenn 4. trägt; vorher Geheimnis-Scan (Zugangsdaten, Pfade) und Lizenzen.
- 06.11. ~05:10 – **Tag-Programm (Nutzer schläft; Laptop bis ~10:00, dann Energiesparmodus) – VORAB FESTGELEGT vor allen
  Gitter-Ergebnissen:**
  · v3g/v3h pausiert (nachholen: `bash kette_v3g.sh`, danach `bash kette_v3h.sh`); IFEval-Basis läuft zu Ende,
    nachsicherung_drive.sh sichert danach automatisch.
  · **Gitter** (kette_tag1.sh): 60 Übungsaufgaben × 2 Seeds, 12k, vLLM-Stil; eigen Seed 1 (Seed 0 vorhanden),
    Kopplung β 5,2 / 4 / 7 (nur Schicht 15). 6 Slots solange IFEval läuft, sonst 12.
  · **Geschärfter Melder** (37_melder_schaerfen.py, Argons C_off): Kandidat „argon“ (C_off⁻¹ k_roh) oder „lda“
    (C_off⁻¹ μ_Schleife); gewählt wird der mit der besseren Trennung auf der zurückgehaltenen Hälfte – nur wenn besser als
    roh. Dann Kopplung mit geschärftem Melder (kw) × 2 Seeds.
  · **Auswahlregel** (38_tag_auswahl.py waehlen): Punktzahl = richtig über 2 Seeds × 60 Aufgaben; Gleichstand → weniger
    falsche Abgaben → weniger Flur; nur Varianten, die eigen übertreffen. **Genau EINE** gewählte Variante geht auf die
    40 MATH-500-Testaufgaben (32k, vLLM-Stil, 12 Slots), gepaart gegen eigen-vL (15/40) und MIT (22/40) =
    **Break-even-Test**. Keine Auswahl nach Testergebnissen.
  · Spätestens 09:30: Sicherung.
- 06.11. ~05:15 – **Geschärfter Melder gebaut** (37_melder_schaerfen.py; Daten: 6 fertige + 4 Schleifen-Transkripte von eigen auf
  Übungsaufgaben, Schicht 15, Hälften A/B). Pegel auf der zurückgehaltenen Hälfte B (Schleife / Denken sonst / vor τy / Antwortteil):
  roh 0,206 / 0,071 / 0,042 / 0,052 → Trennung 3,9 · argon 0,159 / 0,027 / 0,004 / 0,010 → 15,5 · **lda 0,144 / 0,032 / 0,006 / 0,0045
  → Trennung 24,2** (vorab festgelegte Wahl: lda). Gleiche Norm wie roh (0,31), keine Ausreißer (max 0,81 gegen 0,66; Median
  0,04 gegen 0,09). → Der Melder schweigt vor der Lösung und im Antwortteil fast völlig.
  **Kopplung kw75:** geschärfter Melder, β 7,5 (Schleifen-Schub im Mittel wie β 5,2 roh: 7,5 × 0,144 ≈ 5,2 × 0,206), vor τy
  5×, im Antwortteil 8× kleiner. Läuft nach dem Gitter × 2 Seeds (kette_tag2.sh), nimmt an der Auswahl teil.
- 06.11. ~05:25 – **Durchsatz-Problem und Umordnung:** Mit IFEval (12 Slots) und dem CPU-Mechanismustest gleichzeitig erzeugte
  der Nebenserver nur ~15 Tokens/s je Slot (GPU 38 %; Ursache: CPU-Konkurrenz – llama.cpp-Sampling über 248k Vokabeln braucht
  CPU). CPU-Test gestoppt (später schonend nachholen) → ~23 Tokens/s. Volles Gitter wäre nicht vor 10:00 fertig →
  **kette_tag1b.sh** löst kette_tag1.sh ab: eigen Seed 1 läuft zu Ende, dann **kw75 × 2 → β 5,2 × 2 → β 4 × 2 (nur vor 07:45)**,
  β 7 gestrichen. Wächter paket/wecker_tag.sh (Meilenstein / Hänger 25 min / Herzschlag 40 min).
- 06.11. ~05:40 – **FUCHSBAU, erster Mechanismus-Befund** (39_melder_weichen.py, ergebnisse/melder_weichen_20.json; 20 leichte
  Übungsaufgaben, Läufe mit Lösung im Denken; Melder-Pegel an Schicht 15 an jeder Weiche nach τy, Mittel der letzten 4 Tokens):
  | Pegel (roh) an Weiche | eigen (13 Läufe; 5 Ende / 589 Warte / 5.052 Weiter) | Kopplung β 5,2 (9 Läufe; 8 / 192 / 2.491) |
  | Ende                  | 0,045                                                | **0,212**                                 |
  | Warte                 | 0,119                                                | 0,078                                     |
  | Weiter                | 0,083                                                | 0,066                                     |
  | AUC Ende gegen Rest   | **0,33** (geschärfter Melder 0,38)                   | **0,79** (geschärfter Melder 0,76)        |
  | AUC Warte gegen Weiter| 0,61                                                 | 0,51                                      |
  Pegel-Verlauf über die Weichen (eigen): 0,052 → 0,067 → 0,079 → 0,100 → 0,218 (**wächst ×4**); Kopplung: flach ~0,06.
  → **Umkonditionierung sichtbar:** Ohne Kopplung führt hoher Melder-Pegel (Schleife/Zweifel) zu „Warte“, abgegeben wird bei
    niedrigem Pegel. Mit Kopplung wird GENAU bei hohem Pegel abgegeben – derselbe Reiz, andere Antwort (Bild des Nutzers:
    Pawlow, „WSP = Umkonditionieren“; „Die Hand wird innerlich“). Der Auslöser wächst ohne Kopplung mit der Zeit (Argons A(t)).
  → Vorsicht: wenige Abgaben (5 bzw. 8); Weichen innerhalb eines Laufs nicht unabhängig. Grobe Schätzung AUC-Differenz
    z ≈ 2,8. Konservativ (ein Wert je Lauf, Vorzeichentest) folgt auf den 60 × 2-Läufen (Skript erweitert).
- 06.11. ~05:45 – **Planänderung VOR allen Kandidaten-Ergebnissen (Zeit):** IFEval-Basis (soll laut Nutzer parallel laufen) ist
  erst bei 51/120 (Basis hängt oft in Schleifen) und belegt die GPU bis ~07:15; eigen Seed 1 erst 16/60 nach 36 min.
  Neu: kette_tag1c.sh (Seed 0 zuerst für kw75 und β 5,2, dann Seed 1; kein neuer Übungslauf ab 08:40; β 4 nur vor 07:45)
  und kette_tag2b.sh (Auswahl mit beiden Seeds; fehlen sie → **Rückfall: Auswahl nur auf Seed 0**, gepaart gegen eigen Seed 0;
  Testlauf nur bei Start vor 09:00, hartes Ende 09:40, danach Sicherung; Notfall-Sicherung 09:20, falls das Gitter hängt).
- 06.11. ~05:50 – **Form der Abgabe-Kurve auf den 20 Übungsaufgaben** (36_hazard_trend.py, ergebnisse/hazard_trend_kopplung20.txt;
  Abgaben je Weichen-Bereich 1–20 / 21–100 / 101–300 / 301–600 / 601+): eigen [0, 0, 2, 3, 0] (p = 0,15) · **β 5,2 [2, 0, 4, 1, 1]**
  (keine Schonfrist: 2 Abgaben in den ersten 20 Weichen; flach, p = 0,79) · **β 2,5 [0, 1, 0, 5, 1]** (Schonfrist + später Anstieg,
  MIT-ähnliche Form, p = 0,11, aber zu wenige Abgaben) · β 10 [0, 1, 1, 0, 1].
  → Passt zu Argons Mechanismus: roher Melder × großes β feuert zu früh (keine Schonfrist), kleines β hat die richtige Form,
    aber zu wenig Kraft. **Vorab-Vorhersage für kw75** (geschärfter Melder, Schleifen-Schub wie β 5,2): Schonfrist wie β 2,5
    UND Abgabe-Zahl wie β 5,2 – also die MIT-Form. Prüfung auf den 60-Aufgaben-Läufen.
- 06.11. ~05:57 – **Feinschliff Zeitplan/Regel (vor Kandidaten-Ergebnissen):** kette_tag1d.sh wartet vor jedem Lauf bis zu 35 min
  auf das IFEval-Ende (ein Lauf behält seine Slot-Zahl; 12 Slots ohne IFEval ≈ 4× schneller als 6 mit). Auswahlregel:
  verglichen wird nur auf Seeds, die für ALLE Kandidaten vorliegen (sonst Rückfall auf Seed 0) – keine Variante fällt
  bloß aus Zeitgründen heraus. Stand 05:54: eigen Seed 1 27/60, IFEval-Basis 60/120.
- 06.11. ~06:40 – **Zeitplan, 5. Fassung (vor Kandidaten-Ergebnissen):** IFEval-Basis langsamer als gedacht (81/120 um 06:35,
  Ende ~07:50). kette_tag1e.sh: nach eigen Seed 1 auf das IFEval-Ende warten (spätestens 08:15), dann **kw75 und β 5,2 (Seed 0)
  gleichzeitig** auf zwei Nebenservern (8096/8097, je 12 Slots; ohne IFEval passen beide in 8 GB). Seed-1-Paar nur bei Start
  vor 07:55. Auswahl dann nach der Regel „nur gemeinsame Seeds“ (vermutlich Seed 0), danach Testlauf + Sicherung (kette_tag2b).
- 06.11. 06:49 – **eigen Seed 1** (60 Übungsaufgaben, 12k): **20/60 richtig (33 %)**, 18 abgegeben, Denken zu 18, Ø 10.681 Tokens.
  eigen Seed 0 (entschluss-uebung-eigen): 18/60 richtig, 19 abgegeben. → Vergleichsbasis eigen: 38/120 (32 %).
- 06.11. 07:35 – **IFEval vollständig** (120 Prompts, Anweisungen befolgen; ganz richtig / Anweisungen erfüllt / Schleife-Limit / Ø Tokens):
  **Basis 15,0 % / 12,8 % / 80,8 % / 11.948** · eigen 61,7 % / 69,7 % / 6,7 % / 5.348 · MIT 72,5 % / 77,4 % / 2,5 % / 3.753.
  → **Beide Eingriffe verbessern das Befolgen von Anweisungen massiv** (die Basis hängt zu 81 % in Schleifen); kein Schaden durch
    unsere Reparatur, MIT bleibt vorn. Abgleich: Basis bei uns 15,0 % gegen 20,8 % im MIT-Archiv auf denselben Prompts (z = −2,86)
    – Pipeline-Unterschied llama.cpp/vLLM möglich, offen.
- 06.11. 07:35 – **Seed-0-Paar gestartet:** kw75 (8096) und β 5,2 (8097) parallel, je 12 Slots, ~22 Tokens/s je Slot, GPU 52 %.
  Seed-1-Paar entfällt (Start nach 07:55) → Auswahl auf Seed 0 (Regel „gemeinsame Seeds“).
- 06.11. ~07:48 – **Fuchsbau-Vergleichsbasis auf allen 60 Übungsaufgaben** (eigen Seed 0; 44 Läufe mit τy; 18 Ende / 2.419 Warte /
  18.922 Weiter; ergebnisse/melder_weichen_eigen60.json): Pegel roh Ende 0,067 · Warte 0,119 · Weiter 0,082.
  **AUC Ende gegen Rest 0,42** (lda 0,44); je Lauf: Ende-Pegel über dem Median in 11/18 (p = 0,24) → ohne Kopplung hängt die
  Abgabe NICHT am Melder. **AUC Warte gegen Weiter 0,63** (robust: hoher Pegel → „Warte“). **Pegel-Verlauf über die Weichen
  0,049 → 0,057 → 0,073 → 0,099 → 0,166 (×3,4; lda ×6,4)** – der Erdrutsch wächst, auf größerer Datenbasis bestätigt.
  → Messlatte für kw75 / β 5,2 (Seed 0, gleiche Aufgaben): AUC Ende deutlich über 0,5 und Vorzeichentest je Lauf signifikant.
  · IFEval-Abgleich mit dem MIT-Archiv (gleiche 120 Prompts): MIT-Eingriff bei uns 72,5 % gegen 60,0 % im Archiv (z = +5,3), Basis 15,0 % gegen 20,8 % (z = −2,9) → deutlicher Pipeline-Unterschied (llama.cpp gegen vLLM, Vorlage/Sampling); Vergleiche nur innerhalb unserer Pipeline. IFEval-Kette 07:57 fertig, inkl. Sicherung + Drive.
- 06.11. 08:29 – **ERGEBNIS Seed 0 (60 Übungsaufgaben, 12k, gepaart gegen eigen Seed 0):**
  | Variante | richtig | abgegeben (falsch) | „Flur“ | Lösung im Denken |
  | eigen    | 18 (30 %) | 19 (1)  | 4  | 44 |
  | β 5,2 (roher Melder) | 29 (48 %) | 29 (1) | 21 | 34 |
  | **kw75 (geschärfter Melder)** | **35 (58 %)** | 39 (4) | 10 | 40 |
  **kw75 gegen eigen 19:2, McNemar p = 0,0002**; β 5,2 gegen eigen 14:3, p = 0,013; kw75 gegen β 5,2 10:4, p = 0,18.
  → Der geschärfte Melder (Argons C_off, LDA-Variante) **fast verdoppelt die richtigen Antworten** und halbiert gegenüber dem
    rohen Melder das Weiterrechnen im Flur (10 statt 21); frühe Lösungen bleiben weitgehend erhalten (40 gegen 44).
    Nur ein Seed; leichte Übungsaufgaben.
- 06.11. 08:30 – **Fehler (meiner):** kette_tag2b brach die Auswahl mit einem Programmierfehler ab (NameError in 38_tag_auswahl.py
  nach dem Umbau um 05:55 – Parameter hieß „_“). Behoben; Regel unverändert angewandt: gemeinsame Seeds → Seed 0 →
  **GEWÄHLT kw75**. Testlauf auf den 40 MATH-500-Aufgaben 08:32 nachgeholt (kette_tag3.sh, hartes Ende 09:40, danach Sicherung).
  · 08:43 Mechanismustest kw75 pausiert (Testlauf hat Vorrang vor dem harten Ende 09:40); nachholen: 39_melder_weichen.py --laeufe kw75=… (siehe 08:31).
- 06.11. 09:22 – **Testlauf kw75, Zwischenstand 30/40 MATH-500-Aufgaben (gepaart, nur fertige Aufgaben):** kw75 16/30 · eigen-vL
  11/30 (6:1, p = 0,125) · **MIT 15/30 (2:1)** → auf diesen 30 Aufgaben gleichauf mit dem MIT. Die restlichen 10 sind die langen
  (MIT löst davon 7, eigen 4). Hartes Ende von 09:40 auf 09:52 verlegt (kette_tag4.sh), weil Abschneiden laufende Aufgaben
  unfair als falsch werten würde; Wertung danach nur auf fertigen Aufgaben, gepaart. Kurze Sicherung danach (Vollsicherung 08:41).
- 06.11. 09:40 – **BREAK-EVEN MIT DEM MIT: kw75 auf den 40 MATH-500-Testaufgaben (32k, vLLM-Stil, vollständig) 22/40 = 55,0 %**
  (ergebnisse/tag2-test40-kw75). Gepaart: gegen eigen-vL 22 gegen 15 (9:2, McNemar p = 0,065), **gegen MIT 22 gegen 22 (2:2,
  p = 1,0)**; Basis 4/40. Denken geschlossen 40/40, abgegeben 28 (9 falsch), **„Flur“ 12** (Denken zu, Antwortteil bis 32k), Ø 18.716
  Tokens. Läufe mit Lösung im Denken 13 – alle 13 abgegeben (MIT 19/21, eigen 12/20); Weichen bis zur Abgabe Median 516
  (MIT 797, eigen 924). Abgabe-Kurve [0, 1, 2, 5, 5] auf [260, 995, 2.256, 2.269, 2.526] Weichen: Schonfrist + Anstieg,
  Trend p = 0,14 (MIT 0,012, eigen 0,30).
  → **Meilenstein-Bedingung „eigene Reparatur erreicht das MIT-Niveau (55 % auf unseren 40 Aufgaben)“ ERFÜLLT** – mit eigenem
    Verfahren (eigene Richtung, eigene Spalten, eigene Entschluss-Achse, geschärfter eigener Melder; keine MIT-Richtung),
    Auswahl vorab festgelegt und nur auf Übungsdaten, Testmenge genau einmal benutzt.
  → **Noch offen:** Bestätigung auf den Aufgaben 41–80 (Meilenstein-Regel: 80 Aufgaben; v3h pausiert – nachholen für eigen-vL,
    MIT und jetzt kw75); zweiter Seed; „über dem MIT“ ist es noch nicht (Gleichstand).
  → **Nächster Hebel für „über dem MIT“:** die 12 „Flur“-Läufe (Denken geschlossen, Antwort nicht fertig) – z. B. Melder auch
    im Antwortteil schweigen lassen ist schon so; Ziel: Abschluss der ANTWORT (Text-Ende-Schub wie der MIT-Rest, Argon 04:30),
    oder zweite Bedingung „Lösung steht“ (Richtig-Sonde).
- 06.11. ~10:30 – **Bestätigung 41–80 gestartet (Nutzer: „Ja, 41–80 starten“)** – kette_bestaetigung.sh: Phase 1 kw75 + MIT parallel
  (je 6 Slots), Phase 2 eigen-vL (12 Slots); 32k, vLLM-Stil; Urteil mit 40_urteil80.py (vorher trocken getestet).
  **VORAB FESTGELEGTE Lesart auf 80 Aufgaben (gepaart):** geknackt = kw75 > MIT und McNemar p < 0,05 · MIT-Niveau erreicht =
  kw75 ≥ MIT − 2 und MIT nicht signifikant besser · sonst nicht erreicht. Stand Teil 1 (1–40): kw75 22, MIT 22, eigen 15.
- 06.11. 11:05 – **FUCHSBAU BEWIESEN (Übungsdaten, 1 Seed): Die Kopplung polt um, was der Schleifen-Melder auslöst**
  (39_melder_weichen.py, ergebnisse/melder_weichen_kw75_60.json; kw75 Seed 0, 60 Aufgaben, 40 Läufe mit τy, 35 Ende-Weichen):
  | | eigen Seed 0 (60) | kw75 Seed 0 (60) |
  | Pegel (roh) an Ende / Warte / Weiter | 0,067 / 0,119 / 0,082 | **0,186** / 0,105 / 0,073 |
  | AUC Ende gegen Rest | 0,42 | **0,74** (lda 0,73) |
  | je Lauf: Ende-Pegel über dem Lauf-Median | 11/18, p = 0,24 | **28/33, p = 0,00003** (lda 24/33, p = 0,007) |
  | AUC Warte gegen Weiter | 0,63 | 0,62 |
  → Ohne Kopplung ist die Abgabe vom Melder unabhängig; mit Kopplung geschieht sie GENAU dann, wenn der Melder hoch steht –
    konservativ geprüft (ein Wert je Lauf). Der Melder misst weiter Zweifel/Schleife (Warte gegen Weiter unverändert 0,62),
    nur die Antwort darauf ist umkonditioniert: „Wiederholung ERGO gib ab“, Pawlow im Gewicht.
- 06.11. 11:20 – 40_urteil80.py: Urteil kw75 gegen MIT braucht nur diese beiden (eigen = Vergleichsbasis, darf später fertig werden); sofort mit Teildaten getestet (61 Aufgaben: kw75 36, MIT 36, 2:2). Lesart unverändert.
- 06.11. ~11:30 – **Name: kw75 heißt jetzt ERGORE (ERGO-REflex, Name vom Nutzer).** Vergleich ERGORE gegen MIT (Bau, Verhalten, offene Punkte, Herkunft der Ideen) als Entwurf: paket/ERGORE_VERGLEICH.md – wird nach dem 80-Aufgaben-Urteil ergänzt. Wichtig: Auch das MIT ist ein Reflex (implizit); der Unterschied liegt im Wie (getrennter, geschärfter Melder + ausdrückliche Wirkung).
- 06.11. ~11:40 – **Landkarte der „45 %“ (Nutzer: „55 % + 45 %“; Testaufgaben 1–40, nicht gelöste Aufgaben, „gefunden“ = richtige
  Lösung taucht irgendwo im Text auf):**
  | | nicht gelöst | gefunden, aber verloren | nie gefunden | davon falsch abgegeben / Flur / Denken nie zu |
  | eigen  | 25 | **10** | 15 | 1 / 9 / 15 |
  | MIT    | 18 | 3 | 15 | 6 / 5 / 7 |
  | ERGORE | 18 | 4 | 14 | 9 / 9 / 0 |
  Beide (ERGORE und MIT) scheitern an denselben 16 Aufgaben; nur in 2 davon taucht die Lösung bei irgendeinem Modell auf.
  → Der Abschluss-Hebel (ERGO) ist fast ausgeschöpft: eigen verlor 10 gefundene Lösungen, ERGORE nur noch 4 (Obergrenze mit
    Flur-Reflex/wahrem Zünder ~26/40 = 65 %). Der große Rest (~35 %) ist **nie gefunden** = Fähigkeitsgrenze des 0.8B → kein
    WSP-Abschlussproblem, sondern Wissen/Rechnen (Phase 2: größere Modelle, Werkzeuge) und **Ehrlichkeit**: ERGORE gibt in
    7 nie gefundenen Fällen trotzdem eine (falsche) Antwort ab (MIT 5) – für das Nutzerziel „weniger Halluzination“ ein Minus;
    ehrliches „weiß ich nicht“ zählt bei MATH genauso falsch, ist aber für Nutzer besser (Morgengrauen/Harnisch-Idee).
- 06.11. ~11:50 – **Wahrheitsspur im Text (41_wahrheitsspur.py, ergebnisse/wahrheitsspur.txt; Nutzer: „Das Modell zuckt, aber das Ergebnis
  kann nur falsch sein, weil es keine Hinweise auf eine Wahrheit gibt“):** 160 Abgaben (144 richtig, 16 falsch) aus Test- und
  Übungsläufen. Text-Merkmale trennen nur schwach (AUC 0,57–0,66). Einzelbefunde: **MIT-Test: alle 4 falschen Abgaben ohne
  einen einzigen Kandidaten im Denken** (richtige im Mittel 6,7; AUC 0,93) – „aus dem Nichts“ = keine Wahrheitsspur;
  **ERGORE-Test: falsche Abgaben mit springenden Kandidaten** (2,5 verschiedene gegen 1,3). Regel „nur abgeben, was zweimal
  im Denken stand“ ist zu grob: behält 37/144 richtige, lässt 2/16 falsche durch.
  → Text allein reicht nicht. **Material für einen inneren Wahrheitsmelder** (Sonde wie Zhang et al. 2025, arXiv 2504.05419):
    1.126 Kandidaten-Stellen in 152 Übungsläufen (425 richtig, 701 falsch), davon 68 Läufe mit richtigen UND falschen
    Kandidaten (gepaartes Training: gleiche Aufgabe, gleicher Lauf). Geplant nach der Bestätigung (GPU frei).
- 06.11. ~11:55 – **Innerer Wahrheitsmelder – VORAB FESTGELEGT** (Nutzer: „Ja, danach bauen“; „Er darf keine richtigen Antworten
  beeinflussen und muss durch unsere bisherige Filter- und Messstruktur gehen“; „Was wir wollen ist ‚sehen, dass das Modell das
  hier nicht sicher weiß‘ und daraus ableiten können“). 42_wahrheitsmelder.py (trocken getestet), kette_wahrheit.sh (nach der
  Bestätigung). **Nur Übungsdaten** (eigen s0/s1, ERGORE s0, β 5,2 s0); Lesemodell eigen-vL; Kandidaten im Denken UND im
  Antwortteil (Endantwort markiert); Schichten 8/11/13/15/17/19/21/23; L2-Sonde, 5-fach Kreuzvalidierung nach Aufgabe getrennt.
  **Schwelle „unsicher“ = 5 %-Quantil der richtigen Kandidaten im Trainingsteil** (höchstens ~5 % Fehlalarm bei richtigen).
  **Kriterien (beste Schicht nach zurückgehaltener AUC):** brauchbar = AUC ≥ 0,75 UND Fehlalarm bei richtigen ≤ 10 % UND
  ≥ 40 % der falschen Kandidaten erkannt; stark = AUC ≥ 0,85 UND ≥ 60 % erkannt. Nur wenn brauchbar: Sonde einfrieren (alle
  Übungsdaten, beste Schicht) und **genau einmal** auf die Endantworten der Testläufe (ERGORE, MIT) anwenden.
  Vorbehalt: Wahl der besten aus 8 Schichten auf denselben Falten ist leicht optimistisch.
- 06.11. ~12:00 – **Idee Nutzer „Erbschafts-Test“** („Haben die anderen Modelle das ‚Denk … ich verhaspel mich, komm zum Schluss,
  Flurfunkquatsch‘ einfach mit gelernt?“). Richtung geprüft: Laut Qwen3 Technical Report (arXiv 2505.09388) entstehen die kleinen
  Modelle „by leveraging the knowledge from the flagship models“ – Wissen fließt von GROSS nach KLEIN. Das 0.8B hat seine Denk-
  gewohnheiten also vermutlich von den großen Lehrern geerbt (für Qwen3.5 nicht eigens geprüft). Derselbe Bericht beschreibt den
  „thinking budget mechanism“ – unser Klingel-Satz ist also eine antrainierte Reaktion (Konditionierung, Bild des Nutzers).
  → **Phase-2-Befundaufnahme als Erbschafts-Test:** am großen Modell dieselben Messgeräte: gefunden gegen abgegeben (τy),
    „Warte“-Rate vor/nach τy, Weichen-Kurve (flach/steigend), Flur-Quote, Schleifen am Budget-Limit. Gleiche Muster (schwächer)
    → geerbte Gewohnheit, ERGORE vermutlich übertragbar; keine Muster → Schwerpunkt Phase 2 auf Deutsch/Ehrlichkeit.
- 06.11. 12:06 – **MEILENSTEIN BESTÄTIGT AUF 80 AUFGABEN (vorab festgelegte Lesart): MIT-NIVEAU ERREICHT.**
  ERGORE 43/80 = 53,8 % (95 %-Wilson 43–64 %) · MIT 43/80 = 53,8 % · gepaart 4:4, McNemar p = 1,0 (40_urteil80.py).
  Teil 2 (41–80): ERGORE 21/40, Abgabe 62,5 %, Denken zu 95 %, Ø 18.397 Tokens · MIT 21/40, Abgabe 57,5 %, Denken zu 75 %,
  Ø 20.701 Tokens. Über beide Teile braucht ERGORE ~13 % weniger Tokens bei gleicher Trefferzahl.
  → Meilenstein-Regel des Nutzers („eigene Reparatur erreicht das MIT-Niveau, bestätigt auf 80 Aufgaben“) erfüllt – mit eigenem
    Verfahren (ERGORE), ohne MIT-Richtung. Nächster Schritt in der Reihenfolge des Nutzers: „dann knacken und Fuchsbau rein …
    später die großen Modelle“ → über das MIT (Wahrheitsmelder als wahrer Zünder, Flur-Reflex), zweiter Seed; dann Phase 2.
  Phase 2 der Bestätigungskette (eigen-vL auf 41–80, Vergleichsbasis) läuft; danach Wahrheitsmelder (kette_wahrheit.sh).
- 06.11. ~12:15 – **Korrektur „weniger Tokens“ (Prüfung Aufgabe für Aufgabe, 80 Aufgaben):** ERGORE gesamt 1,48 gegen MIT 1,72 Mio.
  Tokens (−14 %), weniger bei 44, mehr bei 28 Aufgaben (Vorzeichentest p = 0,08 – nur Trend). **Bei den 39 von beiden gelösten
  Aufgaben gleich: 13.532 gegen 13.492 Tokens bis zur richtigen Antwort** (ERGORE schneller bei 18/39, p = 0,75).
  → Die Ersparnis stammt aus ungelösten Aufgaben: ERGORE gibt früher auf, oft mit falscher Antwort (falsches Zucken); MIT kreist
    dort öfter bis zum Limit. Nicht „schneller zur richtigen Antwort“. Mit Wahrheitsmelder wäre „früh aufhören UND ehrlich sein“
    möglich – das wäre dann ein echter Gewinn für das Alltagsziel (weniger Babysitting, weniger Halluzination).
- 06.11. ~12:40 – **Nach Schwierigkeitsstufe (MATH-Stufe 1–5, Testaufgaben 1–80; Nutzer: „Ist die Stufe entscheidend?“):**
  Stufe 1 (8): ERGORE 7 · MIT 6 · Basis 0/4 | Stufe 2 (22): 14 · 15 · 1/9 | Stufe 3 (15): 9 · 9 · 2/11 | Stufe 4 (17): 6 · 7 · 1/6 |
  Stufe 5 (18): 7 · 6 · 0/10. → Erfolg fällt mit der Stufe (~85 % → ~38 %), ERGORE und MIT liegen auf JEDER Stufe gleichauf (±1).
  Die Basis scheitert selbst auf Stufe 1 (0/4) – Verhaspeln ist keine Frage der Schwierigkeit; auf Stufe 4–5 dominiert „nie gefunden“.
  Kleine Zahlen je Stufe (8–22 Aufgaben).
- 06.11. ~12:50 – **Phase-2-Messachse „Denk-Stufe“ (Nutzer: viele Modelle haben Stufen off/low/mid/high/xhigh/max/ultra; manche
  lassen sich nicht abschalten).** Geprüft am lokalen Qwen3.6-35B-A3B (Modellkarte + chat_template.jinja): nur `enable_thinking`
  (Standard an) und neu `preserve_thinking` (Denken früherer Nachrichten behalten, für Agenten); **keine Stufen low/mid/high** in
  den offenen Gewichten; kein /think-/nothink-Schalter mehr. Empfehlung der Karte: Denkmodus allgemein temp 1,0 / top_p 0,95 /
  top_k 20 / presence 1,5; präzises Programmieren temp 0,6 / presence 0; ohne Denken temp 0,7 / top_p 0,8; Kontext ≥ 128k.
  Plan: je Modell alle verfügbaren Schalter messen; wo keine Stufen existieren, Budget-Stufen 4k/8k/16k/32k; in jeder Zelle die
  Messgeräte dieser Nacht (richtig, Tokens, gefunden/abgegeben, Warte-Rate, Flur, Schleifen am Limit, Weichen-Kurve). Vorher
  entscheiden: Temperatur 0,6 (vergleichbar mit MIT-Protokoll) und/oder 1,0 (Herstellerempfehlung, Alltag).
  Erwartung: hohe Stufe/großes Budget → Reflex wichtiger; niedrige Stufe → Wahrheitsmelder wichtiger; Immer-Denker → nur Reflex.
- 06.11. ~13:00 – **Empfindlichkeitstest Temperatur – VORAB FESTGELEGT** (Nutzer: „schauen, was mit unseren Erkenntnissen wirklich
  eine deutliche Änderung gibt, wenn man den Parameter ändert oder nicht“). kette_temperatur.sh (nach dem Wahrheitsmelder):
  eigen und ERGORE bei **Temperatur 1,0** (Qwen3.6-Empfehlung), sonst alles gleich (60 Übungsaufgaben, Seed 0, 12k, vLLM-Stil);
  Vergleich mit 0,6 (43_temperatur_vergleich.py, trocken getestet; 03_eval.py hat dafür die Option --temperatur, Standard 0,6
  unverändert). **„Deutliche Änderung“, wenn der gepaarte Gewinn ERGORE − eigen bei 1,0 um ≥ 8 Aufgaben von +17 (bei 0,6)
  abweicht ODER die Signifikanz kippt.** Zusätzlich berichtet: Abgaben, falsche Abgaben, Flur, nie geschlossenes Denken, Tokens.
- 06.11. – Modellbau (Nutzerfrage „Ist das 0.8B dense?“): **ja, dicht** (keine Experten): 24 Schichten (18 lineare Attention /
  Gated-DeltaNet, 6 volle Attention, jede 4.), hidden 1.024, MLP 3.584. Qwen3.6-35B-A3B: **MoE**, 40 Schichten, hidden 2.048,
  256 Experten, 8 aktiv, je 512 + geteilter Experte 512 → ERGORE muss für Phase 2 auf Experten übertragen werden (05m_patch_moe.py).
- 06.11. ~13:05 – **Plan Stufe 2 (Fragen des Nutzers, nach „über MIT“ am 0.8B):**
  **A. Übertragbarkeit auf andere dichte Modelle + Einflussgrößen** (Temperatur, Denk-Stufe/Budget, Anbieter, Trainingsmasse/Größe).
     Hinweis aus dem MIT-Archiv (exp8_math/code/profiles.py, 24.10.2026): MIT prüfte auch **LFM2.5-350M** (andere Bauweise:
     Kurzfaltungen + 6 Attention-Schichten; „gewählt, weil seine Fehler keine Schleifen sind“: antwortet in ~124 Tokens ohne
     Nachdenken; GSM8K 28,0 / MATH-500 11,1) und **Gemma 3 270M IT** (54 % der GSM8K-Antworten ohne \boxed{}; GSM8K 4,1 /
     MATH-500 2,8). → Die „Macke“ ist familien- und trainingsabhängig. Daher je Modell ZUERST Befundaufnahme (welcher Fehler
     dominiert?), erst dann Eingriff. Reihenfolge: gleiche Familie größer (Qwen3.5-2B/4B/9B, dicht) – prüft Größe bei gleicher
     Abstammung; das ERGORE-Rezept wird je Modell neu gemessen (eigene Richtung, Spalten, Achse, Melder) = Test „übertragbar
     ohne Such-Agent“.
  **B. MoE-Zwischenstufe:** kleines MoE (laptoptauglich), am besten mit Denkmodus, um die MoE-Fassung von ERGORE (Melder/Wirkung
     über Experten und Router; 05m_patch_moe.py) zu entwickeln, bevor das 35B drankommt. Kandidaten erst prüfen (Verfügbarkeit,
     Lizenz, Denkmodus); falls kein kleines MoE mit Denkmodus existiert, Mechanik zuerst an einem kleinen MoE ohne Denkmodus üben.
  **C. Vererbung („Learning“):** Hypothese des Nutzers: Modelle hängen über das Training zusammen und nehmen ihre Denk-Macken mit.
     Belegt ist die Richtung groß → klein (Qwen3 Technical Report). Testplan: gleiche Messgeräte an Modellen mit bekannter
     Abstammung – (1) Qwen3.5-Geschwister unterschiedlicher Größe (gleicher Lehrer), (2) ein Modell mit ANDEREM Lehrer auf
     Qwen-Basis, z. B. DeepSeek-R1-Distill-Qwen-1.5B (Basis Qwen, Lehrer DeepSeek-R1): folgen die Macken dem Lehrer oder der
     Basis? Messgrößen: Kognitionswörter-Profil, gefunden/abgegeben, Weichen-Kurve, Flur, Schleifen am Limit.
- 06.11. ~13:15 – **Entscheidungen Nutzer zu Stufe 2:** (A) nach unseren Ergebnissen **spiegeln mit Qwen3.5-4B** (HF Qwen/Qwen3.5-4B,
  erstellt 27.02.2026, 4,66 Mrd. Parameter, BF16 ~9,3 GB; noch nicht lokal – Download erst nach Rückfrage). (B) **kleinstes MoE einer
  Qwen-Familie**: laut HF-API Qwen1.5-MoE-A2.7B (14,3 Mrd. gesamt / 2,7 aktiv, Feb. 2024, KEIN Denkmodus); mit Denkmodus erst
  Qwen3-30B-A3B (30,5 Mrd., Apr. 2025). Vorschlag: Qwen1.5-MoE als Werkbank nur für die MoE-Mechanik (Melder/Wirkung über
  Experten und Router), dann Qwen3-30B-A3B oder direkt Qwen3.6-35B-A3B. (C) Vererbungs-Test heißt **„Ahnenforschung“** (Name Nutzer).
  **Fund:** Qwen veröffentlichte am 27.04.2026 Residual-**SAEs** (Sparse Autoencoder) für Qwen3.5-35B-A3B-Base und Qwen3-30B-A3B-Base
  (Breite 32k/128k, L0 50/100; HF Qwen/SAE-Res-…) – mögliches Werkzeug, um Schleifen-/Zweifel-/Abschluss-Merkmale im großen
  Modell direkt zu finden (für Grundmodelle; Übertragbarkeit auf Denk-Varianten prüfen).
- 06.11. ~13:20 – **Drittes Gegenlesen: DeepSeek („DeepseekFlash4 4.1, High Thinking“, recherche/deepseek/DeepSeek_Feedback_2026-11-06.md).**
  Einordnung: (1) „kausaler Beweis zu stark“ – berechtigt gegenüber Argons Formulierung (bei uns schon 04:35 als überdehnt markiert).
  Die geforderte **Ablation liegt inzwischen vor**: β = 0 gegen β > 0 bei sonst bitgleichem Modell (gleiches α, u_e, Spalten,
  L15/L19) – 60 Übungsaufgaben Seed 0: eigen (β 0) 18 · β 5,2 29 · ERGORE (β 7,5, geschärft) 35 (19:2, p = 0,0002); dazu
  Dosis-Reihe 0/2,5/5,2/10 (20 Aufgaben) und Mechanismus (Abgabe an Melder gekoppelt, 28/33 Läufe, p = 3·10⁻⁵). n = 1 Seed bleibt.
  (2) „Achsen erklären 3–6 % von r⊥“ – richtig; Präzisierung: ERGORE erreicht das MIT-Niveau über eine ANDERE Richtung als der
  MIT-Rest (gleiche Wirkung, andere Geometrie); Träger bei ERGORE = u_e + e⊥ (Ablation), beim MIT = u_MIT (mit r⊥, z. T. K=4-Rauschen).
  (3) Reifikation – berechtigt; „innere Uhr“ ist verworfen/offen, „ERGO-Kante“, „Entschluss-Achse“ sind Arbeitstitel.
  (4) Generalisierung – inzwischen 80 Testaufgaben, zwei Budgets (12k/32k); weiter offen: Seeds, Größen (Qwen3.5-4B geplant), Temperatur (läuft).
  Teil 2: Docs-Widerspruch → **Sprachregelung ab jetzt:** „**kausal belegt** (Intervention/Ablation): Der β-Term verursacht mehr
  Abschlüsse und mehr richtige Antworten und koppelt die Abgabe an den Melder. **Nicht belegt:** dass dies der Mechanismus des
  MIT-Edits oder eine natürliche ‚Entschluss-Achse‘ des Modells ist.“ **r⊥-Definitionen vereinheitlichen:** 21_logit_lens.py
  (gegen u_vL-alle + u_messer3, Rest-Energie ~36 %) vs. 31_ergo_rest.py (gegen u_e allein, ~41 %) – künftig immer angeben, wogegen.
  0.8B → 35B: berechtigt, Engineering-Projekt (BF16 ~70 GB > 64 GB RAM, Shard-weises Patchen, MoE-Experten).
  Fragen: Stufe B (p_exit-Rollouts nach τy, früh/spät) ist **noch nicht gelaufen** (verwandt: Weichen-Statistik, Melder an Weichen);
  Der zweite Rechner läuft (Phase-1-Ketten) – Antwort beim Nutzer.
- 06.11. ~13:35 – Gutachter-Paket für Argon und die KI-Agenten des Nutzers (DeepSeekFlash 4.1, GLM 5.3 Flash; teils Tripod: Fronthirn / Schwitzhirn / neutraler Reflektor): paket/GUTACHTER_PAKET_2026-11-06.md – Stand, Sprachregelung, vier Rollen (Reflektor/Advocatus Diaboli, Statistik, Literatur, MoE-Ingenieur), einheitliches Antwortformat. Ohne Zugangsdaten, Rechnernamen oder Pfade.
- 06.11. ~13:20 – **Viertes Gegenlesen: Poow** (recherche/deepseek/Poow_Antwort_2026-11-06.md). Quellen 6/6 korrekt (u. a. **NEAT**,
  arXiv 2602.02010: Neuron-Based Early Exit – nah an unserem Melder; Manifold Steering 2505.22411: passt zum α=10-Kollaps –
  „vereinbar mit“, nicht „vorhergesagt“).
  **ZIRKULARITÄT (Poows Frage, geprüft – berechtigt):** u_e aus 48 Diagnose-Aufgaben (Überschneidung mit den 60 Übungsaufgaben: 0),
  Messerschneiden-Daten 20 Aufgaben (0) – sauber. ABER **Entschluss-Achse e⊥ und geschärfter Melder wurden aus Läufen auf GENAU
  diesen 60 Aufgaben gebaut**, und auch β und die Auswahl kw75 entstanden dort. → **Das p = 0,0002 der Übungs-Ablation ist teilweise
  zirkulär und überschätzt den Effekt.** Saubere Prüfung = Testaufgaben (keinerlei Berührung mit dem Bau):
  Zwischenstand 76/80: eigen 33/76 (43 %); **ERGORE gegen eigen 12:4 (p = 0,077), MIT gegen eigen 10:2 (p = 0,039)**; ERGORE = MIT.
  → Auf sauberen Aufgaben bringt ERGORE gegenüber eigen etwa +10 Prozentpunkte (Übung: +28) – Effekt real, aber kleiner.
  Meilenstein „ERGORE = MIT“ (nur Testaufgaben) bleibt unberührt. Künftig: Bau-Daten und Prüf-Daten strikt trennen
  (neuer, unberührter Übungssatz für Auswahl/Ablation).
  Folgefrage Poow für später: **Weg-Vergleich** – schließen ERGORE und MIT über dieselben nachgelagerten Neuronen/Logits?
- 06.11. ~13:40 – **Fünftes Gegenlesen: WREN** (Tripod GLM 5.3 Flash / DeepSeek V4.1 Flash / Qwen3.6-35B-A3B; recherche/wren/WREN_Gutachten_2026-11-06.txt;
  Rollen Reflektor, Statistik, Literatur; MoE-Rolle fehlt, Reflektor-Teil im Text abgeschnitten). **Quellen 29/29 per arXiv-API korrekt.**
  **Übernommen:**
  · **Power:** Bei n = 80 sind nur ~10-pp-Unterschiede erkennbar; „über MIT“ um 3–5 pp braucht ~300–870 Aufgaben und ≥ 3–5 Seeds.
  · **Lesart präzisiert:** ERGORE − MIT = **0,0 pp, 95-%-Intervall −6,9 bis +6,9 pp** (4:4, Übereinstimmung 72/80) → „kein messbarer
    Unterschied innerhalb ±7 pp“, nicht „gleich“. Unsere Regel „MIT-Niveau erreicht“ war eine schwache Nicht-Unterlegenheits-Regel.
  · Weichen innerhalb eines Laufs sind abhängig → Trendtest (p = 0,012) zu optimistisch; Cluster-Bootstrap bzw. Frailty-Hazard nachholen.
  · Mehrfachtests: Holm/BH; robust nur Ablation (aber zirkulär, s. 13:20) und Mechanismus (28/33).
  · Token-Ersparnis: Collider-Problem → gepaart geschichtet (beide gelöst / beide falsch) mit Bootstrap auswerten.
  · Wahrheitsmelder: A/B mit Gate an/aus, gepaart; Nicht-Unterlegenheit (unteres KI > −2 pp); identische Antworten auf ohne Gate
    richtigen Aufgaben; FN ≤ 5 %; geschichtet; Kausalität per Intervention prüfen.
  · Fachgebiete (neu ausgewertet, 80 Aufgaben; ERGORE / MIT / eigen): Algebra 16/15/14 · Zählen & Wkt. 1/2/1 · Geometrie 3/3/3 ·
    Interm. Algebra 5/6/1 · Zahlentheorie 4/6/5 · Prealgebra 9/9/7 · Precalculus 5/2/2 → kein klares Fachgebiets-Muster (kleine n).
  **Missverständnisse WRENs (korrigiert):** „4:4 identisch in jeder Aufgabe, verdächtig“ – 4:4 sind die DISKORDANTEN Paare,
  Übereinstimmung 72/80 ist bei schwierigkeitsgetriebenen Aufgaben normal. „Seed-Auswahl post hoc / p-Hacking“ – es wurden keine
  Seeds probiert und verworfen; Testläufe je genau ein Lauf mit Standard-Seed 0; „nur Seed 0“ betraf die Übungs-Auswahl aus Zeitgründen,
  vorab dokumentiert. Zahlenverwechslung „ERGORE 20/12“ – das war eigen. „LDA auf 4 Kontexten“ – die 4 Kontexte sind die MIT-Richtung;
  unser Melder nutzte 10 Transkripte.
  **Literatur, wichtigste Treffer (Abstracts):** 2610.19934 „To Reason but Not to Stop“ (beschnittene LRMs terminieren nicht trotz
  intaktem Erkennen; „commitment“-Richtung per Steering – ERGORE am nächsten); **2605.09502** „Hidden Error Awareness … Diagnostic,
  Not Causal“ und **2605.05715** „Decodable but Not Corrected by Fixed Residual-Stream Linear Steering“ (Fehler sondierbar, aber
  Steuern hilft nicht → Wahrheitsmelder als TOR verwenden, nicht als Schub-Richtung); 2602.08354 „Does Your Reasoning Model Implicitly
  Know When to Stop Thinking?“; 2602.13935 „Statistical Early Stopping“ (Erneuerungsprozess von Unsicherheitswörtern – nah an
  Weichen/Kognitionswörtern); 2504.06514 (Overthinking „ansteckend“ über Destillation) und 2512.20908 (Herkunft in Destillation) für
  die Ahnenforschung; 2406.10881 CoKE (Wissensgrenze, „ich weiß nicht“); Steer2Edit 2602.09870 und ThinkEdit 2503.22048 (Gewichts-
  Edits für Denklänge); REX 2610.25791 (Experten in Qwen3.5-35B-A3B, MoE). WREN fand keine Arbeit mit getrenntem Detektor/Effektor
  im Gewichts-Edit für Denk-Abbruch (nur Abstracts geprüft).
- 06.11. 13:28 – **Bestätigung komplett, saubere Bilanz auf 80 Testaufgaben (keinerlei Berührung mit dem Bau):** eigen 33/80 (41,2 %),
  ERGORE 43/80, MIT 43/80. **ERGORE gegen eigen 14:4, McNemar p = 0,031**; MIT gegen eigen 12:2, p = 0,013; ERGORE gegen MIT 4:4.
  → Antwort auf Poows Zirkularitäts-Frage: Der Kopplungs-Effekt hält außerhalb der Bau-Daten: +12,5 pp (Übung: +28 pp, aufgebläht).
  Vorbehalt: ein Lauf je Modell; dieser Vergleich war nicht als Hauptvergleich vorab festgelegt (Hauptvergleich: ERGORE gegen MIT).
- 06.11. 13:35 – **ERGEBNIS innerer Wahrheitsmelder** (42_wahrheitsmelder.py; ergebnisse/wahrheit_sammlung.npz, _pruefung.json; nur Übungsdaten,
  Kreuzvalidierung nach Aufgabe gruppiert): 183 Läufe, 1.499 Kandidaten-Stellen (566 richtig), 57 Aufgaben, 104 Läufe mit richtigen UND
  falschen Kandidaten; Denken 1.126, Antwortteil 373 (Endantworten 107, davon 7 falsch).
  **Trennschärfe sehr hoch:** AUC 0,906–0,959 über alle Schichten, **beste Schicht 13: AUC 0,959** (Denken 0,956, Antwortteil 0,977);
  gepaart im selben Lauf liegt der richtige Kandidat in **94 %** der 3.788 Paare höher. Grundlinien (gleichstandsfest): Position im
  Lauf AUC 0,58, Endantwort-Kennzeichen 0,59 → kein Positions-Artefakt. → Das Modell „weiß“ innen weitgehend, ob ein Kandidat stimmt
  (passt zu Zhang et al. 2025).
  **Vorab-Kriterium „brauchbar“ NICHT erfüllt:** Mit der vorab festgelegten Kalibrierung (Schwelle = 5-%-Quantil der richtigen im
  Trainingsteil) wurden zurückgehalten **27 % der richtigen Kandidaten fälschlich markiert** (erlaubt ≤ 10 %). Ursache (mein Fehler):
  Schwelle aus den Trainings-Vorhersagen der angepassten Sonde, die dort zu sicher ist.
  **Nachträgliche Analyse, ausdrücklich so markiert:** gleiche 5-%-Vorgabe, Schwelle aber aus inneren zurückgehaltenen Werten
  (verschachtelte Kreuzvalidierung): Schicht 13 **Fehlalarm 5,5 %, falsche erkannt 79 %**; Schicht 8: 4,8 % / 77 %. Endantworten:
  Fehlalarm 1 %, von nur 7 falschen 2 erkannt. → Erfüllt nachträglich „stark“, muss aber auf frischen Daten bestätigt werden.
  Literatur-Warnung (WREN): erkennen ≠ beheben (2605.09502, 2605.05715) → Melder als TOR einsetzen, nicht als Schub-Richtung.
  Nächster Schritt (Vorschlag): Sonde einfrieren (Schicht 13, verschachtelte Schwelle) und genau einmal auf die Endantworten der
  Testläufe (ERGORE 80, MIT 80) anwenden – A/B „Tor an/aus“: verlorene richtige gegen abgefangene falsche Antworten.
- 06.11. ~13:50 – **Wahrheitsmelder auf Testdaten – VORAB FESTGELEGT (vor jedem Blick auf Testdaten; Nutzer: „Ja, nach Temperatur“):**
  Sonde eingefroren (ergebnisse/wahrheitsmelder_eingefroren.npz): Schicht 13, Training auf allen 1.499 Übungs-Kandidaten, Schwelle
  −1,198 = 5-%-Quantil der zurückgehaltenen Werte richtiger Kandidaten (zurückgehaltene AUC 0,959). Lesemodell eigen-vL. Angewendet
  GENAU EINMAL auf die bewertete Endantwort (letztes \boxed im Antwortteil) aller Testläufe ERGORE (1–80) und MIT (1–80); Läufe ohne
  Endantwort werden nicht bewertet (gezählt). Trocken getestet nur an 2 Übungsläufen.
  **Kriterien je Modell:** Hauptkriterium (Nutzer: „darf keine richtigen Antworten beeinflussen“): höchstens 5 % der RICHTIGEN
  Endantworten als „unsicher“ markiert. Nebenkriterium: ≥ 40 % der FALSCHEN Endantworten markiert = brauchbar, ≥ 60 % = stark.
  Keine Schwellen-Änderung nach Sicht der Testdaten.
- 06.11. ~13:55 – **Technischer Notausgang im Melder-Test (vor dem Testlauf, ohne Blick auf Testwerte):** Zählung ohne Sonde:
  Endantworten ERGORE 52 (43 richtig, 9 falsch), MIT 50 (43 richtig, 7 falsch); Länge bis zur Endantwort bis 32.904 Tokens
  (Übungsläufe beim Sammeln ≤ ~12,5k). Damit kein Grafikspeicher-Fehler den Test abbricht: `anwenden` liest einen Lauf, für den der
  Speicher nicht reicht, auf der CPU (fp32) und kennzeichnet ihn ("geraet": "cpu"). Sonde, Schwelle und Lesemodell unverändert.
  Trockentest CPU normal gegen simulierten Speicherfehler: identische Werte (4,085 / 3,413). Auswertung danach mit
  44_melder_urteil.py (nur Zählen, Wilson-Intervalle, beschreibende AUC; keine Schwellen-Änderung).
  **Vorab-Hinweis zur Aussagekraft:** Das Nebenkriterium (≥ 40 % der falschen Endantworten markiert) stützt sich auf nur 9 bzw. 7
  falsche Endantworten; die meisten falschen Läufe haben gar keine Endantwort (Flur oder Limit). Das Hauptkriterium (≤ 5 % der
  richtigen markiert) heißt bei 43 richtigen: höchstens 2 markiert.
  **Schicht 13 liegt vor allen Eingriffen** (ERGORE, eigen und MIT ändern nur Schicht 15/19): Für denselben Text sind die Werte
  bei allen Modellen gleich. Der Melder misst also das Wissen des Basismodells über den Text, nicht eine Eigenschaft des Eingriffs.
- 06.11. ~14:00 – **Wahrer Zünder („Sicherheit ERGO gib jetzt ab“) – VORAB FESTGELEGT, bevor irgendein Sondenwert auf Testdaten
  berechnet ist** (45_wahrer_zuender.py). Regel: Der eingefrorene Melder (Schicht 13) liest die Kandidaten eines Laufs in
  Text-Reihenfolge; beim ERSTEN Kandidaten mit Wert ≥ T_hoch wird abgebrochen und dieser Kandidat abgegeben; sonst bleibt der Lauf,
  wie er war. Nachrechnung auf vorhandenen Läufen exakt (Tor schneidet nur ab). **Laufzeit-Tor, kein reiner Gewichtseingriff.**
  **T_hoch nur auf Übungsdaten** (zurückgehaltene Werte, 5-fach nach Aufgabe; Regel: höchstens 2,5 % der richtig beendeten
  Übungsläufe verloren, dann größter Netto-Gewinn): **T_hoch = 0,375.** Übung (240 Läufe, 102 richtig): gewonnen 38, verloren 1,
  netto +37 (optimistisch, da T dort gewählt). Textregeln ohne Melder: B1 „erster Kandidat“ netto −34; B2 „erster wiederholter
  Kandidat“ netto +18. Kontrolle gemischte Etiketten: AUC 0,496, feuert nie (netto 0).
  **Test (genau einmal, eingefrorene Sonde, T_hoch 0,375):** Kandidaten aller Testläufe ERGORE, MIT, eigen (je 80) mit
  `42 sammeln --schichten 13` lesen; dann `45 test`. **Lesart:**
  (1) Sicherheit je Modell (Nutzer: „darf keine richtigen Antworten beeinflussen“): verloren ≤ 5 % der richtigen (ERGORE/MIT ≤ 2,
  eigen ≤ 1). (2) Hauptvergleich ERGORE+Zünder gegen MIT ohne Tor: mehr richtig und McNemar p < 0,05 = „über MIT (mit
  Laufzeit-Tor)“; mehr richtig ohne Signifikanz = „Tendenz“; sonst „nicht über MIT“. (3) Fairness, immer mitberichtet: MIT+Zünder
  gegen MIT und ERGORE+Zünder gegen MIT+Zünder. Hebt das Tor das MIT ebenso, gilt nur „das Tor hebt beide“.
  (4) Mehrwert des Melders: Netto-Gewinn des Zünders größer als B1, B2 und die Kontrolle mit gemischten Etiketten.
  Erwartung vorab: Bei 32k-Budget gibt es weniger „gefunden, aber verloren“ als bei 12k-Übung → kleinerer Effekt als +37/240.
  Literatur (Volltexte, recherche/volltexte/): Abbruch-Steering rettet nur Fälle mit schon vorhandener Antwort (2610.19934, Anh. E.3);
  Sonden taugen als Tor, nicht als Schub (2605.05715 §6; 2605.09502 §5). Unsere Kombination (Rang-2-Edit mit getrenntem Melder und
  Effektor für Denk-Abbruch) kommt in den drei Arbeiten nicht vor.
- 06.11. 14:33 – **ERGEBNIS Empfindlichkeitstest Temperatur (vorab festgelegte Lesart): DEUTLICHE ÄNDERUNG.** 60 Übungsaufgaben,
  Seed 0, 12k, vLLM-Stil; nur die Temperatur geändert (43_temperatur_vergleich.py):
  | | richtig | abgegeben (EOS) | falsch abgegeben | Flur | Denken nie zu | Ø Tokens | dup8 |
  |---|---|---|---|---|---|---|---|
  | eigen 0,6 | 18 | 19 | 1 | 4 | 37 | 10.577 | 0,155 |
  | ERGORE 0,6 | 35 | 39 | 4 | 10 | 11 | 8.708 | 0,062 |
  | eigen 1,0 | 16 | 15 | 0 | 0 | 45 | 11.242 | 0,001 |
  | ERGORE 1,0 | 15 | 15 | 2 | 15 | 31 | 11.145 | 0,001 |
  Gepaart ERGORE − eigen: bei 0,6 **+17** (19:2, p = 0,0002), bei 1,0 **−1** (2:3, p = 1,0) → Gewinn verschwindet, Signifikanz kippt.
  **Deutung (Hypothese, nicht geprüft):** Bei 1,0 verschwinden die wörtlichen Schleifen (dup8 0,155 → 0,001), das Grundproblem bleibt
  (75 % Limit bei beiden). ERGORE schließt das Denken weiterhin öfter als eigen (29 gegen 15 Läufe), aber ohne fertige Antwort:
  Flur 15 gegen 0. Der Reflex feuert also, gibt aber nichts Brauchbares ab (falsches Zucken in Masse); das Herumwandern
  ersetzt die Schleife. **Vorbehalte:** nur 12k-Budget (bei 1,0 brauchen Läufe länger; 32k nicht geprüft), ein Seed, MIT bei 1,0
  nicht gemessen. **Folge für Phase 2:** Laut der früheren Notiz empfiehlt der Hersteller für Qwen3.6 im Denkmodus Temperatur 1,0
  (vor Phase 2 nachprüfen). Ein Reflex, der nur bei 0,6 trägt, reicht dort nicht. Der Zünder („abgeben, wenn sicher richtig“)
  hängt dagegen nicht an Schleifen und ist der Kandidat, den man bei 1,0 prüfen sollte.
- 06.11. 14:46 – **ERGEBNIS Wahrheitsmelder auf Test-Endantworten (eingefroren, genau einmal angewendet; vorab festgelegte
  Kriterien): Hauptkriterium bei beiden Modellen ERFÜLLT, Nebenkriterium bei beiden „BRAUCHBAR“** (44_melder_urteil.py;
  ergebnisse/wahrheitsmelder_test.json, _urteil.json; kein CPU-Notausgang nötig, auch nicht bei 32k-Läufen).
  | | richtige als „unsicher“ markiert | falsche als „unsicher“ markiert | AUC (beschreibend) |
  |---|---|---|---|
  | ERGORE (52 Endantworten) | 1/43 = 2,3 % [0,4–12,1] | 4/9 = 44 % [19–73] | 0,81 |
  | MIT (50 Endantworten) | 0/43 = 0 % [0–8,2] | 4/7 = 57 % [25–84] | 0,99 |
  | zusammen | 1/86 = 1,2 % [0,2–6,3] | 8/16 = 50 % [28–72] | 0,89 |
  „Tor an“ (markierte Antwort → „Ich weiß es nicht sicher“): ERGORE 42 richtig, 1 richtige verloren, 4 falsche abgefangen,
  5 durchgerutscht; MIT 43 richtig, 0 verloren, 4 abgefangen, 3 durchgerutscht.
  **Vorbehalte:** nur 16 falsche Endantworten (breite Intervalle); die meisten falschen Läufe haben gar keine Endantwort (ERGORE 28,
  MIT 30 ohne Endantwort) und werden vom Melder nicht berührt. Die eine fälschlich markierte richtige Antwort (ERGORE,
  intermediate_algebra/1994, Wert −4,35) steht bei 32.808 Tokens; die Sonde wurde nur an Läufen ≤ ~12,5k gelernt (Längen-Verschiebung
  als mögliche Ursache, nicht geprüft). Durchgerutschte falsche Antworten haben teils hohe Werte (bis 3,4): „sicher falsch“ wie
  in der Literatur (2605.09502: viele falsche Läufe sind hoch konfident).
  **Bedeutung:** Erstmals auf frischen Testdaten bestätigt, dass der Melder richtige Antworten fast nie stört (Bedingung des Nutzers)
  und etwa jede zweite falsche Endantwort erkennt. Als Ehrlichkeits-Tor tauglich; als alleiniger Weg „über MIT“ nicht, weil
  Enthalten keine richtige Antwort hinzufügt.
- 06.11. ~14:52 – **MIT bei Temperatur 0,6 und 1,0 auf den 60 Übungsaufgaben – VORAB FESTGELEGT** (Nutzer: „Mach gerne automatisch
  weiter“; Lücke aus dem Temperatur-Test). kette_mit_temp.sh nach dem Zünder-Einlesen; gleiches Protokoll (Seed 0, 12k, vLLM-Stil),
  MIT-GGUF wie in den Testläufen (Qwen3.5-0.8B-mit-q8_0). Lesart wie beim ERGORE-Temperaturtest (43_temperatur_vergleich.py --name
  MIT): „deutliche Änderung“, wenn der gepaarte Gewinn MIT − eigen bei 1,0 um ≥ 8 Aufgaben vom Gewinn bei 0,6 abweicht ODER die
  Signifikanz kippt. Zusätzlich beschreibend: ERGORE gegen MIT bei 1,0. **Achtung Heimvorteil:** ERGORE wurde auf genau diesen
  60 Aufgaben gebaut (Zirkularität), ein Vergleich ERGORE gegen MIT auf diesen Aufgaben ist daher nicht fair und nur beschreibend.
  Nebennutzen: Die MIT-Läufe bei 0,6 auf Übungsaufgaben erlauben später die Umpolungs-Messung beim MIT auf gleichem Boden.
- 06.11. 15:17 – **ERGEBNIS Wahrer Zünder auf den 80 Testaufgaben (vorab festgelegte Lesart; eingefrorene Sonde, T_hoch 0,375,
  genau einmal angewendet; 45_wahrer_zuender.py → ergebnisse/wahrer_zuender_test.json, logs/45_zuender_test.log):**
  | | ohne Tor | Zünder (gewonnen/verloren) | B1 erster Kandidat | B2 erster wiederholter | Ø Tokens auf beidseits gelösten Aufgaben |
  |---|---|---|---|---|---|
  | ERGORE | 43 | 43 (+4/−4) | 18 | 44 | 14.026 → 10.331 (−26 %) |
  | MIT | 43 | 45 (+2/−0) | 20 | 42 | 13.920 → 9.287 (−33 %) |
  | eigen | 33 | 35 (+3/−1) | 24 | 36 | 15.055 → 9.963 (−34 %) |
  **Urteile:** Sicherheit ERGORE NICHT erfüllt (4 verloren, erlaubt ≤ 2), MIT und eigen erfüllt. Hauptvergleich: **NICHT über MIT**
  (ERGORE+Zünder 43 gegen MIT 43, p = 1,0). Fairness: MIT+Zünder 45. **Mehrwert des Melders gegenüber Textregeln: NEIN**
  (ERGORE: Zünder netto 0, B2 netto +1). Gemischte Etiketten feuern nie.
  **Beschreibend:** Der Zünder spart viele Tokens ohne Genauigkeitsverlust im Mittel: Auf Aufgaben, die mit und ohne Tor richtig
  sind, ein Viertel bis ein Drittel weniger (passt zu Zhang et al. 2025). **Decke jeder Abbruch-Regel (Orakel, mit gold):** falsche
  Läufe mit irgendwo richtigem Kandidaten: ERGORE +7 (Decke 50/80), MIT +3 (46/80), eigen +7 (40/80); nie ein richtiger Kandidat:
  ERGORE 30, MIT 34, eigen 40. → Bei 32k/0,6 holen beide Eingriffe fast alles, was das Modell findet; der Rest wird nie gefunden
  (passt zum MIT-Schluss „Hindernis entfernen, keine Fähigkeit hinzufügen“).
  **NACHTRÄGLICH (nach Sicht der Ergebnisse, ausdrücklich gekennzeichnet): Extraktions-Artefakt.** Die Regel „answer is …“ fängt
  Füllwörter mit ein ('likely -125', '"3"?', 'simply the number 16'); 21 von 3.494 Kandidaten sind inhaltlich richtig, wurden aber
  als falsch bewertet. 2 der 4 ERGORE-Verluste und der eine eigen-Verlust sind solche Artefakte (die Sonde lag dort richtig).
  Bereinigt (für alle Regeln und Modelle gleich): ERGORE+Zünder 46 (+5/−2), MIT+Zünder 45 (+2/−0), eigen+Zünder 36 (+3/−0); B2:
  44 / 42 / 36. ERGORE+Zünder gegen MIT ohne Tor 46:43 (8:5, p = 0,58); gegen MIT+Zünder 46:45 (p = 1,0). Das ist KEIN Beleg,
  nur ein Hinweis für einen neuen, sauberen Test. Die Artefakte betreffen auch die Trainings-Etiketten der Sonde (Rauschen).
  **Folgerungen:** (1) „Über MIT“ ist auf diesem Weg und bei 80 Aufgaben nicht zu holen: Selbst ein perfekter Zünder brächte
  ERGORE höchstens auf 50, das MIT auf 46. (2) Der Zünder ist ein Spar-Werkzeug (ein Drittel weniger Tokens), kein
  Genauigkeits-Werkzeug. (3) Die Testmenge 1–80 ist für Zünder-Varianten verbraucht; jede neue Variante (bereinigte Extraktion,
  neue Schwelle) braucht frische Aufgaben (z. B. MATH-500 81–160). (4) Die Kandidaten-Extraktion muss vor jedem weiteren Bau
  bereinigt werden.
- 06.11. ~16:00 – **Frische Testaufgaben 81–160 – VORAB FESTGELEGT** (Nutzer: „jap gerne veranlassen“; Laptop am Strom bis ~20:25,
  danach Standby). Der MIT-Temperaturlauf wurde dafür um 15:55 angehalten (46 bzw. 41 von 60 fertig; 03_eval setzt fort, Neustart
  danach falls Zeit). kette_test81.sh:
  (1) ERGORE (kopplung-kw75) und MIT (mit-q8_0) auf MATH-500 81–160 (--start 80 --n 80), 32k, vLLM-Stil, je 6 Slots parallel –
  dasselbe Protokoll wie 41–80. (2) Urteil 46_urteil160.py für 81–160 allein UND 1–160 zusammen, Lesart wie 40_urteil80:
  geknackt = ERGORE > MIT und McNemar p < 0,05; MIT-Niveau = ERGORE ≥ MIT − 2,5 % der Aufgaben und MIT nicht signifikant besser;
  sonst nicht erreicht. (3) Falls vor 19:55: **Zünder-Neutest** auf 81–160 mit eingefrorener Sonde und unveränderter Schwelle
  T_hoch 0,375, Etiketten mit bereinigter Extraktion (roh ODER bereinigt richtig; 42 sammeln --bereinigt); Lesart wie beim ersten
  Zünder-Test (Sicherheit ≤ 5 %, ERGORE+Zünder gegen MIT, Fairness MIT+Zünder, Mehrwert gegen B1/B2/gemischt). (4) Falls vor
  19:50: MIT-Temperaturlauf fortsetzen, Lesart wie um 14:52 festgelegt.
  Erwartung vorab: ERGORE ≈ MIT auch auf 81–160 (beide an der Decke des Modells); der Token-Unterschied bleibt.
- 06.11. 18:59 – **ERGEBNIS frische Testaufgaben 81–160 (vorab festgelegte Lesart, 46_urteil160.py): MIT-NIVEAU ERREICHT –
  auf 81–160 allein UND auf 1–160 zusammen.**
  | | ERGORE | MIT | nur ERGORE : nur MIT | McNemar p | Differenz [95 %] | Ø Tokens ERGORE / MIT |
  |---|---|---|---|---|---|---|
  | 81–160 (frisch) | 36/80 (45,0 %) | 34/80 (42,5 %) | 10 : 8 | 0,81 | +2,5 [−7,9; +12,9] | 18.489 / 21.248 |
  | 1–160 | 79/160 (49,4 %) | 77/160 (48,1 %) | 14 : 12 | 0,85 | +1,2 [−5,0; +7,5] | 18.523 / 21.374 |
  Erwartung vorab („ERGORE ≈ MIT“) bestätigt. Auf 160 Aufgaben ist ein Unterschied von mehr als etwa 5 Punkten zugunsten des MIT
  bzw. 7,5 Punkten zugunsten von ERGORE ausgeschlossen (95 %).
  **Tokens (beschreibend; vorab nur als Erwartung „Unterschied bleibt“ genannt):** gesamt −13,3 % (2,96 gegen 3,42 Mio.);
  ERGORE sparsamer bei 88 Aufgaben, nicht bei 55 (Vorzeichentest p = 0,007; Vorzeichen-Permutation des Mittels p = 0,0001).
  **Auf den 65 Aufgaben, die beide lösen, kein Vorteil** (+4,7 %, p = 0,32): Die Ersparnis entsteht bei ungelösten Aufgaben,
  wo ERGORE früher abgibt – wie schon auf 1–80. Denken geschlossen 81–160: ERGORE 96 %, MIT 69 %.
- 06.11. ~19:10 – **Präzisierung Tokens 1–160 (beschreibend): Etwa die Hälfte der Ersparnis hängt an der Schleifen-Abbruchregel
  der Auswertung.** Zerlegung nach Ende-Art: richtige Läufe gleich teuer (ERGORE 1,11 Mio. für 79, MIT 1,01 Mio. für 77). Falsche
  Läufe: ERGORE 1,85 Mio. (81 Läufe), MIT 2,41 Mio. (83). MIT läuft 51-mal bis zum Limit (ERGORE 23); ERGORE endet öfter per EOS
  ohne richtige Antwort (33 gegen 20) und öfter per Schleifen-Abbruch (25 gegen 12; dup8 > 0,9 → Abbruch bei Ø 19,7k).
  Ohne Abbruchregel (Annahme: abgebrochene Läufe liefen bis 32.768) wäre die Ersparnis ≈ −7 % statt −13 %. Die Regel gilt für beide
  gleich, die Aussage „−13 %“ ist also protokollabhängig und so zu nennen.
  **Wie enden die Läufe (1–160)?** ERGORE: 79 richtig | Denken zu, aber falsch: 76 (18 falsche Antwort abgegeben, 43 Antwort nie
  fertig/Flur, 15 Abgabe-Schleife ohne Antwort) | Denken nie zu: 5. MIT: 77 | 41 (17 / 21 / 3) | 42. → ERGORE verlagert das
  Scheitern aus dem Denken in den Antwortteil („falsches Zucken“); falsche abgegebene Antworten etwa gleich (18 gegen 17).
- 06.11. 19:18 – **ERGEBNIS Zünder-Neutest auf frischen Aufgaben 81–160 (vorab festgelegt; eingefrorene Sonde, T_hoch 0,375
  unverändert, Etiketten bereinigt; 45_wahrer_zuender.py → ergebnisse/wahrer_zuender_test81.json):**
  | | ohne Tor | Zünder (gewonnen/verloren) | B1 | B2 | Tokens auf beidseits gelösten |
  |---|---|---|---|---|---|
  | ERGORE | 36 | **39 (+3/−0)** | 22 | 35 | 14.348 → 11.025 (−23 %) |
  | MIT | 34 | **37 (+3/−0)** | 21 | 31 | 12.235 → 9.660 (−21 %) |
  **Urteile:** Sicherheit bei beiden ERFÜLLT (0 verloren). Hauptvergleich: **Tendenz über MIT (nicht signifikant) – mit
  Laufzeit-Tor** (ERGORE+Zünder 39 gegen MIT 34, 11:6, p = 0,33). Fairness: MIT+Zünder 37 – das Tor hebt beide gleich (+3);
  ERGORE+Zünder gegen MIT+Zünder 39:37 (p = 0,81). **Mehrwert des Melders gegenüber Textregeln: JA** (ERGORE netto +3 gegen
  B2 −1, B1 −14, gemischt 0; ERGORE+Zünder gegen B2 4:0, p = 0,125; MIT 37 gegen B2 31).
  **Bedeutung:** Auf frischen Daten und mit bereinigter Extraktion ist der Zünder sicher (kein richtiger Lauf verloren), holt
  verlorene richtige Antworten zurück und spart ein Fünftel der Tokens auf gelösten Aufgaben. Das innere Wahrheitssignal schlägt
  die beste Textregel – erster vorab festgelegter Beleg, dass das Modell innen mehr weiß, als sein Text verrät, und dass sich das
  nutzen lässt. „Über MIT“ nur als Tendenz und nur, weil das MIT ohne Tor verglichen wird; mit Tor auf beiden Seiten gleichauf.
  Zusammen mit 1–80 (roh: +4/−4; nachträglich bereinigt +5/−2) zeigt sich: Der Gewinn ist klein (die Decke), aber sauber.
- 06.11. 19:36 – **ERGEBNIS MIT bei Temperatur 0,6 und 1,0 (vorab festgelegt 14:52; Lauf um 15:55 angehalten und um 19:19
  fortgesetzt, 03_eval setzt fertige Aufgaben nicht neu an): DEUTLICHE ÄNDERUNG.** (In der Ausgabe von 43_temperatur_vergleich.py
  heißen die MIT-Zeilen technisch „ergore06/ergore10“; die Gewinn-Zeilen tragen den richtigen Namen.)
  | 60 Übungsaufgaben, 12k | 0,6 | 1,0 |
  |---|---|---|
  | eigen | 18 | 16 |
  | MIT | 27 | 20 |
  | ERGORE (Heimvorteil) | 35 | 15 |
  | Gewinn MIT − eigen | +9 (10:1, p = 0,012) | +4 (5:1, p = 0,22) |
  | Gewinn ERGORE − eigen | +17 (p = 0,0002) | −1 (p = 1,0) |
  **Beide verlieren bei 1,0, das MIT aber deutlich weniger.** Beschreibend gepaart ERGORE gegen MIT: bei 0,6 35:27 (10:2,
  p = 0,04; Heimvorteil ERGORE, nicht fair), bei 1,0 **15:20** (2:7, p = 0,18) – das MIT liegt bei 1,0 vorn, obwohl ERGORE auf
  diesen Aufgaben gebaut wurde. Flur (Denken zu, Antwort nie fertig) bei 1,0: **ERGORE 15, MIT 1.**
  **Deutung (Plausibel):** Der Abschluss-Schub von ERGORE (β-Term) ist temperaturempfindlich: Bei 1,0 schließt er das Denken
  zu früh, die Antwort wandert ins Limit (falsches Zucken). Die reine Umkehr des MIT schiebt nicht zum Abschluss und bleibt
  robuster. **Folge:** Für Stabilität über die Temperatur braucht der Abschluss eine Bedingung „es gibt etwas Richtiges
  abzugeben“ – genau das liefert der Wahrheitsmelder (Zünder) – statt eines Schubs, der nur an Schleifen hängt.
  Vorbehalte: 12k-Budget, ein Seed, Übungsaufgaben (Heimvorteil für ERGORE).
- 06.11. ~19:45 – **Nachgeprüft: Der Hersteller empfiehlt im Denkmodus Temperatur 1,0** (Nutzer: „schau mal bitte, ob der
  Hersteller 1.0 empfiehlt“). Quellen: (a) Modellkarte Qwen3.5-0.8B (lokal, modelle/Qwen3.5-0.8B/README.md, Abschnitt
  Quickstart/Tip): „Thinking mode for text tasks: temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=1.5“;
  0,6 nur für „VL or precise coding (WebDev)“ – dort mit presence_penalty 0,0. Die eigenen Sprach-Benchmarks des Herstellers für
  dieses Modell liefen mit temperature=1.0. (b) Modellkarte Qwen/Qwen3.6-35B-A3B auf Hugging Face (abgerufen 06.11., „Best
  Practices“): „Thinking mode for general tasks: temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=1.5“; 0,6 nur
  für präzises Coding; Beispiele mit max_tokens bis 81.920.
  **Folgen:** (1) Das Protokoll aus der MIT-Vorlage (0,6 mit presence_penalty 1,5) ist eine Mischform und NICHT die
  Herstellerempfehlung für Mathe im Denkmodus. (2) Bei der Herstellertemperatur schrumpft der Vorteil beider Eingriffe stark (MIT
  +9 → +4, ERGORE +17 → −1; Übung, 12k). Das gehört in jede Darstellung der MIT-Ergebnisse und unserer. (3) Der Hersteller rechnet
  im Denkmodus mit bis zu 81.920 Tokens; unser Test bei 1,0 lief mit 12k → die Budget-Frage ist jetzt die dringendste offene Frage.
  (4) Für Phase 2 (Qwen3.6) ist 1,0 der Normalfall: Temperatur-Stabilität ist Pflicht, kein Zusatz.
  Offen und naheliegend: das UNVERÄNDERTE Grundmodell bei 0,6 und 1,0 auf denselben 60 Übungsaufgaben (zeigt, wie groß das
  Schleifenproblem bei der Herstellertemperatur überhaupt ist) und der Budget-Test (1,0 mit 32k).
- 06.11. ~19:58 – **Argon-Feedback (19:47) geprüft** (recherche/argon/Argon_Feedback_Einordnung_2026-11-06_abend.md): Architektur-
  Angaben stimmen (0.8B Voll-Attention 3/7/11/15/19/23; Vokabular 248.320 bei 0.8B/4B/35B-A3B; 35B-A3B 40 Schichten, 256+1
  Experten). Alle 6 arXiv-IDs existieren; 2608.25231 betrifft moralische Valenz in OLMoE, Einzelzahlen bei Argon zugespitzt.
  Unser 1,0-Test lief bereits mit presence_penalty 1,5 und top_k 20 (Herstellerprofil) – Argons Einwand entfällt.
  **Argon-Versuch 1 Teil A (vorhandene Läufe 1,0/12k):** ERGORE 15 Flur-Läufe, davon `</think>` vor Token 8.000: 10 (Kriterium ≥ 10
  erfüllt → vorzeitiges Zucken + Überlauf in den Antwortteil, nicht das Budget); frühestes Schließen bei Token 672; **in 0 von 15
  stand vorher eine richtige Lösung im Denken** (8 ganz ohne Kandidat). MIT 1 Flur-Lauf, eigen 0. → Der β-Schub zündet bei 1,0
  ohne etwas Abzugebendes. Argons Vorschlag V6 (SwiGLU-UND-Gatter: Gate = Wahrheitssonde über Schwelle, Up = Kandidaten-Ende,
  Down = Abschluss-Vektor; Schleifen-Spalten nur Umkehr) trifft genau diese Ursache und ist der Kandidat für den nächsten Bau.
- 06.11. ~20:05 – **Schritt 1 (Diagnose des Einbruchs bei 1,0) – VORAB FESTGELEGT** (Nutzer: „Wir machen es so … Heute Abend
  machen wir 1) von a bis c“; Reihenfolge 1a, 1b, dann 1c). Nur Übungsdaten (60 Aufgaben leicht60).
  **1a Pegel des Schleifen-Melders** (47_pegel_temperatur.py): Aktivierungen der 64 Spalten von Schicht 15 (Eingang down_proj;
  für denselben Text bei allen Modellen gleich, da die Eingriffe erst in down_proj wirken) entlang der Läufe; Pegel roh
  (u_eᵀW₀ über S) und geschärft (k_scharf). Läufe: ERGORE, eigen, MIT je bei 0,6 und 1,0 (12k). Schwelle θ = 95-%-Quantil des
  geschärften Pegels über alle Denk-Tokens der ERGORE-0,6-Läufe. Kennzahlen je Lauf: Feuerrate (Anteil Denk-Tokens > θ),
  Pegel beim Schließen (Mittel der 16 Tokens vor `</think>`). **Lesart:** (i) „Regime“ = mediane Feuerrate von ERGORE sinkt
  bei 1,0 auf weniger als die Hälfte von 0,6. (ii) „Fehlzündung (Kopplung)“ = die leeren Schließungen von ERGORE bei 1,0
  (Flur) liegen im Median bei einem Pegel ≥ dem Median der ordentlichen Schließungen bei 0,6. (iii) „thermisches Zucken“ =
  diese Schließungen liegen im Median UNTER dem Median aller Denk-Tokens bei 0,6. Mehrere können zugleich gelten.
  **1b Wahrheitsmelder bei 1,0** (48_sonde_invarianz.py): Kandidaten der 1,0-Läufe (eigen, ERGORE, MIT) an Schicht 13 lesen;
  Etiketten bereinigt (roh ODER bereinigt richtig), auch die 0,6-Etiketten neu bereinigt. Zurückgehaltene Werte nach Aufgabe
  (gleiche 5 Faltungen wie beim Einfrieren): Sonde nur auf 0,6-Kandidaten fremder Aufgaben gelernt, auf 1,0-Kandidaten der
  zurückgehaltenen Aufgaben bewertet. **Lesart:** invariant = AUC-Abfall < 0,05 gegenüber 0,6 UND Paar-Trefferquote im selben
  Lauf fällt um ≤ 10 Prozentpunkte; nicht invariant = AUC < 0,85 ODER Paar-Abfall > 10 pp; dazwischen = eingeschränkt.
  **1c Budget:** ERGORE und MIT bei 1,0 mit 32k (max-tokens 32.768), sonst wie bei 12k, je 6 Slots parallel. **Lesart (nach
  WREN):** Budget-Artefakt = ERGORE holt bei 32k auf (ERGORE ≥ MIT − 2) UND die leeren Schließungen von ERGORE fallen unter 5;
  sonst ist das Budget nicht die Hauptursache. Beschreibend: Treffer 12k gegen 32k je Modell, Lage von `</think>`.
- 06.11. 20:24 – **ERGEBNIS Schritt 1a und 1b (vorab festgelegte Lesart).**
  **1a Pegel des Schleifen-Melders (geschärft, Schicht 15; θ = 0,147 = 95-%-Quantil ERGORE 0,6):**
  | | Feuerrate (Median je Lauf) | Pegel beim Schließen: ordentlich | Pegel beim Schließen: leer (Flur) |
  |---|---|---|---|
  | ERGORE 0,6 / 1,0 | 3,5 % / 2,8 % | 0,082 / **0,025** | 0,139 (10) / **0,099 (15)** |
  | MIT 0,6 / 1,0 | 4,1 % / 2,9 % | 0,016 / 0,021 | 0,284 (6) / 0,479 (1) |
  | eigen 0,6 / 1,0 | 4,2 % / 3,2 % | 0,029 / 0,020 | 0,252 (4) / – |
  **Urteil 1a: Regime NEIN** (Feuerrate fällt nur auf 79 %, nicht unter die Hälfte – der Melder hat bei 1,0 durchaus zu beißen,
  obwohl wörtliche Schleifen fehlen); **Fehlzündung JA** (leere Schließungen bei 1,0 im Median bei 0,099 ≥ 0,082, dem Pegel
  ordentlicher Schließungen bei 0,6); **thermisches Zucken NEIN** (0,099 weit über dem Denk-Median 0,032).
  Zusatz (beschreibend): Bei 1,0 kommen die ORDENTLICHEN Schließungen von ERGORE bei niedrigem Pegel (0,025 – natürliches
  Abschließen), die LEEREN bei hohem (0,099): Was der Melder bei 1,0 auslöst, ist überwiegend leer. Leere Schließungen haben bei
  allen Modellen hohen Pegel; ERGOREs β-Schub macht aus solchen Zuständen bei 1,0 15 Schließungen, das MIT nur eine.
  → Ursache des Einbruchs: **Kopplung** – der Schub hängt an einem Melder, der auch auf Zustände ohne Lösung anspringt.
  **1b Wahrheitsmelder bei 1,0 (zurückgehalten nach Aufgabe, Sonde nur bei 0,6 gelernt, Etiketten bereinigt):** 521 Kandidaten
  (165 richtig) aus 129 Läufen. AUC 0,6 = 0,961 → **1,0 = 0,983**; Paar-Trefferquote im selben Lauf 94,3 % → **98,7 %**;
  je Modell bei 1,0: eigen 0,965, ERGORE 0,986, MIT 0,978; Endantworten bei 1,0 AUC 0,96 (nur 2 falsche). **Urteil 1b: INVARIANT.**
  → Die Grundvoraussetzung für Schritt 2 ist erfüllt: Ein Gatter auf Basis der Wahrheitssonde kann bei 0,6 UND 1,0 arbeiten.
  Zusammen: Der Schleifen-Melder ist der falsche Auslöser (feuert ohne Lösung), der Wahrheitsmelder der richtige (hält bei 1,0).
- 06.11. 22:49 – **ERGEBNIS Schritt 1c (Budget bei Temperatur 1,0; 60 Übungsaufgaben; vorab festgelegt ~20:05):**
  | bei 1,0 | richtig | leere Schließungen (Flur) | Denken nie zu | abgegeben (EOS) | Ø Tokens |
  |---|---|---|---|---|---|
  | ERGORE 12k → 32k | 15 → **32** | 15 → 12 | 31 → 6 | 15 → 42 | 11.145 → 21.064 |
  | MIT 12k → 32k | 20 → **31** | 1 → 5 | 38 → 23 | 21 → 32 | 10.498 → 21.374 |
  Gepaart: ERGORE 32k gegen 12k 17:0 (p < 0,0001); MIT 32k gegen 12k 13:2 (p = 0,007); **ERGORE gegen MIT bei 32k: 32 : 31
  (5:4, p = 1,0)**. **Urteil nach vorab festgelegter Regel: „Budget NICHT die Hauptursache“** – Teil 1 erfüllt (ERGORE ≥ MIT − 2),
  Teil 2 nicht (leere Schließungen von ERGORE bleiben 12, gefordert < 5).
  **Ehrliche Lesart (beschreibend):** Der RÜCKSTAND von ERGORE auf das MIT bei 1,0 war ein Budget-Effekt: Mit 32k ist er
  verschwunden (32 : 31). Die neu gelösten ERGORE-Aufgaben waren bei 12k zu 13/17 „Denken nie zu“ (abgeschnitten), 4/17 leere
  Schließungen. Das FALSCHE ZUCKEN dagegen ist KEIN Budget-Effekt: Es bleibt bei 32k (ERGORE 12 gegen MIT 5) – passend zu 1a
  (Fehlzündung). Der Hersteller rechnet im Denkmodus mit bis zu 81.920 Tokens; 12k war für 1,0 zu knapp.
  **Folgen:** (1) Die Aussage „ERGORE bricht bei 1,0 ein“ ist zu korrigieren: Bei 1,0 mit 32k liegt ERGORE gleichauf mit dem MIT
  (Übungsaufgaben). (2) Der verbleibende Defekt ist das falsche Zucken – genau das Ziel des ERGO-Gatters (Schritt 2): 12 leere
  Schließungen bei 1,0/32k sind das Potenzial „über MIT“ in der Herstellertemperatur. (3) Entwicklungs-Tests bei 1,0 nur mit
  ≥ 32k. Vorbehalte: Übungsaufgaben (Heimvorteil ERGORE), ein Seed.
- 06.11. ~23:50 – **Schritt 2: ERGO-Gatter gebaut und geprüft** (50_ergo_gatter.py; Nutzer „Ja, vorbereiten“). Daten: MLP-Eingang
  Schicht 15 aus 600 Übungsläufen (0,6 und 1,0; 12k/32k): 4.960 Kandidaten (1.263 richtig, Etiketten bereinigt), 24.000
  gewöhnliche Tokens. Wahrheitssonde s_T AUC 0,962, Kandidaten-Ende-Melder s_C AUC 0,999 (beide zurückgehalten nach Aufgabe).
  Bauform (umgedreht gegenüber dem ersten Entwurf, weil ein Gatter „Sonde × konstant“ an ~1 % gewöhnlicher Tokens feuern
  würde): gate = s_C (τ_C: 0,1 % der gewöhnlichen Tokens offen; offen an 84 % der Kandidaten-Enden), up = s_T mit Vorzeichen
  (Nullpunkt Mitte richtig/falsch), down = e⊥ (Entschluss-Achse ⊥ u_e); 16 ruhigste Neuronen außerhalb der 64 Schleifen-
  Spalten; Grundlage eigen (Umkehr bitgleich geprüft), kein β-Schub. Funktionsprobe im gebauten Modell (30 Übungsläufe):
  richtige Kandidaten-Enden Gatter-Summe Median +64,5 (94 % > 0,5), falsche −47 (Schub zum Weiterdenken), gewöhnliche Tokens
  ≈ 0 (99 %-Quantil 1,2 ≈ 2,5 % des Zielschubs). q8_0 verträglich (Vorzeichen 99,8 % gleich). GGUF gebaut.
  **Rauchtest (vorab: technisch sauber und Treffer ≥ 0 bei Referenz 2/12)** auf 12 alten Übungsaufgaben bei 1,0/12k läuft;
  Referenz dort: eigen 2/12 (Flur 0), ERGORE 2/12 (Flur 5), MIT 2/12 (Flur 0).
  **Entwicklungstest – VORAB FESTGELEGT, Start erst nach Go des Nutzers:** Set B (60 frische MATH-Train-Aufgaben,
  daten/practice/math_train_setB60.jsonl, Stufen wie MATH-500, keine Überschneidung mit 504 benutzten), 32k, Seed 0,
  vLLM-Stil, je 6 Slots; Gatter, ERGORE, MIT je bei 0,6 und 1,0 (kette_schritt2.sh). Lesart (51_schritt2_urteil.py):
  **K1** falsches Zucken (Denken zu, keine Antwort abgegeben, nicht richtig) beim Gatter ≤ 6/60 bei 0,6 UND 1,0;
  **K2** Treffer Gatter ≥ ERGORE − 2 bei 0,6 und ≥ MIT − 2 bei 1,0; **K3** eingefrorene Wahrheitssonde (Schicht 13) auf den
  Kandidaten der Gatter-Läufe AUC ≥ 0,93. Beschreibend: Gatter gegen MIT bei 1,0 (McNemar), Tokens. Set B ist Übung:
  Entwicklungstest, keine Bestätigung „über MIT“ (die kommt in Schritt 3 auf frischen MATH-500-Aufgaben).
- 07.11. ~00:05 – **Rauchtest ERGO-Gatter bestanden** (vorab: technisch sauber, Treffer ≥ 0): 12/12 Läufe sauber beendet, 1/12 richtig
  (Referenz je 2/12), **leere Schließungen 0** (ERGORE auf denselben 12: 5), Denken nie zu 11/12 (eigen 10, MIT 9) – bei 12k/1,0
  sind fast alle Läufe abgeschnitten; nur ein Hinweis (n = 12).
  **Nachtlauf Schritt 2 – Ergänzungen, VORAB FESTGELEGT vor dem Start** (Nutzer: „Wir sollten sicherstellen, dass wir alles
  mitnehmen was wir bekommen an Messdaten … robust und transparent“): Primär unverändert (K1–K3, Gatter = Schub 1,0).
  **Dosis-Arm (beschreibend, nicht für K1–K3):** Gatter3 = gleiches Gatter mit 3-fachem Schub (κ_d 0,0656) bei 0,6 und 1,0 –
  zeigt, ob der Schub zu schwach ist, und erlaubt morgen eine Ableitung ohne neue Messung. **Schadens-Check (beschreibend):**
  IFEval 120 Prompts (wie bisher, 0,6) für Gatter und ERGORE; Bezug eigen 61,7 %, MIT 72,5 %; „kein deutlicher Schaden“, wenn
  Gatter ≥ eigen − 5 Punkte. **Messdaten:** Kandidaten aller Set-B-Läufe (Schicht 13, für Sonde, Zünder- und „gefunden aber
  verloren“-Nachrechnungen), Gatter-Aktivität je Token (beide Dosen), Pegel des Schleifen-Melders (Gatter gegen ERGORE).
  MIT bei 0,6 entfällt (nur beschreibend, für die Kriterien nicht nötig). **Robustheit:** jeder Lauf bis zu 3 Versuche mit
  Fortsetzen, Server-Neustart bei Ausfall; Wächter mit Herzschlag ≤ 40 min, Claude prüft bei jedem Wecken aktiv.
  **Versionen:** ERGORE = V1 (Schleifen-Reflex, kw75); ERGO-Gatter = V2-Kandidat (Wahrheits-Gatter, Schub 1); Gatter3 = V2-Dosis.
- 07.11. ~02:50 – **Nachuntersuchung in der Nacht (Nutzer: „kein Leerlauf … Nachuntersuchungen“), beschreibend:**
  (a) **Zwischenstand P1** (nicht das Urteil; 34 gemeinsam fertige Set-B-Aufgaben bei 1,0/32k): Gatter 6 richtig, MIT 14; das Gatter
  schließt das Denken selten (24/34 bis zur 32k-Grenze), 4 leere Schließungen.
  (b) **Schub-Probe** (53_gatter_schub_probe.py; 8 richtige, 8 falsche Kandidaten-Enden im Denken aus eigen-Übungsläufen; CPU):
  p(`</think>` als nächstes Token) am Kandidaten-Ende ist bei ALLEN Modellen winzig (Median ~5·10⁻¹³ richtig, ~1·10⁻¹¹ falsch);
  der Gatter-Schub ändert das kaum (Gatter/eigen 0,53×, Gatter3/eigen 0,73× an richtigen). → **Deutung:** Direkt nach dem
  Kandidaten-Ende folgt fast nie `</think>` (zuerst Satzzeichen, Zeilenumbruch, „So the answer…“). Ein Schub an GENAU EINEM Token
  wirkt nur auf dieses eine nächste Token und kommt beim späteren Entscheidungspunkt kaum an. ERGOREs β-Schub wirkt dagegen über
  viele Tokens (der Schleifen-Melder feuert wiederholt). **Konstruktionsfehler des V2-Kandidaten erkannt:** Das Gatter muss am
  Entscheidungspunkt nach dem Kandidaten wirken (nächstes Satzende/Absatz, „Weiche“) bzw. über ein Fenster von Tokens – Argons
  ursprünglicher Vorschlag (Up = Weichen-Detektor) zielte genau darauf. Wird vor einem neuen Bau auf Übungsdaten geprüft
  (Hält das Wahrheitssignal an Positionen NACH dem Kandidaten?); P2–P4 laufen wie vorab festgelegt weiter (Dosis-Arm bestätigt
  oder widerlegt die Deutung im Verhalten).
- 07.11. ~03:20 – **Nachuntersuchung: Wo lebt das Wahrheitssignal NACH dem Kandidaten?** (54_wahrheit_nachlauf.py; 80 Übungsläufe,
  40 richtige / 163 falsche Kandidaten im Denken; Sonde s_T vom Kandidaten-Ende, Schicht 15; beschreibend, Sonde am Ende in-sample):
  AUC am Ende 1,00 → +1: 0,97 → +2: 0,81 → +4: 0,68 → +8: 0,67 → +16: 0,48 → +32: 0,59; an der nächsten Weiche (Satzende/Absatz
  binnen 40 Tokens) 0,96. **Abstand letztes Kandidaten-Ende → `</think>`** bei ordentlich geschlossenen Läufen (68): Median
  **607 Tokens** (25–75 %: 136–1.492). → Die am Kandidaten-Ende gelernte Richtung trägt nur wenige Tokens; geschlossen wird im
  Mittel Hunderte Tokens später. Ein V2.1 braucht eine Bedingung, die an den späteren Weichen gilt („Lösung steht“). Ob sich dafür
  an späten Positionen eine eigene Sonde lernen lässt, prüft 55_wahrheit_spaet.py (läuft, CPU).
- 07.11. 03:38 – **Nachtlauf P1 fertig (Set B, 1,0, 32k; beschreibend bis zum Gesamturteil):** Gatter (V2) **11/60**, MIT **24/60**;
  gepaart nur Gatter 0, nur MIT 13. Gatter: leeres Zucken 5 (≤ 6), falsch abgegeben 0, **Denken nie zu 44/60** (MIT 35);
  Ø 29.832 Tokens (MIT 25.579). → K2 bei 1,0 (≥ MIT − 2) wird klar verfehlt. Das Gatter gibt nie eine falsche Antwort ab, aber
  es schließt fast nie – passend zur Schub-Probe (Anstoß an einem Token verpufft) und zu 54 (geschlossen wird ~600 Tokens später).
  P2 (Gatter 0,6 + ERGORE 0,6) läuft seit 03:38.
- 07.11. ~04:05 – **Nachuntersuchung: Lässt sich „der letzte Kandidat ist richtig“ an SPÄTEN Positionen lesen, wenn man die Sonde
  dort lernt?** (55_wahrheit_spaet.py; 80 Übungsläufe; zurückgehaltene AUC, Schicht 15): +8 Tokens 0,80 · +16: 0,67 · +32: 0,67 ·
  +64: 0,72 · Weichen bis +200: 0,75 (je ~200–600 Positionen, ~50–150 nach richtigem Kandidaten). → **Das Wahrheitssignal ist ein
  kurzes Aufblitzen am Kandidaten-Ende (0,96), kein dauerhafter Zustand.** Ein Gatter an späten Weichen wäre deutlich unschärfer.
  **Fuchsbau-Befund:** Das Modell bewertet seinen Kandidaten im Moment des Hinschreibens – und handelt dann nicht danach; das
  Signal verblasst binnen weniger Tokens, geschlossen wird im Mittel ~600 Tokens später.
  **Folgerung für V2.1 („Zünder im Gewicht“):** Am Kandidaten-Ende selbst handeln, und zwar so stark, dass das Modell SOFORT
  `</think>` schreibt (wie der Laufzeit-Zünder, der auf Testdaten sicher war). Prüfung von Richtung und Stärke läuft
  (56_zig_probe.py: Abschluss-Gradient gegen e⊥, CPU).
- 07.11. ~04:40 – **Nachuntersuchung „Zünder im Gewicht“ (56_zig_probe.py, Trockenlauf mit 2+2 Präfixen, CPU; beschreibend):**
  Der Abschluss-Gradient ĝ (∂ log p(`</think>`)/∂ h₁₅ am Kandidaten-Ende) ist über Präfixe einheitlich (Norm des Mittels 0,89) und
  **steht senkrecht auf der Entschluss-Achse e⊥** (cos −0,01). Idealisierter Anstoß an genau dieser Position (Residual-Norm dort
  ≈ 3,6): entlang ĝ hebt **κ = 5 p(`</think>`) von ~10⁻¹² auf ~0,95**, κ ≥ 10 auf 1,0; entlang e⊥ selbst bei κ = 80 nur auf
  ~5·10⁻⁵. → **Hauptursache des V2-Fehlschlags ist die falsche Wirkrichtung, nicht nur die Dosis:** e⊥ bedeutet „gleich
  schließen“ (über ~16 Tokens gelernt), nicht „jetzt schließen“. V2.1 = Gatter am Kandidaten-Ende mit hoher Wahrheits-Schwelle
  und Wirkrichtung ĝ (sofortiges `</think>`), also der Laufzeit-Zünder als Gewicht. Bei falschen Kandidaten würde derselbe Anstoß
  ebenfalls schließen – die Wahrheits-Schwelle muss streng sein. ĝ aus 16 Präfixen wird berechnet (57_abschluss_gradient.py).
- 07.11. ~05:08 – **V2.1 „Zünder im Gewicht“ gebaut (nur Bau + Offline-Prüfung; kein Lauf):** Abschluss-Gradient ĝ aus 16 richtigen
  Kandidaten-Enden (eigen-Übungsläufe; Einigkeit 0,81, mittlerer paarweiser Kosinus 0,63; ergebnisse/abschluss_gradient.npz).
  Modell modelle/Qwen3.5-0.8B-ergo-zig = eigen (Umkehr bitgleich) + 16 Gatter-Neuronen in Schicht 15: gate = Wahrheit
  (Schwelle τ_T 0,716: zurückgehalten 74,7 % der richtigen, 2,0 % der falschen Kandidaten darüber), up = Kandidaten-Ende
  (95 % positiv), down = κ_d·ĝ mit Gesamtanstoß κ = 7 an einem typischen sicher-richtigen Ende (Probe: κ 5 → p ≈ 0,95).
  Offline-Prüfung auf anderen Übungsläufen (58_zig_pruefen.py) läuft (CPU).
- 07.11. 05:38 – **ERGEBNIS Offline-Prüfung V2.1** (58_zig_pruefen.py; je 8 Präfixe aus Übungsläufen, die NICHT für ĝ benutzt wurden;
  p(`</think>` als nächstes Token)):
  | Stelle | eigen (Median) | V2.1 (Median) | V2.1 Anteil > 0,5 |
  |---|---|---|---|
  | richtige Kandidaten-Enden | 1,5·10⁻¹² | **1,00** | **6/8** (die 2 übrigen liegen unter der Wahrheits-Schwelle) |
  | falsche Kandidaten-Enden | 6,4·10⁻¹¹ | 8,0·10⁻¹¹ | 0/8 |
  | gewöhnliche Denk-Tokens | 1,0·10⁻¹² | 1,2·10⁻¹¹ | 0/8 |
  → **Mechanismus bestätigt:** V2.1 schließt an sicher-richtigen Kandidaten-Enden sofort und lässt falsche Kandidaten und
  gewöhnliche Stellen unberührt – der Laufzeit-Zünder als reiner Gewichts-Eingriff. GGUF (q8_0) gebaut. Offen: Verhalten in
  echter Generierung (Antwortteil nach dem erzwungenen Schließen, Treffer, Tokens) – braucht einen Lauf, nur nach Absprache.
- 07.11. 05:44 – **Wächter-Prüfung P2:** Das Gatter-0,6-Log stand seit 04:59 still (24/60). Kein Hänger: Der Server erzeugt weiter
  ~19 Tokens/s je Platz (Stichprobe über 21 s), alle 6 laufenden Aufgaben sind lange Läufe nahe der 32k-Grenze (bis 30.061 Tokens).
  Hänger-Fenster des Wächters auf 75 min erhöht. **Zeitplan-Folge:** Bei 0,6 laufen viele Aufgaben bis 32k → P2 voraussichtlich
  ~08:30, P3 ~11:30, P4 ~14:30 (statt Vormittag). Entscheidung für den Nutzer am Morgen: Dosis-Arm (Gatter3, laut Schub-Probe
  wohl wirkungslos, weil e⊥ am Kandidaten-Ende nicht schließt) abbrechen zugunsten eines V2.1-Laufs?
- 07.11. 05:49 – **Fortsetzungs-Probe V2.1** (59_zig_fortsetzung.py; 4 richtige Kandidaten-Enden aus Läufen, die nicht für ĝ benutzt
  wurden; 160 neue Tokens, Temperatur 0,6; CPU): eigen schließt in 0/4 (denkt weiter: „Is it possible the question implies …“).
  **V2.1 schreibt in 2/4 sofort `</think>`** und beginnt danach einen sauberen Antwortteil („The problem asks for … 1. Identify …“),
  in den übrigen 2 denkt es wie eigen weiter (vermutlich unter der Wahrheits-Schwelle). Die Endantwort mit \boxed kommt im
  Antwortteil erst nach mehr als 160 Tokens (das Modell schreibt die Lösung geordnet auf) – hier nicht mehr erfasst.
  → Qualitativ funktioniert der Mechanismus auch beim Generieren: sofortiges Schließen, danach geordnete Antwort statt
  Abgabe-Schleife. Treffer und Tokens zeigt erst ein echter Lauf (nach Absprache).
- 07.11. 06:07 – **P2 Zwischenstand und Protokoll-Hinweis:** ERGORE 0,6 auf Set B fertig: **34/60**, Denken immer geschlossen,
  Ø 18.432 Tokens. Gatter 0,6: Ergebnisdatei 46/60 (06:03), das Fortschritts-Log steht aber seit 04:59 bei 24 Zeilen –
  **Log-Ausgabe hängt, die Ergebnisse werden weiter geschrieben** (Server erzeugt normal). Fortschritt deshalb über die
  Ergebnisdatei gezählt; Wächter-Hängerfenster auf 150 min. Falls das Programm am Ende ohne Zusammenfassung endet, wird sie aus
  der Ergebnisdatei nachgerechnet. Beschreibend auf 46 gemeinsamen Aufgaben: Gatter 20 richtig, ERGORE 28; leeres Zucken
  Gatter 11, ERGORE 15; Denken nie zu Gatter 14, ERGORE 0. → V2 verfehlt voraussichtlich auch bei 0,6 K1 und K2.
- 07.11. 06:34 – **P2 fertig; vorläufiges Urteil V2 (K1/K2; K3 folgt am Kettenende):** Gatter 0,6 **27/60**, ERGORE 0,6 **34/60**
  (2:9, p = 0,065); Gatter 1,0 **11/60**, MIT 1,0 **24/60** (0:13, p = 0,0002). **K1 NICHT erfüllt** (leeres Zucken Gatter 0,6: 14,
  1,0: 5; gefordert ≤ 6 bei beiden). **K2 NICHT erfüllt.** → **V2 besteht den vorab festgelegten Entwicklungstest nicht.**
  Ursache nach den Nachuntersuchungen: falsche Wirkrichtung am Kandidaten-Ende (e⊥ schließt dort nicht); V2.1 (Abschluss-
  Gradient) offline bestanden. **Robustheit hat gegriffen:** Der erste Gatter-0,6-Versuch brach mit einem Windows-Socketfehler ab
  (WinError 10055, „Pufferspeicher fehlte oder Warteschlange voll“) – deshalb stand das Log ab 04:59 still; 59/60 Aufgaben waren
  geschrieben, der automatische zweite Versuch hat die fehlende Aufgabe nachgeholt (06:33). Lehre: Socket-Fehler im Streaming
  künftig in 03_eval je Anfrage abfangen und wiederholen. P3 (ERGORE 1,0 + Gatter3 0,6) läuft seit 06:34.
- 07.11. 07:58 – **Zwischenstand Dosis-Arm (beschreibend, 26 gemeinsame Aufgaben bei 0,6):** Gatter3 13 richtig (leeres Zucken 4,
  nie zu 7), Gatter 10 (7, 9), ERGORE 15 (9, 0). → **Meine Vorhersage „Gatter3 wirkungslos“ ist so nicht haltbar:** Der dreifache
  e⊥-Schub ändert im Verhalten etwas (mehr richtig, weniger leeres Zucken), obwohl er p(`</think>`) am Kandidaten-Token selbst
  nicht anhebt – vermutlich über spätere Positionen, die den angestoßenen Zustand per Attention lesen. Klein und verrauscht
  (n = 26); der vorab festgelegte Dosis-Arm läuft deshalb wie geplant zu Ende.
- 07.11. 09:28 – **Korrektur meiner 07:58-Lesart (Dosis-Arm):** Auf 54 gemeinsamen Aufgaben bei 0,6 steht Gatter3 **25** gegen
  Gatter **24** (6:5, p = 1,0) – **kein Treffer-Effekt** des dreifachen Schubs. Der Vorsprung bei n = 26 (13 gegen 10) war Rauschen.
  Leeres Zucken Gatter3 10 (54 Aufgaben) gegen Gatter 14 (60). **Lehre (zum zweiten Mal in dieser Nacht):** Zwischenstände unter
  voller Stichprobe nicht deuten, nur melden.
- 07.11. 09:28 – **P3 Zwischenstand (beschreibend):** ERGORE 1,0 gegen MIT 1,0 auf 52 gemeinsamen Aufgaben **19 gegen 21** (3:5,
  p = 0,73). ERGORE 1,0 gegen ERGORE 0,6 auf denselben 52: **19 gegen 31** (1:13, p = 0,002) – bei diesem 0,8B-Modell und 32k ist 0,6
  auf Set B klar besser als die Hersteller-Empfehlung 1,0 (MIT bei 0,6 auf Set B nicht gemessen).
- 07.11. 09:28 – **Nachuntersuchung nur am Text (nachträglich, Set B = Entwicklungssatz, nicht vorab festgelegt):**
  1. **Schließ-Verhalten:** Gatter/Gatter3 schließen bei 0,6 in 9 bzw. 10 Läufen höchstens 64 Tokens nach einem Kandidaten, davon
     7 bzw. 8 an einem richtigen; ERGORE 0,6 nur 6 (3 richtig). Der gesteuerte Schub erzeugt also schnelle Abschlüsse an meist
     richtigen Kandidaten – aber selten.
  2. **Obergrenze jedes Kandidaten-Zünders** („schließe am ersten richtigen Kandidaten“ = richtig + falsche Läufe, die im Denken
     schon einen richtigen Kandidaten hatten): Gatter 0,6 **31** (ERGORE 0,6 erreicht tatsächlich 34), Gatter 1,0 **24** (MIT 1,0
     tatsächlich 24), Gatter3 0,6 30 von 54. Grund: Viele falsche Läufe bringen gar keinen richtigen Kandidaten hervor (Gatter 1,0:
     21 der 44 nie geschlossenen Läufe haben überhaupt keinen Kandidaten). → **V2.1 auf eigen-Basis kann K2 bei 0,6 selbst
     fehlerfrei kaum erreichen** (Ziel ≥ 32) und bei 1,0 höchstens mit MIT gleichziehen. Prognose aus vorhandenen Texten, keine
     Messung; die V2.1-Bahnen würden sich nach dem ersten Feuern von den Gatter-Bahnen unterscheiden.
  3. **Anatomie des leeren Zuckens** (Denken zu, keine saubere Antwort, falsch): Das Modell schließt `</think>` etwa in der Mitte
     (ERGORE 0,6: Median 51 % des Textes), rechnet im Antwortteil weiter, ohne boxed (2/22 mit boxed), und endet am Limit (10)
     oder in Meta-Schleifen wie „I will formulate the response. Final.“ (8); kein neues <think>. **11 der 22 ERGORE-0,6-Fälle
     schlossen, ohne im Denken je einen Kandidaten gehabt zu haben.** ERGORE 1,0: 15 Fälle, alle am Limit, Antwortteil Median
     ~48.000 Zeichen. → **Größte Verlustklasse von ERGORE:** Schließen ohne Lösung, danach ein ausufernder Antwortteil
     (0,6: 22 von 26 Fehlern; 1,0: 15 von 33). Genau hier wäre ein ehrliches „weiß ich nicht“ die richtige Ausgabe (Leitsatz).
  **Folgerung (Vorschlag, nichts gestartet):** V2.1 in der vorgeschlagenen Form (eigen-Basis) nicht laufen lassen. Stattdessen
  (a) kurze **Antwort-Zwang-Probe** auf den vorhandenen Zuck-Läufen (bei `</think>` + N Tokens abschneiden, „boxed{“ erzwingen,
  zählen, wie viele richtig werden; dasselbe für MIT), Minuten auf der GPU nach dem Kettenende; (b) dieselbe Probe mit erlaubtem
  „weiß ich nicht“ als Einstieg in den Ehrlichkeits-Harnisch; (c) erst danach ggf. „ERGORE + ĝ-Zünder“ (Obergrenze ERGORE + 3).
- 07.11. 09:48 – **Nutzer-Entscheidung „Ja, umstellen“:** P4 abgebrochen (Gatter3 1,0 hatte 0/60, IFEval Gatter 4/120; Ordner in
  `setB-gatter3-t10-abgebrochen` und `ifeval-gatter-nacht-abgebrochen` umbenannt, nichts gelöscht). Begründung: V2 ist durchgefallen,
  Gatter3 0,6 = Gatter 0,6. Kette und Server gezielt per Prozess-ID gestoppt. **Rest seit 09:49:55** (`kette_schritt2_rest.sh`):
  A Antwort-Zwang-Probe (60_antwort_zwang.py) ‖ IFEval ERGORE; B Messdaten (Kandidaten Schicht 13 → K3 und Sonden-AUC je Modell,
  Gatter-Aktivität, Pegel), Urteil, Sicherung – wie geplant, nur ohne Gatter3 1,0.
- 07.11. 09:52 – **Endstand P3:** ERGORE 1,0 **21/60** (leeres Zucken 18, nie zu 19) gegen MIT 1,0 **24/60** (3:6, p = 0,51);
  ERGORE 1,0 gegen ERGORE 0,6: 21 gegen 34 (1:14, p = 0,001). Gatter3 0,6 **28/60** gegen Gatter 0,6 27 (7:6, p = 1,0) und
  ERGORE 0,6 34 (3:9, p = 0,15). → Dosis-Arm: dreifacher e⊥-Schub ohne Treffer-Effekt.
- 07.11. 09:51 – **V2.2 gebaut** (61_v22_bauen.py, Nutzer-Go „Ja, umstellen“ für Bau und Offline-Prüfung): ERGORE (kw75) vollständig +
  die 16 Zünder-Neuronen aus V2.1 (gate = Wahrheit über τ_T 0,716, up = Kandidaten-Ende, down = κ_d·ĝ). Bit-genau geprüft: ERGORE
  ändert nur die 64 Masken-Spalten von down_proj 15/19, die Gatter-Neuronen liegen außerhalb; gate/up von ERGORE = Basis.
  **Fehlerquelle beseitigt:** `wsp_lib.modell_mit_patch` hat eine aus der Basis verlinkte `wsp_patch.json` beim Schreiben
  durchgeschrieben (Hardlink, Befund vom 06.11.). Jetzt wird im Ziel nur der Link gelöst; ERGOREs Metadaten nach dem Bau
  nachweislich unverändert (gleicher SHA-256). Begründung V2.2: V2 und V2.1 fehlte ERGOREs Dauer-Druck → Hängen im Denken.
- 07.11. 09:52 – **Antwort-Zwang-Probe, erstes Ergebnis ERGORE 0,6** (22 Läufe ohne saubere Antwort, alle „leeres Zucken“):
  Antwort am Lauf-Ende erzwungen → **4 richtig** (34 → 38); direkt beim eigenen `</think>` erzwungen → **2 richtig**. Jede
  erzwungene Antwort war eine Zahl/ein Ausdruck (0 ohne Antwort). → In 18 der 22 Fälle hat das Modell die Lösung NICHT – ein
  erzwungenes Antworten erzeugt dort falsche Antworten. Für diese Fälle ist ein ehrliches „weiß ich nicht“ der richtige Weg
  (Ehrlichkeits-Harnisch), nicht mehr Druck.
- 07.11. 09:57 – **Vorab-Lesart V2.2-Entwicklungstest (festgehalten, BEVOR irgendein V2.2-Lauf existiert; Start nur nach Nutzer-Go;
  Einzelheiten paket/SCHRITT2c_V22_VORSCHLAG.md, Auswertung paket/62_v22_urteil.py, Kette kette_v22.sh):** Set B, 60 Aufgaben, 32k,
  Seed 0, vLLM-Stil, V2.2 bei 0,6 und 1,0 parallel. Vergleich mit den vorhandenen Läufen ERGORE 0,6 (34), ERGORE 1,0 (21), MIT 1,0 (24).
  **K1** V2.2 ≥ ERGORE − 2 bei 0,6 UND 1,0. **K2** Zünder-Treffer (`</think>` ≤ 64 Tokens nach richtigem Kandidaten) ≥ 8 bei 0,6
  (ERGORE 3) UND ≥ 8 bei 1,0 (ERGORE 0), und ≥ 75 % der schnellen Abschlüsse an richtigen Kandidaten. **K3** beidseits gelöst: V2.2
  weniger Tokens (Vorzeichentest einseitig, p < 0,05, beide Temperaturen zusammen). Beschreibend: McNemar, leeres Zucken, nie zu,
  Fehlschüsse, Sonde AUC ≥ 0,93. Basiswerte ERGORE (gelöste Aufgaben, Tokens vom ersten richtigen Kandidaten bis `</think>`):
  Median 2.024 (0,6, n 15) und 6.073 (1,0, n 16); MIT 1,0: 6.886 (n 17).
- 07.11. 09:57 – **Antwort-Zwang ERGORE 0,6 im Einzelnen:** Die 18 falschen erzwungenen Antworten sind oft Verlegenheits-Werte –
  fünfmal „1“, einmal die Variable „p“. → Ein erzwungenes Antworten verdeckt Nichtwissen; Kandidat für den Ehrlichkeits-Weg:
  erzwungene Antwort nur ausgeben, wenn die Wahrheitssonde sie trägt, sonst „weiß ich nicht“ (nächste Messung, GPU, nach Absprache).
- 07.11. 10:13 – **Eingriff: CUDA-Speichermangel im Rest-Lauf.** Der Zwang-Server (8096, 6 Slots × 34.816 Kontext) bekam Präfixe bis
  ~33k Tokens, während der IFEval-Server (8097, ebenso 6 Slots) lief: „MUL_MAT failed / CUDA error: out of memory“ auf der 8-GB-Karte
  (im Nachtlauf nie aufgetreten, dort waren die Prompts kurz). Folgen: Zwang ERGORE 1,0 nach 3 Versuchen unvollständig (11 von 55
  Anfragen ohne Antwort), **IFEval-ERGORE-Versuch 1 riss um 10:02 ab** (Verbindung vom Server geschlossen), Versuch 2 setzt fort und
  läuft sauber. Zwang-Zweig der Rest-Kette gezielt gestoppt (IFEval und Kette unberührt). **Nachlauf seit 10:12:32**
  (`kette_zwang_nach.sh`): eigener Server auf 8098 mit EINEM Slot, Anfragen nacheinander, Fortsetzen; Grafikspeicher dabei 4,9 von
  8 GB. `kette_v22.sh` wartet nun auf Rest-Kette UND Zwang-Nachlauf. Lehre: lange Prompts nie mit 2 × 6 Slots auf 8 GB.
- 07.11. 10:13 – **Offline-Prüfung V2.2 (58_zig_pruefen.py, ERGORE gegen V2.2, Übungs-Präfixe aus ERGORE-/MIT-Läufen):**
  p(`</think>`) an richtigen Kandidaten-Enden ERGORE Median 1,8·10⁻¹² (0/8 über 0,5) → **V2.2 Median 1,00 (6/8)**, wie V2.1; an
  falschen Kandidaten-Enden unverändert (ERGORE 6,9·10⁻¹¹, V2.2 9,7·10⁻¹¹, 0/8). Gewöhnliche Stellen: folgt.
- 07.11. 10:17 – **Offline-Prüfung V2.2 vollständig:** gewöhnliche Denk-Tokens p(`</think>`) ERGORE Median 6,1·10⁻¹³, V2.2 4,1·10⁻¹¹
  (Höchstwert 7,9·10⁻¹⁰; 0/8 über 0,5) – absolut weiter vernachlässigbar (über 30.000 Tokens erwartet ~10⁻⁶ Fehl-Abschlüsse).
  Zusammen mit 10:13: richtig 6/8 sofort zu, falsch 0/8, gewöhnlich 0/8 → **V2.2 besteht die Offline-Prüfung wie V2.1.**
  Zwang-Nachlauf: ERGORE 1,0 21 → 29 (ende 8/37, beim eigenen Schließen 6/18), MIT 1,0 24 → 32 (ende 8/36, schließen 1/1).
  → Bei 1,0 hilft der Antwort-Zwang beiden gleich (+8); der Abstand ERGORE–MIT bleibt.
- 07.11. 10:29 – **Antwort-Zwang-Probe vollständig** (alle 6 Set-B-Läufe; Protokoll-Variante wie Budget-Forcing in s1: Antwort am
  Lauf-Ende erzwingen, wenn keine saubere da ist – für alle Modelle gleich): ERGORE 0,6 34 → **38**, ERGORE 1,0 21 → **29**,
  MIT 1,0 24 → **32**, Gatter 0,6 27 → **36**, Gatter 1,0 11 → **28**, Gatter3 0,6 28 → **36**. Paarweise MIT Zwang:
  ERGORE 1,0 gegen MIT 1,0 29:32 (1:4, p = 0,38); ERGORE 0,6 gegen Gatter 0,6 38:36 (4:2, p = 0,69); Gatter 1,0 gegen
  ERGORE 1,0 28:29 (2:3, p = 1,0); ERGORE 0,6 gegen ERGORE 1,0 38:29 (9:0, p = 0,004).
  → **Deutung:** Ein großer Teil der Unterschiede ohne Zwang ist „Antwort herausbringen“, nicht „Lösung finden“. Das Gatter
  (eigen-Basis) hatte bei 1,0 in 17 nie abgeschlossenen Läufen die Lösung schon, dachte aber bis zum Limit weiter. ERGOREs
  Dauer-Druck wirkt wie eine eingebaute Abgabe-Hilfe – mit Zwang-Protokoll schrumpft ERGOREs Vorsprung auf nicht signifikant,
  bei 1,0 liegt MIT vorn (n. s.). 0,6 bleibt klar besser als 1,0. **Für jede Veröffentlichung: Ergebnisse mit UND ohne
  Antwort-Zwang berichten.** Der Nachlauf lief nach dem Speicher-Eingriff fehlerfrei (10:12–10:27, 1 Slot).
- 07.11. 10:34 – **IFEval-Schadenscheck ERGORE (erstmals gemessen; 120 gleiche Prompts, gleiches Protokoll wie 06.11.: 0,6,
  vLLM-Stil, 32k, Seed 0, strikt Prompt-Ebene offiziell; nur 6 statt 12 Slots):** ERGORE **61/120 (50,8 %)** gegen eigen 74
  (61,7 %; 11:24, McNemar p = 0,041), MIT 87 (72,5 %; 4:30, p < 0,0001), Basis 18 (46:3). Tokens Ø ERGORE 2.937, eigen 5.348,
  MIT 3.753, Basis 11.948. Verluste vor allem bei Schlüsselwort-Anweisungen (ERGORE 11/38, eigen 22/38, MIT 26/38) und
  Kombi-Anweisungen (3/16, 7/16, 10/16).
  → **Der Dauer-Druck kostet Anweisungstreue:** ERGORE antwortet kürzer und lässt geforderte Einzelheiten weg. Das ist ein
  echter, vorab als Schadenscheck geplanter Befund. V2.2 (ERGORE + WT-Zünder) erbt den Dauer-Druck und vermutlich diesen Schaden
  – IFEval für V2.2 nach dem Mathe-Test einplanen (~1 h). Gegenpol: eigen + WT-Zünder (V2.1) hat keinen Dauer-Druck; mit
  Antwort-Zwang lag die eigen-Basis (Gatter) in Mathe gleichauf mit ERGORE (36:38 bei 0,6; 28:29 bei 1,0). Zur Besprechung.
- 07.11. 10:49 – **Namen (Nutzer):** V2.2 heißt **ERGORE-WT**, später kurz **ERWT** („W“ = Wahrheit, „T“ = Trau dich); für Phase 2
  z. B. „Qwen3.6-ERWT“, der Ehrlichkeits-Harnisch („weiß ich nicht“) folgt in der nächsten Runde. Bausteine sauber zugeordnet:
  **Umkehr** „Denk nicht endlos im Kreis“ (MIT, eigen, ERGORE) · **Dauer-Druck** „Komm zum Ende, immer, auch ohne Antwort“ (nur
  ERGORE – ERGOREs eigener Beitrag, und laut IFEval die Quelle des Anweisungs-Schadens) · **WT-Zünder** „Deine Antwort ist
  richtig, trau dich und gib ab“ (V2.1 und V2.2). ERGORE = Umkehr + Dauer-Druck; ERWT = Umkehr + Dauer-Druck + WT;
  V2.1 = Umkehr + WT (ohne Dauer-Druck).
- 07.11. 10:58 – **Plan-Änderung Schritt 2c (Nutzer: „V2.1 + V2.2 bei 0,6 sinnig … ggf. kompakteres Set“) – Vorab-Lesart,
  festgehalten BEVOR ein V2.1/V2.2-Lauf existiert; ersetzt die Lesart von 09:57:** V2.2 (ERGORE-WT, gguf ergo-v22) und V2.1
  (eigen-WT, gguf ergo-zig) gleichzeitig bei **0,6** (MIT-Protokoll), **erste 30 Aufgaben von Set B** (Datei-Reihenfolge, ohne
  Mischen; Stufen L1 4, L2 7, L3 5, L4 6, L5 8), 32k, Seed 0, vLLM-Stil, je 6 Slots; ~2 h. Vergleich auf denselben 30 Aufgaben:
  V2.2 gegen ERGORE 0,6 (17/30), V2.1 gegen Gatter 0,6 (12/30; Stellvertreter für die eigen-Basis, da Gatter3 = Gatter zeigte,
  dass der alte e⊥-Schub nichts bewirkt). Basiswerte (erste 30): Läufe mit richtigem Kandidaten im Denken ERGORE 8, Gatter 11;
  davon ≤ 64 Tokens danach geschlossen ERGORE 2 (25 %), Gatter 4 (36 %).
  **K1** kein Schaden: V2.2 ≥ 15, V2.1 ≥ 10 (je Basis − 2). **K2** WT wirkt beim echten Generieren: „Zünd-Quote“ (Anteil der
  Läufe mit richtigem Kandidaten im Denken, die ≤ 64 Tokens nach einem richtigen Kandidaten schließen) ≥ 60 % bei V2.2 UND bei
  V2.1, und ≥ 75 % aller schnellen Abschlüsse (beide zusammen) an richtigen Kandidaten. **K3** Ersparnis: beidseits gelöst
  (V2.2–ERGORE, V2.1–Gatter zusammen) weniger Tokens, Vorzeichentest einseitig p < 0,05. **K4** Sonde (Schicht 13) auf den
  neuen Kandidaten AUC ≥ 0,93. Beschreibend: V2.1 gegen V2.2 (richtig, nie zu, leeres Zucken, Tokens), McNemar, Antwort-Zwang
  auf den neuen Läufen, danach IFEval V2.1 (gegen eigen 74, ERGORE 61). Lesart: K2 bestanden → WT wirkt; Basis-Wahl aus Mathe
  (V2.1 gegen V2.2) UND IFEval gemeinsam besprechen; Nutzer-Idee für danach: „Umkehr + WT mit leichtem Dauer-Druck“
  (vorhandene ERGORE-Varianten mit kleinerem β). Einschränkung: n = 30 – nur grobe Treffer-Vergleiche möglich.
- 07.11. 11:04 – **Nutzer-Idee „Schub für den Ausschlagsgrund des Neurons, damit die Schwelle erreicht ist“ – Offline-Simulation**
  (nachträglich, Set B = Entwicklungssatz; eingefrorene Sonde Schicht 13 als Stellvertreter für das WT-Wahrheitssignal; alle
  1.748 Kandidaten im Denken aus 227 Läufen, 134 Läufe mit richtigem Kandidaten): **Einzelschuss** wie WT heute (Schwelle: 2 %
  der falschen darüber) feuert in 98/134 Läufen am richtigen Kandidaten (73 %), 3 Fehlschüsse; Schwelle gesenkt auf 4 % → 111/134
  (83 %), 9 Fehlschüsse; 6 % → 84 %, 13; 10 % → 87 %, 17 (Sättigung). **„Zweite Chance“** (gleicher Antwortwert zweimal mäßig
  sicher, Summation wie beim Membranpotenzial) ist NICHT besser als die einfach gesenkte Schwelle (bei 9 Fehlschüssen 107 gegen
  111). **Kein einziger Fehlschuss traf einen Lauf, der am Ende richtig war** (Schaden 0 in allen Varianten) – Fehlschüsse
  passieren nur in Läufen, die ohnehin falsch endeten. → Der einfachste „Schub für den Ausschlagsgrund“ ist eine etwas tiefere
  WT-Schwelle (Kandidat: 4-%-Stufe, +10 Prozentpunkte Zünd-Quote). Grenze: ~85 % – die übrigen richtigen Antworten wirken für die
  Sonde unwahr. Läufe ganz ohne richtigen Kandidaten kann kein Zünder retten → dort Harnisch („weiß ich nicht“), nicht
  Dauer-Druck. Saubere Bauform ohne „schmalen Grat“: Umkehr + WT (Schwelle abgestimmt) + Harnisch. Der laufende Test bleibt
  unverändert (vorab festgelegt); eine WT-Variante mit tieferer Schwelle wäre der nächste Bau (nur τ_T ändert sich).
- 07.11. 11:10 – **WT mit 4-%-Schwelle gebaut (Nutzer-Go „WT + 4% Schwelle“), noch kein Lauf:** eigen-WT4
  (modelle/Qwen3.5-0.8B-ergo-zig4; τ_T −0,131 auf der WT-Skala: richtige Kandidaten darüber 82,3 % statt 74,7 %, falsche 4,0 %
  statt 2,0 %; Umkehr 15/19 bitgleich mit eigen) und ERGORE-WT4 (modelle/Qwen3.5-0.8B-ergo-v22-4; gleiche Prüfungen wie V2.2,
  ERGORE-Metadaten unverändert). GGUF und Offline-Prüfung (58) laufen auf der CPU.
- 07.11. 11:10 – **Kann das Modell „weiß ich nicht“ sagen? (Nutzer-Frage; nur Text, alle Set-B-Läufe):** Ja, das Konzept ist da.
  Sätze wie „I don't know“, „I'm not sure“, „unsure“, „cannot determine“, „let me guess“ kommen vor – meist im Denken, bei
  ERGORE 1,0 auch im Antwortteil (unsure 5, guess 7, cannot determine 6). **Sie sagen Fehler voraus:** ERGORE 1,0 Läufe mit
  Unsicherheits-Satz 23 → nur 3 richtig (13 %), ohne 37 → 18 richtig (49 %); Gatter 1,0: 1/10 gegen 10/50; ERGORE 0,6: 2/6
  gegen 32/54; MIT 1,0 schwächer (6/12 gegen 18/48). **Aber nie als Endantwort:** kein einziger Lauf endet mit einer ehrlichen
  Enthaltung (z. B. boxed{unknown}). → Das Modell „weiß manchmal, dass es nicht weiß“, macht daraus aber keine ehrliche Antwort.
  Nutzer-Gedanke dazu: dreiwertig auslösen – Sonde WAHR → WT gibt ab; FALSCH gemessen → weiterdenken; weder WAHR noch FALSCH
  (und kein WAHR mehr bis zum Abschluss) → „trau dich, sag: weiß ich nicht“.
- 07.11. 11:16 – **Ehrlichkeits-Harnisch: Plan festgehalten** (ROADMAP_2026-11.md, Querschnitt). Nutzer: „erstmal so planen und vor
  jedem Schritt nochmal besprechen“ – Schritte 1 (Sonde auf erzwungenen Antworten), 2 („Weiß-nicht“-Richtung), 3 (Prompt-Vergleich)
  starten jeweils erst nach Besprechung. Einordnung in die Fuchsbau-Gleichung: E ↔ WT-Zünder, F ↔ zweiter Blick bei FALSCH,
  K ↔ ehrliches „weiß ich nicht“ als Übergabepunkt an den Harness.
- 07.11. 11:46 – **MiniPC als zweites Labor (Nutzer-Anweisung ~11:40: alle Ressourcen für die Forschung):** Der Alltagsbetrieb auf dem Rechner wurde dafür vorübergehend angehalten [Betriebsdetails entfernt]. Eval-Server nach MiniPC-Regel nur über 03_server.sh :8091,
  12 Slots, mainline-Build (Vulkan, iGPU): 61 Tokens/s einzeln, **185 Tokens/s bei 12 gleichzeitig**; vLLM-Stil-Sampler werden
  angenommen. Code: Laptop-Fassung von 03_eval.py als Kopie; Bewertung gleich (math-verify
  wie MiniPC-Original).
  **Vorab-Lesart MiniPC-Block (erste 30 Aufgaben von Set B, 0,6, 32k, Seed 0, vLLM-Stil, 12 Slots):**
  (1) **Eichung:** ERGORE auf dem MiniPC gegen den Laptop-Lauf (17/30). Gilt als gleichwertig, wenn der Treffer-Unterschied
  ≤ 3 ist und McNemar p ≥ 0,05; sonst nur Vergleiche innerhalb einer Maschine. (2) **eigen-WT4** (Umkehr + WT, 4-%-Schwelle)
  und (3) **ERGORE-WT4**: Zünd-Quote ≥ 60 % und ≥ 75 % der schnellen Abschlüsse an richtigen Kandidaten (wie K2 von 10:58);
  ERGORE-WT4 ≥ ERGORE(MiniPC) − 2; eigen-WT4 gegen Gatter/V2.1 (Laptop) nur, wenn die Eichung besteht.
  Reihenfolge 1 → 2 → 3, je ~60–80 min.
- 07.11. 11:50 – **Offline-Prüfung eigen-WT4 (58_zig_pruefen.py, eigen gegen zig4):** richtige Kandidaten-Enden 6/8 → p(`</think>`)
  ≈ 1 (wie WT 2 %; die 2 übrigen liegen auch unter der 4-%-Schwelle), falsche 0/8 (Median 6,3·10⁻¹¹, eigen 6,4·10⁻¹¹),
  gewöhnliche 0/8 (Median 1,8·10⁻¹¹, Höchstwert 2,6·10⁻⁸) → **bestanden**. ERGORE-WT4 rechnet noch.
  **MiniPC-Block läuft seit 11:47:47** (ERGORE-Eichung zuerst). **Tempo-Vergleich:** Laptop, gemittelt über ganze Nachtläufe
  (inkl. tiefer Kontexte): 22–24 Tokens/s je Platz → ~130–145 je Server (6 Plätze), zwei Server ~270–285 gesamt. MiniPC-Probe
  185 Tokens/s bei 12 Plätzen gilt nur für kurze Texte; der echte Vergleich folgt aus der Eichung (gleiche 30 Aufgaben).
- 07.11. 11:58 – **Offline-Prüfung ERGORE-WT4 (ERGORE gegen v22-4):** richtige Kandidaten-Enden 6/8 → p ≈ 1, falsche 0/8 (Median
  9,3·10⁻¹¹, ERGORE 6,9·10⁻¹¹), gewöhnliche 0/8 (Median 1,7·10⁻¹⁰, Höchstwert 8,7·10⁻⁹) → **bestanden**. Beide WT4-Bauten verhalten
  sich offline wie die 2-%-Bauten; auf diesen 8 Prüf-Präfixen bringt die tiefere Schwelle keinen zusätzlichen Treffer (die
  2 übrigen richtigen liegen tiefer). Ob sie im echten Lauf öfter zündet, zeigt der MiniPC-Block.
- 07.11. 12:10 – **KORREKTUR zur Schwellen-Simulation von 11:04 („Schaden 0 in allen Varianten“): Das war ein Auswertungsfehler.**
  Die Zuordnung Lauf → Endergebnis schlug still fehl (lauf ist „tag/id“, kein Dateipfad), daher stand der Schaden immer auf 0.
  Richtig nachgerechnet (alle 273 Läufe zugeordnet): 2 % → 98/134 Treffer, 3 Fehlschüsse, davon **1** in einem am Ende richtigen
  Lauf; **4 % → 111/134, 9 Fehlschüsse, davon 3**; 6 % → 112, 13, davon 4; 10 % → 117, 17, davon 5. → Die tiefere Schwelle ist
  NICHT kostenlos (+13 Zündungen an richtigen, +6 Fehlschüsse, +2 Schäden). Treffer-Zahlen unverändert.
- 07.11. 12:10 – **Warum erreichen richtige Kandidaten die Schwelle nicht? (Nutzer: „das Neuron muss die Schwelle wirklich
  erreichen“; 769 richtige Kandidaten im Denken, Sonde Schicht 13, 4-%-Schwelle):** unter der Schwelle („hart“, n = 288) gegen
  darüber („leicht“, n = 481): **Prüf-Wort in den 60 Tokens davor 51 % gegen 21 %** (verify/check/confirm/correct …),
  Absicherungs-Wort davor 29 % gegen 17 % (maybe/probably/seems …), Rang im Lauf Median 11 gegen 7, Lauf endet richtig 83 %
  gegen 85 %. → Die harten Fälle sind meist **vorläufige Erwähnungen mitten in einer Prüfung oder unter Vorbehalt** – das
  Modell behauptet die Antwort in dem Moment nicht, und die Sonde liest das zutreffend. Eine tiefere Schwelle würde genau dort
  zünden (Fehlschuss-Risiko). Nutzer-Idee in Mechanik übersetzt: nicht die Schwelle senken, sondern dem Modell helfen, nach
  einer gelungenen Prüfung die Antwort **klar zu behaupten** („So the answer is X“) – dort blitzt das Signal stark und WT zündet.
  Kandidat für einen späteren Baustein (nach den heutigen Läufen besprechen).
- 07.11. 12:11 – **Schritt-2-Urteil fertig (12:01):** V2 verfehlt K1, K2 UND **K3** – Sonde auf Gatter-Läufen AUC **0,892** (< 0,93);
  Gatter3 0,860, ERGORE 0,925, MIT 0,966 (je alle Kandidaten von Set B, Denken und Antwortteil). → Auf Set B liegt die Sonde
  schon bei ERGORE unter 0,93. **Änderung der Lesart des Kompakt-Tests, VOR jedem V2.1/V2.2-Lauf** (die Kette wartete noch,
  es gibt keine setB30-Ergebnisse): K4 wird relativ – AUC auf den neuen Kandidaten ≥ AUC der jeweiligen Basis (ERGORE bzw.
  Gatter) auf denselben 30 Aufgaben − 0,03. Grund: Ein fester Wert 0,93 würde auf Set B auch ohne jeden WT-Schaden verfehlt.
  62_v22_urteil.py entsprechend angepasst; K1–K3 unverändert.
- 07.11. 12:44 – **Argon-Feedback (PDF + Visual) eingeordnet** (recherche/argon/Argon_Feedback_Einordnung_2026-11-07_mittag.md).
  Übernommen: Schwelle per Risikokontrolle auf Lauf-Maxima (je Modell, Kreuzvalidierung nach Aufgaben-ID), 2×2-Trennversuch
  Wahrheit/Behauptung (vor jedem Behauptungs-Schub), Behauptungs-Schub nur als Kaskade (schiebt zum Ergebnissatz, nie zum
  Abschluss), „weiß ich nicht“ zuerst als äußerer Harnisch, vier Pflicht-Kennzahlen (Reinheit der Enthaltung, S_λ für λ = 1/3,
  Kalibrierungsfehler je Lauf, ΔIFEval), Set B als Entwicklungssatz + Bestätigung auf MATH-500 161–300 (N = 140),
  Block-Zuteilung der Aufgaben auf zwei Maschinen. Nicht übernommen: AUC-Toleranz −0,015 (unsere −0,03 steht seit 12:11).
  **Vorschlag Fortsetzungsregel für den Kompakt-Test (Argon F11.2), noch NICHT beschlossen, festgehalten bevor K2 ausgewertet
  wurde** (Teilergebnisse V2.2 17/30, V2.1 15/30 vorhanden, nicht angesehen): Liegt die Präzision der schnellen Abschlüsse
  zwischen 60 und 80 % oder die Zünd-Quote zwischen 40 und 60 %, werden Aufgaben 31–60 für beide Modelle nachgerechnet (~2 h);
  das Urteil K1–K4 bleibt unverändert. Entscheidung des Nutzers.
- 07.11. 12:58 – **Veröffentlichungsplan festgehalten** (ROADMAP, Abschnitt „Veröffentlichung“): erster Zwischenbericht spätestens
  08.11. abends, Entwurf v0.1 liegt vor; Gewichte erst nach Schritt 3; Go des Nutzers nach Säuberung, Geheimnis-Scan,
  Lizenzwahl und Gegenlesen. **2×2-Trennversuch (Argon F7) läuft auf der CPU** (63_wahrheit_behauptung.py): erster Durchgang
  mit 11 Fällen (je Aufgabe einer, Präfix ≤ 8.000 Tokens), Erweiterung auf mehrere Fälle je Aufgabe folgt.
- 07.11. 13:17 – **2×2-Trennversuch Wahrheit gegen Behauptung (Argon F7; 63_wahrheit_behauptung.py; n = 11 harte Fälle, je
  Aufgabe einer, 7 mit Prüf-Wort davor; Präfix ≤ 8.000 Tokens; eingefrorene Sonde Schicht 13, 4-%-Schwelle +0,66):**
  Wahrheits-Effekt ΔWahr im Mittel **+3,60** (positiv in 9/11), Behauptungs-Effekt ΔBehaupt **+0,65** (positiv in 9/11),
  Wechselwirkung **+2,88**. In der Behauptungs-Form trennt die Sonde wahr und falsch stärker als in der Prüf-Form.
  **„So the answer is X_falsch“ erreicht die Schwelle in 0/11** (Argons Widerlegungsgrenze 15 %) → **die Wahrheits-These hält**:
  Die Sonde liest vor allem Wahrheit, mit kleinem Behauptungs-Bias, der keine falsche Antwort über die Schwelle hob.
  **„So the answer is X_wahr“ erreicht die Schwelle in 3/11 (27 %; Wilson-95 % etwa 10–57 %)** → eine klare Behauptung hebt
  gut ein Viertel der harten Fälle sicher über die Schwelle (Argons Annahme 35 %, seine Widerlegungsgrenze für den
  Behauptungs-Schub 20 %). In 2/11 Fällen trennt die Sonde gar nicht (beide Formen tief). Grenzen: kleine Stichprobe,
  Entwicklungssatz, künstlich eingesetzte Sätze.
- 07.11. 13:30 – **MiniPC-Eichung (Vorab-Lesart 11:46):** ERGORE 0,6, erste 30 Set-B-Aufgaben: MiniPC **14/30** gegen Laptop **17/30**
  (nur MiniPC 0, nur Laptop 3; McNemar p = 0,25; gleiche Bewertung je Aufgabe 27/30; Tokens im Mittel 19.678 gegen 19.612).
  **Nach der Vorab-Lesart gleichwertig (Differenz ≤ 3 und p ≥ 0,05) – aber genau an der Grenze, und alle 3 abweichenden Aufgaben
  fielen zugunsten des Laptops aus.** Folge: Vergleiche über Maschinen hinweg nur mit Vorsicht; für Schritt 3 gilt Argons
  Block-Zuteilung (beide Modelle auf derselben Maschine je Aufgabenblock). MiniPC-Tempo über den ganzen Lauf: 10,7 Tokens/s je
  Platz, ~128 gesamt (12 Plätze), etwa wie ein Laptop-Server.
- 07.11. 13:30 – **Kompakt-Test, Rohzahlen (Urteil K1–K4 folgt aus 62_v22_urteil.py):** V2.2 (ERGORE-WT) **15/30**, Ø 11.399 Tokens
  (ERGORE auf denselben 30: 17, Ø 19.612); V2.1 (eigen-WT) **16/30**, Ø 16.179 Tokens (Gatter als eigen-Stellvertreter: 12,
  Ø 24.070). Denken geschlossen: V2.2 29/30, V2.1 25/30.
- 07.11. 13:36 – **URTEIL Kompakt-Test (62_v22_urteil.py, Lesart vorab 10:58/12:11):** **K1 ERFÜLLT** (V2.2 15 ≥ 15; V2.1 16 ≥ 10).
  **K2 NICHT ERFÜLLT** – Zünd-Quote 0 % bei beiden (nur je 1 Lauf mit richtigem Kandidaten im Denken, keine schnellen
  Abschlüsse nach Kandidaten). **K3 ERFÜLLT** (beidseits gelöst: 23 weniger, 2 mehr Tokens, p < 0,0001). **K4 ERFÜLLT** (Sonde
  V2.2 0,928 gegen ERGORE 0,859; V2.1 0,977 gegen Gatter 0,711). McNemar: V2.2–ERGORE 1:3 (p = 0,63), V2.1–Gatter 5:1 (p = 0,22),
  V2.2–V2.1 1:2. Leeres Zucken V2.2 5 (ERGORE 11), V2.1 8 (Gatter 8); nie zu V2.2 1, V2.1 5 (Gatter 10).
- 07.11. 13:36 – **Grund für K2 gefunden (Nachuntersuchung, 64_wt_frueh_zuendung.py, CPU): WT zündet schon am Ende der
  Aufgabenstellung.** Denk-Länge bis `</think>`: Median V2.2 981 (ERGORE 8.868), V2.1 820 (Gatter 17.788); **10/30 (V2.2) bzw.
  9/30 (V2.1) Läufe schreiben `</think>` als allererstes Token – davon 17 von 19 richtig.** Offline auf 5 Aufgabenstellungen: die
  16 WT-Neuronen feuern am letzten Prompt-Token (`\n` nach `<think>`) mit Summe +6,5 bis +8,2 (eigen: +0,4), daneben an
  „assistant“/„<think>“; p(`</think>` als 1. Token) **0,64–0,73** statt ~10⁻³ bei eigen. → **Verteilungs-Leck:** Kandidaten-Ende-
  und Wahrheits-Detektor wurden nur an Stellen im Denken gelernt und geprüft, nie an Prompt-/Vorlagen-Tokens; dort schlagen beide
  an. Die Offline-Prüfung (58) hatte diese Stelle nicht abgedeckt. **Der geplante Mechanismus (Zünden an richtigen Kandidaten im
  Denken) kam dadurch kaum zum Zug.** Nebenbefund [Plausibel]: Wo das Leck stark zündet, ist die Aufgabe oft leicht – sofortiges
  Schließen führte in 17/19 Fällen zur richtigen Antwort („Frühes Vertrauen“?), ungeprüft. **Folgen:** (1) Fix: Kandidaten-Ende-
  Detektor mit Prompt-/Vorlagen-Tokens als Negativbeispielen neu lernen bzw. eine dritte Bedingung „im Denken“; (2) Pflicht-
  Prüfung künftig: p(`</think>` als 1. Token) muss bei eigen-Niveau bleiben; (3) MiniPC-WT4-Läufe haben dasselbe Leck (tiefere
  Schwelle → vermutlich häufiger) und laufen beschreibend weiter.
- 07.11. 13:46 – **Mechanismus des Prompt-Lecks gefunden** (65_wt_leck_diagnose.py): Am letzten Prompt-Token (`\n` nach `<think>`) ist
  das V2.1-Gate nur halb zu (Vor-Aktivierung ≈ −0,55 → SiLU ≈ −0,2, negativer Ast), up ≈ −1,8 → **Produkt ≈ +0,37 je Neuron,
  Schub ≈ +0,9 entlang ĝ** (Ziel an richtigen Kandidaten: 7). An dieser Stelle ist p(`</think>`) schon ~10⁻³ (Qwen kennt leere
  Denkblöcke), der kleine Schub reicht für ~0,7. Die Linearanalyse über alle Prompt-Tokens zeigte das nicht (Median +0,05); erst
  die letzte Position. **Zwei Fix-Bauten** (66_wt_fix_bauen.py, Umkehr bitgleich mit eigen): **A** = V2.1-Bedeutung, Nullpunkt von
  up an den Median gewöhnlicher Denk-Tokens (τ_C −9,24) → Produkt mit dem negativen SiLU-Ast ≤ 0; **B** = dreiwertig (Nutzer-Idee):
  gate = Kandidaten-Ende, up = Wahrheit um τ_T mit Vorzeichen → richtig: Schub zum Abschluss, falsch: Schub weg davon.
  **Pflicht-Prüfung „erstes Token“** (67_erstes_token.py, 30 Set-B-Prompts), p(`</think>` als 1. Token): eigen Median 1,2·10⁻³
  (Max 8,1·10⁻³); **V2.1 Median 0,22 (Max 0,84; 33 % > 0,5)**; **Fix A 0,9·10⁻³ (Max 1,1·10⁻²)**; **Fix B 2,0·10⁻³ (Max 9,1·10⁻³)** →
  beide Fixe schließen das Leck. Offline-Prüfung an Kandidaten-Enden (58) läuft.
- 07.11. 13:46 – **„Frühes Vertrauen“ – erster Befund (beschreibend, klein):** Die Sofort-Abschlüsse von V2.1 lagen auf den Stufen 1–4
  (2/4/2/1, keine Stufe 5), alle 9 richtig; übrige Aufgaben Stufen 1–5 (2/3/3/5/8), 7/21 richtig. **Dieselben 9 Aufgaben mit
  Denken (Gatter): 6/9 richtig bei Ø 19.287 Tokens – ohne Denken (V2.1): 9/9 bei Ø 3.130 Tokens.** → Auf diesen Aufgaben war
  Nicht-Denken genauer UND ~84 % billiger (Überdenken schadet bei leichten Aufgaben). Das Leck-Signal wählt überwiegend leichte
  Aufgaben, aber nicht nur nach Stufe. **Nutzer-Idee: eigene Spur „schneller abschließen ohne Denk-Schleife“** – eine bewusst
  gebaute **Denk-Weiche** am Ende der Aufgabenstellung (eigener Detektor, gelernt auf Übungsdaten, Schwelle mit Garantie).
  Einordnung Fuchsbau: S-Kammer (sicher gelöst → nicht denken). Kleine Stichprobe, Entwicklungssatz, Zufallsprodukt – erst prüfen.
- 07.11. 13:58 – **MiniPC-WT4-Lauf gestoppt (Nutzer-Vorschlag „abbrechen und mit Fix neu in die Pipe“):** Die 4-%-Varianten verstärken das
  Prompt-Leck nicht, sie verlagern es: erstes Token p(`</think>`) Median ~10⁻⁵ (Max 0,41–0,44; 13 % > 0,01), aber eigen-WT4 auf dem
  MiniPC schloss das Denken nach im Median **274 Tokens** ohne Kandidat (0 Sofort-Abschlüsse, 11/20 richtig, nur 1 Lauf mit richtigem
  Kandidaten im Denken). Mechanismus wie beim Prompt-Leck (negativer SiLU-Ast × negatives up), nur an frühen Denk-Stellen. 21/30
  Ergebnisse gesichert. Fix A und eigen (GGUF) auf den MiniPC kopiert. Neue Pflicht-Prüfung „frühe Absätze“ (68_absatz_test.py)
  folgt nach der Offline-Prüfung (58).
- 07.11. 13:58 – **VORSCHLAG Vorab-Lesart Test WT-A (gilt erst mit Nutzer-Go und nur, wenn 58 und 68 bestehen; vor jedem WT-A-Lauf
  festgehalten):** Set B, 60 Aufgaben, 0,6, 32k, Seed 0, vLLM-Stil. **Block-Zuteilung (Argon F11.4):** Aufgaben 1–30 auf dem Laptop
  (eigen ‖ WT-A, je 6 Slots), Aufgaben 31–60 auf dem MiniPC (eigen, dann WT-A, 12 Slots). Paarvergleiche nur innerhalb eines Blocks,
  zusammengefasst über beide Blöcke. **Erstmals echte eigen-Läufe auf Set B** (bisher nur das Gatter als Stellvertreter).
  **K0 Mechanik:** Sofort-Abschlüsse WT-A ≤ eigen + 1 je Block, und frühe Abschlüsse ohne Kandidat (`</think>` in den ersten 500
  Denk-Tokens ohne Kandidat davor) ≤ eigen + 2 gesamt. **K1 kein Schaden:** WT-A ≥ eigen − 3 (60 Aufgaben). **K2 WT wirkt:**
  Zünd-Quote ≥ 60 % und Präzision der schnellen Abschlüsse ≥ 75 %; Fortsetzungsregel: mindestens 10 Läufe mit richtigem Kandidaten
  im Denken, sonst „nicht beurteilbar“ statt „nicht erfüllt“. **K3 Ersparnis:** beidseits gelöst weniger Tokens (Vorzeichentest
  einseitig p < 0,05). **K4 Sonde:** AUC ≥ eigen − 0,03. Beschreibend: Vergleich mit V2.1 (Leck) und Gatter, Zwang-Probe, Denk-Länge.
- 07.11. 14:01 – **Nutzer-Go für den WT-A-Test („Jap in Ordnung. Dann machen wir das so.“):** Die Vorab-Lesart von 13:58 (K0–K4,
  Block-Zuteilung Laptop 1–30 / MiniPC 31–60, je eigen und WT-A) gilt damit als festgelegt – **vor jedem WT-A- und eigen-Lauf auf
  Set B**. Start erst nach bestandener Offline-Prüfung (58: richtige Kandidaten-Enden schließen, falsche und gewöhnliche nicht;
  68: p(`</think>`) an frühen Absätzen auf eigen-Niveau).
- 07.11. 14:03 – **Prognosen für den WT-A-Test (vor jedem WT-A- und eigen-Lauf festgehalten, zum späteren Abgleich):**
  (1) **K0 Mechanik:** Sofort-Abschlüsse und frühe Abschlüsse ohne Kandidat etwa wie eigen (je Block 0–1). (2) **Richtige
  Kandidaten im Denken:** bei eigen auf 60 Aufgaben etwa 18–25 Läufe (Gatter: 11 auf 1–30) → K2 beurteilbar. (3) **Zünd-Quote**
  60–75 % (offline 6/8; die übrigen liegen unter der Schwelle) → K2 knapp; **Präzision** hoch, 85–95 % (Fehlschuss-Rate 2 %).
  (4) **Treffer** WT-A ≈ eigen +0 bis +4 auf 60 Aufgaben (Obergrenze eines Kandidaten-Zünders aus den Gatter-Läufen: +4 auf 60);
  kein großer Sprung. (5) **Tokens auf beidseits gelösten Aufgaben** 20–40 % weniger (eigen denkt nach der ersten richtigen
  Antwort im Median noch Tausende Tokens weiter). (6) **Nie geschlossene Läufe** wie bei eigen – WT hilft nicht, wo keine richtige
  Antwort entsteht (Ort für den späteren Harnisch). (7) **Der Sofort-Abschluss-Effekt von V2.1 verschwindet** (gewollt); auf den
  leichten Aufgaben kehrt das Überdenken zurück → gegenüber V2.1 vermutlich mehr Tokens und dort 1–3 Treffer weniger. Die
  „Denk-Weiche“ wird getrennt und bewusst gebaut. (8) **Sonde (K4)** hält.
- 07.11. 14:16 – **Vorab-Lesart Schritt 3 (Nutzer-Go: „140 frische MATH-500-Aufgaben über Nacht“; festgehalten vor jedem Lauf):**
  MATH-500-Aufgaben **161–300** (Datei-Reihenfolge, von keinem unserer Läufe berührt), 0,6, 32k, Seed 0, vLLM-Stil. **Block-Zuteilung:**
  Laptop 161–260 (MIT ‖ ERGORE, je 6 Slots), MiniPC 261–300 (MIT, dann ERGORE, 12 Slots); Paarvergleiche je Block, dann zusammen.
  **Lesart gleich wie 40_urteil80/46_urteil160:** *geknackt* = ERGORE > MIT und McNemar p < 0,05; *MIT-Niveau erreicht* = ERGORE ≥
  MIT − 3 (2,5 % von 140, abgerundet) und MIT nicht signifikant besser (p ≥ 0,05); sonst *nicht erreicht*. Dasselbe für **1–300
  zusammen** (Grenze −7). Beschreibend: gepaarte Differenz mit 95-%-Intervall, Tokens (Vorzeichentest), je Block. **WT-A kommt nur
  hinzu, wenn das heutige WT-A-Urteil K0, K1 und K2 erfüllt** – dann auf denselben Blöcken, Lesart wie K1–K3 des WT-A-Tests gegen
  ERGORE und MIT. Prognose (vorab): ERGORE und MIT gleichauf (|Differenz| ≤ 5), ERGORE mit 10–15 % weniger Tokens.
- 07.11. 14:21 – **Ergänzung Schritt 3 (Nutzer: „Fix A und WT-A mit reinnehmen“; vor jedem Schritt-3-Lauf):** WT-A (= WT mit Fix A)
  läuft in der Nacht **in jedem Fall mit**, nach MIT und ERGORE auf denselben Blöcken (Laptop 161–260 auf beide Server verteilt:
  161–210 / 211–260; MiniPC 261–300). **Die Lesart bleibt:** Als *Bestätigung* zählt WT-A auf 161–300 nur, wenn das heutige
  WT-A-Urteil K0, K1 und K2 erfüllt; sonst sind die WT-A-Zahlen auf 161–300 *beschreibend*, und für eine spätere WT-Bestätigung
  bleiben die unberührten MATH-500-Aufgaben 301–500. Vergleich WT-A gegen ERGORE und MIT nach K1–K3 des WT-A-Tests.
- 07.11. 14:32 – **„Frühes Vertrauen“ – Signal am Ende der Aufgabenstellung sagt Lösbarkeit voraus (69_fruehes_vertrauen.py;
  nachträglich, beschreibend; nur vorhandene Läufe):** AUC für „wird gelöst“ – Set B ERGORE 0,6 (n 60): Stufe 0,774, **V2.1-Gatter-
  Produkt am letzten Prompt-Token 0,803**; Set B Gatter 0,6: Stufe 0,711, Gatter 0,684; MATH-500 1–160 ERGORE (n 160): Stufe 0,714,
  **Gatter 0,720**; MIT: Stufe 0,746, **Gatter 0,771**. Die Wahrheitssonde s_T allein wirkt **umgekehrt** (AUC 0,19–0,30, also
  0,70–0,81 mit umgedrehtem Vorzeichen), auch innerhalb gleicher Stufen (umgedreht 0,53–0,74). → Vor jedem Denken trägt das
  Modell ein Signal, das Lösbarkeit etwa so gut wie die Schwierigkeitsstufe vorhersagt, teils darüber hinaus. Passt zu Kadavath
  et al. 2022 (P(IK) aus der Frage). Einschränkungen: nachträglich, mehrere Merkmale und Gruppen, Richtung von s_T noch
  ungeklärt (am Prompt-Ende außerhalb des Lernbereichs). Grundlage für die Denk-Weiche.
- 07.11. 14:37 – **IFEval V2.1 (eigen + WT, ohne Dauer-Druck; Schritt 2c, beschreibend):** **77/120 (64,2 %)**, Anweisungen 71,3 %,
  Ø 3.514 Tokens. Gegen eigen 74 (14:11, p = 0,69) – **kein Schaden**; gegen ERGORE 61 (25:9, **p = 0,009**) – klar besser; gegen
  MIT 87 (10:20, p = 0,10). → Ohne pauschalen Dauer-Druck bleibt die Anweisungstreue auf eigen-Niveau. Stützt die Bauform
  „Umkehr + WT ohne Dauer-Druck“. Vorbehalt: V2.1 hatte das Prompt-Leck (in IFEval vermutlich ebenfalls Sofort-Abschlüsse).
  **Frühe Absätze (68), Zwischenstand:** eigen Median 1,9·10⁻⁷ (90 % 1,7·10⁻⁶), V2.1 1,5·10⁻⁷ (1,6·10⁻⁶ … Max 5·10⁻²), **eigen-WT4
  5·10⁻⁷, 90 % 1,5·10⁻⁴ (100× eigen), Max 3·10⁻²** → bestätigt das Leck der 4-%-Variante an frühen Absätzen. Fix A rechnet noch.
- 07.11. 14:44 – **Fix A besteht auch „frühe Absätze“ (68):** p(`</think>` nach Absatz) Median 1,8·10⁻⁷ (eigen 1,9·10⁻⁷), 90 % 1,3·10⁻⁶
  (eigen 1,7·10⁻⁶), Max 2,8·10⁻⁵, 0 % > 0,01 → **alle Offline-Prüfungen bestanden** (erstes Token, richtige/falsche/gewöhnliche
  Stellen, frühe Absätze). Offen gesagt: Der Laptop-Block WT-A startete automatisch um 14:41:58, gut zwei Minuten **bevor** das
  Ergebnis von 68 vorlag (~14:43); das Ergebnis war positiv, die Startbedingung „nach bestandener Prüfung“ also nur knapp nicht
  eingehalten. MiniPC: WT-A startet regulär nach eigen.
- 07.11. 14:44 – **2×2-Erweiterung (GPU, bf16; bis 4 Fälle je Aufgabe, Präfix ≤ 16k; n = 27 neue harte Fälle):** ΔWahr **+4,08** (positiv
  in 96 %), ΔBehaupt +0,82 (positiv in 78 %), Wechselwirkung +2,40; „So the answer is X_falsch“ über der Schwelle **0/27**,
  „X_wahr“ **7/27 (26 %)**. **Zusammen mit dem ersten Durchgang (n = 38): falsche Behauptung nie über der Schwelle (0/38; obere
  95-%-Grenze ≈ 9 %), richtige Behauptung 10/38 (26 %), Wahrheits-Effekt positiv in 35/38.** → Die Sonde liest Wahrheit; eine
  klare Behauptung hebt rund ein Viertel der harten richtigen Fälle sicher über die Schwelle. Grundlage für den Behauptungs-Schub
  (Argon F8; dessen Widerlegungsgrenze 20 %).
- 07.11. 14:58 – **WT-A-Urteil: Ergänzung zu K2 nach Argons Nachmittags-Prüfung (festgelegt, bevor ein WT-A-Lauf ausgewertet ist; Stand:
  Laptop eigen 2/30, WT-A 4/30 fertig und nicht angesehen; MiniPC eigen 5/30, WT-A noch nicht gestartet):** K2 gilt als bestanden, wenn
  **(a)** Zünd-Quote ≥ 60 % und Präzision ≥ 75 % (wie bisher) **oder (b)** Zünd-Quote ≥ 50 % und Präzision ≥ **85 %** und K0, K1, K3
  bestanden. Unverändert: weniger als 10 Gelegenheiten → „nicht beurteilbar“; dann zählt WT-A auf 161–300 nur beschreibend. Berichtet
  werden beide Lesarten. Begründung: Präzision ist wichtiger als Abdeckung, denn ein falscher früher Abschluss wiegt schwerer als ein
  verpasster. Zu erwarten sind nur etwa 16–22 Gelegenheiten (Basisläufe Set B: ERGORE 8/30, Gatter 11/30, nicht Argons 33/60); ein
  einzelner Lauf macht dann 5 Prozentpunkte aus.
  **Zusätzlich beschreibend im WT-A-Urteil (Argon, Prüfstelle 5):** Läufe mit zweitem `</think>` oder ohne `\boxed` im Antwortteil,
  eigen gegen WT-A. **Token-Angaben ab jetzt immer doppelt** (Argon, rote Flagge 2): Ø über alle Aufgaben und Ø auf den gemeinsam
  gelösten Aufgaben.
  **Restleck von Fix A gemessen (Argon F2; 24.000 gewöhnliche Denk-Tokens aus gatter_lern.npz; Einheiten entlang ĝ, volle Zündung
  = 7):** Das Leck über den Minus-Ast beträgt höchstens **0,34** (V2.1: 2,5; zum Vergleich das Prompt-Leck von V2.1: 0,9). Über
  0,3 Einheiten liegen **0,68 %** der Tokens (V2.1: 10,6 %), davon **99 % bei offenem Wahrheits-Gate** (s_T > τ_T; das trifft auf
  1,6 % aller Tokens zu). Argons Annahme „up ≈ −0,8 im 10-%-Quantil“ trifft nicht zu (gemessen: −0,24). → **Fix A+ (1), also den
  Nullpunkt tiefer legen, wird nicht übernommen:** Es würde up gerade dort öfter positiv machen, wo das Gate offen ist, aber kein
  Kandidat endet, und damit das verbleibende Risiko vergrößern. Dieses Risiko zeigt sich in der K2-Präzision. (2), ein steileres
  Gate, ist für eine spätere Version vorgemerkt (kleiner Gewinn). **Für jede weitere WT-Version sind Argons Prüfstellen 3 und 4
  Pflicht:** das Satzende nach einer verworfenen Probe und das Zwischenergebnis einer Teilgröße.
- 07.11. 15:25 – **Nutzer-Go für den Nachtplan („Ja, freigeben“, kurz nach 15:00; Plan aus der Argon-Einordnung, Ehrlichkeit Schritt 1
  eingeschlossen).** Lesarten vorab, festgehalten **vor jedem dieser Läufe**:
  **(N1) Ehrlichkeit Schritt 1** (71_ehrlichkeit_schritt1.py, GPU, keine Modelländerung). Die eingefrorene Schicht-13-Sonde
  (wahrheitsmelder_eingefroren.npz, Schwelle vom 06.11.) wird an der *abgegebenen* Antwort gelesen:
  - Antwort-Arten: letztes `\boxed` im Antwortteil; sonst die erzwungene Antwort (60_antwort_zwang, Variante „ende“); sonst bei
    richtigen Läufen ohne Antwortteil das letzte `\boxed` im Denken; sonst „keine Antwort“.
  - Harnisch-Regel: antworten nur bei Sondenwert ≥ Schwelle, sonst „weiß ich nicht“.
  - **H1 (Argon): AUC auf den erzwungenen Antworten (alle Sätze zusammen) ≥ 0,75, sonst widerlegt.**
  - **H2: S₂ = (richtig − 2·falsch)/N mit Harnisch > S₂ ohne Harnisch (mit Erzwingen), alle Sätze zusammen.**
  - Beschreibend: Risiko-Abdeckung, Enthaltungs-Reinheit, S₁/S₃, je Satz.
  - Sätze: Set B (alle vorhandenen Läufe), MATH-500 1–160 (MIT, ERGORE) und **161–300 als frischer Teil** (getrennt berichtet).
  - Erzwungene Antworten für die neuen Sätze werden vorher mit 60_antwort_zwang erzeugt. Für die MiniPC-Läufe geschieht das auf dem
    Laptop; das ist eine kurze Fortsetzung, vermerkt.
  **(N2) IFEval WT-A** (Laptop, 120 Prompts, wie die bisherigen IFEval-Läufe). Prognose ≥ 72; **widerlegt bei ≤ 64**. Gepaart
  (McNemar) gegen eigen 74, ERGORE 61, MIT 87, V2.1 77.
  **(N3) Denk-Weiche** (eval/03b_eval_ohne_denken.py = 03_eval mit Prompt-Ende `<think>\n\n</think>\n\n`, offizielle
  Nicht-Denk-Vorlage):
  - Lauf: eigen auf Set B (60) und MATH-500 1–160, 0,6, 32k, Seed 0, vLLM-Stil, Laptop.
  - **Haupttest (72_denk_weiche.py):** logistische Regression „ohne Denken gelöst“ ~ Stufe (Dummies) + log(Prompt-Tokens) +
    Datensatz (M0) gegen M0 + s_T + s_C am Ende des Denk-Prompts (M1); Likelihood-Ratio-Test, df 2. **Widerlegt bei p > 0,05.**
  - Dazu 5-fach-CV-AUC M0 gegen M1.
  - Beschreibend: ohne gegen mit Denken je Aufgabe; Weiche (oberstes Quintil der zurückgehaltenen M1-Vorhersage ohne Denken)
    gegen immer Denken. Die Set-B-Denkläufe von eigen stammen zur Hälfte vom MiniPC (vermerkt).
  **(N4) Nur bei offenem WT-A-Tor** (K0 ∧ K1 ∧ K2, 70_wta_urteil.py): WT-A auf MATH-500 1–160, nur Laptop (gepaart mit den
  dortigen MIT-/ERGORE-Läufen), **nur beschreibend** (1–160 waren Entwicklungsdaten; Gate und ĝ stammen aus Übungsläufen).
  **(N5) Zweiter Seed (Seed 1)** auf Set B: MIT, ERGORE, WT-A, eigen; Laptop 1–30, MiniPC 31–60. Beschreibend:
  Sampling-Streuung gegen Modell-Unterschiede. 301–500 bleiben unberührt.
- 07.11. 15:25 – **Nebenbefund aus dem Programmtest von 72 (nachträglich, beschreibend; Denk-Läufe statt ohne-Denken-Läufe):**
  Auf den vorhandenen *Denk*-Ergebnissen (ERGORE, Set B + MATH-500 1–160, n = 220) sagt das Prompt-Ende-Signal kaum mehr voraus
  als Stufe, Prompt-Länge und Datensatz: LR-Test p = 0,08, CV-AUC M0 0,756 gegen M1 0,758. → Der „frühes Vertrauen“-Befund
  (14:32, nur gegen die Stufe verglichen) ist damit für Denk-Läufe **weitgehend durch Schwierigkeit und Länge erklärt**. Die
  eigentliche Prüfung bleibt der Lauf ohne Denken heute Nacht (N3).
- 07.11. 15:37 – **Korrektur an N5 (vor jedem dieser Läufe):** Auf Set B gibt es **keinen MIT-Lauf bei 0,6** (nur MIT 1,0). Deshalb
  rechnet N5 für MIT **Seed 0** als Referenz (Laptop 1–30, MiniPC 31–60, Block-Zuteilung wie eigen und WT-A) statt eines zweiten
  Seeds. **ERGORE Seed 1** läuft ganz auf dem Laptop (1–30 ‖ 31–60), weil Seed 0 (setB-ergore-t06) ganz auf dem Laptop lief; so
  bleibt der Seed-Vergleich auf einer Maschine. **eigen und WT-A Seed 1** laufen in der Block-Zuteilung von Seed 0. Ketten:
  kette_nacht_laptop.sh (wartet auf das Ende von Schritt 3 auf dem Laptop) und kette_minipc_nacht.sh (wartet auf das Ende von
  Schritt 3 auf dem MiniPC).
- 07.11. 15:48 – **N6 (Nutzer: „Ja, füllen“; vor jedem dieser Läufe):** Der MiniPC ist nach seiner Nachtkette (~04:00) frei und rechnet
  **MIT und ERGORE mit Seed 1 auf MATH-500 261–300** (0,6, 32k, vLLM-Stil, 12 Slots; dieselbe Maschine wie Seed 0, Ordner
  s3-mit-261-300-s1 und s3-ergore-261-300-s1). **Beschreibend:** Die vorab festgelegte Hauptaussage bleibt Seed 0 auf 161–300.
  Berichtet werden ERGORE gegen MIT bei Seed 1 (gepaart, McNemar) und die Übereinstimmung Seed 0 / Seed 1 je Modell und Aufgabe.
  Frage dahinter: Hält das Schritt-3-Ergebnis bei einer anderen Stichprobe? Kette: kette_minipc_nacht2.sh (wartet
  auf „Nachtkette MiniPC fertig“). Erwartetes Ende ~07:30.
- 07.11. 15:55 – **Kein Zwischenblick (Nutzer: „Bis 18:00 warten“):** Block 1 (Laptop) wird nicht vorab angesehen. Das WT-A-Urteil (70) läuft erst, wenn beide Blöcke vollständig sind (erwartet ~18:00). Bis dahin wurde nur der Fortschritt gezählt, keine Ergebnisse gelesen.
- 07.11. 15:58 – **Ungewollter Zwischenblick (offen vermerkt):** Beim Prüfen des Wächters habe ich das Ende von logs/kette_wta.log angezeigt. Dort stand die Abschlusszeile des WT-A-Laufs Block 1 (15:55): **16/30 richtig, 37 % Schleife oder Limit**. Das eigen-Ergebnis von Block 1 lief da noch und wurde nicht gesehen, ebenso nichts vom MiniPC. Die Zahl allein sagt nichts über K0–K3. Kriterien und Tor bleiben unverändert (alles vor 14:58 festgelegt); bis zum Urteil steht keine Entscheidung an, die davon abhängt. Abhilfe: Wächter-Berichte blenden ab jetzt die Ergebnis-Zusammenfassungen aus.
- 07.11. 16:23 – **Nachtrag zum Zwischenblick:** Der Wächter-Bericht von 16:23 zeigte außerdem die Sammelzeile der K4-Messdaten von Block 1 (eigen und WT-A *zusammen*: 38 Läufe mit Kandidaten, 316 Kandidaten-Stellen, davon 163 richtig). Ohne Trennung nach Modell ist das keine Kriterien-Größe. Der Filter blendet solche Zeilen jetzt ebenfalls aus.
- 07.11. 17:45 – **WT-A-URTEIL (70_wta_urteil.py, vorab festgelegt; beide Blöcke vollständig um 17:41; Block 2 kopiert,
  md5 geprüft):**
  **K0 Mechanik ERFÜLLT:** 0 Sofort-Abschlüsse, 0 frühe Abschlüsse ohne Kandidat (eigen ebenso). Das Prompt-Leck ist weg.
  **K1 kein Schaden ERFÜLLT:** WT-A **31/60** gegen eigen **23/60** (nur WT-A 9, nur eigen 1; McNemar p = 0,021 – beschreibend,
  denn K1 war als Nicht-Unterlegenheit festgelegt, nicht als Überlegenheitstest).
  **K2 NICHT BEURTEILBAR:** nur **2 Gelegenheiten** in den WT-A-Läufen (eigen 22). Zünd-Quote 1/2, Präzision 1/2; Basis eigen 3/22.
  **K3 Ersparnis ERFÜLLT:** beidseits gelöst 22, weniger Tokens bei 21, mehr bei 1, p < 0,0001. Ø **5.248 gegen 14.776**
  (Summe −64 %, Median je Aufgabe −70 %); über alle Aufgaben Ø 16.523 gegen 24.698.
  **K4 Block 1 NICHT erfüllt:** AUC 0,821 (121 Kandidaten) gegen eigen 0,992 (195). Block 2 folgt nachts; K4 gehört nicht zum Tor.
  **TOR ZU:** WT-A auf 161–300 ist **nur beschreibend**; der Nachtlauf WT-A auf 1–160 entfällt (Kette prüft das selbst).
  Prognosen (14:03): Gelegenheiten eigen 18–25 → 22 ✓; Treffer +0…+4 → **+8**; Tokens −20…−40 % → **−64 %**; Zünd-Quote und
  Präzision nicht messbar.
  Beschreibend: Denken nie geschlossen WT-A 14, eigen 24. Denk-Länge (Median) WT-A ~2.000–2.600 Tokens gegen ~16.000.
  **Zweites `</think>` im Antwortteil bei 36/60 WT-A-Läufen (eigen 1)** – Argons Prüfstelle 5: WT zündet auch nach dem
  Abschluss noch.
- 07.11. 17:45 – **Warum K2 nicht messbar war (NACHTRÄGLICH, beschreibend; 74_wta_abschluss_ort.py):** WT-A schließt das Denken
  meist, *bevor* das Modell „\boxed{…}“ oder „answer is …“ schreibt, also bevor unser Kandidaten-Erkenner etwas sieht. Von 46
  Abschlüssen lagen 33 ohne jeden erkannten Kandidaten davor (eigen: 10 von 36). Typisch ist ein Abschluss direkt nach einem
  Ergebnis-Satz wie „So $\binom{10}{8} = 45$.“
  Ein erweiterter, nachträglicher Erkenner (letzter Wert in den 64 Tokens vor `</think>`) findet:
  - WT-A: **25 von 46 Abschlüssen direkt nach einem richtigen Wert, 21 nach einem anderen Wert** (Zwischen- oder falsches
    Ergebnis; davon 8 Läufe am Ende doch richtig);
  - eigen: 15 von 36 nach richtigem, 20 nach anderem Wert.
  → WT-A schließt häufiger an richtigen Werten, aber nicht sauber; die Präzision liegt bei höchstens ~55 %.
  **Das ist keine Bestätigung der Vorab-Lesart.** Eine echte Prüfung braucht eine vorab festgelegte, breitere Kandidaten-Definition
  auf frischen Daten (301–500 bleiben dafür reserviert).
- 07.11. 18:20 – **Breiterer Antwort-Erkenner v2 (76_kandidaten_v2.py; NACHTRÄGLICH entwickelt, beschreibend; Set B, 60 Aufgaben):**
  v2 = alter Erkenner ∪ Wert-Aussagen („= W“, „is W“ am Satz- oder Formelende).

  | | WT-A | eigen | ERGORE 0,6 |
  |---|---|---|---|
  | richtig | 31 | 23 | 34 |
  | richtiger Wert im Denken (alt / v2) | 3 / 29 | 20 / 22 | 15 / 29 |
  | Zünd-Quote v2 | **26/37 = 70 %** | 15/40 = 38 % | 9/33 = 27 % |
  | Präzision v2 (schnelle Abschlüsse an richtigem Wert) | **26/42 = 62 %** | 15/24 = 62 % | 9/39 = 23 % |
  | Vorsprung: erster richtiger Wert im Klartext vor dem ersten formalen Kandidaten (Median) | – (n 3) | **4.260 Tokens** (n 20) | **4.897** (n 15) |

  → (1) eigen und ERGORE schreiben den richtigen Wert im Median **über 4.000 Tokens früher** im Klartext hin, als sie ihn
  formal festhalten – ein starker beschreibender Beleg für „Knowing Is Not Committing“.
  (2) WT-A schließt fast doppelt so oft direkt nach dem richtigen Wert wie eigen (70 % gegen 38 %), bei **gleicher Präzision** wie
  die natürlichen Abschlüsse von eigen (62 %). ERGOREs Druck schließt dagegen meist nach anderen Werten (23 %), passend zu den
  leeren Abschlüssen.
  (3) Auch nachträglich hielte K2 die Vorab-Schwelle (Präzision ≥ 75 %) nicht. Die Schwelle war aber absolut gesetzt, obwohl
  schon die Basis nur 62 % erreicht. **Für eine künftige Vorab-Lesart: Präzision relativ zur Basis festlegen** (z. B. ≥ eigen
  − 5 Punkte) und Zünd-Quote ≥ Basis + 20 Punkte.
  Alles nachträglich; Bestätigung nur mit vorab festgelegter v2-Definition auf frischen Daten.
- 07.11. 18:26 – **VORAB-TEST H-WT2: Zündet WT-A an der Wahrheit? (Nutzer: „ja bitte“; festgehalten, BEVOR ein WT-A-Lauf auf 161–300
  existiert – geprüft um 18:26: WT-A-Ordner auf dem Laptop 0, auf dem MiniPC 0; die MIT-/ERGORE-Läufe auf 161–300 wurden mit dem
  neuen Erkenner noch nicht angesehen).**
  Daten: MATH-500 161–300, Seed 0, 0,6, 32k – WT-A (s3-wta-161-210, -211-260, -261-300) gegen MIT (s3-mit-161-260, -261-300) auf
  denselben Aufgaben; ERGORE beschreibend.
  Erkenner v2 = alter Erkenner ∪ Wert-Aussagen („= W“, „is W“, „are W“ am Satz- oder Formelende), nur im Denken (vor dem ersten
  `</think>`), richtig per math-verify – genau wie in 76_kandidaten_v2.py (Code-Stand wird nach dem Programmtest mit md5
  festgeschrieben).
  Kennzahlen:
  - Gelegenheit: Lauf mit richtiger Wert-Aussage im Denken.
  - Zündung: Das Denken schließt ≤ 64 Tokens nach der letzten Wert-Aussage, und diese ist richtig.
  - Zünd-Quote = Zündungen / Gelegenheiten.
  - Präzision = richtige / alle schnellen Abschlüsse (≤ 64 Tokens nach irgendeiner Wert-Aussage).
  **H-WT2 bestanden, wenn (a) Zünd-Quote WT-A ≥ MIT + 20 Prozentpunkte UND (b) Präzision WT-A ≥ MIT − 5 Prozentpunkte.**
  Weniger als 20 WT-A-Gelegenheiten → „nicht beurteilbar“. Beschreibend: Fisher einseitig für (a), je Block (Laptop 161–260,
  MiniPC 261–300), gegen ERGORE.
  Das ursprüngliche WT-A-Tor (K0–K2, 17:44) bleibt ZU; H-WT2 ist ein eigener, neuer Test des Mechanismus, kein nachträgliches
  Öffnen des Tors. Auswertung nach Abschluss der Läufe (Nachtkette, nach dem Schritt-3-Urteil).
- 07.11. 18:35 – **H-WT2: Auswertungscode festgeschrieben** – paket/76_kandidaten_v2.py, md5 2f6e7ffa29d7052a807af260090c6140 (Programmtest mit alten Set-B-Läufen bestanden, Testausgabe gelöscht; der Test-Vergleich lief bewusst mit unpassenden Läufen, z. B. MIT bei 1,0, und hat keine Aussagekraft). Noch immer kein WT-A-Lauf auf 161–300 vorhanden (Laptop-Ordner: 0). Aufruf in der Nachtkette: `76_kandidaten_v2.py --schritt3` direkt nach dem Schritt-3-Urteil.
- 07.11. 18:39 – **Zweites `</think>` bei WT-A – Kosten gemessen (beschreibend; Korrektur meiner Aussage „kostet nichts Messbares“):**
  - Betroffen sind 36 der 46 WT-A-Läufe, die das Denken schließen. **Alle 31 richtigen WT-A-Läufe gehören dazu.** Die 10 Läufe mit
    nur einem `</think>` sind alle falsch (Ø ~30k Tokens; eigen ist auf diesen Aufgaben ebenfalls 0/10).
  - Je Lauf erscheint `</think>` meist 3–7-mal, bis zu 21-mal: Das Modell schließt, schreibt die Lösung neu, schließt wieder.
  - **Nach dem zweiten `</think>` entstehen im Median 1.414 Tokens (Mittel 3.259), zusammen 117k von 256k = 46 % aller Tokens
    dieser Läufe.** 35 der 36 Läufe enden mit eos.
  - Treffer kostet der Fehler sichtbar nicht (Läufe ohne Antwort nach `</think>`: WT-A 9, eigen 9), wohl aber **fast die Hälfte
    der Tokens**. Die Ersparnis von −64 % gegenüber eigen entsteht trotz dieses Fehlers; eine Reparatur könnte deutlich mehr
    sparen. Ob sie Treffer kostet oder bringt, ist offen.
- 07.11. 19:22 – **WT-Reparatur gegen das zweite `</think>`: einfache Bauarten NICHT machbar (77_phase_sammeln, 78_wt_bremse
  --analyse; 3.624 Stellen aus 37 Läufen, kein Modell gebaut):** Ein lineares Phasen-Signal am Schicht-15-MLP-Eingang
  („vor dem ersten `</think>`“ gegen „danach“) trennt nur mit **AUC 0,93**:
  - Denk-Tokens: Median −2,5, 90 % −0,2, 99,9 % +3,9.
  - Antwort-Tokens: Median +2,6, 10 % −0,8.
  Für einen sauberen Schalter in den Gewichten bräuchte es fast vollständige Trennung.
  - Bauart a (WT-Gate dämpfen) würde das Gate im Denken um ±47 verschieben. Unbrauchbar.
  - Bauart b (eigene Antwort-Bremse) findet keine Schwelle; der Antwort-Median liegt unter dem 99,9-%-Wert des Denkens.
  **Nebenbefund:** WT-A schiebt genau vor dem zweiten `</think>` (90 % +5,2 Einheiten, Gate offen bei 37 %), sonst im
  Antwortteil kaum (offen 2 %). Das zweite `</think>` ist also WT-verursacht. Der Antwortteil nach einem frühen Abschluss sieht
  innen weitgehend aus wie Denken: Das Modell denkt dort weiter, weshalb es neu ansetzt und wieder schließt.
  **Folge:** Die Reparatur braucht eine andere Bauidee, z. B. ein Signal in einer späteren Schicht oder eine Richtung, die
  „Phase beenden“ statt nur „`</think>` schreiben“ bedeutet. Nichts davon wird überstürzt; das Morgen-Fenster wird neu belegt.
- 07.11. 19:27 – **Argons Prüfstellen 3–5 offline gemessen (75_pruefstellen.py, CPU)**
  Aufbau: eigen und WT-A auf identischen Texten (36 Läufe aus eigen- und WT-A-Läufen von Set B); gemessen wird p(`</think>`).

  | Stelle | eigen | WT-A | Bewertung |
  |---|---|---|---|
  | P0 Gültigkeit: Stellen, an denen WT-A tatsächlich schloss (n 19) | Median 10⁻¹⁰ | **Median 1,0** (79 % > 0,5) | Messung bildet die echten Abschlüsse ab ✓ |
  | P3 Satzende nach verworfener Probe (n 83) | ~5·10⁻¹¹ | gleich, Max 9·10⁻⁹ | **kein Fehlschuss** ✓ |
  | P4z Zwischenergebnis ≠ gold (n 213) | ~10⁻¹² | gleich, Max 6·10⁻⁶ | **kein Fehlschuss** ✓ |
  | P4r Wert = gold im Denken (n 85) | ~10⁻¹² | 11 % > 0,1, 7 % > 0,5 | zündet gezielt an einem Teil der richtigen Werte |
  | P5 Antwortteil, Satzenden und Wert-Aussagen (n 110) | Median 2,5·10⁻¹⁰ | Median 4,5·10⁻¹⁰, 1 % > 0,01 | an typischen Stellen fast unverändert |

  → WT-A **besteht Prüfstelle 3 und 4 sauber**. Das zweite `</think>` entsteht an wenigen Stellen im Antwortteil, wo WT
  stark schiebt (Phasen-Messung: Gate offen bei 37 % der Tokens vor dem zweiten `</think>`). Über tausende Antwort-Tokens
  summiert sich das. Die nachträgliche Heuristik aus 74 („21 Abschlüsse nach anderem Wert“) überschätzt Fehlschüsse
  wahrscheinlich; an Zwischenergebnissen zündet WT-A laut P4z praktisch nie.
- 07.11. 19:32 – **N7 Morgen-Fenster (Nutzer: „WT-A Seed 1“; vor jedem dieser Läufe; WT-A-Ordner auf 161–300 bisher: 0):** WT-A mit
  **Seed 1 auf MATH-500 161–260** (Laptop, 161–210 ‖ 211–260, 0,6, 32k, vLLM-Stil; Ordner s3-wta-161-210-s1, s3-wta-211-260-s1).
  Kette kette_morgen_laptop.sh startet, sobald die Nachtkette fertig ist (erwartet ~05:30, Ende ~07:00).
  **Beschreibend:** Stabilität von WT-A über zwei Stichproben – Treffer Seed 0 gegen Seed 1 (gepaart, Übereinstimmung je
  Aufgabe), Tokens, Zünd-Quote und Präzision v2 (Erkenner aus 76) je Seed. H-WT2 bleibt bei Seed 0, wie festgelegt. Die frühere
  Idee „Reparatur morgens auf Set B testen“ entfällt (Reparatur nicht machbar, siehe 19:22).
- 07.11. 22:38 – **SCHRITT-3-HAUPTURTEIL ERGORE gegen MIT (vorab festgelegt 14:16; gerechnet, sobald MIT und ERGORE auf beiden Blöcken
  vollständig waren; WT-A bewusst noch nicht ausgewertet; MiniPC-Daten per scp, md5 geprüft):**

  | | ERGORE | MIT | nur ERGORE : nur MIT | McNemar p | Differenz (95 %) | Urteil |
  |---|---|---|---|---|---|---|
  | **161–300 (frisch)** | **65/140 (46,4 %)** | **80/140 (57,1 %)** | 7 : 22 | **0,0081** | **−10,7 [−18,0; −3,4]** | **NICHT ERREICHT** |
  | Laptop-Block 161–260 | 51/100 | 58/100 | 4 : 11 | 0,12 | −7,0 | beschreibend |
  | MiniPC-Block 261–300 | 14/40 | 22/40 | 3 : 11 | 0,057 | −20,0 | beschreibend |
  | 1–300 zusammen | 144/300 (48,0 %) | 157/300 (52,3 %) | 21 : 34 | 0,10 | −4,3 [−9,2; +0,5] | **NICHT ERREICHT** (Grenze −7) |

  - **Prognose (14:16) „gleichauf, |Differenz| ≤ 5“: falsch.** MIT ist auf den frischen Aufgaben signifikant besser.
  - **Technisch geprüft:** gleiches Protokoll (0,6, Strafen-Fenster 40960, presence 1,5, Seed 0), richtige Modelle (Server-Logs),
    keine leeren oder abgebrochenen Läufe. Die Richtung ist auf beiden Maschinen dieselbe, also kein reiner Maschinen-Effekt. Der
    Abstand ist auf dem MiniPC größer, passend zur Eichung, bei der ERGORE dort schwächer war.
  - **Tokens:** ERGORE gesamt Ø 18.629 gegen 21.525 (−13 %); auf gemeinsam gelösten Aufgaben keine Ersparnis (28:30), wie auf 1–160.
  - **Beschreibend:** ERGORE schließt das Denken öfter (96–97 % gegen 82–85 %), bricht aber öfter in Schleifen ab (Schleifen-Abbruch
    19 + 8 gegen 8 + 2). MIT läuft öfter ans Limit, löst aber mehr.
  - **Folge:** „ERGORE erreicht MIT-Niveau“ gilt für 1–160 (79 : 77), **nicht für frische Aufgaben**. Im Bericht ehrlich und
    prominent korrigieren. Wahrscheinlich teils Gewinnerfluch: 1–160 war über Tage Entwicklungs- und Vergleichsmenge. WT-A (ohne
    Dauer-Druck) folgt, sobald sein MiniPC-Block fertig ist.
- 07.11. 23:45 – **H-WT2, technische Änderung vor der Auswertung (keine Logik-Änderung):** 76_kandidaten_v2.py liest jetzt einen Zwischenspeicher ergebnisse/wertcache.json, falls vorhanden. Erzeugt wird er von 80_wertcache.py: dieselben (Wert, gold)-Paare, dieselbe Prüfung korrekt(c, g) oder korrekt(bereinigt(c), g), nur parallel auf 6 Prozessen. Grund: math-verify braucht unter Windows ohne Zeitlimit 0,1–0,5 s je Paar; bei ~9.000 Paaren allein für MIT 161–260 hätte H-WT2 1–2 h gebraucht und die Nachtkette verzögert. Neue md5: 49593ddc3142734c4c13d69cc7b59dda (vorher 2f6e7ffa…). Ausgewertet war zu diesem Zeitpunkt noch nichts; die WT-A-Läufe auf 161–300 sind nicht angesehen. Kontrolle: Die Nachtkette rechnet H-WT2 später noch einmal mit demselben Skript; beide Ergebnisse müssen gleich sein.
- 08.11. 00:06 – **Warum ERGORE auf 161–300 weniger löst (79_ergore_verluste.py; NACHTRÄGLICH, beschreibend; Erkenner v2 mit
  Vorab-Abgleich 80):**

  | 140 Aufgaben | ERGORE | MIT |
  |---|---|---|
  | richtig | 65 | 80 |
  | Denken zu, **falsche** Antwort | **31** | 17 |
  | Denken zu, **keine** Antwort | **39** (17 Schleife, 13 Limit, 9 eos) | 21 (13 Limit, 7 Schleife, 1 eos) |
  | Denken nie zu | 5 | **22** |
  | falsch, obwohl der richtige Wert im Denken stand | 23 | 25 |

  - Auf den 22 Aufgaben, die **nur MIT** löst, macht ERGORE: 8× falsche Antwort, 13× zu ohne Antwort, 1× nie zu. **In 12 von 22
    stand der richtige Wert schon in ERGOREs Denken.** ERGORE schließt dort im Median nach 10.277 Tokens, MIT nach 20.005.
  - → **Kern:** Der Dauer-Druck lässt ERGORE zu früh und ohne Wahrheitsbedingung abgeben. Daraus entstehen fast doppelt so viele
    falsche Antworten und fast doppelt so viele Abschlüsse ohne Antwort; danach hängt ERGORE im Antwortteil (Schleife oder
    Limit). MIT denkt weiter, wenn es nicht fertig ist (22× nie zu). Das kostet Tokens, aber selten eine falsche Abgabe.
  - **Beide verlieren Antworten, die sie schon hatten** (23 bzw. 25), ERGORE durch zu frühes, MIT durch zu langes Denken.
  - Ein Paar von 23.833 überschritt beim Vorab-Abgleich das Zeitlimit von 20 s (`\binom{22+735235k}{2356}` gegen gold 6) und
    gilt als nicht richtig.
- 08.11. 00:10 – **N2 IFEval WT-A (vorab festgelegt 15:25; vollständig, 120 Prompts, Laptop):**
  - **70/120 (58,3 %)**, Anweisungen 66,2 %, Ø 5.279 Tokens, Schleife oder Limit 6,7 %.
  - **Lesart:** Prognose „≥ 72“ knapp verfehlt; Widerlegungs-Grenze „≤ 64“ nicht erreicht. Weder bestätigt noch widerlegt.
  - Gepaart:
    - gegen eigen 74: 10 : 14, p = 0,54 – kein signifikanter Schaden;
    - gegen ERGORE 61: 25 : 16, p = 0,21 – besser, aber nicht signifikant;
    - gegen V2.1 77: 13 : 20, p = 0,30;
    - **gegen MIT 87: 8 : 25, p = 0,005 – MIT klar besser.**
  - → WT-A liegt bei der Anweisungstreue zwischen eigen und ERGORE und ist von beiden nicht signifikant verschieden. Den
    signifikanten Schaden, den ERGORE gegenüber eigen hatte (−13, p = 0,041), zeigt WT-A nicht (−4, p = 0,54). MIT bleibt bei
    der Anweisungstreue klar vorn.
- 08.11. 00:34 – **WT-A auf 161–300 (beschreibend, Tor zu) und VORAB-TEST H-WT2 (vorab festgelegt 18:26; Code 76 mit Vorab-Abgleich 80,
  md5 49593ddc…; Zeitlimit-Fall 1 von 25.068 Paaren):**
  **H-WT2 BESTANDEN:**
  - (a) Zünd-Quote v2: WT-A **65 % [55/85]** gegen MIT **36 % [37/102]**, +29 Punkte (gefordert ≥ +20); Fisher einseitig p = 0,0001.
  - (b) Präzision v2: WT-A **61 % [55/90]** gegen MIT **44 % [37/85]** (gefordert ≥ MIT − 5).
  - ERGORE beschreibend: 23 % [19/83], Präzision 23 %.
  - → **Der Mechanismus ist auf frischen Aufgaben vorab festgelegt bestätigt:** WT-A schließt viel öfter direkt nach dem richtigen
    Wert, und seine schnellen Abschlüsse treffen häufiger als die von MIT.
  **Treffer (beschreibend):**
  - WT-A **61/140 (43,6 %)**: Laptop 44/100, MiniPC 17/40.
  - Gegen MIT 80: 7 : 26, **p = 0,0013, −13,6 Punkte** [−21,3; −5,8].
  - Gegen ERGORE 65: 12 : 16, p = 0,57.
  **Tokens:** auf gemeinsam gelösten Aufgaben **Ø 7.146 gegen MIT 13.233 (44 weniger, 9 mehr)**, gegen ERGORE 6.403 gegen 12.045;
  über alle Aufgaben Ø 19.064 (MIT 21.525).
  **Deutung (nachträglich):**
  - MIT hat mehr Gelegenheiten: In 102 Läufen steht der richtige Wert im Denken, bei WT-A in 85. MIT denkt weiter und findet den
    Wert öfter.
  - WT-A schließt früh. Liegt der richtige Wert schon vor, ist das gut (65 %). Liegt er noch nicht vor, schneidet WT-A die längere
    Suche ab: 35 der 90 schnellen Abschlüsse liegen an einem anderen Wert.
  - Von MITs 80 richtigen Läufen kommen 37 über einen schnellen Abschluss am richtigen Wert, 43 über späteres Abschließen. Bei WT-A
    sind es 55 und 6.
  - → Der Wahrheits-Auslöser funktioniert, ist aber für Treffer gegen MIT nicht präzise genug. Es fehlt ein „noch nicht → weiter
    suchen“ (siehe Nutzer-Idee „Nachsicht“).
- 08.11. 00:42 – **Warum WT-A auf 161–300 weniger löst als MIT (79_ergore_verluste.py --wta; NACHTRÄGLICH, beschreibend) –
  KORRIGIERT meine Deutung von 00:34 („schließt zu früh, schneidet Suche ab“):**

  | 140 Aufgaben | WT-A | MIT |
  |---|---|---|
  | richtig | 61 | 80 |
  | Denken zu, **falsche** Antwort | **10** | 17 |
  | Denken zu, **keine** Antwort | **32** (23 Limit, 6 Schleife, 3 eos) | 21 (13 Limit, 7 Schleife, 1 eos) |
  | Denken **nie** zu | **37** (27 Limit, 10 Schleife) | 22 |
  | falsch, obwohl der richtige Wert im Denken stand | 30 | 25 |

  - Auf den 26 Aufgaben, die nur MIT löst, macht WT-A: **12× zu ohne Antwort** (6 Limit, 4 Schleife, 2 eos), **10× nie zu**
    (6 Limit, 4 Schleife), **nur 4× falsche Antwort**. In 15 von 26 stand der richtige Wert schon in WT-As Denken.
  - → **WT-A gibt seltener Falsches ab als MIT (10 gegen 17).** Es verliert durch **Schweigen** und **Denk-Limit**:
    - Im Antwortteil läuft es oft bis ans Limit (23 gegen 13). Das ist der bekannte Fehler mit dem zweiten `</think>`:
      schließen, neu ansetzen, wieder schließen, bis das Budget weg ist.
    - Wenn WT nicht zündet, verhält sich WT-A wie eigen. Dessen Umkehr bricht Schleifen schwächer als MITs Richtung, daher
      37 gegen 22 Läufe ohne Abschluss.
  - **Folge für den nächsten Bau:** (1) Effektor „Phase beenden“ gegen das Weiterrechnen im Antwortteil (Weg R1, MITs r⊥);
    (2) WT auf MITs Basis statt auf eigen (MIT + WT). Beides adressiert genau die beiden Verlustquellen. Die Wahrheitsbedingung
    selbst ist nicht das Problem; sie verhindert falsche Abgaben.
- 08.11. 01:07 – **Ausschlussverfahren WT-A gegen MIT auf 161–300 (83_ausschluss.py; nur Text; NACHTRÄGLICH, beschreibend;
  Nutzer ~01:05: „Ursache, warum die Präzision bei den einen Aufgaben erreicht wurde und bei den anderen nicht“):**
  - Paare: beide richtig 54, nur WT-A 7, nur MIT 26, keiner 53. Die „19“ sind also 26 − 7.
  - Kontext-Kurve, richtiger Wert im Denken bis X Tokens (von 140):

    | bis | 2k | 4k | 8k | 16k | 32k |
    |---|---|---|---|---|---|
    | WT-A | 55 | 65 | 76 | 82 | 85 |
    | MIT | 66 | 79 | 86 | 96 | 102 |

  - Abgabe nach Fund-Zeitpunkt:

    | Fund bei | 0–4k | 4–8k | 8–16k | 16–32k |
    |---|---|---|---|---|
    | WT-A | 45/65 | 4/11 | 5/6 | 1/3 |
    | MIT | 66/79 | 6/7 | 5/10 | 0/6 |

  - Trichter:
    - WT-A: Wert da 85 → am richtigen Wert geschlossen (G1) 55 → richtig abgegeben 48. Wert da, dort nicht geschlossen (G2) 30
      → richtig 6.
    - MIT: 102 → G1 37 → 33. **G2 65 → 44.**
  - → WT-A kommt fast nur über den Reflex-Abschluss zum Erfolg (48 von 61). MIT hat einen zweiten Weg: finden, lange prüfen
    (Fund → Abschluss im Median 12.289 Tokens, WT-A 1.018), dann abgeben (44 von 80).
  - G1 gegen G2 bei WT-A:

    | Merkmal | G1 | G2 |
    |---|---|---|
    | erster richtiger Wert (Median) | 719 Tokens | 1.963 Tokens |
    | Stufe (Median) | 3 | 4 |
    | Schluss-Rahmung vor dem Wert | 35 % | 17 % |
    | Konkurrenz-Werte davor (Median) | 12 | 16 |

    Anteil G1 nach Stufe: 1–3 75 %, 4–5 50 %. Nach Fach: Algebra 81 %, Zählen/Wahrscheinlichkeit 40 %, Präkalkül 43 %.
  - Die 26 „nur MIT richtig“:
    - 11× stand der Wert nie in WT-As Denken;
    - 6× war er da, WT-A schloss woanders;
    - 5× schloss WT-A am richtigen Wert, die Abgabe misslang;
    - 4× war er da, WT-A schloss nie.
  - Abgabe-Verluste nach Abschluss am richtigen Wert: WT-A 7 von 55 (5 davon mit zweitem `</think>`), MIT 4 von 37.
- 08.11. 00:54–01:00 – **Vorfall (offen berichtet): Probelauf 82 auf der CPU bremst die Nachtkette.**
  - Probelauf: 6 Threads, float32, ein Lauf mit 24.676 Tokens, 5 min.
  - Folge: Server-Durchsatz 25–28 → 19,6 / 17,7 t/s für etwa 10 min. Ursache war Speicherdruck: vorher nur ~0,8 GB frei,
    ~26.000 Seitenfehler/s.
  - Konsequenz: keine schweren CPU-Läufe während der Ketten; die Zuck-Messung läuft auf der GPU (s. u.).
  - Danach liefen nur zwei kurze Rauchtests (bf16, 2 Threads, je ~1 min).
- 08.11. 01:16 – **MIT+WT gebaut (84_mit_wt_bauen.py, nur Bau, KEIN Lauf ohne Absprache):** modelle/Qwen3.5-0.8B-mit-wt.
  - Aufbau: Basis + MIT-Edit (minipc/mit_richtung.npz, α 6,0003/6,0002) + 16 WT-Neuronen bitgleich aus WT-A.
  - Prüfungen:
    - WT-Zeilen und -Spalten bitgleich ✓.
    - MIT-Nachbau gegen MIT-GGUF: relativer Abstand 0,00495 (L15) / 0,00493 (L19). Rauschmaß Basis gegen Basis-q8_0: 0,00588 /
      0,00529. Gleich innerhalb der Quantisierung; ohne Edit wären es 0,70 / 0,55.
    - Keine Überlappung der WT-Neuronen mit MITs Spalten.
  - Begründung für die Eichung: Der L15-MLP-Eingang ist für denselben Text bei Basis, eigen, MIT, WT-A und MIT+WT gleich, weil alle
    Eingriffe in down_proj von L15/L19 bzw. in den 16 Neuronen sitzen.
- 08.11. ~01:30 – **Zuck-Messung (82, md5 67901b15…) als GPU-Schritt VOR WT-A Seed 1** in kette_morgen_laptop.sh eingefügt.
  - Skript paket/zucken_gpu.sh (md5 a0d5cdc5…), höchstens ~60 min. Seed 1 läuft danach unverändert und verschiebt sich um ≤ 1 h.
  - Die Morgen-Kette wurde dafür angehalten (sie wartete nur) und um 01:27 neu gestartet.
  - **LESART VORAB** (festgelegt, bevor Messdaten existieren; beschreibend):
    - Begriffe: „Zucken“ an einer Wert-Aussage = S_max ≥ 0,5 im Fenster [+0, +12]. „Tor offen“ = zT_max > 0.
    - (a) Wahrheit erkannt? AUC(zT) richtig gegen falsch: ≥ 0,8 „ja“; 0,6–0,8 „teilweise“; < 0,6 „nein“.
    - (b) Horizont? „Hinweis auf einen Horizont-Effekt des W-Signals“, wenn der Anteil „Tor offen“ an richtigen Werten von 0–2k
      zu ≥ 4k um ≥ 20 Prozentpunkte fällt, an falschen aber höchstens um 5 Prozentpunkte. Kein Beweis, Schwierigkeit ist verwoben.
    - (c) Gegenschub („entmutigt“)? Maß ist die Summe der verlorenen gezogenen Abschluss-Wahrscheinlichkeit an natürlichen
      Abschluss-Stellen (ohne Reflex ≥ 5 %) über alle 140 Läufe: ≥ 3 „spürbar“; < 1 „vernachlässigbar“.
    - (d) SCHÄTZUNG MIT+WT (keine Messung):
      - Kopplung an MITs Läufe; Zusatz-Abschluss q = (p_mit − p_ohne)/(1 − p_ohne) je ausgewählter Stelle.
      - Abgabe-Erfolg: π_r = 33/37 (MIT, am richtigen Wert), π_f = 6/37 (≤ 8 Tokens nach falschem Wert, gepoolt).
      - „Unklar“ sind Läufe, in denen der Reflex MITs eigenen Abschluss senkt.
      - Ein echter MIT+WT-Lauf wird dem Nutzer nur vorgeschlagen, wenn der neutrale Wert ≥ 85/140 (MIT + 5) UND die untere Grenze
        ≥ 78/140 (MIT − 2) liegt. Sonst kein Vorschlag; berichtet wird trotzdem.
- 08.11. 01:33 – **Format-Prüfung „Schweigen?“ (81_format_check.py; NACHTRÄGLICH, beschreibend).**
  - Technik: Der erste Lauf (00:24, ein Prozess je Paar) brach am Zeitlimit ab. Jetzt füllt 80_wertcache.py --antwortteil den
    Zwischenspeicher parallel: 1.544 neue Paare, 23 s, keine neuen Zeitlimit-Fälle.
  - Läufe „Denken zu, aber kein \boxed“, und wie oft der richtige Wert trotzdem im Antworttext steht:

    | Modell | zu ohne \boxed | davon richtiger Wert im Antworttext |
    |---|---|---|
    | WT-A | 32 | **14** |
    | MIT | 21 | 7 |
    | ERGORE | 39 | 11 |

  - Bei WT-A kommt der richtige Wert früh: im Median bei ~12 % des Antwortteils. In 12 der 14 Läufe ist die letzte Wert-Aussage aber
    falsch, und in 8 der 14 folgen weitere `</think>`.
  - → Dieses „Schweigen“ ist meist kein Nicht-Wissen. Das Modell sagt den Wert im Antwortteil, rechnet weiter, verliert ihn wieder und
    gibt nichts ab. Das ist ein Abgabe-Fehler (Nutzer: „Thinking und Antwort sind zwei verschiedene Paar Schuhe“; „Prüfung bei
    Abgabe“).
  - Die Bewertung bleibt beim Protokoll (nur \boxed zählt). Diese Zahlen sind keine Umwertung.
- 08.11. ~01:35 – **„Nachsicht“ erkundet (83_ausschluss.py, neuer Abschnitt; NACHTRÄGLICH, erkundend):** Abschlüsse am richtigen
  Wert (G1), aufgeteilt nach der Zahl der richtigen Erwähnungen VOR dem Abschluss.

  | Modell | Erwähnungen vorher | n | richtig abgegeben | weiteres `</think>` im Antwortteil | Antwortteil (Median) |
  |---|---|---|---|---|---|
  | WT-A | 1× | 12 | 11 | 12 (100 %) | ~2.100 Tokens |
  | WT-A | 2× | 4 | 3 | 4 (100 %) | ~2.000 Tokens |
  | WT-A | 3–5× | 15 | 13 | 15 (100 %) | ~1.760 Tokens |
  | WT-A | 6×+ | 24 | 21 | 20 (83 %) | ~2.660 Tokens |
  | MIT | 6×+ | 36 | 33 | 4 (11 %) | 674 Tokens |

  MIT hat außerdem einen G1-Abschluss nach 3–5 Erwähnungen. MIT schließt also nie nach der ersten Erwähnung.
  - → Nach einem Reflex-Abschluss denkt WT-A fast immer im Antwortteil weiter, auch wenn der Wert vorher schon 6× dastand. Mehr
    Bestätigung im Denken ändert das kaum. Deutung (Hypothese): **Ein von außen gesetzter Abschluss ist für das Modell kein innerer
    Abschluss.** Der Zustand „noch nicht fertig“ bleibt und setzt sich im Antwortteil fort. MITs Abschlüsse kommen aus dem Zustand
    „fertig“ (r⊥: natürliche Schlusswörter).
  - Die Abgabe gelingt trotzdem meist (87–92 %). Der Preis sind ~2.000 Tokens und 7 von 55 Verlusten. Das ist nicht die Hauptquelle
    des Rückstands; die Hauptquelle ist der fehlende zweite Weg ohne Zucken (s. 01:07).
- 08.11. ~01:37 – 82_zucken.py nur in der AUSWERTUNG ergänzt, die Messung bleibt unverändert. md5 jetzt 254bdbdb…, vorher 67901b15….
  - Neuer Abschnitt „Stellschraube Wahrheits-Schwelle“ (erkundend, ohne Entscheidungsregel): Die Schwelle wird um
    δ = 0 / 0,5 / 1 / 2 / 3 z-Einheiten gesenkt.
  - Gezählt wird, ob der ERSTE Zucker S' ≥ 0,5 an einem richtigen oder an einem falschen Wert läge.
  - Das gilt nur bis zum ersten Zucker; danach wäre der Lauf anders verlaufen.
- 08.11. 01:40 – Technisch: Die GPU-Zuck-Messung (zucken_gpu.sh) rechnet in **bf16** statt float32. Grund: Bei float32 kann die
  Aufmerksamkeit der 32k-Läufe auf den speicherhungrigen Rechenweg fallen und den Grafikspeicher (8 GB) sprengen. bf16 nutzt den
  sparsamen Weg; die Gated-DeltaNet-Schichten rechnen intern ohnehin in float32. Zu erwarten sind kleine Abweichungen (zT etwa
  ±0,05). Abgleich mit dem CPU-float32-Probelauf (algebra/1282) folgt nach der Messung.
- 08.11. 01:41 – Korrektur: Drei Zeitstempel dieser Nacht hatte ich geschätzt statt abgelesen. Sie sind jetzt auf die echte Uhrzeit
  berichtigt:
  - „Nachsicht“: ~01:35 statt 01:42;
  - Auswertungs-Ergänzung 82: ~01:37 statt 01:47;
  - bf16: 01:40 statt 02:05.
  Alle drei liegen vor jeder GPU-Messung; die Reihenfolge ist unverändert.
- 08.11. 01:40 – Gegenprobe: H-WT2 in der Nachtkette (01:37, logs/76_hwt2.log) liefert dasselbe Ergebnis wie meine Handrechnung
  von 00:34: BESTANDEN, Zünd-Quote 65 % [55/85] gegen 36 % [37/102], p = 0,0001, Präzision 61 % [55/90] gegen 44 % [37/85]. ✓
- 08.11. 03:09 – **(N1) EHRLICHKEIT SCHRITT 1 – URTEIL (71, vorab festgelegt 07.11. 15:25; Kette 01:42–03:07):**
  - **H1 BESTANDEN.** Die eingefrorene L13-Sonde trennt erzwungene Antworten mit AUC **0,833** (n 542). Gefordert war ≥ 0,75.
  - **H2 BESTANDEN.** S₂ = (richtig − 2·falsch)/N: mit Harnisch **+0,174**, ohne Harnisch (mit Erzwingen) **−0,295**.
    S₁ +0,350 gegen +0,136, S₃ −0,002 gegen −0,727.
  - Alle 1.280 Antworten:

    | | offiziell | erzwungen | mit Harnisch |
    |---|---|---|---|
    | richtig | 592 | 726 | 673 |
    | falsch | – | 552 | 225 |
    | S₂ | +0,198 | −0,295 | +0,174 |

    Der Harnisch enthält sich 380-mal; 327 davon wären falsch gewesen. Er verliert dabei 53 richtige.
  - Frischer Teil 161–300 (N 420):
    - AUC 0,825 (erzwungen 0,798);
    - S₂ offiziell / erzwungen / Harnisch: +0,186 / −0,238 / +0,126;
    - Enthaltungen 114, davon 89 falsch.
  - Risiko-Abdeckung (alle): Treffsicherheit 56,8 % bei voller Abdeckung, 75 % bei 70 %, 87 % bei 50 %, 95 % bei 30 %.
  - → Ein Modell, das zum Antworten gezwungen wird, schadet sich (S₂ negativ). Mit „weiß ich nicht“ bei fehlendem Wahrheits-Signal
    wird das Erzwingen nützlich. Den offiziellen Lauf ohne Erzwingen schlägt der Harnisch bei S₂ knapp nicht (+0,174 gegen
    +0,198). Er liefert aber 81 richtige Antworten mehr, bei 225 statt ~170 falschen.
- 08.11. 03:11 – **(N3) DENK-WEICHE – URTEIL (72, vorab festgelegt 07.11. 15:25; Kette 03:07–03:10):**
  - **Haupttest WIDERLEGT.** Likelihood-Ratio M1 (+ s_T, s_C am Prompt-Ende) gegen M0 (Stufe, log Länge, Datensatz): LR 4,03, df 2,
    **p = 0,133**. 5-fach-CV-AUC M0 0,723, M1 0,730.
  - → Die inneren Signale am Ende der Aufgabenstellung sagen nicht über Schwierigkeit und Länge hinaus voraus, ob das Modell ohne
    Denken löst. Die Weiche (oberstes Quintil ohne Denken) bringt nichts Verwertbares: Set B +2 Treffer, MATH-500 −3 bzw. −6
    Treffer, bei 8–13 % weniger Tokens.
  - **Beschreibend und auffällig:** eigen OHNE Denkblock (offizielle Nicht-Denk-Vorlage, das Modell rechnet sichtbar in der Antwort)
    löst **109/220**, im Mittel 8.177 Tokens.

    | | eigen ohne Denken | gegen | nur ohne : nur mit | p |
    |---|---|---|---|---|
    | Set B | 32/60 | eigen mit Denken 23/60 | 14 : 5 | 0,064 |
    | MATH-500 1–160 | **77/160** | **MIT mit Denken 77/160** | 22 : 22 | 1,0 |
    | MATH-500 1–160 | 77/160 | ERGORE 79 | – | 0,875 |

  - Deutung (Hypothese): Beim 0.8B ist der Denkblock weitgehend Schleifen-Raum. Im Antwortmodus rechnet das Modell knapper und gibt
    ab („Thinking und Antwort sind zwei verschiedene Paar Schuhe“).
- 08.11. 03:11 – **K4 Block 2 (70, Kette 01:42):** Die Sonde auf den WT-A-Transkripten erreicht AUC **0,942** (54 Kandidaten), eigen
  0,996 (185). Das ist schlechter als eigen − 0,03; Block 1 lag bei 0,821 gegen 0,992. **K4 in beiden Blöcken nicht erfüllt.** Das
  Tor war ohnehin zu (K4 gehört nicht zum Tor).
- 08.11. 06:47 – **(N5) Zweiter Seed auf Set B (85_seeds.py; vorab als beschreibend festgelegt 07.11. 15:25/15:37):**

  | Modell | Seed 0 | Seed 1 | gleich gelöst je Aufgabe | Mittel |
  |---|---|---|---|---|
  | WT-A | 31/60 | 33/60 | 87 % | 32 |
  | ERGORE | 34/60 | 29/60 | 85 % | 31,5 |
  | eigen | 23/60 | 25/60 | 77 % | 24 |
  | MIT (nur Seed 0) | 27/60 | – | – | 27 |

  - WT-A gegen eigen ist in beiden Seeds gleich gerichtet: +8 (p = 0,021) und +8 (p = 0,057). Der Set-B-Vorteil des Reflexes
    gegenüber seiner Basis ist also kein Seed-Zufall.
  - WT-A gegen MIT auf Set B (Seed 0): 31 gegen 27, p = 0,34. Auf den frischen 161–300 liegt MIT dagegen klar vorn (80 gegen 61).
    Set B ist Entwicklungs-Satz, daher Vorsicht (Winner's Curse).
  - Sampling-Streuung zwischen den Seeds: ±2 bis ±5 Treffer von 60. Zum Beispiel ERGORE 34 → 29, wobei 7 Aufgaben nur in Seed 0
    und 2 nur in Seed 1 gelöst wurden.
- 08.11. 07:30 – **ZUCK-MESSUNG WT-A, eigene Läufe 161–300 (82, GPU bf16, 06:46–07:11; 136 von 140 Läufen, die übrigen 4 nach Seed 1).
  Lesart vorab (01:30):**
  - **(a) Wahrheit erkannt: „teilweise“.**
    - AUC(zT) richtig gegen falsch 0,680; Vorab-Spanne 0,6–0,8. AUC(S) 0,534.
    - Tor offen an 16 % der richtigen gegen 6 % der falschen Wert-Aussagen.
    - Lauf-Ebene: In 75 von 83 Läufen mit richtigem Wert öffnet das Tor mindestens einmal an einem richtigen Wert.
  - **(b) Horizont: Vorab-Regel NICHT erfüllt.**
    - Tor offen an richtigen Werten: 0–2k ~52 %, ab 4k ~11 % (−41 Punkte).
    - An falschen Werten: 13,5 % → 4,1 % (−9 Punkte, erlaubt waren ≤ 5).
    - zT sinkt mit der Tiefe bei BEIDEN um ~2 Einheiten (richtig: Median +0,8 bei 1–2k bis −2,8 ab 16k; falsch: −2,9 bis −4,7).
    - Deutung: Das Wahrheits-Signal wird mit zunehmender Tiefe insgesamt leiser. Die Schwelle ist auf frühe Stellen geeicht; spät
      wird sie kaum noch erreicht. Ob Tiefe oder Schwierigkeit die Ursache ist, bleibt verwoben.
  - **(c) Gegenschub: zwischen den Vorab-Marken.** Verlorene Abschluss-Wahrscheinlichkeit 1,69; „vernachlässigbar“ wäre < 1,
    „spürbar“ ≥ 3. An 11 natürlichen Abschluss-Stellen senkt der Reflex die gezogene Abschluss-Wahrscheinlichkeit im Median von 0,24
    auf 0,07. Leicht entmutigend, aber selten.
  - Trichter nach Vorab-Begriff (Zucken = S ≥ 0,5): Wert da 83 → Tor offen 75 → Zucken 32 → zu ≤ 64 Tokens 31 → richtig 27.
  - **NACHTRÄGLICH ergänzt (Wirkungs-Maß statt S-Schwelle):** Die Grenze S ≥ 0,5 unterschätzt das Zucken, weil schon S ~ 0,2 an
    empfindlichen Stellen reicht. Darum wird jeder tatsächliche Abschluss (erstes </think>, 102 gemessen) eingeordnet:

    | Abschluss | n | am richtigen Wert | am falschen Wert | woanders | richtig abgegeben |
    |---|---|---|---|---|---|
    | vom Reflex getragen (ohne Reflex < 2 %, mit ≥ 20 %) | **68** | 46 | 18 | 4 | **50** |
    | natürlich (ohne Reflex ≥ 5 %) | 25 | 4 | 15 | 6 | 5 |
    | unklar | 9 | 5 | 2 | 2 | 5 |

    - → **Es gab ein Zucken, und es trägt WT-As Erfolg:** 50 der richtigen Abgaben folgen auf einen Reflex-Abschluss.
    - Wo der Reflex schließt, liegt der Wert zu 68 % richtig (46 von 68).
    - WT-As eigene, natürliche Abschlüsse sind schwach: 5 von 25 richtig, meist an falschen Werten. Das ist der fehlende zweite Weg
      (vgl. 01:07).
  - **Stellschraube (erkundend):** Schwelle um δ z-Einheiten gesenkt, ERSTER Zucker an richtigem / falschem Wert:

    | δ | richtig | falsch | Präzision |
    |---|---|---|---|
    | 0 | 26 | 19 | 58 % |
    | 0,5 | 36 | 28 | 56 % |
    | 1 | 42 | 32 | 57 % |
    | 2 | 41 | 51 | 45 % |
    | 3 | 37 | 65 | 36 % |

    → Bis δ ≈ 1 bringt mehr Mut deutlich mehr Treffer bei gleicher Präzision; darüber kippt es.
- 08.11. 07:44 – **SCHÄTZUNG MIT+WT (82, MIT-Läufe 161–300 mit dem Modell MIT+WT, GPU 07:11–07:41; 130 von 140 Läufen). Keine
  Messung; Lesart vorab 01:30 (d):**
  - Erwartet richtig: **66,2 von 130** (Spanne 65,8–67,6). MIT hat auf denselben 130 tatsächlich **77**, WT-A 58.
  - Nach Gruppe:

    | Gruppe | n | erwartet | MIT tatsächlich |
    |---|---|---|---|
    | nur MIT richtig | 26 | 20,9 | 26 |
    | nur WT-A richtig | 7 | 3,0 | 0 |
    | gleich | 97 | 41,8 | 51 |

  - **Vorab-Regel (neutral ≥ MIT + 5, unten ≥ MIT − 2) klar verfehlt → KEIN Vorschlag für einen MIT+WT-Lauf.** Das gebaute GGUF
    (gguf/Qwen3.5-0.8B-mit-wt.gguf, 07:42) bleibt ungenutzt.
  - Ursache: Auf MITs Texten zuckt der Reflex an falschen Werten, bevor MIT selbst fertig geprüft hätte. Erster Zucker: falsch in 27,
    richtig in 61, kein Zucker in 42 Läufen. Dazu kostet jede frühe Abgabe am richtigen Wert das Abgabe-Risiko (π_r 0,89).
  - Schwelle verschoben (grobe Schätzung, erkundend): δ −3 … +3 ergibt 54–67 erwartet richtig. Keine Schwelle erreicht MIT.
  - **„Nachsicht“ simuliert (Nutzer-Idee, erkundend):** Der Reflex feuert erst beim k-ten Zucker auf DENSELBEN Wert (δ 0):

    | k | Feuer falsch | Feuer richtig | grob erwartet richtig |
    |---|---|---|---|
    | 1 | 27 | 61 | 66,6 |
    | 2 | 15 | 63 | 69,5 |
    | 3 | 11 | 60 | 71,2 |
    | 5 | 9 | 53 | 72,6 |

    → Bestätigung halbiert die Fehl-Abschlüsse und nähert sich MIT, übertrifft es aber nicht. Der Gewinn wären Tokens: früher
    Abschluss statt ~12.000 Tokens Prüfen.
  - **Horizont, Gegenprobe auf MITs Texten:** Dieselbe Sonde liest denselben L15-Eingang. Das Tor öffnet an richtigen Werten bei
    51 / 65 / 68 / 61 / **59 %** (0–1k … 8–16k) und erst ab 16k seltener (34 %). An falschen Werten öffnet es bei 9–15 %.
    → **Das Wahrheits-Signal verblasst nicht von selbst mit der Tiefe.** Auf MITs sorgfältigen Texten hält es bis 16k. Auf WT-As
    späten Texten ist es schwach, weil WT-A dort meist in Schleifen oder Verwirrung steckt. Gemessen wird also der Zustand des
    Textes, nicht der Abstand zum Anfang.
  - AUC(zT) auf MITs Texten 0,728 (WT-A-Texte 0,680). Gegenschub 2,82 verlorene Abschlüsse über 130 Läufe, knapp unter „spürbar“.
  - 82 nur in der Auswertung ergänzt: strengere Schwellen, Nachsicht-Simulation, Abschluss-Einordnung. md5 jetzt 42e701fd….
- 08.11. 09:36 – **Nutzer-Go für den Tagesplan („Ja, starten“; Plan 09:35 im Chat).** Jede Aufgabe dauert höchstens ~1 h. Lesarten
  vorab, jeweils vor dem Lauf:
  **(N8) INT auf frischen Aufgaben.**
  - Lauf: eigen (Qwen3.5-0.8B-eigen-vL-q8_0) in der offiziellen Nicht-Denk-Vorlage (eval/03b_eval_ohne_denken.py) auf MATH-500
    161–300. Seed 0, T 0,6, 32k, vLLM-Stil.
  - Blöcke wie im Schritt 3: Laptop 161–210 ‖ 211–260 mit je 6 Slots, MiniPC 261–300 mit 12 Slots.
  - Hauptvergleich: eigen ohne Denken gegen MIT mit Denken (Seed 0), gepaart, N = 140.
  - **„INT hält auf frischen Aufgaben“ bei ≥ MIT − 7 (≥ 73/140); „widerlegt“ bei ≤ MIT − 14 (≤ 66/140); dazwischen „offen“.**
  - Beschreibend: gegen WT-A 61 und ERGORE 65; je Block; Tokens (Mittel, auf gemeinsam gelösten Aufgaben).
  - Prognose (Claude): 72 ± 6.
  - Vorher auf der GPU des Laptops: die fehlenden 14 Läufe der Zuck-Messung (82, 4 WT-A + 10 MIT), höchstens 15 min.
- 08.11. 09:43 – **Flur/Horizont getrennt (88_flur.py; NACHTRÄGLICH, beschreibend).** Daten: Zuck-Messung auf WT-A- und MIT-Texten,
  100.482 Wert-Aussagen. Schleifen-Grad = Anteil wiederholter 8-Gramme in den 512 Tokens davor.
  - **Richtige Werte, logistische Regression** (standardisiert, 95 % Lauf-Bootstrap) für „Tor offen“:

    | Faktor | Koeffizient | 95 % |
    |---|---|---|
    | log Tiefe | **+0,29** | −0,01; +0,58 |
    | Schleifen-Grad | **−0,81** | −1,14; −0,45 |
    | Stufe | **−0,72** | −1,02; −0,32 |
    | MIT-Text | +0,57 | |

  - Tor offen an richtigen Werten bei wenig Schleife: 56 / 57 / 61 / 41 % (0–2k / 2–8k / 8–16k / ab 16k). Bei viel Schleife:
    – / 29 / 33 / **15 %**.
  - Nach Stufe: S1–S2 auch bei 8–16k noch 71–72 % offen. S5 liegt in jeder Tiefe nur bei 12–22 %.
  - Falsche Werte: Tiefe −0,07 (n. s.), Schleife −0,24, Stufe −0,22.
  - → **Nicht die Tiefe macht das Wahrheits-Signal leise, sondern Schleifen und Schwierigkeit.** Eine tiefenabhängige Schwelle ist
    damit nicht angezeigt. Der „Flur“ ist der Schleifen-Zustand: Wo das Modell kreist, verstummt die Wahrheit. Bei den schwersten
    Aufgaben (S5) ist sie von Anfang an leise; dort weiß das Modell es vermutlich nicht.
- 08.11. 09:47 – **(N7) WT-A Seed 1 auf 161–260: Robustheit (beschreibend wie vorab festgelegt; 76 --seed1, 85 --satz frischA;
  Laptop 07:42–09:44).** Zuvor wurden die neuen Wert-Paare über 80 (3.337 Paare, keine neuen Zeitlimit-Fälle) in den
  Zwischenspeicher geholt.

  | | WT-A Seed 0 | WT-A Seed 1 | MIT Seed 0 |
  |---|---|---|---|
  | richtig (von 100) | 44 | **47** | 58 |
  | Zünd-Quote v2 | 61 % (38/62) | **54 % (33/61)** | 34 % (25/74) |
  | Präzision der schnellen Abschlüsse | 58 % (38/65) | **57 % (33/58)** | 40 % (25/63) |
  | Ø Tokens | 19.203 | 18.880 | 21.211 |

  - Gepaart Seed 0 gegen Seed 1: beide 36, nur s0 8, nur s1 11, keiner 45 (p = 0,65); 81 % Übereinstimmung je Aufgabe.
  - → **Mechanismus und Rückstand sind beide robust.** WT-A schließt in beiden Seeds viel öfter und präziser direkt nach dem
    richtigen Wert als MIT. Trotzdem löst es 11–14 Aufgaben weniger. Die Seed-Streuung (±3) ist klein gegen diesen Abstand.
- 08.11. 09:50 – **Argons Antwort auf das Reflexions-Paket** (recherche/gutachter/2026-11-08/, als PDF und Text). Zwei rote Flaggen
  sofort geprüft:
  - **presence_penalty:** Alle Läufe auf 1–160, 161–300 und ohne Denken liefen mit demselben Protokoll: presence 1,5, Fenster
    40960, T 0,6, top-k 20, 32k, Schleifen-Abbruch an. ✓ Kein Protokoll-Unterschied.
  - **Wertungs-Asymmetrie bei INT:** Argons Vermutung war, ein früher richtiger Wert zähle trotz späterer Schleife. Alle 77
    INT-Treffer auf 1–160 und alle 32 auf Set B enden regulär (eos), kein einziger über Schleifen-Abbruch oder Limit. MIT mit
    Denken 1–160: ebenso 77 von 77 eos. ✓ Kein Parser-Artefakt.
  - **Übernommen:**
    - Morgengrauen mit dem INT-Lauf als Gratis-Kontrollgruppe auf denselben stummen Aufgaben;
    - Blitze dedupliziert, höchstens 3 Sätze mit verschiedenen Werten;
    - neutrale Rahmung („Zwischennotizen zur Prüfung“);
    - Deckel 4.096 Tokens;
    - INT doppelt auswerten: letztes \boxed und streng nur bei regulärem Ende;
    - Kaskade zusätzlich mit Schwellen, die auf 1–160 geeicht und blind auf 161–300 angewandt werden.
  - **Neu als Puzzleteil (Argon):**
    - ĝ ist ein Ein-Token-Impuls. Schon einen Schritt später verstummen die WT-Neuronen, und die Aufmerksamkeit sieht einen mitten
      im Prüfsatz abgebrochenen Text. Daher das zweite </think>.
    - Ein Effektor entlang −r⊥ würde einen semantischen Schluss-Satz einleiten (WT-R, siehe Roadmap).
    - Kurzversuch „Replay der stummen Antwortteile“: zweites </think> gesperrt (Arm A) bzw. −r⊥-Effektor (Arm B).
  - **Korrektur an Argon:** π_r = 0,89 stammt aus MITs eigenen Abschlüssen (33/37), nicht aus WT-A. Berechtigt bleibt der Einwand
    der Schichtung: Leichte Aufgaben liefert MIT fast immer ab. Mit π_r = 1 käme die Bestätigungs-Variante (k = 5) auf etwa 78
    statt 72,6 von 130, also ungefähr MIT-Niveau. → Die Schätzung „MIT+WT 66/130“ gehört nicht als Beleg in den Bericht.
- 08.11. 09:58 – **(N6) Seed 1 auf 261–300, MiniPC (85 --satz frischB; beschreibend wie vorab) = WRENs Split-Diagnose zum
  ERGORE-Einbruch:**

  | Block 261–300 (40 Aufgaben) | Seed 0 | Seed 1 | Mittel |
  |---|---|---|---|
  | MIT | 22 | **16** | 19 |
  | ERGORE | 14 | **16** | 15 |
  | WT-A | 17 | – | – |

  - ERGORE gegen MIT: Seed 0 3 : 11 (p = 0,057), **Seed 1 6 : 6 (p = 1,0)**.
  - MIT selbst schwankt zwischen den Seeds stark: 22 → 16 (8 : 2, p = 0,11).
  - Laptop-Block 161–260 (nur Seed 0): ERGORE 51 gegen MIT 58 (−7).
  - → **Das vorab festgelegte Urteil (Seed 0) bleibt: „nicht erreicht“.** Der große Abstand im MiniPC-Block (−8 von 40) war aber
    zu einem guten Teil Seed-Glück für MIT; über beide Seeds sind es −4 von 40. Kein Maschinen-Artefakt, denn beide Modelle liefen
    je Block auf derselben Maschine. Die Lücke ist also eher **−5 bis −7 Punkte** als −10,7. Der Bericht nennt beides.
- 08.11. 09:58 – **Nutzer: „Mut-Stellschraube erstmal unberührt lassen.“** Der Testlauf entfällt. Alle drei Gutachter rieten ebenfalls
  ab bzw. wollten ihn nur erkundend.
- 08.11. 09:59 – **Poows Vorschlag „relative Schwelle“ geprüft (90_relative_schwelle.py; erkundend):** z-Wert gegenüber den früheren
  Aussagen desselben Laufs. Er trennt **schlechter** als der feste Wert:
  - AUC WT-A-Texte 0,683 → 0,605, MIT-Texte 0,726 → 0,720.
  - Erste Zucker (WT-A, z ≥ 1,5): 19 richtig / 21 falsch, gegen 26 / 19 bei der festen Schwelle.
  - → Verworfen. Die absolute Höhe des Wahrheits-Signals trägt mehr Information als die laufinterne.
- 08.11. 09:59 – **Zuck-Messung vollständig (140/140 für WT-A und MIT; Nachlauf 09:44–09:52).** Die Zahlen ändern sich kaum:
  - WT-A: Reflex-Abschlüsse 69 (46 am richtigen, 18 am falschen Wert, 5 woanders), daraus 51 richtig. AUC zT 0,683.
  - MIT+WT-Schätzung: 67,9 von 140 gegen MIT 80. Mit Bestätigung k = 5: 75,8.
- 08.11. 10:02 – **Nutzer-Go für den angepassten Plan („Ja, so machen“).** Lesarten vorab, festgelegt bevor INT-Ergebnisse zu 161–300
  vorliegen. Bisher sind 18 von 100 Laptop-Läufen fertig; nichts davon wurde angesehen.
  **(N9) INT-Kaskade** (89_int_kaskade.py; eingefrorene L13-Sonde am Ende der INT-Antwort):
  - **Vorbedingung (WREN):** Die Sonde trennt INT-Antworten auf 161–300 mit AUC ≥ 0,75. Sonst gilt die Kaskade nur beschreibend.
  - Varianten:
    - F: feste Schwelle −1,198 für INT- und Denk-Antworten.
    - K (Argon): Schwellen auf 1–160 geeicht und blind auf 161–300 angewandt. τ_INT maximiert S₂ von „INT + Harnisch“ auf 1–160,
      τ_Denk maximiert S₂ von „MIT + Zwang + Harnisch“ auf 1–160.
  - Rückgriff im Denkmodus: MIT (Hauptvergleich); ERGORE und WT-A beschreibend.
  - **Lesart (Argon), Variante K mit MIT auf 161–300:**
    - „bestätigt“ bei S₂ ≥ +0,25 UND richtigen Abgaben ≥ 75 (MIT − 5);
    - „widerlegt“ bei S₂ ≤ +0,19 ODER richtigen Abgaben < 75;
    - sonst „offen“.
  - Zusätzlich: strenge Wertung (INT zählt nur bei regulärem Ende), Zweignutzung als Kreuztabelle, Tokens.
  **(N10) Morgengrauen** (91_morgengrauen.py):
  - **Menge:** WT-A-Läufe auf 161–300 (Seed 0) ohne abgegebene Antwort, also Denken zu ohne \boxed oder nie zu. Das ist ohne
    Lösungswissen beobachtbar.
  - **Notizen:**
    - die ≤ 3 Wert-Aussagen der ersten Runde mit dem höchsten Wahrheits-Tor zT_max (aus 82);
    - verschiedene Werte, zT_max ≥ −1;
    - je der Satz mit dem Wert plus der Satz davor, höchstens ~400 Zeichen;
    - gerahmt als „Notes from an earlier attempt (unverified, may contain mistakes)“;
    - qualifiziert sich nichts, gibt es keine Notizen; die Aufgabe ist dann gleich der Kontrolle.
  - **Runde 2:** eigen im Antwortmodus (Nicht-Denk-Vorlage), Protokoll wie INT (T 0,6, 32k, vLLM-Stil, Seed 0), gleicher
    Maschinen-Block wie die Kontrolle.
  - **Kontrolle:** der INT-Lauf (eigen, Antwortmodus, ohne Notizen) auf denselben Aufgaben.
  - **Lesart:**
    - „wertvoll am Signal“ bei Notizen − Kontrolle ≥ +5 richtige Läufe (WREN) UND ≥ 10 richtigen Läufen mit Notizen;
    - „widerlegt“ bei Notizen ≤ Kontrolle;
    - dazwischen „offen“.
  - Beschreibend: Wie oft übernimmt die Antwort einen Notiz-Wert (richtig/falsch)?
- 08.11. 10:04 – Morgengrauen-Aufgaben gebaut (91, md5 995ce3d5…).
  - **69 stumme WT-A-Läufe:** 49 im Laptop-Block, 20 im MiniPC-Block; 65 davon mit Notizen.
  - Nur beschreibend, für die Auswahl nicht benutzt: In 10 von 65 Notizen steckt der richtige Wert.
  - Ketten gestartet; sie warten auf INT:
    - Laptop: kette_tag_laptop2.sh = INT-Sonde (89) + Morgengrauen 161–260;
    - MiniPC: kette_minipc_mg.sh.
- 08.11. 10:09 – Lesarten vorab für die Nachmittags-Schritte (Laptop nach Morgengrauen):
  **(N11) Strafen-Test (WREN): Ist der INT-Vorteil ein Artefakt von presence 1,5?**
  - eigen auf Set B 1–20, Seed 0, T 0,6, 32k, vLLM-Stil, aber **presence 0,0** (eval/03c_eval_presence.py), Laptop.
  - Arme: Denken (1–10 ‖ 11–20) und Antwortmodus (1–20).
  - Vergleich mit den vorhandenen Läufen mit presence 1,5, ebenfalls Laptop: setB30-eigen-t06 bzw. setB60-ohne-eigen-t06,
    jeweils die Aufgaben 1–20.
  - Vorteil V(p) = Antwortmodus − Denken, richtig von 20.
  - **„Hinweis auf Strafen-Artefakt“, wenn V(0) ≤ V(1,5) − 4; „kein Hinweis“, wenn V(0) ≥ V(1,5) − 1; sonst „offen“.**
  - Bei n = 20 ist das nur ein grober Hinweis. Beschreibend dazu: Tokens und Schleifen-Rate.
  **(N12) Wirktiefe-Vortest (93_wirktiefe.py, GPU, erkundend):**
  - An WT-As Reflex-Abschlüssen am richtigen Wert, gierig: echter Reflex, keiner, Schub ĝ, Schub −r⊥, Schub +r⊥ (je κ 7, einmalig).
  - Gemessen:
    - Abschluss, Schluss-Satz davor, saubere Abgabe danach gegen Weiterdenken;
    - p(</think>) über 20–30 gesperrte Schritte (Wirktiefe).
  - **Lesart:** Ein Effektor gilt als Kandidat für ein „inneres fertig“, wenn er gegenüber ĝ (a) häufiger einen Schluss-Satz vor
    </think> erzeugt UND (b) danach seltener weiterdenken lässt. Erst dann wird gebaut und in echter Generierung getestet.
- 08.11. 10:36 – **Vorderzimmer gegen Hinterzimmer: Wirkt INT nur bei leichten Aufgaben?** (NACHTRÄGLICH, beschreibend,
  Entwicklungsdaten.) Begriffe des Nutzers: „Vorderzimmer“ = Antwortmodus (INT), „Hinterzimmer“ = Denkblock.
  - **Nach offizieller Stufe** (1–160; INT = eigen ohne Denken, MIT mit Denken):

    | Stufe | 1 | 2 | 3 | 4 | 5 |
    |---|---|---|---|---|---|
    | INT | 11 | 22 | 18 | 19 | 7 |
    | MIT | 12 | 25 | 18 | 16 | 6 |

    INT ist also nicht nur bei leichten Aufgaben gut; bei Stufe 4–5 liegt es sogar knapp vorn (26 gegen 22).
  - **Nach modell-eigener Schwierigkeit** (Länge der INT-Antwort):
    - 1–160, INT gegen MIT: schnell (< 1.000 Tokens) 41 gegen 50; lang (> 8.000) 15 gegen 10. Achtung: Hier sind Modus und Modell
      vermischt, denn MIT ist das stärkere Modell.
    - **Set B, dasselbe Modell (eigen) in beiden Modi:**

      | INT-Antwort | n | INT (Vorderzimmer) | Denken Seed 0 | Denken Seed 1 |
      |---|---|---|---|---|
      | schnell (< 1.000 Tokens) | 26 | 21 | 19 | 19 |
      | lang (> 8.000 Tokens) | 25 | **8** | 2 | 3 |

  - → Beim selben Modell hilft das Hinterzimmer weder bei schnellen noch bei schweren Aufgaben. Bei den schweren schadet es
    deutlich. [Plausibel] Für das 0.8B ist der Denkblock nicht der Ort, an dem schwere Aufgaben gelöst werden, sondern der Ort, an
    dem es sich verliert. Kleine Fallzahlen; der Frischtest (N8) läuft.
- 08.11. 10:43 – **(N8) INT AUF FRISCHEN AUFGABEN – URTEIL (94_int_frisch.py, vorab festgelegt 09:40):**
  - eigen ohne Denken **71/140**, MIT mit Denken **80/140** (nur INT 15 : nur MIT 24, p = 0,20).
  - **Vorab-Lesart: „offen“.** Gefordert für „hält“ war ≥ 73, „widerlegt“ wäre ≤ 66.
  - Alle 71 Treffer enden regulär (eos); streng gewertet ebenfalls 71.
  - Tokens auf gemeinsam gelösten Aufgaben: **INT 3.661 gegen MIT 14.639** (−75 %).
  - Je Block (beschreibend):

    | Block | INT | MIT Seed 0 | MIT Seed 1 |
    |---|---|---|---|
    | 161–260 (Laptop) | **57** | **58** (15 : 16, p = 1,0) | – |
    | 261–300 (MiniPC) | 14 | 22 (0 : 8, p = 0,01) | 16 (4 : 6, p = 0,75) |

  - Gegen die eigenen Gewichts-Bausteine: INT 71 gegen WT-A 61 (p = 0,19; im Laptop-Block 57 : 44, p = 0,04) und gegen ERGORE 65
    (p = 0,44).
  - → Der Antwortmodus ist auf frischen Aufgaben unser bester eigener Weg. Er hält mit MIT im großen Block exakt mit, bei einem
    Viertel der Tokens. Im kleinen Block liegt er gegen MITs (auffällig hohen) Seed 0 zurück, gegen MITs Seed 1 nicht. Die
    Vorab-Lesart bleibt „offen“, nicht „hält“.
- 08.11. 10:48 – **Nutzer-Go: MIT im Vorderzimmer („Ja gerne“). Lesart vorab (N13), bevor ein Lauf existiert:**
  - Lauf: MIT (Qwen3.5-0.8B-mit-q8_0) in der offiziellen Nicht-Denk-Vorlage (03b) auf MATH-500 161–300, Seed 0, T 0,6, 32k,
    vLLM-Stil.
  - Blöcke wie im Schritt 3: MiniPC 261–300 nach Morgengrauen, Laptop 161–210 ‖ 211–260 nach dem Strafen-Test.
  - Hauptvergleich: MIT ohne Denken gegen MIT mit Denken (Seed 0), gepaart, N = 140.
  - **Lesart:**
    - „Das Hinterzimmer lohnt sich bei MIT“, wenn MIT mit Denken ≥ MIT ohne Denken + 7.
    - „Auch bei MIT keine Hilfe“, wenn MIT ohne Denken ≥ MIT mit Denken − 2.
    - Sonst „offen“.
  - Beschreibend: gegen eigen ohne Denken (71), je Block, Tokens, strenge Wertung.
  - Prognose (Claude): MIT ohne Denken 72 ± 7, also eher „lohnt sich“ oder „offen“. Begründung: MITs Hinterzimmer hat einen
    funktionierenden Ausgang (44 von 65 Läufen über den langen Prüfweg gerettet).
- 08.11. 10:49 – **Token-Bild INT gegen MIT im Block 161–260** (beschreibend, zu N8). Treffer 57 gegen 58.
  - **Gemeinsam gelöst (42):** Median **1.024 gegen 13.779 Tokens**, Mittel 3.845 gegen 14.053 (27 %). INT ist bei 41 von 42
    günstiger.
  - **Alle 100:** Summe 845.695 gegen 2.121.062 (40 %). Je richtiger Antwort **14.837 gegen 36.570 Tokens**.
- 08.11. 10:56 – **Nutzer-Go „gerne simulieren“.** Simuliert wird die vom Nutzer bevorzugte **Zustands-Tür** (Weg 2), rein aus
  vorhandenen Daten. Die Zeit-Uhr (Weg 1) bleibt auf der Roadmap. Lesart vorab, erkundend (N14, 95_zustandstuer.py):
  - Läufe: Denkläufe von WT-A und MIT auf 161–300 (Seed 0), mit den Wahrheits-Werten je Wert-Aussage aus der Zuck-Messung (82).
  - **Tür:**
    - Sie öffnet beim ersten Token, an dem der Schleifen-Grad w (Anteil wiederholter 8-Gramme in den 512 Tokens davor, wie 88)
      ≥ W liegt, frühestens ab 1.000 Tokens.
    - Ist vorher mindestens ein Wahrheits-Blitz (zT_max > 0) an einer Wert-Aussage gefallen, wird der Wert mit dem höchsten
      zT_max abgegeben (Feierabend).
    - Sonst „weiß ich nicht“ (Pausenraum).
    - Öffnet die Tür nie, bleibt das tatsächliche Ergebnis des Laufs.
  - Varianten: W = 0,3 / 0,5 / 0,7. Wahl des Werts: höchster Blitz bzw. jüngster Blitz.
  - Kennzahlen: richtig / falsch / enthalten, S₂, Tokens; jeweils gegen den tatsächlichen Lauf.
  - **Lesart (erkundend):** „Die Zustands-Tür trägt“, wenn sie bei mindestens zwei der drei W-Werte mehr richtige Abgaben UND ein
    höheres S₂ liefert als der tatsächliche Lauf, für WT-A oder MIT.
- 08.11. 10:57 – **(N14) Zustands-Tür simuliert (95, erkundend): NICHT getragen.** Bei allen W liefert die Tür weniger richtige
  Abgaben und ein schlechteres S₂ als der tatsächliche Lauf.

  | Lauf | Tür bei W | Tür offen | richtig (gegen tatsächlich) | falsch | S₂ (tatsächlich) |
  |---|---|---|---|---|---|
  | WT-A | 0,3 | 96 | 38–41 (61) | 64–67 | −0,69 bis −0,62 (+0,29) |
  | WT-A | 0,7 | 75 | 54 | 63 | −0,51 |
  | MIT | 0,7 | 97 | 52–64 (80) | 69–81 | −0,79 bis −0,53 (+0,33) |

  - Nachträglich geprüft, nur zur Einordnung: eine strenge Tür nahe am Schleifen-Abbruch (w ≥ 0,9 ab 4.096 Tokens). Sie öffnet bei
    beiden Modellen in 68 Läufen und bleibt negativ: WT-A 56–57 richtig, MIT 70–71, S₂ −0,04 bis −0,42.
  - → Zwei Gründe:
    - (1) Hohe örtliche Wiederholung tritt auch in erfolgreichen, prüfenden Phasen auf. MIT erreicht sie in 68 Läufen und löst
      trotzdem 80. Wiederholung allein ist also kein Zeichen für „verirrt“.
    - (2) Der stärkste Wahrheits-Blitz zeigt oft auf einen falschen Wert. Das Tor öffnet auch an 6–12 % der falschen Aussagen,
      und von denen gibt es viel mehr.
  - Folge für Weg 2 und 3: Die Tür braucht ein spezifischeres „verirrt“-Signal (zum Beispiel kein neuer Wert mehr, nur Wiederholung
    desselben) und eine spezifischere Wahrheit (Kandidaten-Ende, wiederholte Bestätigung). Mit den heutigen Signalen ist sie nicht
    baubar. Das war der Zweck der Simulation vor dem Bau.
- 08.11. 11:12 – **(N9) INT-KASKADE – URTEIL (89; Lesart vorab 09:58).** Technik: Die Sonden-Messung lief in den 20 min bis 359 von
  360 Läufen; der letzte wurde auf der CPU nachgeholt.
  - **Vorbedingung (WREN) auf 161–300 NICHT erfüllt:** Die Sonde trennt INT-Antworten nur mit AUC **0,681** (1–160: 0,759; Set B:
    0,74). Die Kaskade gilt damit nur beschreibend.
  - **Hauptvariante K streng mit MIT, 161–300:**
    - S₂ **+0,321** (MIT allein +0,271; MIT + Zwang + Harnisch +0,221);
    - richtig **67**, falsch 11, enthalten 62 (Zweige: INT richtig 27 / falsch 7, Denken richtig 40 / falsch 4, weiß nicht 62);
    - → nach Regel **WIDERLEGT**, weil weniger als 75 richtig.
  - Tokens sinken nicht, sie steigen auf Ø 25.981, weil die meisten Aufgaben in den Denk-Zweig fallen.
  - **Ursache:** Im Antwortmodus ist die Sonde stark nach oben verschoben. INT-Antworten haben Median **+3,4 (richtig)** bzw.
    **+1,9 bis +2,6 (falsch)**, die eingefrorene Schwelle liegt bei −1,2.
    - Variante F lässt deshalb fast alles durch: 161–300 mit 67 falschen Abgaben, S₂ −0,45.
    - Die auf 1–160 geeichte Schwelle (3,8) ist auf frischen Aufgaben zu streng.
  - → Die Wahrheits-Sonde ist eine **Hinterzimmer-Sonde**. Im Vorderzimmer klingt jede Aussage behauptend, das Signal verschiebt
    sich, und die Trennung wird schwächer. Für INT braucht es eine eigene **Vorderzimmer-Sonde**, gelernt auf Antwort-Texten
    (Poows Vorschlag V1, WRENs Vorbedingung).
- 08.11. 11:33 – **Ergänzung zu N12, vor dem Lauf** (Nutzer-Bild 11:15: „Tür aufreißen“ = erzwungen, ohne Begleitung; „zur Tür
  begleiten“ = mit Sicherheit und Führung):
  - Zwei Bedingungen kommen hinzu, „ĝ begleitet“ und „−r⊥ begleitet“. Der gleiche Gesamtschub κ wird auf drei Schritte verteilt
    (je κ/3: letzte Präfix-Stelle und die zwei folgenden), statt einmal voll gesetzt zu werden.
  - Lesart wie N12: Begleitung gilt als besser, wenn sie häufiger einen Schluss-Satz vor </think> und seltener Weiterdenken danach
    erzeugt als der einmalige Schub derselben Richtung.
  - Zeitlimit des Schritts in kette_tag_laptop3.sh auf 35 min erhöht (Datei wartet noch, ist noch nicht ausgeführt).
- 08.11. 11:42 – **(N10) MORGENGRAUEN – URTEIL (92; Lesart vorab 09:58).** 69 stumme WT-A-Läufe, die in Runde 1 nichts abgegeben
  hatten.
  - Notizen-Arm (eigen im Antwortmodus mit Notizen aus den stärksten Wahrheits-Blitzen): **22 richtig**.
  - Kontrolle (INT-Lauf ohne Notizen, dieselben Aufgaben): **25 richtig** (beide 13, nur Notizen 9, nur Kontrolle 12, p = 0,66).
  - → **Vorab-Lesart: WIDERLEGT** (Notizen − Kontrolle = −3).
  - Beschreibend:
    - **Die zweite Chance im Vorderzimmer an sich rettet ein Drittel der stummen Läufe** (22 bzw. 25 von 69); WT-A hatte dort 0.
      Es wirkt der Raumwechsel, nicht die Notizen.
    - Enthalten die Notizen den richtigen Wert (10 Aufgaben), helfen sie: 8 gegen 5. Sonst führen sie eher in die Irre. Übernommen
      wird ein Notiz-Wert 14-mal, davon 7 richtig.
    - Tokens: Notizen 10.507, Kontrolle 13.321.
  - → Die Notizen sind nur so gut wie die Wahrheits-Auswahl. Die stärksten Blitze treffen den richtigen Wert nur in 10 von 65
    Fällen (vgl. AUC 0,68).
- 08.11. 11:42 – **Antworten des Nutzers auf die Fragen-Anker in Messungen übersetzt (96_durchstreichen.py; NACHTRÄGLICH,
  beschreibend):**
  - **Durchstreichen** (Rücknahme-Wort ≤ 60 Tokens nach einem Wert; grobes Maß, „wait“ zählt mit):

    | Text | richtige Werte durchgestrichen | falsche Werte durchgestrichen |
    |---|---|---|
    | WT-A, Denken | **74 %** | 60 % |
    | MIT, Denken | **59 %** | 45 % |
    | INT, Antwortmodus | 18 % | 14 % |

    - Das Wahrheits-Tor an durchgestrichenen gegen behaltene richtige Werte ist praktisch gleich: WT-A −2,48 gegen −2,50; MIT
      +0,20 gegen +0,39.
    - → Im Hinterzimmer werden **richtige Werte sogar häufiger durchgestrichen als falsche**, unabhängig vom Wahrheits-Signal.
      Das Durchstreichen dort ist kein Urteil über Wahrheit, sondern eine Gewohnheit („Wait, let me check“ nach jedem Ergebnis).
      Im Vorderzimmer wird selten gestrichen. (Nutzer: „Warum wird durchgestrichen, WENN das Durchgestrichene wahr ist?“)
  - **Schnell sicher gegen schnell geraten** (INT unter 1.000 Tokens, 90 richtig / 37 falsch): Kein Signal trennt.
    - AUC Durchstreichen 0,49, Zweifel-Wörter 0,48, verschiedene Werte 0,50, Sonde 0,54; nur die Länge leicht (0,37: falsche etwas
      länger).
    - → Das falsche Viertel der schnellen Antworten sind **sichere Irrtümer**. Die Intuition irrt still.
  - **Schilder** (Wörter in den 12 Tokens vor dem ersten </think>):
    - vor MITs natürlichen Abschlüssen: „answer“ 31 %, „so“ 17 %, „final“ 14 %, „ready“ 8 %;
    - vor WT-As Reflex-Abschlüssen: „answer“ 10 %, sonst Rechenzeichen („frac“, „times“, „sqrt“).
    - → Das Haus hat eigene Schilder („So the final answer is …“, „I'm ready“). Der natürliche Abschluss geht an ihnen vorbei, der
      Reflex-Abschluss überspringt sie. Das stützt „zur Tür begleiten“ statt „Tür aufreißen“ (Bedingung in N12).
- 08.11. 11:45 – **Nutzer-Go: Tagesform-Test (N15), Lesart vorab.**
  - Lauf: eigen ohne Denken (INT) mit **Seed 1** auf MATH-500 261–300, MiniPC, 12 Slots, nach MIT im Vorderzimmer.
  - Vergleich je Aufgabe mit INT Seed 0 (261–300) und dem Hinterzimmer MIT Seed 0 gegen Seed 1 (261–300; 75 % gleich gelöst,
    22 → 16).
  - **These des Nutzers:** Das Vorderzimmer ist tagesform-stabiler, weil das Wissen schnell abgerufen wird.
  - **Lesart:**
    - „bestätigt“, wenn INT zwischen den Seeds bei ≥ 85 % der Aufgaben gleich abschneidet UND sich die Trefferzahl um ≤ 3 von 40
      ändert;
    - „widerlegt“, wenn die Übereinstimmung ≤ 75 % liegt (wie MIT im Hinterzimmer);
    - dazwischen „offen“.
  **(N16) Knoten „Zustands-Tür“ mit dem Bild des Nutzers neu (erkundend, nur vorhandene Daten):** „kaum Antworten“ statt bloßer
  Wiederholung.
  - Die Tür öffnet, wenn der Schleifen-Grad ≥ 0,5 ist UND in den letzten 2.000 Tokens kein neuer Wert mehr auftauchte, frühestens
    ab 2.000 Tokens.
  - Abgabe-Regel wie N14 (höchster Blitz) und zusätzlich „bestätigt“: nur ein Wert mit ≥ 2 Blitzen, sonst „weiß ich nicht“.
  - Lesart wie N14: „trägt“, wenn mehr richtige Abgaben UND ein höheres S₂ als der tatsächliche Lauf, für WT-A oder MIT.
- 08.11. 11:47 – **(N16) Tür „kaum Antworten“ (97, erkundend): besser als die einfache Tür, trägt aber noch nicht.**

  | Lauf | Tür offen | richtig (tatsächlich) | falsch | S₂ (tatsächlich) |
  |---|---|---|---|---|
  | WT-A | 55 | 56–57 (61) | 42–49 | −0,20 bis −0,29 (+0,29) |
  | MIT | 68 | 69 (80) | 39–52 | −0,06 bis −0,25 (+0,33) |

  - Abgabe nur bei bestätigtem Wert (mindestens 2 Blitze) senkt die falschen Abgaben, reicht aber nicht.
  - → Das „verirrt“-Signal wird schärfer. Der schwache Punkt bleibt die Wahrheit beim Abgeben, also welcher Wert genommen wird.
    Ohne bessere Wahrheits-Sonde am Wert-Moment ist keine Tür baubar.
- 08.11. 11:47 – **Schilder des Hauses über den langen Atem (98_schilder.py; NACHTRÄGLICH, beschreibend; Nutzer: „bleibt das auf den
  langen Atem gleichfalls stabil?“).** Schild = Schluss-Formulierung in den 30 Tokens vor dem ersten </think> (answer, final,
  therefore/thus/so, ready, I'll write …).

  | Abschlüsse | mit Schild | richtig mit / ohne Schild | Schild nach Atem: kurz / mittel / lang |
  |---|---|---|---|
  | MIT Seed 0, 161–300 (118) | **58 %** | 45/68 · 35/50 | 70 / 67 / **56 %** |
  | MIT Seed 1, 261–300 (30) | **57 %** | 11/17 · 5/13 | – / 75 / **69 %** |
  | MIT Set B (41) | **59 %** | 15/24 · 12/17 | – / 75 / 53 % |
  | WT-A Reflex (69) | 28 % | 15/19 · 36/50 | 24 / 33 / – |
  | WT-A natürlich (34) | 26 % | 4/9 · 6/25 | – / 40 / 10 % |
  | eigen Set B (36) | 33 % | **11/12 · 12/24** | – / 17 / 40 % |
  | ERGORE 161–300 (135) | 32 % | 24/43 · 41/92 | 12 / 30 / 49 % |

  - → **Bei MIT sind die Schilder stabil:** über Seeds (58/57 %), Aufgabensätze (59 %) und auch beim langen Atem (56–69 %).
  - Unsere eigene Familie (eigen, ERGORE, WT-A) hängt sie nur in 26–33 % auf.
  - Wo sie es tut, ist der Abschluss häufiger richtig (eigen 11/12 gegen 12/24; ERGORE 56 % gegen 45 %). Bei MIT macht das Schild
    beim Treffer keinen klaren Unterschied.
  - Deutung (Hypothese): **Die Schilder gehören zu MITs Haus.** Das passt zu MITs Rest-Richtung r⊥, deren Top-Tokens
    Schlusswörter sind. Der Wirktiefe-Vortest (läuft) prüft, ob ein Schub entlang r⊥ die Schilder auch in eigen aufhängt.
- 08.11. 11:50 – Technisch: Der Wirktiefe-Vortest braucht ~7 min je Bedingung. In 35 min schafft er voraussichtlich nur WT-A, keiner,
  ĝ, −r⊥ (und vielleicht +r⊥).
  - 93 ist jetzt fortsetzbar und überspringt fertige Bedingungen.
  - kette_tag_laptop4.sh holt die fehlenden („+r⊥“, „ĝ begleitet“, „−r⊥ begleitet“) vor MIT im Vorderzimmer nach, höchstens
    30 min. MIT-INT verschiebt sich dadurch um ≤ 30 min.
  - Die Lesart (N12 + Ergänzung) bleibt unverändert.
- 08.11. 12:06 – **Nutzer: „Die Schildergeschichte ist ein weiterer Hinweis … das INT-Thema lässt mich nicht los … gezielt offline
  testen.“**
  Vorab notierte Fragen (N17, erkundend, nur Text und vorhandene Messungen; 99_schilder_int.py):
  - **(S1)** Ist ein Abschluss mit Schild ein inneres „fertig“? Prüfgröße im Antwortteil: weniger zweites </think>, kürzer, öfter
    \boxed. Verglichen wird mit Schild gegen ohne, je Modell.
  - **(S2)** Schilder mitten im Denken: Wie oft schreibt ein Modell „the (final) answer is“ und schließt dann binnen 200 Tokens,
    statt weiterzudenken? MIT gegen unsere Familie.
  - **(S3)** Schild plus Wahrheit (WT-A- und MIT-Texte): Wie hoch ist das Wahrheits-Tor am Wert direkt hinter dem Schild? Wie oft
    ist dieser Wert richtig? Kandidat für einen „Schild-Reflex“.
  - **(I1)** Karte Vorder- gegen Hinterzimmer: Wo gewinnt INT, wo das Denken? Nach Fach, Stufe und Antwort-Art, 1–300.
  - **(I2)** Festlegungs-Risiko im Vorderzimmer: Bleibt ein langer, falscher INT-Lauf beim ersten genannten Wert („festgelegt“),
    oder wechselt er?
- 08.11. 12:08 – **(N17) Ergebnisse Schilder und Vorderzimmer (99_schilder_int.py; erkundend):**
  - **(S1) Abschluss mit Schild ≈ inneres „fertig“.** In unserer Familie und bei MIT Seed 1 ist der Antwortteil nach einem Abschluss
    mit Schild sauberer:

    | | mit Schild | ohne Schild |
    |---|---|---|
    | eigen Set B: zweites </think> / \boxed / richtig | **0 % / 92 % / 92 %** | 4 % / 67 % / 50 % |
    | ERGORE: zweites </think> / Antwortteil (Median) / richtig | **40 % / 1.698 Tokens / 56 %** | 61 % / 6.983 Tokens / 45 % |
    | MIT Seed 1: zweites </think> / richtig | **18 % / 65 %** | 38 % / 38 % |

    - Bei WT-A: \boxed 79 % gegen 65 %, richtig 68 % gegen 56 %; das Weiterdenken bleibt aber (~75 %).
    - MIT Seed 0 zeigt keinen Unterschied.
  - **(S2) Schilder mitten im Denken bleiben meist ohne Tür:** 5–9 Schilder je Lauf („the (final) answer is …“), aber nur 2–10 %
    davon führen binnen 200 Tokens zum Abschluss (WT-A 2 %, eigen 4 %, MIT 5–7 %, ERGORE 10 %).
  - **(S3) Schild plus Wahrheit ist ein scharfes Signal:**
    - Werte direkt hinter einem Schild sind zu 45 % richtig, alle anderen zu 5–6 %.
    - Das Wahrheits-Tor trennt dort mit **AUC 0,80 (WT-A-Texte) / 0,85 (MIT-Texte)** statt 0,67 / 0,71.
    - → Möglicher Baustein „Schild-Reflex“: als Kontext das eigene Schild des Modells statt unseres Kandidaten-Ende-Melders, dazu
      die Wahrheit, dann Abgabe. Damit lockert sich der Knoten „Wahrheit beim Abgeben“.
  - **(I1) Karte Vorder- gegen Hinterzimmer** (1–300; INT = eigen ohne Denken, nur INT : nur Denken):

    | Fach / Stufe | gegen MIT | gegen ERGORE |
    |---|---|---|
    | Zahlentheorie | 2 : 11 | 5 : 9 |
    | Algebra | 4 : 12 | 6 : 11 |
    | Geometrie | 6 : 1 | 8 : 1 |
    | Präkalkül | 10 : 3 | 9 : 3 |
    | Stufe 1 | 0 : 5 | 0 : 5 |
    | Stufe 4 | 14 : 11 | 20 : 11 |

    → Das Hinterzimmer hilft bei Zahlentheorie und Algebra, wo Fallprüfen und Nachrechnen zählen, und bei den leichtesten
    Aufgaben (Flüchtigkeitsfehler). Das Vorderzimmer ist stärker bei Geometrie, Präkalkül und Stufe 4. Kleine Zellen.
  - **(I2) Korrektur meiner Annahme „Festlegungs-Risiko im Vorderzimmer“: nicht gestützt.** Lange INT-Läufe bleiben nicht beim
    ersten Wert (falsche: nur 1 % enden mit ihm; Ø 149 verschiedene Werte). Auch das Vorderzimmer hat bei langen Läufen einen Flur:
    Es wandert, statt sich festzulegen.
- 08.11. 12:15 – **(N12) WIRKTIEFE-VORTEST – Ergebnis (93; 30 Reflex-Abschlüsse am richtigen Wert; gierig).** Alle 7 Bedingungen
  liefen im ersten Fenster (11:40–12:14); der Nachhol-Schritt in kette_tag_laptop4.sh findet nichts mehr zu tun.

  | Bedingung | schließt | sofort | p(</think>) gesperrt, Schritt 0 / 1 / 2 / 5 | Schluss-Satz davor | Weiterdenken danach |
  |---|---|---|---|---|---|
  | WT-A (echter Reflex) | 26/30 | 26 | 0,75 / 0,27 / 0,03 / 0 | 0 | 4 |
  | keiner (eigen) | 0/30 | – | 0 / 0 / 0 / 0 | – | – |
  | ĝ einmal κ 7 | 30/30 | 30 | 1,00 / 0,02 / 0 / 0 | 0 | 4 |
  | −r⊥ einmal | 0/30 | – | 0 | – | – |
  | +r⊥ einmal | 0/30 | – | 0 | – | – |
  | ĝ begleitet (3 × κ/3) | 17/30 | 0 (Median Schritt 1) | 0,01 / 0,36 / 0,32 / 0 | 0 | **11** |
  | −r⊥ begleitet | 0/30 | – | 0 | – | – |

  - **Lesart N12:** Kein Effektor erfüllt die Bedingung. Keiner erzeugt einen Schluss-Satz, und Begleitung führt sogar zu mehr
    Weiterdenken.
  - **Wirktiefe bestätigt (Nutzer, Argon):** Jeder Schub wirkt genau so lange, wie er gesetzt wird. Danach fällt p(</think>) auf
    null. Es entsteht kein bleibender Zustand.
  - **r⊥ als einmaliger Schub bewegt nichts,** in keinem Vorzeichen. MITs Schilder entstehen also nicht durch einen Stoß, sondern
    durch einen Eingriff, der laufend an vielen Stellen wirkt.
  - Deutung (Hypothese): Ein inneres „fertig“ lässt sich nicht anstoßen, es muss sich über die Schluss-Strecke aufbauen. Daher der
    Schild-Reflex als nächster Bau-Kandidat:
    - Er feuert während das Modell sein eigenes Schild schreibt („the answer is X“, mehrere Tokens), nur bei hoher Wahrheit.
    - Er begleitet damit synchron zu den eigenen Schlusswörtern (vgl. S3: Wahrheit trennt dort mit AUC 0,80–0,85).
    - Nicht heute.
- 08.11. 12:15 – Wächter-Alarm „HÄNGER Laptop“ (12:14) war ein Fehlalarm: 60 min ohne 03_eval-Log während des GPU-Vortests. Der
  Strafen-Test läuft seit 12:14.
- 08.11. 12:22 – **Nutzer: Schild-Reflex als gezielte Aufgabe an Argon, inklusive Testbeispiel und Simulation.** Vorher simulieren wir
  ihn selbst offline auf vorhandenen Daten. Lesart vorab (N18, erkundend, 100_schild_reflex.py):
  - Läufe: Denkläufe von WT-A und MIT auf 161–300 (Seed 0), Wahrheits-Tor je Wert-Aussage aus 82.
  - **Auslöser:** Das Modell schreibt selbst ein Schild („the (final) answer is“, „so the answer“, „therefore the answer“), und
    der Wert direkt dahinter (≤ 15 Tokens) hat zT_max ≥ τ. Dann gilt der Reflex als gefeuert: Abgabe dieses Werts.
  - Ohne Auslöser bleibt das tatsächliche Ergebnis des Laufs.
  - Varianten: τ = 0 / 1 / 2. Dazu „Nachsicht“: erst beim 2. Schild mit demselben Wert und zT ≥ τ.
  - Kennzahlen: richtig / falsch / ohne Abgabe, S₂, Tokens (Auslöse-Stelle statt Lauf-Ende), je gegen den tatsächlichen Lauf.
  - **Lesart:** „Der Schild-Reflex trägt in der Simulation“, wenn er bei mindestens einer τ-Variante mehr richtige Abgaben UND ein
    höheres S₂ liefert als der tatsächliche Lauf, bei WT-A oder MIT. Zusätzlich muss er Tokens sparen.
- 08.11. 12:24 – **(N18) Schild-Reflex simuliert (100): trägt bei WT-A knapp, bei MIT nicht.**

  | Lauf | Variante | feuert | richtig (tatsächlich) | falsch | S₂ (tatsächlich) | Tokens (tatsächlich) |
  |---|---|---|---|---|---|---|
  | WT-A | τ 0 / 1, erstes Schild | 10–11 | **64 (61)** | 9 | **+0,329 (+0,293)** | 18.260 (19.064) |
  | WT-A | τ 2 | 3 | 62 | 9 | +0,314 | 18.816 |
  | MIT | τ 0, erstes Schild | 59 | 75 (80) | 30 | +0,107 (+0,329) | 17.945 (21.525) |
  | MIT | τ 0, Nachsicht (2. Schild) | 37 | 78 | 21 | +0,257 | 19.826 |

  - **Vorab-Lesart erfüllt für WT-A:** mehr richtig, höheres S₂, weniger Tokens. Der Effekt ist klein (+3). Die Simulation nimmt an,
    dass die Abgabe gelingt; real eher +1 bis +2.
  - **Für MIT nicht erfüllt:** Der Reflex unterbricht MITs funktionierenden Prüfweg (wie bei MIT+WT).
  - → Es ist die erste simulierte Tür, die WT-A nicht schadet. Sie feuert selten und genau dort, wo WT-A sich sonst verliert.
    Weitergabe an Argon als gezielte Bauaufgabe (Nutzer).
- 08.11. 12:39 – **Argon, Teil 2** (Entscheidungsmatrix, Manuskript-Plan, Literatur; abgelegt unter gutachter/2026-11-08). Zwei
  Zahlen, die die Matrix verlangt, nachgerechnet:
  - **Seed 1, H-WT2-Maß (161–260):** WT-A 33/61 gegen MIT 25/74, Fisher einseitig p = 0,014 (Seed 0 im selben Block: p = 0,0012).
    Argons Kriterium „p < 0,01“ ist mit Seed 1 knapp verfehlt; signifikant auf 5 % bleibt es.
  - **Geschachtelte Modelle Tiefe** (88 --geschachtelt; richtige Wert-Aussagen, standardisiert): Der Tiefen-Koeffizient ist
    M1 −0,49 → M2 (+ Stufe) −0,27 → M3 (+ Schleife) **+0,46** → M4 (+ Quelle) +0,26.
    → Er kehrt sich um. Argons Kriterium „|β_Tiefe| schrumpft um > 60 %“ ist erfüllt: Die Sonde liest den Zustand, nicht die Tiefe.
- 08.11. 12:55 – **Replay der stummen WT-A-Antwortteile (N19), Lesart vorab, bevor ein Lauf existiert.** Nutzer: „wenn es nur
  10 Min. sind, warum nicht“. Grundlage: Argon Teil 2, Kurzversuch 1; Skript 101_replay.py.
  - **Daten:** die 32 WT-A-Läufe aus 161–300 (Seed 0), die das Denken geschlossen, im Antwortteil aber kein \boxed{} geschrieben
    haben.
    - 14 davon mit frühem richtigen Wert im Antwortteil (81_format_check).
    - Keiner der 32 war ursprünglich richtig.
    - 12 der 32 (8 der 14) setzten im Antwortteil ein weiteres </think>.
  - **Präfix:** Prompt + Denkteil bis einschließlich des ersten </think> (Median 16.708 Tokens, max. 33.434).
  - **Neu generiert wird nur der Antwortteil:**
    - höchstens 1.024 Tokens;
    - Protokoll der Läufe (vLLM-Stil, presence 1,5), Seed 0;
    - WT-A-GGUF (md5 auf Laptop und MiniPC gleich), MiniPC, 12 Slots.
  - **Arme:**
    - Arm A: zweites </think> gesperrt (logit_bias).
    - Arm K: Kontrolle ohne Sperre, gleicher Seed (Nochmal-Effekt, Einwand WREN). A und K laufen gekoppelt und trennen sich erst
      dort, wo </think> eine Rolle spielt.
    - Argons Arm B (Effektor −r⊥ statt ĝ) entfällt: Im Wirktiefe-Vortest (N12) öffnet ein Schub entlang −r⊥ die Tür gar nicht.
  - **Begriffe:** „gerettet“ = das letzte \boxed{} im neuen Antwortteil ist richtig (Bewertung wie 03_eval). „Sauber“ heißt
    zusätzlich: Ende mit eos.
  - **Lesart (a), Argons Kriterium:** „bestätigt“, wenn Arm A ≥ 10 der 14 rettet; „widerlegt“, wenn < 7; sonst „offen“.
  - **Lesart (b), Sperre gegen Kontrolle (alle 32, gepaart):** „Sperre trägt“, wenn A mindestens 3 mehr rettet als K; „kein
    Sperr-Effekt“, wenn A − K ≤ 1; sonst „offen“.
  - **Hinweis vorab zu Argons zweitem Kriterium („Doppel-</think> < 25 %“):**
    - In Arm A ist es durch die Sperre trivial erfüllt.
    - Argons Ausgangswert 83–100 % passt nicht zu unseren Daten (12/32 = 38 %; 8/14).
    - Die Rate in Arm K berichten wir beschreibend.
  - **Beschreibend:**
    - WT-A hochgerechnet (61 + gerettete);
    - gepaarte Tabelle A/K;
    - Rettungen unter den 18 ohne frühen richtigen Wert.
  - **Einordnung vorab:**
    - Selbst „bestätigt“ hieße nur: Nach einem Reflex-Abschluss verliert WT-A die Aufgabe im Antwortteil (Abgabe-Hygiene).
    - Ein inneres „fertig“ ist damit nicht gebaut.
    - Die Sperre ist ein Eingriff von außen (Sampler), kein Gewichts-Bau. Sie dient der Diagnose, nicht als Vorschlag (Nutzer:
      „Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen“).
- 08.11. 12:57 – **(N11) Strafen-Test: kein Hinweis auf ein Strafen-Artefakt.** Set B 1–20, eigen, Seed 0, Laptop.

  | presence | Denken | Antwortmodus (INT) | V = INT − Denken | Ø Tokens Denken / INT |
  |---|---|---|---|---|
  | 0,0 | 7/20 | 9/20 | +2 | 23.284 / 4.785 |
  | 1,5 | 8/20 | 10/20 | +2 | 25.893 / 8.338 |

  - V(0) = V(1,5) → Lesart **„kein Hinweis“**. Der Vorsprung des Vorderzimmers ist kein Artefakt der presence penalty.
  - Beschreibend: Ohne Strafe enden 12/20 Denk-Läufe nicht mit eos (mit Strafe 11/20). INT endet in beiden Fällen immer mit eos.
    Ohne Strafe schreibt INT nur gut halb so viele Tokens.
  - n = 20: grober Hinweis.
- 08.11. 12:57 – **(N15) Tagesform: widerlegt, genau auf der Grenze.**

  | Lauf (261–300) | Seed 0 → Seed 1 | gleich gelöst | κ |
  |---|---|---|---|
  | INT (Vorderzimmer) | 14 → 16 | 75 % | 0,47 |
  | MIT (Hinterzimmer) | 22 → 16 | 75 % | 0,51 |
  | ERGORE (Hinterzimmer, beschreibend) | 14 → 16 | 80 % | 0,57 |

  - Die Trefferzahl ändert sich um +2 (Kriterium ≤ 3 erfüllt). Gleich gelöst werden aber nur 75 %, und die Lesart sagt
    „≤ 75 % = widerlegt“.
  - Die These des Nutzers (Vorderzimmer tagesform-stabiler) trägt auf diesen 40 Aufgaben nicht. Die Zahl der Treffer schwankt
    wenig. Welche Aufgaben gelöst werden, wechselt im Vorderzimmer aber genauso wie im Hinterzimmer (κ zufallsbereinigt).
  - n = 40, ein Seed-Paar: Ein Unterschied von 5–10 Prozentpunkten wäre damit nicht nachweisbar.
- 08.11. 13:09 – **Vorderzimmer-Signal „Intuition zweimal fragen“** (NACHTRÄGLICH, beschreibend; Nutzer-Frage nach einer
  Vorderzimmer-Sonde). INT Seed 0 gegen Seed 1 auf 261–300, n = 40:
  - Gleiche Antwort in beiden Seeds: 12 Aufgaben, davon 10 richtig (83 %). Verschiedene Antworten: 28 Aufgaben, Seed 0 nur 4
    richtig (14 %). Grundrate 35 %.
  - Als Zimmer-Weiche gedacht (gleich → abgeben, sonst Hinterzimmer), nachträglich:
    - mit WT-A 20/40 (WT-A allein 17, INT allein 14);
    - mit ERGORE 19/40 (allein 14);
    - mit MIT 21/40 (allein 22).
    - Auf diesen schweren Aufgaben kostet die Weiche mehr Tokens als das Hinterzimmer allein, weil beide INT-Läufe lang sind
      (Ø ~8.000).
  - Nur Hypothese, n = 40, nachträglich gewählt. Ein vorab festgelegter Test (mehr Aufgaben, Lesart vorab) steht aus.
- 08.11. 13:12 – **Nutzer-Go „Ja, mit einplanen“: zwei Vorderzimmer-Tests. Lesarten vorab, bevor ein Lauf oder eine Messung
  existiert.**
  **(N20) Zweifach-Intuition: „Die Intuition zweimal fragen“.**
  - **Läufe:** eigen ohne Denken (INT, 03b) mit **Seed 1** auf MATH-500 161–260, sonst gleiches Protokoll wie Seed 0 (T 0,6,
    32k, vLLM-Stil).
    - Laptop: 161–185 ‖ 186–210, nach Vorderzimmer-Sonde (N21).
    - MiniPC: 211–260, nach dem Replay.
  - **Paare:** Seed 0 / Seed 1 auf 161–260 = **100 Aufgaben, die hier noch niemand gesehen hat (Hauptauswertung)**. 261–300 ist
    schon gesehen (Eintrag 13:07) und wird nur getrennt berichtet.
  - **„Gleich“:** Beide Seeds liefern ein \boxed{}, und die Antworten sind gleichwertig (math_verify in beide Richtungen, wie
    03_eval).
  - **Signal:** Δ = P(Seed 0 richtig | gleich) − P(Seed 0 richtig | verschieden).
    - „trägt“, wenn Δ ≥ 30 Prozentpunkte UND P(richtig | gleich) ≥ 70 %;
    - „widerlegt“, wenn Δ ≤ 15 Prozentpunkte;
    - sonst „offen“.
  - **Weiche (zweitrangig):** gleich → INT-Antwort abgeben, sonst Hinterzimmer = WT-A Seed 0 auf derselben Aufgabe.
    - „lohnt“, wenn die Weiche ≥ max(INT Seed 0 allein, WT-A allein) + 3 richtig liefert;
    - „lohnt nicht“, wenn ≤ max(…);
    - sonst „offen“.
  - **Beschreibend:**
    - Weiche mit MIT und ERGORE als Hinterzimmer;
    - Tokens;
    - gedeckelte „schnelle Intuition“: eine INT-Antwort zählt nur, wenn sie innerhalb von 2.000 / 4.000 Tokens fertig ist. Das ist
      aus den ungedeckelten Läufen exakt nachrechenbar, weil derselbe Seed bis zum Deckel denselben Text liefert.
  **(N21) Vorderzimmer-Sonde (103_vorderzimmer_sonde.py).**
  - **Stelle:** letztes Token des letzten \boxed{…} in Texten aus dem Antwortmodus (wie 89 Teil A).
  - **Zustand:** Ausgang der Schichten 4, 6, 8, 10, 11, 12, 13, 14. Bis dorthin sind alle unsere Modelle bei gleichem Text
    identisch (Edits ab Schicht 15). Gelesen wird mit eigen, gierig, ohne Generierung.
  - **Training:** INT-Texte (eigen ohne Denken) auf Set B (setB60-ohne-eigen-t06, setB20-p0-eigen-antwort) und 1–160
    (m500-001-080 / 081-160-ohne-eigen-t06).
    - Etikett: Die abgegebene Antwort ist richtig.
    - Läufe ohne \boxed{} fallen heraus.
  - **Modellwahl nur im Training:**
    - Kreuzvalidierung 5-fach, gruppiert nach Aufgabe;
    - gewählt werden Schicht und L2-Stärke;
    - logistische Regression auf standardisierten Zuständen;
    - danach eingefroren.
  - **Test, einmal:** INT Seed 0 auf 161–300 (Hauptauswertung).
  - **Beschreibend:**
    - MIT-im-Vorderzimmer-Texte 161–300;
    - INT Seed 1;
    - nur schnelle Läufe (≤ 2.000 Tokens);
    - zum Vergleich die eingefrorene Hinterzimmer-Sonde an denselben Stellen (int_sonde.jsonl).
  - **Grundlinie:** logistische Regression auf log(Tokens) + Stufe, gleiche Trainingsdaten. Kombiniert: Grundlinie +
    Sonden-Wert.
  - **Lesart:**
    - „Vorderzimmer-Sonde trägt“, wenn Test-AUC ≥ 0,70 UND AUC(kombiniert) − AUC(Grundlinie) ≥ +0,05;
    - „selbstsichere Fehler bestätigt“ (an der Abgabe keine lineare Wahrheits-Information), wenn Test-AUC ≤ 0,60;
    - sonst „offen“.
  - **Einordnung vorab:**
    - Trägt sie, wäre das der Baustein für eine Zimmer-Weiche von innen („unsicher → Hinterzimmer“).
    - Trägt sie nicht, bleibt die Zweifach-Intuition (N20) als Prüfung ohne Schubs.
    - Bei rund 240 Trainingsläufen ist N21 ein Vortest. Später lässt er sich mit Etiketten aus der Zweifach-Intuition stark
      vergrößern (keine Lösungen nötig; Kossen et al. 2024).
- 08.11. 13:20 – **(N19) Replay der stummen WT-A-Antwortteile: widerlegt (a), kein Sperr-Effekt (b).**

  | 32 stumme Läufe | \boxed{} | richtig | Ende eos | weiteres </think> |
  |---|---|---|---|---|
  | Arm A (Sperre) | 1 | 1 | 1 | 0 |
  | Kontrolle K | 0 | 0 | 0 | 3 |

  - (a) Argons Kriterium: 1 von 14 gerettet (< 7) → **widerlegt**. (b) A − K = +1 → **kein Sperr-Effekt**. WT-A hochgerechnet
    62/140.
  - Fast alle neuen Antwortteile laufen bis zum Deckel von 1.024 Tokens weiter, ohne abzugeben. Auch ohne die Tür „</think>“
    denkt das Modell nach dem Reflex-Abschluss im Antwortteil einfach weiter.
  - Deutung, Argons eigene Widerlegungs-Klausel: Der Fehler liegt schon vor dem ersten </think>. Der Reflex schließt, bevor
    das Modell innen „fertig“ ist. Die Abgabe-Hygiene im Antwortteil rettet nichts.
  - Das passt zur Wirktiefe (N12): Ein erzwungener Abschluss ist kein innerer Abschluss.
  - Grenze: Der Deckel von 1.024 Tokens (Argons Vorgabe) zählt keine Rettung, die länger braucht.
- 08.11. 13:25 – **Nutzer-Go „Ja, so oder so bitte für den MiniPC ab ca. 14:10“ und Frage „Wo haben wir unseren
  Schilder-Testversuch mit dabei?“. Zwei Lesarten vorab, bevor ein Lauf existiert.**
  **(N22) Zweifach-Intuition auf neuen Aufgaben (Wiederholung von N20) und mehr Training für die Vorderzimmer-Sonde.**
  - **Aufgaben:** 40 MATH-Trainingsaufgaben, die in keinem Lauf und keiner Teilmenge vorkommen.
    - Je 8 pro Stufe, fester Zufalls-Seed 20261108.
    - Datei: daten/practice/math_train_neu40.jsonl.
  - **Läufe:** INT (eigen ohne Denken, 03b) mit Seed 0 und Seed 1. MiniPC, 12 Slots, nach dem Seed-1-Block 211–260.
  - **Lesart wie N20:** „trägt“, wenn Δ ≥ 30 Prozentpunkte UND P(richtig | gleich) ≥ 70 %; „widerlegt“, wenn Δ ≤ 15
    Prozentpunkte; sonst „offen“.
    - Bei n = 40 nur eine grobe Wiederholung.
  - **Beschreibend:**
    - Die 80 Abgaben erweitern das Sonden-Training um etwa ein Drittel (240 → 320).
    - Eine zweite Sonden-Fassung damit (N21b) wird nach dem eingefrorenen N21-Test nur beschreibend berichtet. Es wäre der zweite
      Blick auf dieselbe Testmenge.
  **(N23) Schild-Replay: Liefert das Modell ab, wenn die Tür an seinem EIGENEN Schild schließt?** (105_schild_replay.py)
  - **Anlass:**
    - Die Schild-Reflex-Simulation (N18) nahm an, dass die Abgabe immer gelingt.
    - Das Replay (N19) zeigt: Nach WT-As Reflex-Abschlüssen gelingt sie fast nie (1 von 32 mit \boxed{}).
    - Offen ist, ob das an der Stelle liegt. Das Bild des Nutzers dazu: Das Schild hängt der Bewohner selbst auf.
  - **Quelle:** WT-A-Denktexte 161–300 (Seed 0), Wert-Aussagen und Wahrheits-Tor aus der Zuck-Messung (82). Nur Stellen vor dem
    ersten </think>.
  - **Stellen je Lauf:**
    - S = erste Wert-Aussage höchstens 15 Tokens nach einem eigenen Schild (Muster wie 100);
    - N = Kontrolle: die Wert-Aussage ohne Schild in den 15 Tokens davor, die S zeitlich am nächsten liegt (gleicher Lauf);
    - F = die Stelle, an der der simulierte Schild-Reflex (N18, τ 1) feuern würde, falls sie nicht S ist (beschreibend).
  - **Eingriff:**
    - Schnitt nach dem letzten Token des Werts;
    - dann das Token </think> eingesetzt, wie es ein Reflex täte;
    - dann neu generiert, höchstens 1.024 Tokens, WT-A-GGUF, Protokoll der Läufe, Seed 0, Laptop.
  - **Begriffe:** „Abgabe“ = \boxed{} im neuen Antwortteil. „Sauber“ heißt zusätzlich: Ende mit eos.
  - **Lesart (gepaart über die Läufe mit S und N):**
    - „Schild-Abschluss liefert ab“, wenn die Abgabe-Rate bei S ≥ 50 % liegt UND mindestens 20 Prozentpunkte über N;
    - „widerlegt“, wenn sie bei S ≤ 20 % liegt ODER höchstens 5 Prozentpunkte über N;
    - sonst „offen“.
  - **Beschreibend:**
    - richtig unter den Abgaben (S mit richtigem gegen falschen Wert);
    - weiteres </think>;
    - N18 neu gerechnet mit der echten Abgabe an F statt der Annahme „Abgabe gelingt immer“.
- 08.11. 13:29 – **Ergänzung zu N23, vorab (vor jedem Lauf):**
  - WT-A hat nur in **19 von 140** Läufen einen Wert direkt hinter einem eigenen Schild (strenges Muster wie 100). Die Lesart
    N23 gilt unverändert für diese 19 Paare; bei dieser Größe ist sie nur ein grober Hinweis.
  - **Beschreibend** kommen MITs Denktexte (161–300) dazu: gleiche Stellen-Regeln, MIT-GGUF.
    - 74 Läufe mit S und N, 18 zusätzliche Feuerstellen F (Tor zT aus der Zuck-Messung auf MIT-Texten).
    - Dieselben Schwellen werden beschreibend angelegt, aber nicht als Urteil gewertet.
  - Reihenfolge Laptop: Sonde sammeln → Schild-Replay WT-A → MIT → Zweifach-Intuition 161–210.
- 08.11. 13:37 – **(N13) MIT im Vorderzimmer: „Das Hinterzimmer lohnt sich bei MIT“.** MIT ohne Denken **59/140** gegen MIT mit Denken
  **80/140**: nur ohne Denken 6, nur mit Denken 27, McNemar p = 0,0003.
  - Je Block: 26:30 | 20:28 | 13:22.
  - Meine Prognose (72 ± 7) lag deutlich zu hoch.
  - **Beschreibend:**
    - MITs Vorderzimmer ist schwächer als unser eigenes (INT 71; 14 gegen 26 Aufgaben, p = 0,08) und etwa gleich WT-A mit
      Denken (61).
    - Tokens je richtiger Antwort: 16.433 gegen 37.670 (MIT mit Denken).
    - Landkarte: MIT verliert ohne Denken vor allem auf Stufe 3–4 (14:21, 11:22) und in Algebra/Präalgebra/Zahlentheorie.
    - Obergrenze einer perfekten Zimmer-Wahl MIT ohne/mit Denken: 86.
  - **Lesart für das Hausbild:**
    - Ein Hinterzimmer lohnt sich, wenn es einen funktionierenden Ausgang hat (MIT).
    - Unseren Modellen fehlt dieser Ausgang. Ihr bester Weg bleibt das Vorderzimmer.
    - Der Umkehr-Edit (eigen) stärkt das Vorderzimmer, MITs Edit tut das nicht.
    - Das stützt die gekoppelte Kette des Nutzers (Vorderzimmer zuerst, geordneter Wechsel nur bei Unsicherheit, Hinterzimmer mit
      Ausgang).
- 08.11. 13:59 – **(N21) Vorderzimmer-Sonde: „offen“, knapp. Beschreibend bei schnellen Läufen deutlich besser als alles bisher.**
  - Training: 239 Abgaben (Set B + 1–160). Kreuzvalidierung wählt Schicht 13, λ 100 (CV-AUC 0,805). Danach eingefroren und einmal
    getestet.
  - **Test INT Seed 0, 161–300 (n 140):**
    - Sonde AUC **0,763**;
    - Grundlinie (log Tokens + Stufe) 0,723;
    - kombiniert 0,763, also Zuwachs +0,041.
    - Lesart: AUC ≥ 0,70 erfüllt, Zuwachs ≥ +0,05 knapp verfehlt → **offen**.
  - Die eingefrorene Hinterzimmer-Sonde an denselben Stellen: AUC 0,681.
  - **Beschreibend, nachträglich gewählte Teilmengen:**

    | Teilmenge | n (richtig) | neue Sonde | Grundlinie | alte Hinterzimmer-Sonde |
    |---|---|---|---|---|
    | ≤ 2.000 Tokens | 57 (38) | **0,794** | 0,629 | 0,627 |
    | ≤ 1.000 Tokens | 43 (28) | 0,786 | 0,669 | 0,636 |
    | > 2.000 Tokens | 83 (33) | 0,728 | 0,692 | 0,616 |

    - Bei schnellen Läufen, also der Intuition, wo Länge kaum etwas verrät, liest die neue Sonde Wahrheit:
      - Schnelle Abgaben mit Sonden-Wert über dem Median: 29, davon 26 richtig (90 %).
      - Über dem 70. Perzentil: 17, davon 16 richtig (94 %).
      - Grundrate der schnellen: 67 %.
    - Meine frühere Aussage „Fehler im Vorderzimmer sind selbstsicher (AUC ≈ 0,5)“ galt nur für die Hinterzimmer-Sonde. Die
      Information ist da; die alte Sonde hörte nur auf das falsche Merkmal.
  - Nur ein Vortest, n klein, Teilmengen nachträglich. Eine vorab festgelegte Prüfung auf frischen Daten steht aus (N22-Läufe,
    INT Seed 1).
- 08.11. 14:00 – **(N24) Bestätigung der eingefrorenen Vorderzimmer-Sonde auf frischen Aufgaben. Lesart vorab, bevor die Läufe
  existieren.** Die neu40-Läufe gehen damit zuerst in diese Prüfung, nicht ins Training (N21b erst danach).
  - **Sonde:** N21 eingefroren (Schicht 13, λ 100, Standardisierung aus dem Training).
  - **Grundlinie:** log Tokens + Stufe, ebenfalls eingefroren aus dem Training.
  - **Daten:** INT-Abgaben der 40 neuen MATH-Trainingsaufgaben, Seed 0 und 1 (bis zu 80; Aufgaben nie gesehen). Die Zustände
    werden nach Ende der Laptop-Kette auf der GPU gesammelt.
  - **Lesart:**
    - „bestätigt“, wenn AUC (alle) ≥ 0,70 UND AUC (schnelle, ≤ 2.000 Tokens) ≥ 0,70 UND beide mindestens +0,05 über der
      Grundlinie auf derselben Menge;
    - „widerlegt“, wenn AUC (alle) ≤ 0,60;
    - sonst „offen“.
  - **Beschreibend:** INT Seed 1 auf 161–260 (neue Texte, bekannte Aufgaben); Präzision bei Freigabe über dem Trainings-Median
    der Sonde.
- 08.11. 14:07 – **Nachtrag zu N21, beschreibend.** Dieselbe eingefrorene Sonde, ohne erneute Wahl, ergibt dasselbe Urteil:
  - auf MITs Vorderzimmer-Texten 161–300 (n 138, 59 richtig): AUC **0,776**;
  - auf INT Seed 1, 261–300 (n 40, 16 richtig): AUC **0,836**.
  - Die Sonde überträgt sich also auf ein anderes Modell im Vorderzimmer und auf neue Stichproben.
- 08.11. 14:14 – **(N23) Schild-Replay WT-A: formal „widerlegt“ (Deckel 1.024). Dazu eine Korrektur, die auch N19 betrifft.**
  - **Ergebnis:**
    - S (am eigenen Schild) 0/19 Abgaben; N (ohne Schild) 0/19.
    - F (Schild + Wahrheits-Tor) 2/9, beide richtig.
    - N18 mit echter Abgabe: 56 statt 61 richtig.
  - **Korrektur (wichtig): Der Deckel von 1.024 Tokens ist für WT-A zu kurz.**
    - Bei WT-As **richtigen** Läufen ist der natürliche Antwortteil nach dem ersten </think> im Median **1.989 Tokens** lang (75 %:
      3.148).
    - Nur **18 %** passen unter 1.024, 52 % unter 2.048, 85 % unter 4.096.
    - Zum Vergleich: MIT Median 631 (76 % ≤ 1.024), ERGORE 617 (60 %).
    - Stichproben der neuen Antwortteile zeigen dasselbe: WT-A rechnet im Antwortteil die Aufgabe noch einmal sichtbar durch („To
      find …“, „One last check …“) und wird vom Deckel abgeschnitten.
  - **Folgen:**
    - Die Urteile N19 und N23 bleiben formal so stehen, wie sie vorab festgelegt waren.
    - **Meine Deutung zu N19 („Der Fehler liegt schon vor dem ersten </think>“) nehme ich zurück. Sie ist durch diesen Test nicht
      gedeckt.**
    - Gezeigt ist nur: Innerhalb von 1.024 Tokens gibt WT-A nach einem eingesetzten </think> fast nie ab. Das gilt aber auch für
      die meisten seiner natürlichen, erfolgreichen Abgaben.
    - Der Fehler lag bei mir: Ich habe Argons Deckel übernommen, ohne ihn an WT-As Antwortlängen zu prüfen.
- 08.11. 14:14 – **(N25) Nachtest mit fairem Deckel, Lesart vorab, bevor ein Lauf existiert.**
  - **Gleiche Stellen und Arme wie N19 und N23 (WT-A),** aber höchstens **4.096** Tokens im neuen Antwortteil. Das deckt 85 % der
    natürlichen richtigen WT-A-Antwortteile ab.
  - **Technik:**
    - Laptop, WT-A-GGUF, Kontext je Slot 38.912 (Präfix bis 33.434 + 4.096).
    - Sonst gleiches Protokoll, Seed 0.
    - Läuft nach Ende der Laptop-Kette (h, i).
  - **Lesarten unverändert:**
    - N19 (a): ≥ 10 von 14 gerettet = bestätigt, < 7 = widerlegt;
    - N19 (b): A − K ≥ +3 = Sperre trägt, ≤ +1 = kein Effekt;
    - N23: S ≥ 50 % Abgaben UND ≥ +20 Punkte über N = liefert ab; S ≤ 20 % ODER ≤ +5 Punkte = widerlegt.
  - **Zusätzliche Vergleichsgröße:** Natürliche richtige WT-A-Abgaben passen zu 85 % unter 4.096. Abgabe-Raten deutlich darunter
    sprechen also wirklich gegen den Eingriff, nicht gegen den Deckel.
  - Die MIT-Ergänzung von N23 behält 1.024 (MIT-Antwortteile sind kurz, 76 % ≤ 1.024).
- 08.11. 14:25 – **N23-Ergänzung MIT (beschreibend; Deckel 1.024, für MIT fair): Am eigenen Schild gibt MIT doppelt so oft ab.**

  | MIT, 74 Läufe | Abgaben | richtig | weiteres </think> |
  |---|---|---|---|
  | S am eigenen Schild | 27 (36 %) | 26 | 0 |
  | N ohne Schild | 13 (18 %) | 13 | 8 |
  | F Schild + Tor (18) | 4 (22 %) | 4 | 1 |

  - Gepaart: nur S 17, nur N 3 (McNemar zweiseitig p ≈ 0,003). Die Schwellen der Lesart (≥ 50 % und ≥ +20 Punkte) sind nicht
    erreicht → beschreibend „offen“.
  - Am Schild mit richtigem Wert: 19/36 abgegeben, alle 19 richtig.
  - Bemerkenswert: Abgaben nach einem Schnitt an einem *falschen* Wert sind trotzdem fast immer richtig (S 7/8, N 10/10). MIT
    rechnet im Antwortteil neu und korrigiert sich.
  - N18 mit echter Abgabe bei MIT: 58 statt 80 richtig. Ein von außen gesetzter Schnitt schadet MIT, auch am Schild.
  - **Deutung (vorsichtig):**
    - Das eigene Schild markiert bessere Abschluss-Momente (doppelte Abgabe-Rate).
    - Ein eingesetztes </think> ersetzt aber auch dort kein inneres „fertig“: Zwei Drittel geben innerhalb von 1.024 Tokens
      nicht ab.
- 08.11. 14:49 – **(N20) Zweifach-Intuition: Signal „trägt“, Weiche zu WT-A „lohnt nicht“.** Hauptauswertung 161–260, 100 Aufgaben,
  hier vorher nicht gesehen.
  - **Signal:**
    - Gleiche Antwort in beiden Seeds: **38 Aufgaben, davon 37 richtig (97 %)**.
    - Verschieden: 62 Aufgaben, Seed 0 richtig 32 %.
    - Δ = **+65 Punkte** → **trägt** (Kriterien: Δ ≥ 30 und ≥ 70 %).
  - **Weiche** (gleich → INT, sonst WT-A mit Denken): 54 richtig, gegen INT allein 57 und WT-A allein 44 → **lohnt nicht**.
    WT-As Hinterzimmer ist als Rückfall zu schwach.
  - **Beschreibend:**
    - Weiche zu MIT: **63** (INT allein 57, MIT allein 58), aber mit 3,2 statt 2,1 Mio. Tokens.
    - Weiche zu ERGORE: 57.
    - Mit gedeckelter schneller Intuition (≤ 2.000 / 4.000 Tokens) sind alle 18 bzw. 24 gleichen Antworten richtig (100 %). Die
      Weiche bringt dann aber keinen Gewinn mehr (MIT 58–59).
    - Zusammen mit 261–300 (schon gesehen): Bei 50 von 140 Aufgaben sind sich zwei Intuitionen einig, davon 47 richtig (94 %).
  - **Deutung:**
    - Die Einigkeit zweier Intuitionen ist ein sehr starkes Sicherheits-Signal des Vorderzimmers.
    - Ein Zimmerwechsel lohnt sich nur, wenn das Hinterzimmer einen funktionierenden Ausgang hat (wie N13: MIT ja, WT-A nein).
    - Für die gekoppelte Kette des Nutzers fehlt also ein Hinterzimmer mit Ausgang für unsere Modelle. Bis dahin bleibt INT allein
      der beste eigene Weg.
- 08.11. 15:02 – **Nutzer: „A und B ja. Dann würde ich nochmal einen ‚halben Test‘ machen mit frischen MATH-Aufgaben. Dann C,
  die wichtigsten Daten ein-/nacharbeiten, max. 30 Min. Dann D.“ (N26) Halber Test, Lesart vorab, bevor ein Lauf existiert.**
  - **Aufgaben:** MATH-500 **301–370** (70 Aufgaben).
    - In keinem Lauf benutzt (geprüft).
    - Stufen 1–5: 3 / 15 / 14 / 21 / 17.
    - „Halb“ heißt: halb so groß wie der Schritt-3-Test (140).
  - **Läufe:** INT (eigen ohne Denken, 03b), Seed 0 und Seed 1, gleiches Protokoll (T 0,6, 32k, vLLM-Stil).
    - Laptop 301–345 (zwei Server). Dazwischen werden auf der GPU die Zustände für N24 gesammelt.
    - MiniPC 346–370 (Seed 0 ‖ Seed 1).
    - Danach die Sonden-Zustände der 140 Abgaben (GPU).
    - Kein Hinterzimmer-Lauf: Der wäre stundenlang und wird erst besprochen.
  - **Lesarten:**
    - **(a) Zweifach-Intuition wie N20:** „trägt“, wenn Δ ≥ 30 Punkte UND P(richtig | gleich) ≥ 70 %; „widerlegt“, wenn Δ ≤ 15
      Punkte.
    - **(b) Vorderzimmer-Sonde, eingefroren (N21), wie N24** auf allen Abgaben beider Seeds:
      - „bestätigt“, wenn AUC ≥ 0,70 UND AUC (≤ 2.000 Tokens) ≥ 0,70 UND beide ≥ +0,05 über der eingefrorenen Grundlinie
        (log Tokens + Stufe);
      - „widerlegt“, wenn AUC ≤ 0,60.
    - **(c) Gekoppelte Vorderzimmer-Regel, eingefroren:**
      - Abgeben, wenn beide Seeds dieselbe Antwort geben ODER (Seed 0 ≤ 2.000 Tokens UND Sonden-Wert von Seed 0 ≥ **0,0524**,
        dem Trainings-Median).
      - Sonst „weiß ich nicht“ (Pausenraum).
      - Maß S₂ = (richtig − 2 · falsch) / n.
      - Vergleich mit der eingefrorenen Längen-Regel „abgeben, wenn Seed 0 ≤ 2.000 Tokens“.
      - „Kette trägt“, wenn S₂(Kette) ≥ S₂(Längen-Regel) + 0,05 UND mindestens 80 % der Abgaben richtig sind;
      - „trägt nicht“, wenn S₂(Kette) ≤ S₂(Längen-Regel);
      - sonst „offen“.
  - **Beschreibend:**
    - INT-Trefferzahl je Seed;
    - Tokens;
    - Abgabe-Quote der Kette;
    - die Kette mit Einigkeit allein und mit Sonde allein.
- 08.11. 15:03 – **Ergänzung zu N26, vorab, noch kein Lauf:** Die Aufteilung wird an die Gerätegeschwindigkeit angepasst: Laptop 301–355,
  MiniPC 356–370. Aufgaben, Seeds und Lesarten bleiben unverändert.
- 08.11. 15:19 – **(N25) Fairer Nachtest mit Deckel 4.096.**
  - **Replay der 32 stummen WT-A-Antwortteile:**
    - Arm A (Sperre): 0 von 14 gerettet. Kontrolle K: 2 von 14 (beide sauber).
    - Urteile wie vorab: (a) **widerlegt**, (b) A − K = −2 → **kein Sperr-Effekt**.
    - Auch mit genug Platz (85 % der natürlichen richtigen Antwortteile passen unter 4.096) liefert der Antwortteil dieser Läufe
      fast nie ab: 2 von 32.
    - Die Deutung von 13:20 („Der Reflex schließt, bevor das Modell innen fertig ist“) ist damit wieder gestützt. Die Rücknahme
      von 14:15 galt dem zu kurzen Deckel, nicht der Deutung selbst. Einschränkung: Es sind ausgewählte Fehlschläge, die
      Schwierigkeit lässt sich nicht trennen.
    - Bemerkenswert: Die 2 Rettungen in K kamen in Läufen, die ihr Weiterdenken selbst mit einem eigenen zweiten </think>
      schlossen. Die Sperre nimmt dem Modell genau diesen eigenen Abschluss.
  - **Schild-Replay WT-A (19 Paare):**
    - S 6/19 (32 %) gegen N 4/19 (21 %), gepaart 3 : 1 → **offen**.
    - F (eigenes Schild + Wahrheits-Tor): **5 von 9 abgegeben, alle 5 richtig**.
    - N18 mit echter Abgabe: 59 statt 61, S₂ gleich (+0,293).
  - **Deutung:** Schild und Wahrheit zusammen markieren bei WT-A die Momente, in denen ein Abschluss trägt (5 von 9, alle
    richtig). Über alle Läufe gewinnt der Reflex aber nichts, weil er auch Läufe abbricht, die später selbst richtig abgegeben
    hätten. Das innere „fertig“ (eigenes </think>) bleibt der Schlüssel.
- 08.11. 15:32 – **(N27) D: dritte Intuition (Nutzer-Reihenfolge „… dann D“). Lesart vorab, bevor ein Lauf existiert.**
  - **Läufe:** INT (eigen ohne Denken) mit **Seed 2** auf MATH-500 161–260, sonst gleiches Protokoll.
    - Laptop 161–195 ‖ 196–230;
    - MiniPC 231–260;
    - jeweils nach dem halben Test.
  - **Regel „Mehrheit aus drei“:** abgeben, wenn mindestens zwei der drei Seeds (0, 1, 2) gleichwertige Antworten geben, sonst
    „weiß ich nicht“.
  - **Vergleich:** „Einigkeit aus zwei“ (Seeds 0/1, N20) gab 38 von 100 ab, 37 richtig.
  - **Lesart:**
    - „Mehrheit trägt“, wenn sie ≥ 48 Aufgaben abgibt (≥ +10) UND ≥ 90 % davon richtig sind;
    - „trägt nicht“, wenn < 85 % richtig sind ODER < 43 abgegeben werden (< +5);
    - sonst „offen“.
  - **Beschreibend:**
    - Einstimmigkeit aus drei;
    - die Einigkeit der anderen Seed-Paare (0/2, 1/2) als Wiederholung von N20;
    - Weiche mit MIT bzw. WT-A als Rückfall;
    - Tokens.
- 08.11. 15:40 – **Vorab-Ergänzungen nach WRENs „V-PRE“ (Feedback 15:38). Festgelegt, bevor Daten existieren:** Es gibt noch
  keine Zustände für N24/N26 und keinen Seed-1-Lauf auf 301–370.
  - **N24 und N26 (b), zweite Lesart, längen-geschichtet:**
    - „schnell bestätigt“, wenn die eingefrorene Sonde auf Abgaben ≤ 2.000 Tokens AUC ≥ 0,75 erreicht UND mindestens +0,10 über
      der eingefrorenen Grundlinie (log Tokens + Stufe) auf derselben Teilmenge liegt;
    - „schnell widerlegt“, wenn AUC (≤ 2.000) ≤ 0,65;
    - sonst „offen“.
    - Die Hauptlesart bleibt unverändert.
  - **N26 (c), Zerlegung vorab:**
    - Die gekoppelte Regel wird getrennt für die Einigkeits-Teilmenge und für den Rest berichtet.
    - Jeweils gegen INT Seed 0 allein auf derselben Teilmenge.
    - Dazu die Token-Bilanz.
  - **(N28) Gekoppelte Regel mit Hinterzimmer, bedingt.** Gilt nur, falls MIT mit Denken auf 301–370 nachgerechnet wird. Das ist
    noch nicht entschieden: etwa 1 h Rechenzeit, Nutzer fragen.
    - Regel: abgeben, wenn Seed 0 = Seed 1 (INT); sonst MIT mit Denken.
    - „hält“, wenn (i) Gesamt ≥ MIT allein UND (ii) Präzision der Einigkeits-Abgaben ≥ 90 % UND (iii) Tokens je richtiger Antwort
      < MIT allein;
    - „widerlegt“, wenn (i) oder (ii) verfehlt.
    - Zerlegung wie oben, Einigkeits-Teilmenge und Rest getrennt gegen jedes Modell allein.
  - **N27, zweite Lesart:** Die Mehrheit aus drei muss zusätzlich beim Maß S₂ = (richtig − 2 · falsch)/100 (sonst „weiß ich
    nicht“) mindestens so gut sein wie die Einigkeit aus zwei.
- 08.11. 15:42 – **Drei Null-Kosten-Prüfungen zu WREN/Argon (NACHTRÄGLICH, beschreibend, 161–300). Darunter eine Korrektur meiner
  Korrektur.**
  - **(a) Weiteres </think> im Antwortteil, alle Läufe mit Abschluss:**
    - WT-A **79/103 (77 %)**, bei den *richtigen* WT-A-Läufen **58/61**;
    - MIT **19/118 (16 %)**, bei den richtigen 9/80.
    - **Korrektur:** Meine Aussage „83–100 % gilt auf frischen Daten nicht (12/32 = 38 %)“ bezog sich nur auf die 32 stummen Läufe,
      also die falsche Teilmenge. Über alle Abschlüsse bestätigt sich Argons Größenordnung auch auf frischen Daten.
    - **Neu:** WT-As *erfolgreicher* Weg ist fast immer „Reflex-Abschluss → im Antwortteil weiterdenken → eigenes zweites </think>
      → abgeben“. Das erklärt die langen Antwortteile (Median 1.989). Es erklärt auch, warum die Sperre des zweiten </think> im
      Replay nichts rettet (0 gegen 2).
  - **(b) Zerlegung der gekoppelten Regel** (einig → INT, sonst MIT):
    - Einigkeits-Teilmenge (50): INT 47, MIT 43. Rest (90): MIT 37, INT 24.
    - Regel 84 gegen MIT 80. Der Gewinn stammt ganz aus der Einigkeits-Teilmenge: Die Regel ist ein Selektor, kein Verstärker
      (WRENs Unterscheidung).
    - **Tokens je richtiger Antwort: Regel 53.990 gegen MIT allein 37.670.** Zwei volle INT-Läufe kosten mehr, als die Regel spart.
      WRENs Kriterium (iii) für N28 wäre auf 161–300 verfehlt.
  - **(c) Argons These „MITs Schluss-Anteil drückt im Vorderzimmer zu früh aufs Turn-Ende“:**
    - Auf den 26 Aufgaben, die INT löst und MIT im Vorderzimmer nicht, sind MITs Läufe nicht kürzer (Median 3.190 gegen 2.904).
      Alle geben ein \boxed{} ab.
    - Über alle 140 ist MITs Vorderzimmer kürzer (2.300 gegen 3.912).
    - Für die verlorenen Aufgaben ist die These also nicht gestützt.
  - Argons p-Angabe für N20 nachgerechnet: Fisher einseitig p = 9,3 · 10⁻¹².
- 08.11. 15:43 – **Nutzer-Go „Ja, nach D“: N28 wird gerechnet.**
  - MIT mit Denken (Protokoll wie s3-mit, 03_eval, vLLM-Stil, Seed 0) auf MATH-500 301–370.
  - Aufteilung: Laptop 301–328 ‖ 329–355, MiniPC 356–370, jeweils nach D.
  - Lesart unverändert wie 15:40.
- 08.11. 15:59 – **(N22) Zweifach-Intuition auf 40 neuen MATH-Trainingsaufgaben: Signal „trägt“, aber mit geringerer Präzision.**
  - Gleiche Antwort: 17 Aufgaben, davon 13 richtig (**76 %**). Verschieden: 23, Seed 0 richtig 13 %. Δ = +63 Punkte → trägt
    (Kriterien Δ ≥ 30 und ≥ 70 % erfüllt).
  - Grundrate Seed 0: 16/40.
  - Gedeckelt: ≤ 4.000 Tokens 81 % (16 gleich), ≤ 2.000 Tokens 87 % (15 gleich).
  - Einordnung: Die Trennung wiederholt sich. Die Präzision bei Einigkeit liegt mit 76 % aber deutlich unter den 97 % von N20
    (n = 17, breite Unsicherheit). Die 97 % sind eher die obere Schätzung.
- 08.11. 15:59 – **(N24) Vorderzimmer-Sonde auf 40 neuen Aufgaben (79 Abgaben, 34 richtig): „offen“. Zweite Lesart (längen-geschichtet):
  „offen“.**

  | Menge | Sonde | Grundlinie (log Tokens + Stufe) | Zuwachs |
  |---|---|---|---|
  | alle 79 | **0,852** | 0,841 | +0,012 |
  | schnell ≤ 2.000 (43, 29 richtig) | **0,823** | 0,736 | +0,086 |

  - Hauptlesart: Beide AUC ≥ 0,70, aber der Zuwachs über alle (+0,012) verfehlt +0,05 → **offen**.
  - Zweite Lesart: 0,823 ≥ 0,75, aber +0,086 < +0,10 → **offen**.
  - Freigabe über dem Trainings-Median: 33 Abgaben, 25 richtig (76 %; Grundrate 43 %).
  - **Einordnung:** Die Sonde liest Richtigkeit auch auf neuen Aufgaben gut (0,85). Länge und Stufe allein wissen auf diesen
    Aufgaben aber fast genauso viel. Den Mehrwert gibt es nur bei schnellen Antworten, und er ist kleiner als die nachträglichen
    +0,165 auf 161–300 (jetzt +0,086).
- 08.11. 16:03 – **Nutzer: „Sollten wir trotzdem nicht verwerfen. Sofern sie sicheren Mehrwert gibt und keine Nachteile – messbar.“ (N29)
  Mehrwert-ohne-Nachteil-Test der Vorderzimmer-Sonde auf 301–370. Lesart vorab: Es gibt noch keine Sonden-Zustände für 301–370,
  und Seed 1 läuft noch.**
  - **(a) Sonde als Schiedsrichter (Mehrwert, den Länge und Stufe nicht liefern können):**
    - Wo die zwei Intuitionen uneinig sind und beide ein \boxed{} geben, wird die Antwort mit dem höheren Sonden-Wert genommen.
    - Vergleiche: immer Seed 0; die kürzere Antwort (Längen-Schiedsrichter).
    - „Mehrwert“, wenn die Sonde ≥ 3 mehr richtige liefert als Seed 0 UND ≥ 2 mehr als der Längen-Schiedsrichter;
    - „kein Mehrwert“, wenn sie nicht mehr richtige liefert als Seed 0;
    - sonst „offen“.
    - Die Einigkeits-Aufgaben berührt der Schiedsrichter nicht. Dort ist ein Nachteil also ausgeschlossen.
  - **(b) Kein Nachteil in der Kette:**
    - „kein Nachteil“, wenn S₂(Einigkeit ODER Sonde) ≥ S₂(Einigkeit allein). Jede zusätzliche falsche Abgabe kostet 2, also müssen
      die zusätzlichen Sonden-Abgaben zu mindestens 2/3 richtig sein.
    - „Nachteil“, wenn S₂ sinkt.
  - **Beschreibend:**
    - Schiedsrichter + Kette zusammen (einig → abgeben; uneinig → Sonden-Wahl, wenn ihr Wert ≥ Median, sonst „weiß ich nicht“);
    - gleiche Auswertung auf 161–300, sobald die Seed-1-Zustände dort gesammelt sind.
- 08.11. 16:44 – **(N26) Halber Test auf unberührten Aufgaben MATH-500 301–370 (70 Aufgaben).** INT Seed 0: 35 richtig, Seed 1: 39.
  - **(a) Zweifach-Intuition: trägt.** Gleich 31 Aufgaben, **28 richtig (90 %)**. Verschieden 39, Seed 0 richtig 18 %. Δ = +72
    Punkte.
    - Über N20, N22 und N26 zusammen: 78 von 86 einigen Antworten richtig (91 %).
  - **(b) Eingefrorene Sonde, 138 Abgaben:**
    - alle: AUC 0,765 gegen Grundlinie 0,717, Zuwachs **+0,048** (gefordert +0,05) → **offen**;
    - schnelle (≤ 2.000, n 63): 0,606 gegen 0,599 → zweite Lesart **„schnell widerlegt“** (≤ 0,65).
    - Der Vorsprung bei schnellen Antworten aus 161–300 (nachträglich) und neu40 (+0,086) wiederholt sich hier **nicht**.
  - **(c) Kette gegen Länge:**
    - Kette S₂ +0,129 gegen Länge +0,086 (Zuwachs +0,043 < 0,05), Präzision 74 % (< 80 %) → **offen**.
    - Beschreibend die beste Regel: **Einigkeit allein**, 31 abgegeben, 90 % richtig, S₂ +0,314.
- 08.11. 16:44 – **(N29) Mehrwert ohne Nachteil:**
  - **(a) Sonde als Schiedsrichter: „Mehrwert“.**
    - 37 uneinige Aufgaben mit zwei Antworten, bei 18 davon ist eine der beiden richtig.
    - Sonde wählt **11** richtig, Seed 0 hat 7, die kürzere Antwort 7.
  - **(b) Sonde als zusätzliches Abgabe-Tor: „Nachteil“.** S₂ der Kette +0,129 gegen Einigkeit allein +0,314. Die 11 zusätzlichen
    Abgaben sind nur zu 3/11 richtig.
  - Beschreibend „immer antworten“ (einig → diese Antwort, sonst Schiedsrichter):
    - Sonde 39/70, Seed 0 35, kürzer 35;
    - Seed 1 allein 39, Mittel einzelner Läufe 37, Obergrenze 46.
  - **Folgerung für den Bau:** Die Sonde nicht als Freigabe nutzen, sondern als **Schiedsrichter zwischen zwei Intuitionen**. Dort
    bringt sie messbar Mehrwert, und die Einigkeits-Abgaben bleiben unberührt. Die Freigabe macht allein die Einigkeit.
- 08.11. 17:25 – **(N27) Dritte Intuition (161–260, Seeds 0/1/2): „offen“, knapp. Zweite Lesart erfüllt.** Richtig je Seed: 57 / 50 / 50.

  | Regel (sonst „weiß ich nicht“) | abgegeben | richtig | S₂ |
  |---|---|---|---|
  | Einigkeit aus zwei (0/1) | 38 | 37 (97 %) | +0,350 |
  | **Mehrheit aus drei** | **62** | 55 (89 %) | **+0,410** |
  | Einstimmig aus drei | 29 | 29 (100 %) | +0,290 |

  - Lesart: Mit 62 Abgaben ist das Ziel ≥ 48 erreicht. Mit 89 % Präzision ist das Ziel ≥ 90 % um einen Punkt verfehlt → **offen**.
  - Zweite Lesart (S₂ ≥ Einigkeit aus zwei): +0,410 gegen +0,350 → **erfüllt**.
  - Beschreibend:
    - Andere Seed-Paare: 0/2 einig 42, davon 40 richtig; 1/2 einig 40, davon 35 richtig.
    - Weiche „Mehrheit, sonst Hinterzimmer“: mit MIT **66** (MIT allein 58); mit WT-A **62** (WT-A allein 44, INT Seed 0 allein 57).
  - Einordnung: Drei Intuitionen geben deutlich öfter ab, bei kaum geringerer Präzision. Zusammen mit dem eigenen Hinterzimmer
    (WT-A) schlägt die Kette INT allein (62 gegen 57). Mit zwei Intuitionen ging das nicht (54).
- 08.11. 18:09 – **Quelle geprüft (offener Punkt seit 07.11.):** Der MIT-Blogpost heißt laut Originalseite „Sparks of Weight-Space
  Programming: LLMs can natively read & write neural network weights“. Autoren: Rikiya Takehi, Jayden Teoh, Alex Zhang, Omar Khattab
  (MIT CSAIL), 2. 11. 2026. „Teoh“ ist richtig. Die Literaturangabe im Bericht ist ergänzt.
- 08.11. 18:43 – **Nutzer: „Ja, das bereiten wir vor“ (Nachtlauf). (N30) Beratung im Vorderzimmer + eigenes Hinterzimmer auf 150 frischen
  Aufgaben. Lesart vorab; Start erst nach Nutzer-Go, kein Lauf existiert.**
  - **Aufgaben:** 150 MATH-Trainingsaufgaben, nie benutzt (auch nicht neu40).
    - Stufen wie MATH-500: 13 / 27 / 32 / 38 / 40.
    - Zufalls-Seed 202611082, Datei daten/practice/math_train_nacht150.jsonl.
  - **Läufe**, Protokoll wie immer (T 0,6, 32k, vLLM-Stil, presence 1,5):
    - MiniPC: INT (eigen ohne Denken) mit Seeds 0, 1, 2.
    - Laptop: WT-A mit Denken und MIT mit Denken, je Seed 0.
  - **Hauptregel „Beratung + eigenes Hinterzimmer“ (B+H):** Geben mindestens zwei der drei Intuitionen gleichwertige Antworten
    (math-verify in beide Richtungen), wird diese abgegeben. Sonst gilt die Antwort von WT-A mit Denken.
  - **(H1) B+H gegen INT allein (Seed 0):**
    - „trägt“, wenn B+H ≥ INT + 5 von 150;
    - „widerlegt“, wenn B+H ≤ INT + 1;
    - sonst „offen“.
  - **(H2) B+H gegen MIT allein (gepaart):**
    - „schlägt MIT“, wenn B+H ≥ MIT + 5 UND McNemar einseitig p < 0,05;
    - „mindestens gleichauf“, wenn B+H ≥ MIT;
    - „unter MIT“, wenn B+H ≤ MIT − 5;
    - sonst „offen“.
  - **(H3) Einigkeit zweier Intuitionen (Seeds 0/1), vierte Bestätigung:**
    - „hält“, wenn die Präzision ≥ 85 % ist;
    - „widerlegt“, wenn sie < 75 % ist.
  - **(H4) Mehrheit aus drei:**
    - „trägt“, wenn die Präzision ≥ 85 % ist UND die Abdeckung mindestens 10 Prozentpunkte über der Einigkeit aus zwei liegt;
    - „trägt nicht“, wenn die Präzision < 80 % ist.
  - **Beschreibend:**
    - B+H mit MIT als Hinterzimmer;
    - Einstimmigkeit aus drei;
    - Tokens je richtiger Antwort (B+H, INT, MIT, WT-A);
    - die Sonde als Schiedsrichterin, falls die Zustände danach gesammelt werden.
  - **Laufzeit-Schätzung** aus den heutigen Durchsätzen (Laptop etwa 190, MiniPC etwa 100 Tokens/s): etwa 7–8 h.
- 08.11. 18:46 – **Nutzer-Go „Ja, starten“ für den Nachtlauf (N30).**
  - MiniPC gestartet um 18:45 (INT Seeds 0/1/2).
  - Laptop wartet auf das Ende von N28, dann WT-A ‖ MIT.
  - Nutzer: „Okey, dann machen wir es so“: Der Bericht v0.2 wird nach dem Gegencheck veröffentlicht, *bevor* das Ergebnis von N30
    existiert. Die Lesart N30 steht darin als öffentliche Vorab-Registrierung.
- 08.11. 18:48 – **(N28) Einig → INT, sonst MIT mit Denken, auf unberührten Aufgaben 301–370 (70): „offen“.**
  - Regel **40** gegen MIT allein **38** (INT allein 35).
  - Kriterien: (i) Gesamt ≥ MIT: ja. (ii) Präzision der Einigkeit 90 % (28/31): ja. (iii) Tokens je richtiger Antwort 56.835 gegen
    MIT 41.025: nein → **offen**, wie vorab erwartet.
  - Zerlegung: Einigkeits-Teilmenge (31) INT 28 gegen MIT 26; Rest (39) MIT 12 gegen INT 7. Der Gewinn kommt aus beiden Teilen:
    vorne die Präzision, hinten MITs Ausgang.
  - Beschreibend: INT 35 gegen MIT 38 auf 301–370 (nur INT 8, nur MIT 11). Tokens je richtiger Antwort INT 16.981 gegen MIT
    41.025.
- 08.11. 18:51 – **Nacht vorbereitet.**
  - Auswertung N30 geschrieben (109_nacht150.py, rechnet erst, wenn alle fünf Läufe vollständig sind).
  - Morgen-Kette (kette_tag_laptop11.sh) wartet auf beide Nachtblöcke. Dann holt sie die INT-Läufe, sammelt die Sonden-Zustände
    (beschreibend, Schiedsrichterin) und rechnet die vorab festgelegte Auswertung.
  - Der Wächter läuft weiter (Herzschlag 40 min).
- 08.11. 18:55 – **Argons Gegencheck v0.2: grünes Licht.** Eingearbeitet:
  - [Muss] Die gepoolten 91 % (78/86) sind in Kurzfassung und 3.10 ausdrücklich als beschreibend markiert, weil jeder Satz einzeln
    vorab festgelegt war.
  - [Sollte] In der Kurzfassung steht ein Punkt „Two modes, two costs“: Ein einzelner INT-Lauf ist der effiziente Weg, mehrere
    Intuitionen kaufen Präzision mit Tokens.
  - Zur Zitat-Frage (A/B) hat Argon nichts gesagt. WREN und Poow stehen noch aus.
- 08.11. 19:03 – **WRENs Fazit zum Bericht v0.2 eingearbeitet** (abgelegt unter gutachter/2026-11-08):
  - **Weiterdenken nach drei Gruppen getrennt** (Kurzfassung und 3.9): Entwicklung 83–100 %, alle Abschlüsse frisch 77 %, die 32
    stummen Läufe 12/32. MIT 16 %.
  - **Vertrauensintervalle** (gepaarter Bootstrap, 10.000 Ziehungen):
    - WT-A − MIT −13,6 Punkte [−21,4; −5,7];
    - INT − MIT −6,4 [−15,0; +2,1];
    - ERGORE − MIT −10,7 [−17,9; −3,6], bestätigt die berichtete Angabe;
    - Schiedsrichterin +4 richtige [−1; +10]. Das ist ausdrücklich als zerbrechlich gekennzeichnet (18 entscheidende Aufgaben).
  - **Kurzfassung Punkt 4:** zusätzlich die Feldzahl (1 von 86 richtigen als unsicher markiert, 8 von 16 falschen erkannt).
  - **2×2-Test:** Satz „konservatives Tor, gefragt ist, *was* es liest“ vor die Tabelle gestellt.
  - **IFEval WT-A:** die Lesart (≥ 72 bestätigt, ≤ 64 widerlegt) direkt dabei.
  - **Kaskade:** die Lesart (S₂ UND ≥ 75 richtige) erklärt, warum sie trotz höherem S₂ widerlegt ist.
  - **Tiefe:** Die geschachtelten Modelle (−0,49 → +0,46) und das volle Modell mit Bootstrap (+0,29) sind als zwei Spezifikationen
    benannt.
  - **Abschnitt 4:** „mainly work in E“ als [interpretation] markiert.
  - **N28:** der Gewinn aus beiden Zimmern (vorne 28:26, hinten 12:7) in der Kurzfassung.
  - **Abschnitt 7:** TODO ersetzt durch die Beschreibung des Veröffentlichungsordners.
  - **Neu:** eine Kurzfassung (Abstract) mit drei Kernaussagen.
  - **Kopf:** „work period 4–8 November 2026“. Nutzer: „1 Tag stimmt nicht – wir sind seit Mittwoch dabei“. WRENs
    „Ein-Tages-Projekt“ war falsch; der Bericht selbst behauptete das nirgends.
  - **Für v0.3 vorgemerkt:** Kurzfassung auf die Punkte 1, 3, 6, 9, 10 kürzen; Haus-Zeichnung mit Zahlen als Abbildung 1.
- 08.11. 19:09 – **Tiefen-Regression auf dem endgültigen Datenstand neu gerechnet** (88_flur.py). Die Bericht-Tabelle stammte von 09:42,
  vor dem letzten Stand der Zuck-Dateien (09:47/09:52).
  - Neu: Tiefe **+0,26** [+0,01; +0,49], Schleifen-Grad **−0,80** [−1,08; −0,50], Stufe **−0,68** [−1,06; −0,32], Quelle MIT +0,55.
    109.561 Wert-Aussagen.
  - Das ist identisch mit dem geschachtelten Modell M4.
  - Die Aussage (Schleifen und Schwierigkeit, nicht Tiefe) bleibt. Die Tor-Tabellen ändern sich kaum (≈ 60 % / 15 %).
  - Der Bericht ist angepasst; der alte Stand liegt in flur_0942.json.
- 08.11. 19:11 – **Bericht v0.2 eingeloggt** (Nutzer: „loggen wir den Bericht ein … ansonsten go!“), englisch, nach Argons und WRENs
  Gegencheck und meiner Schlussdurchsicht.
  - **Letzte Korrekturen:**
    - Abstract („reduces reasoning loops“; 77 % = alle Abschlüsse auf frischen Aufgaben);
    - Kurzfassung 7 (51 von 61 nach Reflex-Abschlüssen, wie im Trigger-Audit);
    - Tiefen-Tabelle auf dem endgültigen Datenstand;
    - Grenzen und nächste Schritte aktualisiert;
    - vier Literaturangaben, die bisher nur in der Liste standen, im Text belegt (Kadavath, Azaria/Mitchell, Ferrando, Arditi);
    - Fußnoten q9/q10 entfernt (Nutzer: „unten bei den Zitaten 9 und 10 raus nehmen“).
  - **Fassung A** (alle Zitate), SHA-256 c8fc28b6a1956b11cb88510b83bbb524c29ee2cba4402d786e9a7f0f1971492f
  - **Fassung B** (gekürzte Zitate), SHA-256 ddfdeffb397a4e4dea21692cd274409260501b48d1fbc5f22631b919b957f617
  - Scan auf Pfade, Rechnernamen und Zugangsdaten: sauber.
- 08.11. 19:20 – **PDFs gebaut** (veroeffentlichung/build_pdf.py; markdown-it, eigenes Layout, Druck über Chrome, ohne Downloads):
  - Englisch A und B.
  - Deutsch A und B, übersetzt aus der eingeloggten Fassung (maßgeblich bleibt Englisch; Zitate des Autors im Original).
  - Dazu CITATION.cff im Veröffentlichungsordner.
  - Entwürfe für GitHub, Hugging Face und die Mail an die MIT-Autoren (veroeffentlichung/ENTWUERFE_VEROEFFENTLICHUNG.md).
  - Veröffentlicht ist nichts; A oder B entscheidet der Nutzer.
- 08.11. 19:22 – **Nutzer-Entscheidung: Fassung B (gekürzt) wird veröffentlicht.**
  - Im Veröffentlichungsordner liegen jetzt: Bericht englisch (MD, identisch mit der eingeloggten Fassung B) und PDF, dazu die
    deutsche Übersetzung (MD, PDF).
  - README angepasst. Scan sauber.
- 08.11. 19:26 – **Argons PDF-Durchsicht: zwei kosmetische Funde behoben.**
  - Roh-LaTeX in 3.6 steht jetzt als wörtliche Modell-Ausgabe in Code.
  - In Fassung B sind die doppelten Fußnoten mit den deutschen Originalen weg; sie stehen bereits im Anhang.
  - Argons Sicherheits-Suche (Pfade, IP-Adressen, Schlüssel, ssh) über den Veröffentlichungsordner: keine Treffer.
  - **Neue Prüfsummen** (inhaltlich unverändert):
    - A: c536d1dbb2a862e9f94ce05006b3c423d13b76b3f3ff3913ec1596b30929c7fb
    - B: 78c394cc5530fee8bf9ef953e49673f0c1a48f96e5b82cb1beb583d7258ece1f
  - PDFs neu gebaut; Veröffentlichungsordner aktualisiert.
- 08.11. 19:42 – **Veröffentlichung, Schritt 1 vorbereitet (GitHub; hochgeladen ist noch nichts).**
  - GitHub-Konto des Nutzers: NeoCortex0815. Lokales Repo im Veröffentlichungsordner angelegt (Zweig main).
  - Commit-Identität nur für dieses Repo: „Dave Uhlemann (NeoCortex)“ mit der Noreply-Adresse von GitHub. Die echte
    Mail-Adresse kommt in keinen Commit. Zeilenenden bleiben unverändert (autocrlf aus).
  - **Kontakt statt Mail-Adresse** (Nutzer: „Mailadresse gehört nicht ins paper? Wenn jemand was will, dann auf Github oder
    Huggingface?“):
    - vorgesehene Repo-Adresse github.com/NeoCortex0815/knowing-is-not-committing;
    - eingetragen im Kopf und in Abschnitt 7 des Berichts (EN, DE), im README („Questions and corrections“ → Issues), in
      CITATION.cff (repository-code) und in den Entwürfen (die DOI bleibt Platzhalter);
    - Skript veroeffentlichung/kontakt_einsetzen.py; wiederholbar, falls sich der Repo-Name ändert.
  - PDFs neu gebaut. Kontrolle: PDF-Metadaten, Text und entpackte Datenströme ohne Pfade, Rechnernamen oder Adressen. Textscan
    über den Veröffentlichungsordner: sauber.
  - Die Protokoll-Kopie im Veröffentlichungsordner endete um 18:09, also *vor* der Vorab-Festlegung von N30. Sie wird mit diesem
    Eintrag erneuert und gesäubert.
  - Wächter: Die Hängerprüfung schaut jetzt auf jeden Nachtlauf einzeln (WT-A ‖ MIT am Laptop, INT Seeds 0–2 am MiniPC). Vorher
    sah sie nur das jüngste Log; ein einzelner hängender Lauf wäre so unbemerkt geblieben.
  - **Neue Prüfsummen** (inhaltlich unverändert bis auf die Kontaktzeile):
    - A: 826c3b16cbe0ce7730a5d01c0d6932ec8a2c79b4094fe87566142dcf5badf4bc
    - B: 25d2bbb66cf1e5b1ba3d396d73a4facc1bc44dfc6522c2482855896b784309b9
