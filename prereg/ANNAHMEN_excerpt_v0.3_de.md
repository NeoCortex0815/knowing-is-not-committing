# Auszug aus dem Protokoll der Vorab-Festlegungen (08.11.2026, 19:53, bis 09.11.2026, 10:41)

*Zum Bericht v0.3. Die vollständige Kopie des Protokolls bis 08.11., 19:42, liegt daneben in ANNAHMEN_pre-registration-log_de.md.
Dieser Auszug enthält die späteren Einträge, die N30, N31 und den Bericht v0.3 betreffen, wörtlich. Andere Einträge dieses
Zeitraums fehlen; Stellen, die spätere Arbeiten betreffen, sind mit „[…]“ gekürzt. Rechnernamen, Pfade und Angaben zu privaten
Systemen sind wie in der vollständigen Kopie bereinigt.*

*Die eingefrorenen Definitionsdateien von N31 (MEILENSTEIN2_N31_N32.md, MEILENSTEIN2_ZUSATZ_WREN.md und
MEILENSTEIN2_ZUSATZ2_WREN_REF.md) erscheinen mit der nächsten Arbeit. Ihre SHA-256 stehen schon hier, in den Einträgen von 22:06,
22:44 und 23:05 am 8. 11.*

---

- 08.11. 19:53 – **GitHub: v0.2 hochgeladen** (Nutzer: „Go“).
  - Repo github.com/NeoCortex0815/knowing-is-not-committing, öffentlich, Zweig main, Commit 18ec64c, 319 Dateien. Die
    Anmeldung beim Hochladen hat der Nutzer selbst bestätigt.
  - Von außen geprüft: alle 319 Dateien im Baum; Lizenz als Apache-2.0 erkannt; Autor über die Noreply-Adresse mit dem Konto
    verknüpft; Berichte, PDFs und Protokoll erreichbar; Issues offen.
  - Die Protokoll-Kopie im Repo reicht bis 19:42; dieser Eintrag folgt danach.
  - Nächste Schritte: Zenodo für das Repo freischalten, dann Release v0.2 auf GitHub (vergibt die DOI).
- 08.11. 20:01 – **Release v0.2 veröffentlicht, DOI vergeben.**
  - GitHub-Release v0.2 (Tag auf Commit 18ec64c, kein Pre-release), vom Nutzer um 19:58 veröffentlicht.
  - Zenodo hat es sofort archiviert:
    - Konzept-DOI (alle Versionen) **10.5281/zenodo.24058693**;
    - Versions-DOI v0.2 **10.5281/zenodo.24058694**.
  - Eintrag geprüft: Titel und Stichwörter aus CITATION.cff, Autor „Uhlemann, Dave“, Software, Apache 2.0, frei zugänglich,
    ZIP 2,3 MB, Verweis auf den GitHub-Stand v0.2. Beide DOIs lösen auf.
  - README: DOI-Badge und Zitierhinweis (lokaler Commit, Hochladen nach Nutzer-Go).
  - CITATION.cff bleibt vorerst ohne DOI. Zenodo liest diese Datei bei jedem Release; ein DOI-Feld darin prüfen wir vor v0.3.
  - Entwürfe (Hugging Face, MIT-Mail) tragen die Konzept-DOI. Die PDF-Links zeigen auf den festen Stand v0.2 statt auf main.
- 08.11. 21:46 – **VORSCHLAG Vorab-Lesart (N31) „Kopplung Wissen → Festlegen“ (Roadmap Punkt 6).** Gilt erst mit Nutzer-Go und wird vor
  jeder Auswertung festgelegt; das Skript (111_) läuft bis dahin nur trocken.
  - **Frage:** Folgt die *eigene* Festlegungs-Neigung des Modells seinem Wahrheitssignal? Das ist die Mechanik hinter „Wissen ist
    nicht Festlegen“.
  - **Daten:** nur die vorhandene Zuck-Messung 82, keine neue Messung, je 140 Läufe 161–300 (Seed 0):
    - WT-A-Texte mit dem WT-A-Modell; die Ablation ohne die 16 WT-Neuronen entspricht ≈ eigen;
    - MIT-Texte mit dem MIT+WT-Modell; die Ablation entspricht MIT allein.
    - Einheit: Wert-Aussagen im Denken, deren Wahrheit bekannt ist.
  - **Größen:**
    - Wissen K = zT_max;
    - Festlegen F = log10(max(p_t_abl, p_arg_abl)), die rohe Wahrscheinlichkeit für </think> ohne Reflex.
  - **Kennzahlen:** AUC(F; richtig gegen falsch) je Quelle, zum Vergleich AUC(K) auf denselben Aussagen. Cluster-Bootstrap über
    Läufe, 10.000 Ziehungen, Seed 20261109.
  - **Lesarten:**
    - (H6a) eigen: AUC_F < 0,60 bei AUC_K ≥ 0,75 → „Wissen ohne Festlegen bestätigt“; AUC_F ≥ 0,70 → „widerlegt“; sonst „offen“.
    - (H6b) MIT: AUC_F ≥ 0,70 → „MITs Ausgang koppelt an Wahrheit“; AUC_F < 0,60 → „MIT ebenfalls entkoppelt“; sonst „offen“.
    - (H6c) AUC_F(MIT) − AUC_F(eigen) ≥ 0,10 mit 95-%-KI ohne 0 → „MIT koppelt stärker“; KI enthält 0 → „kein Unterschied
      nachweisbar“.
  - **Vorab bekannt (offengelegt):**
    - die Abschluss-Orte aus 82: MIT natürlich 36 am richtigen, 48 am falschen Wert; WT-A natürlich 4 / 15;
    - die Horizont-Tabellen von zT.
    - Die Kopplung F~K je Aussage wurde nie ausgewertet.
  - **Beschreibend:** Spearman(K, F) unter den richtigen Aussagen; dieselben Kennzahlen mit der gezogenen Wahrscheinlichkeit (ps);
    nach Tiefe.
  - **Folge (vorab):**
    - H6b koppelt → MITs Vorteil liegt in einer Kopplung von Wissen und Festlegen. Nächster Bau: diese Kopplung im eigenen
      Hinterzimmer (innerer Ausgang).
    - Beide entkoppelt → MIT legt sich aus anderen Gründen fest (Schilder, Prüf-Phrasen). Der Fokus geht dann auf Schilder.
