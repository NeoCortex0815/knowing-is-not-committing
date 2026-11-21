# Auszug aus dem Protokoll der Vorab-Festlegungen (17.–21.11.2026): SGNE-CC, N40–N45 und Fassung 0.5

*Zum Bericht v0.5, Abschnitte 3.13 und 3.14. Dieser Auszug enthält die Einträge zu Definition, Einfrieren, Prognosen, Läufen, Ergebnissen
und Berichtigungen der Tests N40–N45 wörtlich, dazu Daves Entscheidungen zu diesen Tests und die Nennung von SGNE-CC. Andere Einträge
dieser Tage fehlen; Teile, die andere Arbeiten betreffen, sind mit „[…]“ gekürzt. Rechnernamen, Pfade und Angaben zu privaten Systemen
sind wie in den früheren Auszügen bereinigt. „Spiegel“ meint die Kopie des Projekts, in der jede Ergebniszeile vor dem Rechnen im
Haupt-Thread neu bewertet wird (Skript 133). Die Methode SGNE-CC stammt von Igor M. Zhuk (auf Hugging Face: Nondual-Observer); bis zu
seinem Wunsch vom 20.11. heißt er im Protokoll Nondual-Observer.*

---
- 17.11. 14:52 – **HF: neue Diskussion #5 und Kommentar in #2** (Nondual-Observer, 17.11.): eigene Gewichtsänderung SGNE-CC (Drehungen in MLP und GatedDeltaNet, Normen erhalten) und Nachprüfung unserer Zahlen auf allen 500 MATH-500-Aufgaben bei 32K. Nur gelesen, nichts heruntergeladen. Entwürfe 2j (#2) und 5a (#5) in veroeffentlichung/ENTWUERFE_VEROEFFENTLICHUNG.md; Dave postet. Beim Prüfen bemerkt: Unsere 8 %/92 % (post, pp 1,5) stammen aus dem 16K-Protokoll; die veröffentlichte Änderung bei 32K auf 161–300 steht nach v0.4 bei 82/140, nicht 80/140 (im Entwurf zuerst falsch, berichtigt). […]
- 17.11. 15:38 – **Download SGNE-CC freigegeben** (Dave: „Ja, freigeben“): Nondual-Observer/Qwen3.5-0.8B-SGNE-CC, Revision a0f617d4…, nur model.safetensors (1.746.942.632 Bytes, laut API SHA-256 d0b745ce6e48ff0b…) und config.json, in den neuen leeren Ordner modelle/Qwen3.5-0.8B-sgne-cc/; nur lesen, keine ihrer Skripte ausführen. Ihre tokenizer.json ist laut API byte-gleich mit unserer (5f9e4d49…). Laptop-Platte 97 % voll, 38 GB frei. Entwurf paket/ENTWURF_N40_SGNE_CC.md (Kennung N40 vorgeschlagen, nicht eingefroren).
- 17.11. 15:38 – **SGNE-CC heruntergeladen** 15:37:28–15:37:57: model.safetensors SHA-256 d0b745ce6e48ff0b2b22f9dadf229ba246afabebd9ae8308f07a4cd1824d0324 = Angabe der API; config.json b90b86f35c8e6925… inhaltlich gleich mit dem Original Qwen3.5-0.8B (sortierter Vergleich ohne Unterschied). Beide schreibgeschützt. Nichts ausgeführt.
- 17.11. 15:44 – **N40 Teil 1 eingefroren vor dem Rechnen** (Dave: „Ja, Teil 1 jetzt“): Skript paket/149_n40_gewichte.py (6153dab31ef2d139…), Entwurf paket/ENTWURF_N40_SGNE_CC.md (8879955c2ee8547a…; Lesart „Angaben bestätigt“ nur bei genau 15 down_proj/802 Spalten, 9 out_proj/1.182 Spalten, einer Gate-Zeile in Schicht 16, sonst nichts, Normänderung ≤ 0,2 %). Selbsttest bestanden (8 Prüfungen, u. a. Drehung erhält die Norm, gestreckte Spalte erkannt, Rang-1-Richtung |cos| = 1); Trockenlauf: 488 Tensoren auf beiden Seiten, Formen gleich, MIT-Richtung und eigen-vL vorhanden.
- 17.11. 15:45 – **N40 Teil 1 gerechnet** (149 unverändert 6153dab3…, 15:44:35–15:44:41; Ausgabe ergebnisse/n40_teil1_gewichte.json
  43987bfa440cf0d1…, Log logs/149_n40_teil1.log):
  - [pre-registered] **„Angaben bestätigt“**: down_proj in 15 Schichten (3, 7, 11–23) mit zusammen 802 Spalten, größte Normänderung
    0,139 %; GatedDeltaNet-out_proj in 9 Schichten (12, 13, 14, 16, 17, 18, 20, 21, 22) mit 1.182 Spalten, größte Normänderung 0,163 %
    (seine Angabe ≤ 0,16 %, unsere Grenze 0,2 %); sonst nur eine Zeile: Schicht 16, linear_attn.in_proj_a, Zeile 12 (997 von 1.024
    Werten). Nichts weiter geändert.
  - [descriptive] Die Spalten werden deutlich gedreht (Median 8–29°, höchstens 94°). Die Änderung ist je Schicht fast Rang 1 (erster
    Singulärwert 95–100 % der Energie; Schicht 15: 68 %, 19: 73 %, 23: 56 %).
  - [descriptive] **In den Schichten 15 und 19 schreibt SGNE-CC fast genau in MITs Richtung:** |cos| der Hauptrichtung zu MITs u_15 0,990,
    zu u_19 0,994; alle 64 MIT-Spalten jeder Schicht sind unter den gedrehten (90 bzw. 104 Spalten). In den übrigen down_proj-Schichten
    |cos| 0,33–0,51 zu MITs Richtung (zufällig wären etwa 0,03), Schicht 23 ist die Ausnahme (0,04). Zu unserer eigenen Richtung 0,76/0,78
    in 15/19 (wie eigen gegen MIT).
  - [interpretation] SGNE-CC ist nicht unabhängig von der MIT-Änderung: Es sieht aus wie MITs Richtung, als normerhaltende Drehung
    geschrieben, plus weitere Schichten und der GatedDeltaNet-Teil. Der Vergleich SGNE-CC gegen MIT-p50c prüft dann vor allem „Drehung
    statt Addition“ und die zusätzlichen Orte. Sein Text nennt diese Herkunft nicht; als Frage stellen, nicht als Vorwurf.
- 17.11. 16:09 – **HF #2, neue Antwort von Nondual-Observer an uns** (gelesen): Seine 14 %/19 % bei T = 0 prüfen nur den letzten Kandidaten am Ende des abgeschnittenen Entwurfs (letzte Antwort-Formel oder letzte Zahl; nur letztes \boxed ohne EOS: 3 %/6 %). Er hat unsere Kandidaten-Regeln (42_wahrheitsmelder.py v1, 76_kandidaten_v2.py v2, aus unserem öffentlichen Repo) auf seine 500er-Spuren angewandt: T = 0,6/pp 1,5, post: richtiger v2-Wert im Denken in 57 % (streng 8 %); T = 0: im Denken post 41 %, MIT 46 %, SGNE-CC 55 %; davon abgegeben post 0/207, MIT 25/228 (11 %), SGNE-CC 215/277 (78 %); mit v1 in den 92 gekappten SGNE-Entwürfen kein unabgegebener Treffer. [interpretation] Mit unserem Zähler entspricht das bei T = 0 einer Lücke von etwa 0,22 für SGNE-CC (MIT 0,89, post 1,0). In #5 ist ein Kommentar von ihm verborgen (Inhalt nicht sichtbar); sein Eröffnungsbeitrag wurde bearbeitet, inhaltlich wie gelesen. Entwurf 5b daraufhin überarbeitet (der Absatz über die verschiedenen Zähler ist erledigt).
- 17.11. 16:19 – **N41 definiert** (Dave: „Dem sollten wir definitiv nachgehen!“): „Welcher Teil von SGNE-CC legt fest?“, Entwurf paket/ENTWURF_N41_SGNE_ABLATION.md (5fba3e982a9d7410…, nicht eingefroren). Arme aus vorhandenen Tensoren: MIT, S-voll (= N40 Teil 2), S-1519, S-MLP, S-GDN; Lesarten D (Drehung statt Addition) und O (zusätzliche Orte). Lizenz laut seiner NOTICE: Apache-2.0 für Patch und Code, der Checkpoint zusätzlich unter den Qwen-Bedingungen; Nachbau und Abwandlung erlaubt, bei Veröffentlichung LICENSE, NOTICE und Änderungsvermerk. N40 gilt als definiert seit Daves Freigabe von Download und Teil 1.
- 17.11. 17:42 – **N40 Teil 2 vorbereitet und eingefroren, vor dem Lauf** (Dave: „dann jetzt machen“, nur CPU; Lauf nach dem Abendlauf):
  - Modellordner modelle/Qwen3.5-0.8B-sgne-cc-hf/ (seine Gewichte unverändert kopiert, d0b745ce…; Tokenizer, Vorlage, config und Index aus
    unserem Original; HERKUNFT.txt mit Lizenzhinweis). Umwandlung mit llama/convert_hf_to_gguf.py (ohne -I, weil das Werkzeug sein eigenes
    Unterverzeichnis braucht; kein fremder Code): gguf/Qwen3.5-0.8B-sgne-cc-q8_0.gguf, 833.592.320 Bytes, SHA-256 60f965336740481e…, Log
    logs/gguf-sgne-cc-L.log. Prüfung: gegenüber gguf/Qwen3.5-0.8B-q8_0.gguf unterscheiden sich genau 25 von 335 Tensoren (15 ffn_down,
    9 ssm_out, 1 ssm_alpha) – deckt sich mit Teil 1.
  - […]
  - Auswertung paket/150_n40_sgne_lauf.py (2672fc7793672bde…): Selbsttest bestanden (11 Prüfungen), Trockenlauf: post, base, wta je 50 Zeilen
    vollständig, sgne fehlt (noch nicht gelaufen).
  - **Abweichung vom Entwurf, vor dem Datenkontakt:** G2 bekommt die Vorbedingung „mindestens 10 Läufe mit dem richtigen Wert im Denken,
    sonst ‚so nicht prüfbar‘“ (wie S4); die Fallback-Lesart ist eine Näherung seiner Regel (letzte Antwort-Formel, sonst letzte Zahl im Text,
    nur wenn kein \boxed{} abgegeben wurde), nur beschreibend. Die neue Antwort wird vor dem Rechnen im Haupt-Thread neu bewertet und in den
    Spiegel kopiert (150 --spiegeln, wie 144). Die Vergleichswerte post 5, base 27, WT-A 19 sind bekannt (schon veröffentlicht bzw. gelesen).
- 18.11. 01:08 – **Prognose Claude zu N40 Teil 2** (vor dem Lauf; Dave sieht sie erst nach seiner eigenen): SGNE-CC richtig 22 von 50 (Spanne 15–29); L 0,30 (0,15–0,45); Schleife oder Grenze etwa 15 % (5–35 %). Urteile: G1 „hilft deutlich“ (gegen post 5), gegen WT-A (19) „gleichauf“; G2 „legt sich fest“; G3 „weniger Schleifen“.
- 18.11. 01:29 – **N41 Kern vorbereitet und eingefroren, vor dem Lauf** (Dave 18.11.: nach dem Nachtlauf mit Erholungspause):
  - Arm S-1519 mit paket/152_n41_arm_s1519.py (77f9e3be9fc01079…): Original, nur mlp.down_proj 15 und 19 aus SGNE-CC; Prüfung bestanden
    (gegenüber dem Original genau diese 2 Tensoren anders, beide byte-gleich mit SGNE-CC). safetensors ca3dfa9d4c7aa580…; GGUF
    gguf/Qwen3.5-0.8B-s1519-q8_0.gguf 7b3b504665cdce83… (Log logs/gguf-s1519-L.log). GGUF-Prüfung: S-1519 und MIT (gguf/Qwen3.5-0.8B-mit-q8_0.gguf,
    c20c24cf14caf5e6…) unterscheiden sich vom Original-q8_0 in genau denselben 2 Tensoren (blk.15/19.ffn_down); S-1519 dort gleich SGNE-CC.
  - […]
  - Auswertung paket/151_n41_kern.py (37df8f41b8cafeef…, nutzt 150 mit Prüfsummenprüfung): Selbsttest bestanden, Trockenlauf: post/base/wta
    vollständig, mit/s1519/sgne fehlen (noch nicht gelaufen).
  - **Zusatz zum Entwurf N41 (5fba3e98…), vor dem Datenkontakt:** „festgelegt“ = richtiger Wert im Denken UND richtige Abgabe, gepaart über
    die Aufgaben, in denen beide Arme den Wert finden; Vorbedingung mindestens 10 solche Aufgaben, sonst „so nicht prüfbar“. O bekommt die
    Gegenstufe „Betrag ≤ 5 pp: ‚die weiteren Orte tragen nichts Messbares‘“. Zusätzlich 5 min Pause zwischen den Armen.