- 08.11. 21:50 – **Skripte für N31 und N32 vorbereitet, nur trocken gelaufen, keine Kennzahl berechnet.**
  - 111_kopplung.py --trocken: eigen 140 Läufe mit 43.848 Aussagen (2.468 richtig); MIT 140 Läufe mit 65.713 Aussagen
    (4.262 richtig). Alle haben Ablationswerte.
  - Die Rang- und AUC-Funktion ist nur an Spielzahlen geprüft (vektorisiert, 11 ms je Rangberechnung).
  - […]
  - Die echten Läufe folgen erst nach Nutzer-Go und wenn der Laptop frei ist.
- 08.11. 21:52 – **Selbsttests der Methoden N31/N32 bestanden** (Nutzer: „unsere Hinweise und Methodik … in erste kleine Scripts,
  Trockentests verlagern und für die nächsten Tage vorbereiten“). Künstliche Daten mit bekannter Antwort; die echten Daten sind
  unberührt, es gibt keine Ergebnisdateien kopplung_N31.json bzw. ahnenforschung_N32.json.
  - […]
  - 111 --selbsttest:
    - Fall gekoppelt gegen entkoppelt: H6a bestätigt, H6b koppelt, H6c MIT stärker (Δ 0,47).
    - Fall zweimal entkoppelt: H6b entkoppelt, H6c kein Unterschied (Δ −0,01; KI −0,04 bis +0,03).
- 08.11. 22:06 – **N31 und N32 eingefroren: Meilenstein 2 nach N30** (Nutzer: „Bitte diese Definition von N31 und N32 als extra .md
  einfrieren: das ist ein gutes Setup für unseren zweiten Meilenstein nach N30“).
  - Die Vorschläge von heute Abend gelten damit als Vorab-Lesarten; Definition in Worten und technisch in
    paket/MEILENSTEIN2_N31_N32.md.
  - SHA-256 der Definition: 0794e241bdeb06a5b8efa3c4691eefc98471e10bc30b22d135b431e6c078e6ef
  - Skripte, eingefroren mit: 110_ahnenforschung.py 1494848a891187047ed5770c7192e6119d88f6507832a4ba86847be137a51f29; 111_kopplung.py 1a44bfb743a12a36de1abee7f6891ba829170530adcc410ff352fce26f795554
  - Beim Einfrieren gibt es keine Ergebnisse (kopplung_N31.json und ahnenforschung_N32.json existieren nicht). Gerechnet wird nach
    N30, wenn der Laptop frei ist.
- 08.11. 22:14 – **Prognose Claude vor dem N30-Ergebnis** (Nutzer: „Was denkst du, wo werden wir liegen?“). Festgehalten zum
  späteren Abgleich.
  - Blind: Keine Zwischenergebnisse angesehen. Nur zwei Einzelzeilen (je eine Aufgabe, „OK“) erschienen zufällig in einer
    Logausgabe.
  - **Grundlage, nur Daten vor N30:**
    - N27 (161–260): Mehrheit + WT-A = 62, INT Seed 0 = 57, MIT = 58 auf 100; Mehrheit aus drei mit 89 % Präzision bei 62 %
      Abdeckung.
    - Zwei Intuitionen: 37/38, 13/17 auf *Trainingsaufgaben* (neu40), 28/31.
    - N28: 40 gegen MIT 38.
  - **Abschlag:** B+H wurde nach dem Blick auf 161–260 gewählt (Auswahl-Effekt). Außerdem sind es Trainingsaufgaben, und neu40
    zeigte dort die schwächste Einigkeit. Deshalb erwarte ich etwa den halben Vorsprung aus N27.
  - **Erwartung auf 150:** B+H − INT ≈ +5, B+H − MIT ≈ +3; Präzision der Einigkeit ≈ 85 %.
  - **Wahrscheinlichkeiten (subjektiv):**
    - H1: trägt ~55 %, offen ~25 %, widerlegt ~20 %.
    - H2: schlägt MIT ~10 % (braucht wegen McNemar etwa +12), mindestens gleichauf ~55 %, offen ~23 %, unter MIT ~12 %.
    - H3: hält ~55 %, offen ~35 %, widerlegt ~10 %.
    - H4: trägt ~50 %, offen ~30 %, trägt nicht ~20 %.
  - **Wahrscheinlichstes Bild:** MIT-Niveau mit eigenem System auf frischen Aufgaben, aber nicht darüber. Die Einigkeit liegt
    knapp an der 85-%-Linie. Tokens je richtiger Antwort über MIT (wie N28).