- 18.11. 01:29 – **Prognose Claude zu N41 Kern** (vor dem Lauf, verdeckt bis Dave seine abgibt): MIT richtig 24 von 50 (18–30), S-1519 richtig 14
  (6–22); D etwa +5 pp (−15 bis +25) → „offen“; O etwa +10 pp → „offen“. Begründung: Die Drehung schiebt in 15/19 schwächer in MITs Richtung
  als die Addition (Normen erhalten, Hauptrichtung nur 68/73 %), darum vermutlich weniger Schleifen-Abbau.
- 18.11. 01:55 – **N40 Teil 2 gelaufen** 01:25:56–01:54:27 (28½ min), 50 von 50, Exit 0; ergebnisse/n40-sgne-denken/ergebnisse.jsonl 91908f7d8346b32d…, zusammenfassung.json 453428f4521146ea… (nicht geöffnet). Spiegel mit 150 --spiegeln: Quelle und Spiegel gleich (91908f7d8346…), also keine Zelle neu gesetzt; Trockenlauf 150 jetzt mit allen 4 Armen vollständig. […] Beides wird mit Dave gelesen (vorher seine N40-Prognose). Kette N41: Erholungspause seit 01:54:54 (GPU 52 °C).
- 18.11. 05:55 – **N41 Kern gelaufen** (Exit 0): MIT 02:24:56–04:09:00 (ergebnisse.jsonl 77b48edc2fc33f53…), S-1519 04:14:07–05:54:45 (1a449d086487c623…), je 50 von 50; GPU am Ende 56 °C, Server gestoppt. Spiegel mit 151 --spiegeln (Ausgabe oben, verblindet). Nicht gelesen; mit Dave nach seiner Prognose.
- 18.11. 06:20 – Dave: „skipp und gleich zur Auswertung und dann zum weiteren Vorgehen“ → keine Prognose von Dave zu N40/N41; ausgewertet wird jetzt ([…], 150, 151).
- 18.11. 06:27 – **Ausgewertet: […], N40 Teil 2, N41 Kern** (ohne Daves Prognose, auf seinen Wunsch):
  - […]
  - **N40 Teil 2** (150, Ausgabe n40_teil2_auswertung.json 85c3cec9aed01793…, Einzelzeilen ergebnisse/n40_teil2_einzelzeilen.csv 9a629f352c007cb6…):
    - [pre-registered] **G1 „hilft deutlich“**: SGNE-CC 22 von 50 gegen post 5 (nur SGNE 17, nur post 0, McNemar p < 0,0001); gegen WT-A (19)
      +3 → **„gleichauf“**. **G2 „legt sich fest“**: L = 0,20 (4 von 20 gefundenen nicht abgegeben). **G3 „weniger Schleifen“**: 4 %.
    - [descriptive] Festgelegt 80 % (Base 82 %, WT-A 65 %, post 21 %); G5 13/20; Tokens im Mittel 6.583 (post 14.491, Base 10.943); Tokens je
      richtige Antwort 14.961 (Base 20.265, WT-A 56.523, post 144.909); an der Grenze 4 %. Fallback-Näherung: 0 zusätzliche. Zeitgrenze: 0.
  - **N41 Kern** (151, Ausgabe n41_kern_auswertung.json d4db5a066094c345…, Einzelzeilen ergebnisse/n41_kern_einzelzeilen.csv fa9ae7a2999ae81a…):
    - [descriptive] MIT 20 von 50 (L 0,31, Schleife oder Grenze 46 %, an der Grenze 38 %, Tokens je richtige 57.246); S-1519 15 von 50 (L 0,53, 58 %,
      36 %, 75.159); richtig MIT gegen S-1519 7 : 2, p = 0,09.
    - [pre-registered] **D „offen“**: festgelegt S-1519 0,52 gegen MIT 0,74 über 27 gemeinsame Funde, −22 pp. Die Lesart sah nur „die Drehung
      trägt“ (≥ +20) und „Ort und Richtung genügen“ (Betrag ≤ 5) vor; der Unterschied geht in die Gegenrichtung (Drehung schwächer als
      Addition) und ist nach der Regel „offen“. **O „die weiteren Orte tragen“**: SGNE-CC 0,89 gegen S-1519 0,61 über 18 gemeinsame Funde, +28 pp.
      Nebenwirkung: keine.
    - [interpretation] Der Festlege-Gewinn von SGNE-CC kommt nicht von der Drehung am MIT-Ort: allein in 15/19 gedreht wirkt sie schwächer
      als MITs Addition. Er kommt von den übrigen Orten (13 weitere down_proj, GatedDeltaNet, Gate-Zeile): Schleifen 58 % → 4 %, festgelegt
      +28 pp. Welcher dieser Orte trägt, zeigt erst S-MLP gegen S-GDN. Vorbehalt: 18–27 gemeinsame Funde, ein Seed.
  - **Prognosen Claude** (01:10 und 01:29): N40 SGNE 22 – getroffen; L 0,30 (0,15–0,45) – getroffen (0,20); Schleifen 15 % (5–35 %) – zu hoch (4 %);
    alle vier N40-Urteile getroffen. N41 MIT 24 (18–30) – in der Spanne (20); S-1519 14 (6–22) – getroffen (15); D +5 (−15 bis +25) – verfehlt
    (−22, Richtung falsch), Urteil „offen“ getroffen; O +10 „offen“ – verfehlt (+28, „die weiteren Orte tragen“).