- 08.11. 22:14 – **Nutzer-Go: N31 und N32 rechnen heute Nacht im freien Laptop-Fenster** („ja bitte“).
  - kette_tag_laptop12.sh läuft im Hintergrund. Sie wartet auf „Tagesplan Laptop (o) Nachtlauf fertig“ (die Server sind dann
    gestoppt), dann laufen 111 und 110 unverändert gegenüber den eingefrorenen Prüfsummen.
  - Meilensteine gehen ins Ketten-Log, der Wächter wird dadurch geweckt.
  - **Abweichung in der Reihenfolge (vermerkt, wie für Abweichungen vereinbart):** Der Ablauf in MEILENSTEIN2_N31_N32.md nennt
    „1. N30 abwarten“. N31/N32 rechnen nun im Fenster nach den Laptop-Läufen, *bevor* das N30-Urteil vorliegt (MiniPC bis
    ~3:30–4 Uhr). Inhaltlich unabhängig: N31 nutzt die Zuck-Messung 82, N32 nur Gewichte; Lesarten, Daten und Schwellen
    unverändert.
- 08.11. 22:32 – **WRENs Durchsicht von Meilenstein 2 erhalten** (vom Nutzer vorgelegt). Abgelegt unter
  recherche/gutachter/2026-11-08/WREN_2225_Meilenstein2_N31_N32.txt. **WRENs Wetten, festgehalten vor jeder Rechnung:**
  - N31: AUC_F eigen 0,52–0,62, MIT 0,55–0,68, eher „offen“. MITs Kopplung wohnt an den Schildern: AUC_F, eingeschränkt auf
    Stellen nahe eigener Abschluss-Formeln, bei MIT ≥ 0,70, über alles nicht.
  - […]
  - Geprüft: Die von WREN vermutete Schwäche der K-Bedingung stimmt. 82 weist AUC_zT = 0,683 (WT-A-Texte) und 0,726 (MIT-Texte)
    auf denselben Aussagen aus. Die eingefrorene H6a-Bedingung „AUC_K ≥ 0,75“ hätte H6a für eigen nie bestätigen können.
    Fehler in meiner Lesart: Der bekannte Wert war vor dem Einfrieren nicht nachgesehen worden.
  - Ablation in 82: Die 16 Aktivierungen werden auf 0 gesetzt (stummgeschaltet), nicht auf die Originalgewichte zurückgesetzt.
    Weil es stille Neuronen sind, ist das ≈ eigen bzw. MIT, aber nicht exakt.
- 08.11. 22:44 – **Zusatz zu N31/N32 vor dem Datenkontakt eingefroren** (Nutzer: „Ja, einbauen“; nach WRENs Durchsicht).
  - Datei paket/MEILENSTEIN2_ZUSATZ_WREN.md, SHA-256 ff3ac8ba873811dfd7d956444204d7c6afd6d63b45b548663947b9027297f3ac
  - Die ursprüngliche Definition ist unverändert; SHA-256 weiterhin 0794e241bdeb06a5b8efa3c4691eefc98471e10bc30b22d135b431e6c078e6ef
  - Skripte neu eingefroren: 110_ahnenforschung.py 5400caac096637495730353c4ea477cb917abd100b95ca4538846ef7bba51f67; 111_kopplung.py e815f93de2cc99ed991decbc3b9398efd8ae6f487e19adb0e21c1f0dde41b1ea
  - **N31:** H6a liest nur F, K bekommt Bänder (bekannt: 0,683 / 0,726 → „schwach“); vollständige Deutungsmatrix; neue Schild-Messung
    (eigen 1.004, MIT 733 Aussagen hinter Schildern); Einschränkungen zu Zeitpunkt, Trajektorien, Ablation und Zählung (37).
  - […]
  - **Probe beim Bau** (kein Urteil): MITs ΔW ist Rang 1 auf 64 Spalten (L15, L19); Kosinus eigen–MIT 0,757 / 0,773, wie im
    Bericht 0,76 / 0,77.
  - Beide Selbsttests bestanden; keine Ergebnisdateien vorhanden. Die Kette startet unverändert gegen 1:50 Uhr.
- 08.11. 23:05 – **Zweiter Zusatz zu N31/N32 vor dem Datenkontakt eingefroren** (nach WRENs Referenz-Nachbau; […]).
  - Datei paket/MEILENSTEIN2_ZUSATZ2_WREN_REF.md, SHA-256 14a98d8253b2cae9079b902419f959cc6b98934e00a567fad138039684c2dc87
  - 111_kopplung.py neu eingefroren: a9e6547e415c2b1b0ba2a2bcc18fc36756668951d85b4a0ddb76769fffbdac2d
  - 110_ahnenforschung.py unverändert: 5400caac096637495730353c4ea477cb917abd100b95ca4538846ef7bba51f67
  - **Neu (nur N31):** H6c „eigen koppelt stärker“ (spiegelbildlich, WREN A13); Ziehungen ohne beide Klassen werden gezählt (A4).
  - Die 15 offenen Stellen aus WRENs AMBIGUITAETEN.md sind ausdrücklich beantwortet. A8 (Kosinus) weicht bewusst von WRENs Nachbau
    ab, Begründung im ersten Zusatz.
  - Selbsttest 111: 5 von 5 Fällen richtig. Keine Ergebnisdateien.
  - WRENs Paket ist abgelegt unter recherche/gutachter/2026-11-08/WREN_ref_N31_N32/; seine Skripte wurden nur gelesen, nicht
    ausgeführt.
  - […]
- 08.11. 23:35 – **Verwandte Arbeit, vom Nutzer gefunden:** Li, Yan, Arish, Banerjee: „Knowing Is Not Choosing: What Explicit
  Verification Adds Beyond Generative Preference“, arXiv 2609.33142 (v1 27.09.2026, v2 29.09.2026, cs.CL). Bisher nur die
  Zusammenfassung gelesen.
  - Inhalt: Faktenwissen zerlegt in Erzeugen, Ordnen und Auswählen. Signale vor dem Erzeugen sagen das Wissen voraus, nicht die
    Auswahl. Eine ausdrückliche Prüfung (P(True)) verbessert die Auswahl, bei Gemma, Qwen3 und Llama; in einer vorab festgelegten
    Gemma-Gruppe +5 Punkte Mehrheits-Genauigkeit. Ergebnisse hängen von der Definition von „richtig“ ab.
  - Einordnung:
    - Titel und Grundthese sehr nah an […] und sechs Wochen älter, deshalb zu zitieren. Gegenstand und Werkzeuge sind
      verschieden (keine Gewichts-Edits, keine Denkschleifen, keine Sonde im Denkverlauf). Die eigenen Merkmale bleiben.
    - […]
  - Offen: ob der Verweis schon in v0.3 kommt (Zuschreibung wegen des nahen Titels) oder mit den Nachkorrekturen. Entscheidet der
    Nutzer. Vor dem Zitieren den Volltext lesen.
- 08.11. 23:37 – **Nutzer-Entscheidung: Li et al. 2026 wird schon in v0.3 zitiert** („Ja, schon in v0.3“): ein Satz im Hintergrund plus
  Literatureintrag. Der Wortlaut EN/DE steht in veroeffentlichung/v0.3/BAUSTEINE_v0.3.md.
  - Grund: faire Zuschreibung beim sehr nahen, älteren Titel. Das ist keine inhaltliche Nachkorrektur.
  - **Volltext (etwa zur Hälfte gelesen):**
    - Modelle: Gemma 2 (2B/9B/27B), Qwen3-8B, Llama 3.1 8B; dazu Qwen3.5-2B/4B, Qwen3.6-27B, Qwen3.8-27B.
    - Daten: kurze Faktenantworten (Wikidata, 600 frische Fragen); „Wissen“ = Abdeckung unter K Stichproben.
    - Innere Auslesungen (Mittelwert-Richtung, SAE-Merkmal) sagen die Abdeckung voraus (AUROC 0,69–0,82), helfen aber kaum bei der
      Wahl (+0,006–0,015).
    - P(True) verbessert die Ordnung (+0,078–0,119 AUROC) und die Mehrheits-Genauigkeit bei Gemma um ~5 Punkte.
    - Keine Denkmodelle, kein Denkblock, kein Festlegen.
- 09.11. 00:18 – **Nutzer-Entscheidung: Farquhar et al. 2024 (semantische Entropie, Nature 630:625–630) wird schon in v0.3 zitiert** („Ja, auch in v0.3“). Ein Satz in Abschnitt 3.10 bei der Beratung der Intuitionen plus Literatureintrag; Wortlaut EN/DE in veroeffentlichung/v0.3/BAUSTEINE_v0.3.md. Grund: die engste Vorarbeit zur Beratung der Intuitionen, bisher nicht zitiert. Vor dem Einloggen die Zusammenfassung im Original lesen.
- 09.11. 01:56 – **Prognose Claude vor N31 und N32** (blind, festgehalten zum späteren Abgleich). Beim Schreiben existieren weder
  kopplung_N31.json noch ahnenforschung_N32.json; N31/N32 sind nicht gestartet (der MIT-Lauf von N30 läuft noch). Keine
  Zwischenergebnisse angesehen.
  - **N31** (Lesarten wie eingefroren, mit beiden Zusätzen):
    - H6a eigen: „Festlegen blind“ ~50 %, „offen“ ~40 %, „gekoppelt“ ~10 %.
    - H6b MIT: „offen“ ~45 %, „ebenfalls entkoppelt“ ~40 %, „koppelt an Wahrheit“ ~15 %.
    - H6c: „kein Unterschied nachweisbar“ ~60 %, „MIT koppelt stärker“ ~25 %, „offen“ ~10 %, „eigen koppelt stärker“ ~5 %.
    - Am Schild (MIT): „offen“ ~45 %, „koppelt am Schild“ ~30 %, „blind am Schild“ ~25 %.
    - Begründung: MITs schnelle Abschlüsse sind auf 161–300 nur zu 44 % richtig (v0.2); MITs Vorteil sehe ich eher im längeren
      Prüfen und eigenen späten Abschluss als in einer Kopplung von Wissen und Festlegen.
    - Wahrscheinlichstes Bild: beide eher blind, Deutung „beide blind“; die Schilder rücken in den Mittelpunkt.
  - […]