- 18.11. 08:53 – **N40 veröffentlicht (Dave: „N40 posten“)**: Einzelzeilen und Aufbau in release/wsp-qwen08b/results/n40-sgne-cc (README, per_item.csv = ergebnisse/n40_teil2_einzelzeilen.csv 9a629f35…), Geheimnis-Scan über die Änderung ohne Treffer, Commit ef3beb9 mit Noreply-Identität, gepusht, online geprüft. Beitragstext 5c für #5 in ENTWUERFE (nur N40, WT-A nicht genannt); Dave postet.
- 18.11. 17:39 – **N41 Teil 2 vorbereitet und eingefroren, vor dem Lauf** (Dave: „ja dann schnüre den Plan dafür, dass der Laptop über Nacht laufen kann … Laptop kannst du gerne wieder über Nacht blockieren“):
  - Arme mit paket/157_n41_arme_mlp_gdn.py: S-MLP (alle 15 geänderten down_proj von SGNE-CC; safetensors 788c53507c815ba8…, GGUF gguf/Qwen3.5-0.8B-s-mlp-q8_0.gguf ed320a393e52cf57…) und S-GDN (9 out_proj und in_proj_a der Schicht 16; safetensors 811d39fa59a79a7f…, GGUF gguf/Qwen3.5-0.8B-s-gdn-q8_0.gguf 5d34e783020a836c…). Prüfung bestanden: gegenüber dem Original genau 15 bzw. 10 Tensoren anders, dort gleich SGNE-CC; zusammen die 25 von SGNE-CC. GGUF-Prüfung: 15 ffn_down bzw. 9 ssm_out + 1 ssm_alpha, dort gleich SGNE-CC.
  - Auswertung paket/156_n41_mlp_gdn.py (nutzt 151 mit Prüfsumme): Lesarten M (festgelegt SGNE − S-MLP: ≥ +20 pp „der GatedDeltaNet-Teil trägt mit“, Betrag ≤ 5 „der MLP-Teil genügt“) und G (festgelegt S-GDN − post: ≥ +20 pp „wirkt allein“, Betrag ≤ 5 „wirkt allein nicht“), sonst „offen“, Vorbedingung ≥ 10 gemeinsame Funde. Selbsttest bestanden, Trockenlauf: Vergleichsarme vollständig, neue fehlen.
  - Kette paket/kette_n41b_laptop.sh: S-MLP, Erholungspause (≥ 30 min, bis GPU ≤ 50 °C), S-GDN; Protokoll wie N41.
  - Prüfsummen (157, 156, Kette): 3d0b0991e12cb8f7 1ecfcfb38f8889cc b1d2d4f6287fe5fd 
  - **Prognose Claude** (vor dem Lauf): S-MLP richtig 18 (10–25), Schleife oder Grenze 35 %; S-GDN richtig 10 (5–18), Schleife oder Grenze 60 %. M „offen“ (der GatedDeltaNet-Teil trägt etwas, nicht alles), G „offen“. Begründung: Schleifen sind ein Wiederholungs-Phänomen, der rekurrente Teil dürfte beim Schleifenabbau mithelfen, allein aber nicht genügen.
- 19.11. 00:00 – **Nach dem Neustart der Sitzung** [descriptive]: Die Kette N41 Teil 2 endete mit der Sitzung; S-MLP vollständig (18:09:46, 50 von 50), S-GDN abgebrochen bei 37 von 50 (letzte Zeile 19:34). Laptop leer (kein Server, kein Python, GPU 44 °C). […] **Fortsetzung S-GDN** mit paket/kette_n41c_laptop.sh (gleiches Protokoll; die beim Abbruch laufenden Aufgaben werden mit demselben Seed neu gezogen, wie bei früheren Server-Neustarts) – Dave: Laptop frei, über Nacht erlaubt.
- 19.11. 00:36 – **N41 Teil 2 gelaufen**: S-MLP 17:39–18:09 (ergebnisse.jsonl 0c4233d834524c65…), S-GDN 18:39–19:34 (37) und Fortsetzung 00:00–00:35 (50 von 50; 55c4496b41ea3837…). Spiegel mit 156 --spiegeln (verblindet). Nicht gelesen; Auswertung mit Dave.
- 19.11. 15:26 – **N41 Teil 2 ausgewertet** (156, Ausgabe n41_teil2_auswertung.json 584840ae003460e5…, Einzelzeilen ergebnisse/n41_teil2_einzelzeilen.csv
  d4013278ed79a3d7…; Dave: „gerne durchführen“, ohne eigene Prognose):
  - [descriptive] **S-GDN** (nur GatedDeltaNet-out_proj und Gate-Zeile): **26 von 50**, L 0,29 (festgelegt 71 %), Schleife oder Grenze 34 %, an der
    Grenze 30 %, Tokens im Mittel 18.557, je richtige 35.687. **S-MLP** (nur die 15 down_proj): 13 von 50, L 0,39, Schleife oder Grenze 20 %, an der
    Grenze 4 %, Tokens im Mittel 4.965, je richtige 19.098; richtiger Wert im Denken nur in 18 Läufen. Zum Vergleich: SGNE-CC voll 22, MIT 20, S-1519 15,
    post 5, Base 27.
  - [pre-registered] **G „der GatedDeltaNet-Teil wirkt allein“**: festgelegt S-GDN 0,78 gegen post 0,22 über 23 gemeinsame Funde, +57 pp; richtig 26
    gegen 5 (21 : 0). **M „offen“**: SGNE-CC 0,85 gegen S-MLP 0,69 über 13 gemeinsame Funde, +15 pp; richtig 22 gegen 13 (9 : 0, p = 0,002).
  - [descriptive] S-MLP gegen S-1519 (die 13 weiteren down_proj-Schichten): +6 pp beim Festlegen über 18 gemeinsame Funde.
  - [interpretation] Der rekurrente Teil (9 GatedDeltaNet-Spalten-Drehungen plus Gate-Zeile) trägt allein fast die ganze Wirkung, in den Treffern
    sogar mehr als SGNE-CC voll (26 gegen 22; Unterschied klein, ein Seed). Der MLP-Teil allein macht die Spuren sehr kurz und schleift wenig, findet
    den richtigen Wert aber seltener – er wirkt eher wie eine Bremse des Denkens als wie ein Festleger. Das passt dazu, dass die Drehung am MIT-Ort
    allein schwächer war als die Addition. Vorbehalt: 13–23 gemeinsame Funde, ein Seed, n = 50.
  - Prognose Claude (18.11. 17:3x): S-MLP 18 (10–25) – in der Spanne (13), Schleifen 35 % – zu hoch (20 %); S-GDN 10 (5–18) – klar verfehlt (26),
    Schleifen 60 % – zu hoch (34 %); M „offen“ getroffen; G „offen“ verfehlt („wirkt allein“).