- 09.11. 02:00 – **Abweichung: Einzelwerte von N30 unbeabsichtigt gesehen.** Beim Prüfen, ob N31/N32 starten, habe ich das Ende des
  Ketten-Logs ausgegeben. Die Zeilen „fertig nacht150-wta“ und „fertig nacht150-mit“ enthalten die Zusammenfassung des Laufs, also
  den Anteil richtig je Arm (WT-A und MIT mit Denken). Die Regel B+H und der Antwortmodus (MiniPC) waren nicht darunter; ein Urteil
  H1–H4 ist daraus nicht ablesbar.
  - Folgen: keine. Meine N30-Prognose steht seit 08.11. 22:14, die Prognose zu N31/N32 seit 01:56. Lesarten, Daten und Skripte
    bleiben unverändert.
  - Damit Dave blind lesen kann, stehen die Werte hier nicht. Sie stehen im Ketten-Log; er entscheidet am Morgen, wann er sie liest.
  - Vorkehrung: Ab jetzt gebe ich vom Ketten-Log nur noch Zeilen mit „==“ aus (Meilensteine ohne Zahlen).
- 09.11. 08:49 – **Lesesitzung mit Dave beginnt. Daves N30-Prognose, vor dem Öffnen** (abgefragt 08:46–08:49; alle
  Ergebnisdateien ungeöffnet): H1 „trägt“; H2 „offen“; H3 „offen“; H4 „trägt“. Ohne Prozentangaben.
  - Dave kannte dabei Claudes Prognose (Lesemappe) und die Abweichung von 02:00, nicht aber die Werte selbst.
- 09.11. 08:51 – **N30 gemeinsam mit Dave geöffnet** (ergebnisse/nacht150.json, logs/109_nacht150.log; Urteile nach der Lesart vom
  08.11. 18:43).
  - Richtig von 150: B+H 74 | INT Seed 0 66 (Seeds 1/2: 68/60) | MIT 67 | WT-A 59 | Mehrheit + MIT-Hinterzimmer 75.
  - **H1 „trägt“** (74 gegen 66, +8).
  - **H2 „mindestens gleichauf“** (74 gegen 67, +7; nur B+H 15, nur MIT 8; McNemar einseitig p = 0,105; „schlägt MIT“ verfehlt).
  - **H3 „offen“** (66 einig, Präzision 77 % = 51/66). Die vierte Bestätigung ist nicht gelungen; bisher dreimal ≥ 85 %.
  - **H4 „trägt nicht“** (101 Abgaben, Abdeckung 67 % gegen 44 %; Präzision 66 % = 67/101).
  - Beschreibend: einstimmig aus drei 47, davon 40 richtig (85 %). Abgeleitet: Auf den 49 Aufgaben ohne Mehrheit hatte WT-A 7
    richtig (74 − 67), MIT 8 (75 − 67).
  - Tokens je richtiger Antwort: B+H 72.001 | INT 19.898 | MIT 49.089 | WT-A 50.593. B+H zählt alle drei INT-Läufe und WT-A nur
    auf den Aufgaben ohne Mehrheit.
  - Prognosen: Dave 2 von 4 (H1, H3), Claude 2 von 4 (H1, H2); beide lagen bei H4 falsch.
- 09.11. 09:01 – **N30 nachträglich, beschreibend** (nach dem Öffnen; abgeleitet aus nacht150.json und den Zusammenfassungen der Läufe).
  - Vertrauensleiter des Vorderzimmers: alle drei einig 47 (40 richtig, 85 %); genau zwei von drei 54 (27 richtig, 50 %); keine
    Mehrheit 49 (WT-A dort 7 richtig, 14 %).
  - Eigener Abschluss bzw. Schleife oder Limit: INT Seed 0 98,7 % / 1,3 %; MIT 54,7 % / 45,3 %; WT-A 46,7 % / 53,3 %.
  - […]
- 09.11. 09:08 – **Daves N31-Prognose, vor dem Öffnen** (N30 war da schon bekannt; kopplung_N31.json ungeöffnet): H6a „offen“; H6b
  „koppelt“; H6c „offen“; am Schild (MIT) „koppelt am Schild“. Ohne Prozentangaben.
- 09.11. 09:10 – **N31 gemeinsam mit Dave geöffnet** (ergebnisse/kopplung_N31.json; Lesart MEILENSTEIN2_N31_N32.md und
  MEILENSTEIN2_ZUSATZ_WREN.md).
  - eigen (WT-A-Trajektorien; 43.848 Aussagen, 2.468 richtig): AUC_F 0,513 [0,464; 0,566] → **H6a „Festlegen blind
    (bestätigt)“**; AUC_K 0,683 (Band „schwach“).
  - MIT (65.713 Aussagen, 4.262 richtig): AUC_F 0,428 [0,391; 0,461] → **H6b „MIT ebenfalls blind“**; AUC_K 0,726 (Band
    „schwach“).
  - **H6c „offen (Fall vorab nicht benannt)“:** MIT − eigen = −0,085 [−0,150; −0,026].
  - Schild: eigen AUC_F 0,689 [0,453; 0,780] → „offen“ (AUC_K 0,80); MIT AUC_F 0,381 [0,267; 0,519] → **„blind am Schild“**
    (AUC_K 0,85).
  - Vorab festgelegte Deutung: beide blind → MIT legt sich aus anderen Gründen fest; der Fokus geht auf die Schilder.
  - Beschreibend:
    - mit der gezogenen Wahrscheinlichkeit beide 0,50;
    - Spearman(K, F) unter den richtigen Aussagen: eigen +0,10, MIT −0,16;
    - nach Tiefe: eigen 0,46–0,53, MIT 0,41–0,50.
  - Prognosen:
    - Dave 1 von 4 (H6c), Claude 1 von 4 (H6a);
    - WREN: H6c getroffen; H6a knapp unter seiner Spanne 0,52–0,62.
    - Niemand erwartete, dass auch MIT blind ist.
  - Vorab benannte Einschränkung: F liegt nur an zwei Stellen in den ersten 12 Tokens nach dem Wert. Ein echtes Fenster wäre N31b
    (neuer GPU-Lauf); Entscheidung Dave.
- 09.11. 09:26 – **Lesesitzung abgeschlossen, Prognose-Bilanz** (Kategorien getroffen; Tabelle in LESEMAPPE_09-11.md):
  - N30: Dave 2/4 (H1, H3), Claude 2/4 (H1, H2).
  - N31: Dave 1/4 (H6c), Claude 1/4 (H6a), WREN 1/4 (H6c; H6a knapp außerhalb seiner Spanne).
  - […]
  - Gemeinsamer Fehler aller drei: zu viel Ordnung erwartet. Wir hielten die Einigkeit für präziser, MITs Tür für gekoppelt […].
- 09.11. 09:45 – **Daves Entscheidung zum Umfang von v0.3** (Antwort auf Claudes Empfehlung von 09:40; wörtlich): „Okey dann bauen wir
  jetzt die v0.3 inkl. deiner Empfehlung zur "Vertrauensleiter" … Gerne das Package unter KnowingIsNotCommitting_v0.3 packen im
  projectordner. Wenn du mit der englischen und deutschen.md fertig bist, lasse ich nochmal von WREN und ARGON gegenlesen. Erst
  wenn wir sicher sind, gibts das Egnlische und deutsche PDF“.
  - v0.3 enthält damit: N30 mit den zwingenden Folgen; **neu N31** (Abschnitt 3.12, Korrektur der v0.2-Deutung „checks and
    commits well“); die Vertrauensleiter als nachträglichen, beschreibenden Befund im N30-Abschnitt, ohne die Deutung als
    „weiß ich nicht“-Signal; die Sätze zu Li et al. 2026 und Farquhar 2024.
  - […]
  - Ablauf: englische und deutsche .md im Ordner KnowingIsNotCommitting_v0.3, dann Gegenlesen durch WREN und Argon, PDFs erst
    danach.
- 09.11. 09:50 – **N30 nachträglich, beschreibend: Vertrauensleiter je Stufe** (paket/114_n30_leiter.py →
  ergebnisse/n30_leiter.json; für v0.3, nach Daves Entscheidung von 09:45).
  - Einstimmig 47: B+H 40, INT s0 40, MIT 37, WT-A 31. Zwei gegen eine 54: B+H 27, INT s0 21, MIT 22. Keine Mehrheit 49: B+H (WT-A)
    7, INT s0 5, MIT 8.
  - Der Vorsprung von B+H vor INT (+8) kommt also aus den geteilten Stimmen (+6) und dem Hinterzimmer (+2); der vor MIT (+7) aus
    dem Vorderzimmer (+3 einstimmig, +5 geteilt), im Hinterzimmer liegt MIT vorn (8 gegen 7).
  - **Fehler von Claude, vor jeder Verwendung bemerkt:** Der erste Lauf nutzte das System-Python ohne math-verify. Dann vergleicht
    eval/03_eval.py Antworten nur als normalisierten Text und findet weniger Einigkeiten (einstimmig 44 statt 47, Mehrheiten 97
    statt 101, B+H 72 statt 74). Mit dem Projekt-Python (venv) stimmen alle Zahlen mit dem Nachtlauf 109 überein.
    - Die Logs 109 und 113 enthalten die math-verify-Warnungen, liefen also mit math-verify.
    - 114 bricht jetzt ab, wenn math-verify fehlt.
  - **Dave (wörtlich, während der Arbeit an v0.3):** „Wir sollten hinweisen, dass wir uns zukünftige Nachtests zu dem Titel Thema
    vorbehalten“. Kommt als Satz in v0.3 (Kopf und nächste Schritte).
- 09.11. 10:02 – **Bericht v0.3 gebaut, bereit zum Gegenlesen** (Entscheidung Dave 09:45; Ordner KnowingIsNotCommitting_v0.3).
  - Bau: veroeffentlichung/v0.3/baue_v03.py aus der veröffentlichten v0.2 (Fassung B), 24 geprüfte Ersetzungen je Sprache.
  - Zahlen gegen nacht150.json, n30_leiter.json und kopplung_N31.json geprüft: alle stimmen. […]; keine Pfade, Rechnernamen oder Adressen. LanguageTool: drei kleine Stellen nachgebessert, sonst Fehlalarme.
  - Prüfauftrag für WREN und Argon: KnowingIsNotCommitting_v0.3/PRUEFAUFTRAG_v0.3.md. PDFs erst nach dem Gegenlesen (Dave).
  - SHA-256:
    - KnowingIsNotCommitting_v0.3/Knowing_Is_Not_Committing_v0.3.md: 8e79523b3ee6603177053ca86c6a5eaca32ef4e951972340f9b545d04b9e3519
    - KnowingIsNotCommitting_v0.3/PRUEFAUFTRAG_v0.3.md: a1bc16cebd5a1703891b67c8ec966aa7532153de0c6c9e8c29c113880cbf96c3
    - KnowingIsNotCommitting_v0.3/Wissen_ist_nicht_Festlegen_v0.3.md: 1df58b07adac432080469a20e4b5d053857fe77fa6dd72c679d3130d851d2ae2
    - veroeffentlichung/v0.3/baue_v03.py: fb5076fdf09453f9af5c6c0d131172769c5b8bf367f10ee61da0e16eae97c7ff
    - paket/114_n30_leiter.py: 6f44797514b5e7d5a6d86dd0ea02562f88f8d063c64fba7a70c14410ffd782a0