- 20.11. 11:14 – **N41 Wiederholung mit Seed 1, Lesart vor dem Lauf** (Dave: „Ja gerne“, mit dem Hinweis: „das wäre dann Schmücken mit fremden Lorbeeren, weil es nicht unsere Methodik ist … unser Beisteuern bezieht sich bisher wohl nur noch auf B+H und Wissen ist nicht Handeln“; [interpretation] Claude: Methode bleibt seine, Nennung klar; unser Beitrag ist die Prüfung). Arme: S-GDN und SGNE-CC, Seed 1, sonst Protokoll wie N40/N41 (50 Aufgaben, 0,6, pp 1,5, 32K). Lesart [pre-registered]: **„Wirkung wiederholt“**, wenn S-GDN mit Seed 1 mindestens 20 von 50 löst UND festgelegt ≥ 0,60; sonst „nicht wiederholt“. Beschreibend: S-GDN gegen SGNE-CC in beiden Seeds (richtig, festgelegt, Schleife oder Grenze). Prognose Claude: S-GDN 23 (17–29), SGNE-CC 21 (15–27); „Wirkung wiederholt“.
- 20.11. 11:19 – **Dave zu Paper 1 v0.5**: „Ja gerne alles so einplanen. Wir könnten ihn fragen bzw. mitteilen, was wir vorhaben und das heute Abend in unserem Paper mit einer v0.5 aktualisieren mittels seiner Methode und unseren Messungen sowie neuen Erkenntnissen unter seiner Benennung.“ → Entwurf v0.5 heute (EN, DE), Hinweis an Nondual-Observer in #5 vorab (Entwurf 5d), Veröffentlichung nach Daves Go.
- 20.11. 11:25 – Auswertung Seed 1: paket/158_n41_seed1.py (f1b81e332c382dec…, nutzt 156 mit Prüfsumme), Lesart wie vor dem Lauf festgelegt; Selbsttest siehe Ausgabe.
- 20.11. 11:30 – **Dave zu v0.5 und #6**: „ehrlich und transparent“ → Base und WT-A bleiben als Vergleich in 3.13. „#6 soll keinen Einfluss auf Paper Knowing is not committing haben, aber wir könnten für #6 einen kleinen Beitragskommentar entwerfen mit Verweis auf unsere Erkenntnisse und dem Paper. Ich deute daraus auch unsere B+H-Möglichkeiten für maximalen Gewinn.“ → 6a um B+H (N30) ergänzt.
- 20.11. 11:36 – **N42 definiert und eingefroren, vor dem Rechnen**: Entwurf paket/ENTWURF_N42_BH_FESTLEGER.md (2d16869a1e800fcd…), Skript paket/159_n42_bh_festleger.py (ec054d5fe63afbc1…, nutzt […] mit Prüfsumme). Lesarten K1 (I-post + SGNE-CC) und K2 (I-post + S-GDN): richtig(B+H) − richtig(Hinterzimmer allein) ≥ +3 „Kopplung hilft“, ≤ −3 „kostet Treffer“, sonst „gleichauf“; Tokens je richtige ≤ 70 % „spart“, ≥ 130 % „kostet“. Nur vorhandene Läufe (Datenkontakt mit den Einzelläufen; neu ist ihre Kopplung). Selbsttest bestanden, Trockenlauf vollständig. **Prognose Claude:** K1 B+H 26 gegen SGNE-CC 22 „Kopplung hilft“, Tokens „kostet“; K2 B+H 27 gegen S-GDN 26 „gleichauf“, Tokens „ähnlich“.
- 20.11. 11:39 – **N42 gerechnet** (159, Ausgabe nachrechnung_mv/ergebnisse/n42_auswertung.json d228eac99bd2c500…; Zeitgrenze 0):
  - [descriptive] Intuitionen: I-post 21/24/23 (Mittel 22,7), I-eigen 22/25/26 (24,3); einstimmig je 18 Aufgaben, alle 18 richtig (100 %). Mehrheit
    (mindestens zwei gleich) abgegeben: I-post 26-mal, I-eigen 31-mal, je etwa 81 % richtig; sonst Hinterzimmer (24- bzw. 19-mal).
  - [pre-registered] **K1** I-post + SGNE-CC: 24 gegen 22 (+2) → „gleichauf“, Tokens je richtige 57.587 gegen 14.961 → „kostet Tokens“.
    **K2** I-post + S-GDN: 28 gegen 26 (+2) → „gleichauf“, 63.401 gegen 35.687 → „kostet Tokens“.
  - [descriptive] Alle Kopplungen: I-post + post 21 (gegen 5), + WT-A 25 (19), + MIT 24 (20), + SGNE-CC 24 (22), + S-GDN 28 (26); I-eigen + post 25,
    + WT-A 25, + MIT 25, + SGNE-CC 26, **+ S-GDN 30** – die höchste Zahl aller Arme auf diesen 50 Aufgaben, über der vortrainierten Base (27); Tokens je
    richtige 57.000–78.000.
  - [interpretation] B+H hebt jedes Hinterzimmer, am stärksten die schwachen (post +16, WT-A +6, MIT +4). Bei den festlegenden Hinterzimmern (SGNE-CC,
    S-GDN) bleibt der Gewinn mit +2 unter unserer Schwelle und kostet die drei Intuitionen. Die besten Zahlen erreicht die Kopplung aus unseren
    Intuitionen (eigene Richtung) und dem GatedDeltaNet-Teil (30 von 50). Einstimmige Intuitionen waren hier immer richtig – eine sparsamere Fassung
    (erst zwei Intuitionen, die dritte nur bei Uneinigkeit) liegt nahe.
  - Prognose Claude: K1 26 „hilft“ – verfehlt (24, „gleichauf“), Tokens „kostet“ getroffen; K2 27 „gleichauf“ – getroffen (28), Tokens „ähnlich“ – verfehlt.
- 20.11. 11:41 – **N43 „Sparsames B+H“ definiert und eingefroren, vor dem Rechnen** (Dave: „Das ist Hammer! … einen Test mit sparsamer Methode angehen“): paket/160_n43_bh_sparsam.py (9e79991e58cc6ccb…, nutzt 159 mit Prüfsumme; nur vorhandene Läufe wie N42). Varianten voll / sequenziell (gleiche Entscheidungen, Seed 2 nur bei Uneinigkeit) / zwei (nur Seeds 0 und 1) / einstimmig (nur bei drei gleichen). Lesart je Hinterzimmer SGNE-CC und S-GDN, mit I-post und I-eigen: „sparsam trägt“ bei richtig(zwei) ≥ richtig(voll) − 1 UND Tokens je richtige ≤ 75 % von voll; „sparsam kostet Treffer“ bei ≤ −3; sonst „offen“. Selbsttest bestanden. **Prognose Claude:** „zwei“ meist „sparsam trägt“ (−1 bis +1 Treffer, etwa 70 % der Tokens); „einstimmig“ eher mehr Treffer bei festlegenden Hinterzimmern, aber teurer.
- 20.11. 11:41 – **N43 gerechnet** (Uhrzeit berichtigt um 11:44: zuerst 11:46 geschätzt statt abgelesen) (160, nachrechnung_mv/ergebnisse/n43_auswertung.json a0ca43c9d79f4a52…; Zeitgrenze 0):
  - [descriptive] „sequenziell“ liefert dieselben Treffer wie „voll“ bei 4–8 % weniger Tokens. „zwei“ (nur Seeds 0 und 1) verliert bei den festlegenden
    Hinterzimmern 0–1 Treffer und braucht 71–88 % der Tokens; bei schwachen Hinterzimmern verliert es mehr (I-eigen + post 20 statt 25).
    „einstimmig“ bringt keine zusätzlichen Treffer und kostet mehr Tokens.
  - [pre-registered] I-post + SGNE-CC: zwei 24 = voll 24, Tokens 40.786 gegen 57.587 (71 %) → **„sparsam trägt“**. I-post + S-GDN (27 gegen 28; 85 %),
    I-eigen + SGNE-CC (25 gegen 26; 78 %), I-eigen + S-GDN (29 gegen 30; 88 %) → „offen“ (Treffer gehalten, Ersparnis unter 25 %).
  - [interpretation] Die Tokens stecken vor allem im Hinterzimmer (Läufe mit Denken), die Intuitionen sind billig; darum spart Weglassen einer
    Intuition wenig. Höchste Trefferzahl: I-eigen + S-GDN (30, 58.687 Tokens je richtige); höchste Sparsamkeit bleibt SGNE-CC allein (22, 14.961).
  - Prognose Claude: „zwei meist sparsam trägt“ – nur in einem von vier Fällen; „einstimmig mehr Treffer“ – verfehlt.