- 09.11. 10:11 – **Daves Entscheidungen zu v0.3 nach dem ersten Entwurf** (wörtlich gekürzt):
  - Untertitel: „Ja Untertitel bitte "report"“. So umgesetzt.
  - Nennung: „Das wäre ggf. unfair gegenüber dir, Poow und ARGON oder? Wir sollten feststellen, wer an der v0.3 wirklich nochmal
    mitgewirkt hat und auch alle neutral benennen - gleiches Schema wie im paper v.0.2“.
    - Belegt aus Protokoll und Gutachten:
      - Claude: Auswertungen N30/N31, Texte.
      - WREN: Durchsicht der N31-Lesarten (Fehler in H6a, gespiegelter Fall H6c, Zählregel), Messung hinter den Schluss-Sätzen,
        Referenz-Implementierung; dazu Kommentar und H4-Prognose zu N30 (08.11. 18:59).
      - Argon: Gegencheck v0.2 (grünes Licht, ohne N30-Bezug im Text); für v0.3 das anstehende Gegenlesen.
      - Poow: später Kommentar zu v0.2, […]; kein Beitrag zu den neuen Teilen.
      - Li et al. hat Dave gefunden (08.11. 23:35); Farquhar stammt aus Claudes Literatursuche (09.11. 00:16).
    - Umgesetzt: kein Titel mehr. Abschnitt 8 behält den v0.2-Absatz und bekommt einen neutralen Satz zu Fassung 0.3. Der Teil
      „Argon und WREN haben gegengelesen“ gilt erst nach deren Durchsicht.
    - […]
  - Sonde als Schiedsrichterin: „Lassen wir als bewusste Frage und Möglichkeit normal offen und bestehen“. Der Satz bleibt.
  - **Versäumnis von Claude:** WRENs N30-Prognose (H4 „trägt“, Präzision ≥ 90 %, Abdeckung +10–15; 08.11. 18:59) fehlte in der
    Lesemappe. Sie ist nachgetragen; Ergebnis „trägt nicht“, WRENs Bilanz damit 1 von 9.
  - Neu gebaut, SHA-256:
    - KnowingIsNotCommitting_v0.3/Knowing_Is_Not_Committing_v0.3.md: d9391a5f98141f8ab69372c7dd62c04959df3f8877c0f3f5116440742434fd66
    - KnowingIsNotCommitting_v0.3/PRUEFAUFTRAG_v0.3.md: 0feee366969e3e1081e0176b687cecbadfe411d2dd63c4074071a6f3b6a9a6cb
    - KnowingIsNotCommitting_v0.3/Wissen_ist_nicht_Festlegen_v0.3.md: 49aca9804cbdc445d634146af4e857f9cf1fb643a9625f1506b733e6b800b249
    - veroeffentlichung/v0.3/baue_v03.py: 476f373a3dd6714096c94d58d0f39846303335a26592976fe7b1ba692c74f9b9
- 09.11. 10:14 – **Dave gibt v0.3 zum Gegenlesen an WREN und Argon** (wörtlich): „Die Klärung zu "Soll WREN die N31-Datentabelle zum
  Nachrechnen bekommen?" und alles weitere verschieben wir auf später, wenn der Report sauber veröffentlicht wurde.“
  - Der Prüfauftrag sagt das jetzt so: Ein Nachrechnen bespricht WREN nach der Veröffentlichung, dieses Gegenlesen gilt dem Text.
    Neue SHA-256: KnowingIsNotCommitting_v0.3/PRUEFAUFTRAG_v0.3.md: 32388b1c16e9f6be08ce9aeb23659382f7e663f983a00bce58dd4fc49c82910a
  - Die beiden Berichtsdateien sind unverändert (Prüfsummen von 10:11).
- 09.11. 10:27 – **Argons Gegenlesen von v0.3 erhalten** (abgelegt: recherche/gutachter/2026-11-09/Argon – Gegenlesen v0.3.txt).
  - Bestätigt:
    - 43.848 + 65.713 = 109.561 Wert-Aussagen, genau die Menge der Tiefen-Regression in 3.9;
    - 85 / 91 / 77 % in allen Abschnitten gleich nachgezogen;
    - EN und DE an den neuen Stellen gleich.
  - **Fund, übernommen (vorgemerkt):** In EN 3.10 fehlt vor dem Zitat „Several intuitions confer …“ eine Leerzeile. Der Fehler
    steht schon in v0.2; DE hat die Leerzeile. Die Behebung kommt zusammen mit den Funden von WREN und Poow in einem Bau.
  - Richtigzustellen:
    - Die LaTeX-Stelle in 3.6 (binom) ist seit v0.2 unverändert, nicht „nun“ formatiert.
    - „Einstimmigkeit vermeidet genau die Hälfte der Fehl-Abgaben“ stimmt nicht. Von 34 falschen Abgaben der Mehrheit stammen 27
      aus geteilten Stimmen (79 %); dafür gingen 27 richtige verloren. Das ist ohnehin nachträglich, also nur als eigener Test.
  - Nicht übernommen, weil überzogen:
    - „methodisch unangreifbar“;
    - „tiefgehende mechanistische Studie“;
    - „Glaubwürdigkeit, die weit über das 0,8B-Modell hinausstrahlt“;
    - „fertiges Werkzeugset, um große Reasoning-Modelle … chirurgisch zu kalibrieren“ […];
    - „bereit für das finale Release“ (das entscheidet Dave nach WREN und Poow).
  - […]
- 09.11. 10:28 – **WRENs Gegenlesen von v0.3 erhalten** (abgelegt: recherche/gutachter/2026-11-09/WREN – Gegenlesen v0.3.txt).
  - Urteil: „Nach einem Fix publikationsreif.“ Zahlen, Lesart-Ausgänge, Kennzeichnungen, Statistik-Wortlaut und Begriffe EN/DE
    ohne Abweichung.
  - **Fund, übernommen:** DE 3.11 „Was es bedeutet“: „MIT schlägt sie … nicht“ liest sich mit MIT als Subjekt und dreht die
    Aussage um. Jetzt: „Sie schlägt MIT … nicht“. Fehler von Claude (gemeint war die Regel als Objekt).
  - Zugleich behoben: Argons Fund, die Leerzeile vor dem Zitat in EN 3.10 (als 25. Ersetzung im Bau-Skript).
  - Neu gebaut, SHA-256:
    - KnowingIsNotCommitting_v0.3/Knowing_Is_Not_Committing_v0.3.md: 4ec15168693f6f2487a9e494225f046950396627ee0d802e0618d02539452f15
    - KnowingIsNotCommitting_v0.3/Wissen_ist_nicht_Festlegen_v0.3.md: 8308b2dcbf188ae96ca5ab3b601b835e71e4e63498e82c4ce197b4750e477418
    - veroeffentlichung/v0.3/baue_v03.py: 65e3c8e95857d1a2feb540fb5ddf6460ddcbe17620ac9c63285021a64e6edda7
  - Poows Rückmeldung steht noch aus.
- 09.11. 10:39 – **v0.3 korrigiert und PDFs gebaut** (Dave: „Wir bauen jetzt trotzdem die fertige pdf in deutsch und englisch und
  bereiten das Release vor“; Poow steht noch aus).
  - **Fehler von Claude, beim Vorbereiten des Release bemerkt:** 3.12 sagte, die N31-Lesart sei vor der Auswertung „einmal“
    geändert worden. Es waren zwei Zusätze vor dem Datenkontakt (22:44 nach WRENs Durchsicht; 23:05 nach seinem Referenz-Nachbau).
    Der zweite benannte den spiegelbildlichen H6c-Fall („unser Modell koppelt stärker“ bei ≤ −0,10 mit KI unter 0) und das
    Mitzählen von Bootstrap-Ziehungen ohne beide Klassen (es gab keine). Jetzt in Tabelle, Absatz und Grenzen (EN, DE)
    nachgetragen. Das Urteil H6c bleibt „offen (Fall vorab nicht benannt)“, weil −0,085 > −0,10.
  - PDFs: build_pdf.py mit neuer Option --kopf (Kopfzeile je Fassung; ohne Angabe wie v0.2). EN 28 Seiten, DE 31 Seiten.
    Neue Stellen am gerenderten PDF geprüft.
  - SHA-256:
    - KnowingIsNotCommitting_v0.3/Knowing_Is_Not_Committing_v0.3.md: 09ef94341d54d7696f7971c48278b35340e17e04c2e00cc68523607d1aefbf0a
    - KnowingIsNotCommitting_v0.3/Wissen_ist_nicht_Festlegen_v0.3.md: 8da17015189cc45ca0ddb1b9a90f6904fd4eceda9d8d1623140f0f8511f303b6
    - KnowingIsNotCommitting_v0.3/Knowing_Is_Not_Committing_v0.3.pdf: f378be2137d8c71f0d0aa525cd0b7cfdfd57968b989f94d5fcb836f28e42260c
    - KnowingIsNotCommitting_v0.3/Wissen_ist_nicht_Festlegen_v0.3.pdf: 5aa72fb3f5b4dadcde340b3d3fdde218da0aecec0d29535983139029ecd55c08
    - veroeffentlichung/v0.3/baue_v03.py: 535abc181832f5a9942005fc8fbb9009f00404208d145b45089ad8ddef86ebec
    - veroeffentlichung/build_pdf.py: acc6711f9ef94a81f83968042204850b9e5ca873f1439eb641a7b563dd947502
- 09.11. 10:41 – **Daves Entscheidungen zum Release v0.3:**
  - Protokoll-Kopie: „Ja“ zum Auszug. Alle Einträge zu N30, N31 und zum Bericht v0.3 kommen wörtlich und gesäubert hinein; Stellen
    zu späteren Arbeiten werden sichtbar mit „[…]“ gekürzt. Die drei eingefrorenen Definitionsdateien folgen mit der nächsten
    Arbeit; ihre Prüfsummen stehen schon im Auszug. Die v0.2-Kopie des Protokolls bleibt unverändert im Repo.
  - CITATION.cff: „Ja“ zur Konzept-DOI 10.5281/zenodo.24058693 als doi.
  - Ablauf (Claudes Empfehlung, Antwort auf Daves Frage nach der „kompletten Runde“): GitHub-Release v0.3 → Zenodo vergibt
    automatisch die neue Versions-DOI; ein Kommentar in der eigenen HF-Diskussion #4 (Entwurf Claude, posten Dave); keine zweite
    Mail ans MIT-Team, außer sie haben geantwortet; Reddit/LessWrong später.