- 20.11. 11:45 – **Berichtigung zur N43-Deutung (eigener Fehler):** Die Läufe ohne Denken sind *nicht* billig. Mittlere Tokens je Lauf über die 50 Aufgaben:
  I-post 7.119 / 7.242 / 8.803, I-eigen 7.766 / 9.357 / 8.270; Hinterzimmer post 14.491, WT-A 21.479, MIT 22.898, SGNE-CC **6.583**, S-GDN 18.557.
  [descriptive] Ein SGNE-CC-Lauf mit Denken ist also billiger als ein einzelner Lauf ohne Denken der unveränderten Fassung. Darum kostet B+H mit SGNE-CC
  so viele Tokens (die drei Intuitionen), und darum spart „zwei“ dort am meisten. Der Satz „die Tokens stecken vor allem im Hinterzimmer, die
  Intuitionen sind billig“ im Eintrag 11:41 gilt nur für post, WT-A, MIT und S-GDN als Hinterzimmer, nicht für SGNE-CC.
- 20.11. 11:45 – **Nachträglich, beschreibend (nicht vorab festgelegt), Anlass Dave:** „B+H und SGNE-CC könnten MIT übertreffen, mit Blick auf die Tokens“.
  Gepaart gegen MIT allein (n41-mit-denken) auf denselben 50: SGNE-CC allein; I-post + SGNE-CC voll und zwei; I-post + MIT voll. Exakter
  McNemar (einseitig), nur zur Einordnung. Skript im Scratchpad (paar_gegen_mit.py), nutzt 159 und 160 mit Prüfsumme; keine neue Kennzahl im Bericht ohne Kennzeichnung.
- 20.11. 11:46 – **Ergebnis nachträglich, beschreibend (gegen MIT allein, 20 von 50; exakter McNemar einseitig):** SGNE-CC allein 22 (nur SGNE 3, nur MIT 1; p = 0,31);
  I-post + SGNE-CC voll 24 (6 : 2; p = 0,15); zwei 24 (5 : 1; p = 0,11); I-post + MIT voll 24 (5 : 1; p = 0,11). [interpretation] Auf 50 Aufgaben vorn, aber
  nicht belastbar. Die Token-Ersparnis gegenüber MIT kommt von SGNE-CC selbst (14.961 je richtige), B+H legt +2 Treffer bei fast vierfachen Tokens drauf.
  Innerhalb von B+H spart SGNE-CC statt MIT als Hinterzimmer 26 % (voll) bzw. 39 % (zwei) der Tokens je richtige bei gleichen Treffern. Entwurf 5e für #5.
- 20.11. 12:15 – **Dave: Go für die Nacht** („Ja lass uns das so für die Nacht eintakten“): Laptop nach Seed 1 mit N44 (SGNE-CC auf nacht150, 150 Aufgaben aus N30) und N45 (100 frische MATH-Trainingsaufgaben; Berater = unverändertes Modell ohne Denken, Seeds 0–2; SGNE-CC und MIT mit Denken), bis in die Nacht. Gespräch morgen Vormittag; v0.5 morgen, vorbereitet mit Platzhaltern; Nondual-Observer bekommt mehr Zeit für eine Antwort auf 5d. Keine Prognose von Dave (nicht abgegeben).
- 20.11. 12:26 – **N44 und N45 „B+H mit SGNE-CC gegen MIT“ definiert und eingefroren, vor dem ersten Lauf** (Dave 20.11.: „A + B (100 statt 50), das kann
  dann auch in die Nacht rein laufen“; Go: „Ja lass uns das so für die Nacht eintakten“). Entwurf paket/ENTWURF_N44_N45_BH_SGNE.md. Prüfsummen: ENTWURF_N44_N45_BH_SGNE.md b848e3d21cfb682a…; 161_n45_frisch100.py cc6abc5e5cf3805d…; 162_n44_n45_bh_sgne.py 4973d2cbe70ade32…; kette_n44n45_laptop.sh d826171429cbad4a…; wecker_n44n45.sh c05e4fec17009506….
  - N44: SGNE-CC mit Denken auf den 150 Aufgaben aus N30 (neu), Berater I-eigen, MIT und N30-B+H vorhanden. N45: 100 frische Aufgaben, gezogen mit 161
    um 12:21 ohne Modellkontakt (Stufen 8/18/21/26/27, Seed 202611201; Aufgaben 55af5f7b30889a5c…, Kennungen 32387a4f31f4b203…; Überschneidung mit
    basis50 und nacht150: 0); neu: Berater I-post Seeds 0–2 (Antwortmodus, 03b), SGNE-CC und MIT mit Denken. Alles Laptop, Blöcke zu 25.
  - Lesarten [pre-registered, je Satz]: H1 sparsam + SGNE-CC gegen MIT allein („übertrifft MIT“ / „hinter MIT“ bei p < 0,05 einseitig, sonst
    „gleichauf“; Tokens je richtige ≤ 70 % „spart“, ≥ 130 % „kostet“, sonst „ähnlich“); H2 ebenso gegen SGNE-CC allein („B+H legt zu“ / „B+H kostet
    Treffer“ / „gleichauf“); H3 sparsam gegen voll (≥ −round(0,02 n) und ≤ 75 % Tokens „sparsam trägt“; ≤ −round(0,06 n) „sparsam kostet Treffer“;
    sonst „offen“). Alles Weitere beschreibend; beide Sätze zusammen nur beschreibend.
  - […]
  - Reihenfolge der Kette: Erholungspause | N44 SGNE-CC | Pause | N45 Berater s0, s1 | Pause | SGNE-CC | Pause | MIT | Pause | Berater s2.
    Start nach dem Ende der Seed-1-Kette; Auswertung erst morgen mit Dave (N44 und N45 gemeinsam).
  - **Prognose Claude (verdeckt; Dave hat keine abgegeben):** N44: SGNE-CC allein ≈ 70/150, sparsam ≈ 78; H1 knapp „übertrifft MIT“ (Δ ≈ +11,
    p ≈ 0,04), Tokens „ähnlich“ (≈ 80 % von MIT); H2 „gleichauf“, Tokens „kostet“; H3 knapp „sparsam trägt“. N45: MIT ≈ 40, SGNE-CC ≈ 44,
    sparsam ≈ 48 von 100; H1 „gleichauf“, Tokens knapp „spart“ (≈ 67 %); H2 „gleichauf“, „kostet Tokens“; H3 „offen“ oder knapp „trägt“.
- 20.11. 12:56 – Dave: „jap alles kontrolliert und go“ (Windows-Updates für die Nacht geprüft; Go für die Nacht mit Seed 1, N44, N45).
- 20.11. 12:58 – **HF #5, Antwort von Nondual-Observer auf 5d** (nachgelesen): möchte mit Klarnamen genannt werden, „Igor M. Zhuk (SGNE-CC)“ (oder „Igor Zhuk /
  Nondual-Observer (SGNE-CC)“), mit Links zum Modell und zu #2 und #5; **keine Vorabprüfung nötig**, „publish whenever you are ready“. Er bestätigt die
  Zerlegung (GatedDeltaNet trägt im hybriden 0.8B). […] Für Paper 1 ohne Folgen (nur 0,8B); Nennung in v0.5 nach Daves Entscheidung anpassen. Entwurf 5f (kurze Antwort).
- 20.11. 13:37 – **Seed-1-Kette fertig** (13:36:32; n41-sgdn-denken-s1 und n40-sgne-denken-s1 je 50 Zeilen, Server gestoppt). **Nachtkette N44/N45 gestartet** 13:36:57 (paket/kette_n44n45_laptop.sh, Prüfsummen der GGUFs und der Aufgaben bestanden, Kettenprozesse laufen), beginnt mit Erholungspause; Wächter paket/wecker_n44n45.sh gestartet.
- 20.11. 13:39 – **N41 Seed 1 gerechnet** (158 f1b81e33…, gespiegelt 13:37, Ausgabe nachrechnung_mv/ergebnisse/n41_seed1_auswertung.json, Einzelzeilen
  ergebnisse/n41_seed1_einzelzeilen.csv, Log logs/158_seed1_rechnen.log; Zeitgrenze: 0 nicht prüfbar):
  - [pre-registered] S-GDN Seed 1: **29 von 50**, festgelegt **0,78** → **„Wirkung wiederholt“**.
  - [descriptive] SGNE-CC Seed 1: 20 von 50, festgelegt 0,81, Schleife oder Grenze 8 %, 17.373 Tokens je richtige. S-GDN Seed 1: Schleife oder Grenze 30 %,
    29.488 Tokens je richtige, richtiger Wert im Denken 37. S-GDN gegen SGNE-CC (Seed 1) 29 gegen 20, 11 : 2, p = 0,011; S-GDN Seed 1 gegen Seed 0
    29 gegen 26 (5 : 2).
  - [interpretation] In beiden Seeds löst der GatedDeltaNet-Teil allein mehr als der volle Edit (26 und 29 gegen 22 und 20) und findet den richtigen Wert
    öfter (35 und 37 gegen 20 und 16); der volle Edit legt sich etwas häufiger fest, schleift kaum und braucht weniger Tokens. Der MLP-Teil wirkt
    wie eine Bremse, die Länge spart und Treffer kostet (wie in der Deutung von 3.13).
  - Prognose Claude (11:14): S-GDN 23 (17–29), SGNE-CC 21 (15–27), „Wirkung wiederholt“ – Urteil getroffen; S-GDN am oberen Rand, SGNE-CC getroffen.
- 20.11. 13:41 – Nennung umgestellt (nennung_zhuk.py): im Fließtext „Igor M. Zhuk“, Handle Nondual-Observer nur noch in Kennungen, beim ersten Nennen in 3.13, im Dank und in der Quelle; betrifft v0.5 EN/DE, results/n40-sgne-cc/README.md (bisher veröffentlicht mit „Nondual-Observer“, Änderung kommt mit dem v0.5-Commit), results/n41-ablations/README.md, baue_results.py. Grundlage: sein Wunsch in #5 und Daves gepostete Antwort 5f.
- 20.11. 15:36 – **N44 fertig** (n44-sgne-nacht150: 150 Zeilen, 15:35:28); Erholungspause, dann N45. N44 verblindet in den Spiegel kopiert und neu bewertet (162 --spiegeln n44; nur Prüfsummen ausgegeben, keine Kennzahl). Wächter neu gestartet.
- 21.11. 03:25 – **Nachtkette N44/N45 fertig** (03:24:55; ohne FEHLER und ohne WARNUNG im Kettenlog; alle sechs neuen Läufe vollständig: N44 150, N45 je 100; Server gestoppt).
  N45 verblindet in den Spiegel kopiert und neu bewertet (162 --spiegeln n45; nur Prüfsummen, keine Kennzahl). **Nicht ausgewertet** – Auswertung
  (162 --rechnen n44 n45) morgen Vormittag mit Dave, vorher Gelegenheit für Daves Prognose. Laptop-GPU frei.
- 21.11. 11:23 – Dave: „wir rechnen gleich“ (keine Prognose von Dave). Start der Auswertung 162 --rechnen n44 n45.
- 21.11. 11:48 – **N44 und N45 gerechnet** (162 4973d2cb…, 11:23 bis spätestens 11:47; Ausgaben n44_auswertung.json 1297ddb8…, n45_auswertung.json 492f1632…,
  n44_n45_gesamt.json 51159847…, ergebnisse/n44_n45_einzelzeilen.csv 8b9ff66f…; Log logs/162_rechnen.log; Gleichheit: 0 nicht prüfbar; Festlegen: 7 Kandidaten
  an der Zeitgrenze, als ungleich gezählt, nur beschreibend betroffen):
  - **N44** (150 Aufgaben aus N30, Berater I-eigen) [pre-registered]: H1 sparsam + SGNE-CC gegen MIT 70 gegen 67 (14 : 11, p = 0,35) → **„gleichauf“**,
    Tokens je richtige 47.676 gegen 49.089 (97 %) → „ähnlich“. H2 gegen SGNE-CC allein 70 gegen 62 (10 : 2, p = 0,019) → **„B+H legt zu“**, Tokens 3,2-fach →
    „kostet Tokens“. H3 sparsam 70 gegen voll 78 (−8; Schwellen −3/−9), 83 % der Tokens → „offen“.
  - **N45** (100 frische Aufgaben, Berater I-post) [pre-registered]: H1 sparsam + SGNE-CC gegen MIT **59 gegen 49** (18 : 8, p = 0,038) → **„übertrifft MIT“**,
    Tokens je richtige 31.342 gegen 44.715 (70,1 %, knapp über der Schwelle 70 %) → „ähnlich“. H2 gegen SGNE-CC allein 59 gegen 52 (9 : 2, p = 0,033) →
    **„B+H legt zu“**, Tokens 2,7-fach → „kostet Tokens“. H3 sparsam 59 gegen voll 61 (−2; Schwelle −2 erfüllt), aber 83 % der Tokens → „offen“.
  - [descriptive] Volles B+H + SGNE-CC gegen MIT: N44 78 gegen 67 (17 : 6, p = 0,017), N45 61 gegen 49 (18 : 6, p = 0,011). SGNE-CC allein gegen MIT: N44 62
    gegen 67, N45 52 gegen 49, bei 14.882 bzw. 11.736 Tokens je richtige (MIT 49.089 bzw. 44.715). Festgelegt: SGNE-CC 79 % / 82 %, MIT 69 % / 60 %;
    Schleife oder Grenze SGNE-CC 5 % / 3 %, MIT 45 % / 37 %. Berater allein: I-eigen 69/72/65 von 150, I-post 58/48/46 von 100. N44 gegen N30-B+H (WT-A):
    voll 78 gegen 77 (3 : 2), sparsam 70 gegen 77 (5 : 12). Beide Sätze zusammen (250): sparsam 129 gegen MIT 116 (32 : 19, p = 0,046).
  - **Prognose Claude (20.11. 12:2x) gegen Ergebnis:** N44 H1 „knapp übertrifft“ → gleichauf (verfehlt), H2 „gleichauf“ → legt zu (verfehlt), H3 „knapp
    trägt“ → offen (verfehlt), Tokens H1 „ähnlich“ getroffen; SGNE-CC allein 70 → 62, sparsam 78 → 70 (zu hoch). N45 H1 „gleichauf“ → übertrifft MIT
    (verfehlt, zu vorsichtig), Tokens „knapp spart (≈ 67 %)“ → 70,1 % „ähnlich“ (knapp verfehlt), H2 verfehlt, H3 „offen“ getroffen; MIT 40 → 49,
    SGNE-CC 44 → 52, sparsam 48 → 59 (alle zu niedrig).
  - [interpretation] Daves These hält auf den frischen Aufgaben: sparsames B+H mit SGNE-CC übertrifft MIT (vorab festgelegt, einseitig, nicht für
    mehrere Lesarten korrigiert) bei etwa 70 % von MITs Tokens je richtige Antwort; auf den 150 N30-Aufgaben nur gleichauf, dort trägt erst die volle Regel
    (78 gegen 67, beschreibend). In beiden Sätzen legt B+H gegenüber SGNE-CC allein Treffer zu, kostet aber das 2,7- bis 3,2-Fache an Tokens. Den Token-
    Vorteil gegenüber MIT bringt SGNE-CC; die Treffer über SGNE-CC hinaus bringt das Vorderzimmer.
- 21.11. 13:15 – Dave: „Ja, übernehmen“ – Deutung und Kurztexte zu 3.14 gesetzt (texte_314.py); keine Platzhalter mehr in v0.5 EN/DE.
- 21.11. 14:08 – **Gutachten Gemini Neon zu v0.5** (von Dave eingefügt) abgelegt: recherche/gutachter/2026-11-21/. Fünf Muss-, sieben Sollte-Punkte; Prüfung am Text und an den Daten folgt, v0.5 bis dahin nicht veröffentlicht.
- 21.11. 14:11 – **Nachträglich, beschreibend (Anlass Gutachten Gemini Neon, Frage 3: treibt Seed 0 das sparsame B+H in N45?):** sparsames B+H + SGNE-CC mit allen drei Berater-Paaren (0,1), (0,2), (1,2), in N44 und N45, gegen MIT allein (diskordante Paare, ohne p-Wert). Nicht vorab festgelegt; geht nur beschreibend in 3.14 ein. Skript veroeffentlichung/v0.5/paare_sparsam.py (nutzt 162 mit Prüfsumme).
  - Ergebnis (beschreibend): sparsam + SGNE-CC je Paar (0,1)/(0,2)/(1,2): N44 70/70/74 von 150 (MIT 67; 14:11, 14:11, 13:6), N45 59/55/57 von 100 (MIT 49; 18:8, 16:10, 16:8). Das vorab festgelegte Paar (0,1) ist in N45 das beste der drei; alle drei liegen vor MIT.
- 21.11. 14:15 – **Gutachten Gemini Neon eingearbeitet** (gutachten_neon_v05.py; Prüfung je Punkt in veroeffentlichung/v0.5/EINARBEITUNG_GUTACHTEN_v0.5.md): zutreffend und eingearbeitet: neun Spalten → 1.182 Spalten in neun Schichten (eigener Fehler); richtig ohne Fund (SGNE-CC 6/7, S-MLP 2, WT-A 2, S-GDN 1/0) mit Erklärung, L definiert; „sparsam“ in Kasten, Kurzfassung, README, CITATION; p-Werte aus beschreibenden Zeilen in 3.14 gestrichen; unverändertes Vorderzimmer und Seed-Paare beschreibend in 3.14, Zusatz in 3.10; N41 über gemeinsame Funde; Base-Vorlage; Schleifen-Abbruch, Aufgabensätze und Holm-Umfang in Abschnitt 2; Abschnitte 4, 6, 7 nachgezogen; Status-Satz; Schreibweise GatedDeltaNet; DE „je richtige Antwort“; Tabelle 3.8 mit vollen Zellen. Nicht zutreffend: κ = 7 (steht so im PDF), \binom (wörtliches Modellzitat), DE-Reihenfolge 3.11 (Quelltext korrekt). Offen: TL;DR 9 (15.500 gegen 36.800, Herkunft nicht gefunden; älterer Text).
