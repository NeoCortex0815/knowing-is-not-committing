# Auszug aus dem Protokoll der Vorab-Festlegungen (12.–13.11.2026): Bewertungsfehler und Fassung 0.4

*Zum Bericht v0.4. Dieser Auszug enthält die Einträge zum Fund des Bewertungsfehlers, zur Nachrechnung, zur Eichung und zur Fassung 0.4 wörtlich.
Andere Einträge dieser Tage fehlen; Teile, die andere Arbeiten betreffen, sind mit „[…]“ gekürzt. Rechnernamen, Pfade und Angaben
zu privaten Systemen sind wie in den früheren Auszügen bereinigt. „Spiegel“ meint die Kopie des Projekts, in der nur die
gespeicherte Bewertung berichtigt ist (Skript 133).*

---
- 12.11. 11:14 – **Messfehler gefunden: „richtig“ auf dem MiniPC zu niedrig** [descriptive] (Prüfung der Messwerkzeuge nach Daves Frage
  „Messfehler oder Messungenauigkeit …?“; Werkzeug paket/132_bewertung_nachpruefen.py, Liste logs/132_pruefung_alle.txt):
  - Ursache, auf dem MiniPC nachgestellt: 03_eval.py bewertet in Arbeits-Threads. math-verify setzt unter Linux seine Zeitgrenze mit
    signal.alarm und wirft im Thread „doesn't support threaded environment“. korrekt() fängt das still ab und nimmt den Text-Abgleich
    _norm. Auf dem Laptop ist die Zeitgrenze abgeschaltet (Windows-Anpassung), dort greift math-verify auch in Threads. Gleiche
    Versionen auf beiden Geräten (math-verify 0.9.0, latex2sympy2_extended 1.11.0, sympy 1.14.0).
  - […]
  - Betroffen sind auch gelesene und veröffentlichte Werte: […] und
    Läufe aus Paper 1 (N30 nacht150-int-eigen, Set B minipc-b2-*, s3-*, neu40-int, ht-*, mg-*). Die Urteilsskripte von Paper 1 lesen
    meist das gespeicherte Feld „korrekt“. Umfang und Richtung je Urteil sind noch zu prüfen.
  - […]
- 12.11. 11:17 – **Nachrechnung nach dem Bewertungsfehler: Vorgehen** (Dave: „Das ist einschneided. Das sollte unbedingt untersucht und
  behoben werden … ggf. eine korrigierte v.04 Fassung zu "Knowing is Not Committing"“):
  - Spiegel nachrechnung_mv/ (paket/133_spiegel_neubewertung.py, Selbsttest bestanden): Kopien von paket/, eval/ und daten/, 201
    Skripte byte-gleich (Manifest); modelle/ als Verknüpfung, nur gelesen; ergebnisse/ als Kopie, in der nur der Wert „korrekt“ neu
    gesetzt ist, mit derselben Funktion wie 03_eval.py, aber im Haupt-Thread auf dem Laptop. 45 Ordner geändert, davon 42 gelesene
    mit 147 Abgaben falsch → richtig; […]
  - Die eingefrorenen Skripte laufen unverändert aus dem Spiegel; nur die Eingabe ist berichtigt. Originale bleiben unberührt.
    Reihenfolge: […]; dann alle Urteilsskripte von Paper 1, alt gegen neu.
- 12.11. 11:44 – **Nachrechnung Paper 1: Ankündigung, vor dem Rechnen** (Karte nachrechnung_mv/PAPER1_KARTE.md, von einem Hilfs-Agenten nur
  lesend erstellt; die Prüfung, dass die Skripte reine Auswertungen sind, hat Claude selbst wiederholt):
  - 23 Ordner aus Paper 1 betroffen; 23 veröffentlichte CSVs in results/runs haben 65 Zellen „0“ statt „1“ in der Spalte correct.
  - Nachgerechnet werden unverändert aus dem Spiegel: 70, 73, 76 --schritt3 (Kontrolle: H-WT2 muss gleich bleiben), 85 (beide
    Sätze), 83, 94, 102, 104, 108, 107, 92, 109, 114. Lesart: Es gelten die eingefrorenen Urteilsregeln der jeweiligen Tests
    unverändert; der Vergleich alt gegen neu ist beschreibend.
  - Nicht jetzt: Skripte, deren Zwischendateien das alte „korrekt“ eingebacken haben (71, 82 --auswerten, 89, 95, 97, 100, 103, der
    N18-Teil von 105). Sie brauchen ein Nachziehen dieser Felder oder neue Messungen; das entscheidet Dave.
  - Keine Prognose-Runde: Es kommen keine neuen Daten, nur eine berichtigte Bewertung bekannter Abgaben.
- 12.11. 11:49 – **Nachrechnung Paper 1, erster Teil** (13 Skripte unverändert aus dem Spiegel, alle ohne Fehler; Gegenüberstellung
  nachrechnung_mv/NACHRECHNUNG_BERICHT.md; Logs nachrechnung_mv/logs/p1_*.log):
  - [pre-registered, berichtigt] Drei veröffentlichte Urteile ändern sich, alle zugunsten unserer Methode: N30 H2 „at least level“
    → „beats MIT“ (77 gegen 67, 16 : 6, p = 0,026); N8 „open“ → „holds“ (76 gegen 82, Schwelle MIT − 7); N27 „open by one point“ →
    „holds“ (56 von 62, 90 %).
  - Unverändert im Urteil, mit neuen Zahlen: N30 H1, H3, H4; Haupturteil ERGORE gegen MIT (66 gegen 82, p = 0,005); WT-A 63/140;
    H-WT2 (Kontrolle, gleich); Set B K1 (33 gegen 26, p = 0,065; zweiter Seed +7); N13; N10; Abschnitt 3.9 (Skript 83).
  - Noch offen, weil das alte „korrekt“ in Zwischendateien steckt: 71, 82 --auswerten, 89, 95, 97, 100, 103 (N21, N24, N26b), N18-Teil
    von 105. Die Felder lassen sich ohne Grafikkarte über die Kennungen nachziehen.
- 12.11. 13:41 – **Nachziehen der Zwischendateien im Spiegel: Ankündigung, vor dem Rechnen** (Dave 13:3x: „Ja, nachziehen“):
  - Geprüft, wie jedes Feld entstand (Quelltext der eingefrorenen Skripte, unverändert):
    - zucken_WT-A_ergo-zigA.jsonl, zucken_MIT_mit-wt.jsonl (82): korrekt, wta_korrekt, mit_korrekt kommen direkt aus den
      ergebnisse.jsonl der Quellordner; gruppe folgt daraus („nur MIT richtig“, „nur WT-A richtig“, „gleich“); art wechselt nur
      zwischen „geschlossen, falsche Antwort“ und „richtig“ (die anderen Arten hängen am Text, nicht an korrekt). Gemessen wurden
      alle 140 Aufgaben, die Auswahl hängt also nicht an korrekt.
    - int_sonde.jsonl (89 Teil A) und vorderzimmer/*.npz (103, meta.korrekt): korrekt direkt aus ergebnisse.jsonl; Zustände und Werte
      hängen nur am Text (letztes \boxed), nicht an korrekt.
    - ehrlichkeit_schritt1.jsonl (71): korrekt_offiziell direkt; korrekt bei Art „antwort“ ebenso. Bei Art „keine“ oder
      „erzwungen“ könnte ein jetzt richtiger Lauf in den Zweig „denken“ fallen, der einen neuen Grafikkarten-Wert bräuchte. Solche
      Fälle werden gezählt und nicht erfunden; gibt es sie, steht das als Grenze im Bericht.
    - Die erzwungenen Antworten (antwort_zwang/*.jsonl, 60) sind im Haupt-Thread neu bewertet: 0 Abweichungen in 25 Dateien. Die
      Lehrsätze des Trainings (TRAIN der Sonde 103) sind nicht betroffen, die eingefrorene Sonde bleibt also dieselbe.
    - daten/replay_wta_stumm.jsonl (101): keine der 32 Kennungen ist betroffen; nur die fest eingetragene „61“ (jetzt 63) im Feld
      wta_hochgerechnet ist veraltet. Wird nicht geändert, nur vermerkt.
    - Nebenfund: zwei frühe Teil-Läufe in ergebnisse/minipc/ (3 Abweichungen) werden von keinem Skript gelesen.
  - Vorgehen: neues Skript paket/134_zwischendateien_nachziehen.py (Selbsttest, Trocken mit Zählungen, dann Ziehen); es ändert nur
    Dateien im Spiegel, prüft je Datei, dass sich außer den genannten Feldern nichts ändert, und schreibt Prüfsummen ins Manifest
    MANIFEST_ZWISCHEN.json. Danach unverändert aus dem Spiegel: 82 --auswerten (WT-A, MIT), 95, 97, 100, 105 --auswerten (drei
    Aufrufe), 71 --nur-bewerten, 89 Teil B, 103 --auswerten, 103 --bestaetigen N24, 107 (für N26b), 101 --auswerten nur beschreibend.
  - Eingefroren (SHA-256, erste 16 Stellen): 71 71faa549ccceabae, 82 4d4033be200ef008, 89 d6920cfd8387f47b, 95 0de997772b56cf59,
    97 ceb26d4f3b35cd2f, 100 772f9a9d5e7eb517, 103 04a87d534294d88e, 105 5e7aadc0fbb40290, 107 dc0bc63a555890d4.
  - Lesart: Es gelten die eingefrorenen Urteilsregeln unverändert. Für N24 und N26b ist die eingefrorene Sonde maßgeblich (sie
    ändert sich nicht, siehe oben); nur die Bezeichnungen der Testläufe werden berichtigt. Alt gegen neu ist beschreibend.
  - […]
- 12.11. 13:50 – **Nachrechnung Paper 1, zweiter Teil: nach dem Nachziehen der Zwischendateien** (134, SHA 90eaff2f2222d15f, Selbsttest
  bestanden, Trocken gleich Ziehen; Manifest nachrechnung_mv/MANIFEST_ZWISCHEN.json a6d457f1baa07802; Logs nachrechnung_mv/logs/p1_*.log;
  Gegenüberstellung NACHRECHNUNG_BERICHT.md Abschnitt 5):
  - Nachziehen: 13 Dateien, 56 Datensätze; jede Herleitung geprüft (altes Feld = alter Quellwert), 0 Grenzfälle; alle 15 Aufrufe
    der eingefrorenen Skripte ohne Fehler. Die eingefrorene Vorderzimmer-Sonde bleibt dieselbe (Gewichte bis auf 1e-8 gleich).
  - [pre-registered, berichtigt] Ein viertes Urteil ändert sich, wieder zugunsten unserer Methode: **N24 „offen“ → „bestätigt“**
    (79 Abgaben, 43 statt 34 richtig; AUC 0,860 gegen Grundlinie 0,808, +0,052; schnelle 0,827 gegen 0,670). Knapp über der
    Schwelle +0,05; die Änderung kommt vor allem aus der Grundlinie.
  - Unverändert im Urteil, neue Zahlen: 3.8 H2 bestanden (602 / 736 / 683; S₂ +0,22 / −0,27 / +0,20); Audit 53 von 63 (statt 51
    von 61); N9 widerlegt (69 richtig, MIT 82); N21 offen (+0,03); N26b offen (+0,036); N26 (a) trägt, (c) offen; N29 (a) Mehrwert
    (12 gegen 8), (b) Nachteil (+0,17); N28 offen (41 von 70); N14, N16 widerlegt; N18 „nichts gewonnen“ (61 statt 63).
  - […]
  - Noch nicht neu bestimmt (für den v0.4-Text): Bootstrap-Intervall des Schiedsrichters, „35 to 39 of 70“, Risiko-Abdeckung 3.8,
    „26 of 29“ (N21), S₂ frisch in 3.8.
- 12.11. 14:01 – **v0.4 „Knowing Is Not Committing“: Entwurf begonnen** (Dave 13:5x: „Ja, v0.4 entwerfen“; veröffentlicht wird nur nach
  seinem Go und einem Geheimnis-Scan):
  - **Intervalle** (paket/135_intervalle_v04.py, 05da5d5dfea65bce; [descriptive]): gepaarter Bootstrap über Aufgaben, 10.000 Ziehungen.
    Selbsttest: auf den alten Bewertungen trifft es WRENs veröffentlichte Intervalle (ERGORE −10,7 [−17,9; −3,6], WT-A −13,6
    [−21,4; −5,7], INT −6,4 [−15,0; +2,1], Schiedsrichter +4 [−1; +9 statt +10]). Neu: ERGORE −11,4 [−19,3; −4,3], WT-A −13,6
    [−21,4; −6,4], INT −4,3 [−13,6; +4,3]; Schiedsrichter unverändert (gleicher Differenz-Vektor), Text „−1 to +10“ bleibt.
  - **Tabellen** (paket/136_v04_tabellen.py, bb6465e613ef355a): 23 Lauf-Tabellen mit 65 Zellen 0 → 1 (Rundweg Byte für Byte, gold
    und pred geprüft), 26 Urteilsdateien; keine Pfade im neuen Inhalt. Bereitgestellt unter veroeffentlichung/v0.4/staging/ (Manifest
    8869e4ade3ee0199), nicht im Repo. Die Kontrolle H-WT2 (55/85 gegen 37/102) ist in kandidaten_v2_schritt3.json unverändert.
  - **N30-Kosten** (115 aus dem Spiegel): B+H 69.196 statt 72.001 Tokens je richtige Antwort, Antwortmodus 19.033 statt 19.898
    (69 statt 66 richtig), MIT 49.089 und WT-A 50.593 unverändert. Faktor B+H/MIT 1,41 statt 1,47.
  - **Neu und gegen die Robustheit:** N13 (MIT Hinterzimmer gegen Vorderzimmer) hat jetzt exakt p = 0,00132 (7 : 26; alt 0,00032).
    Die Holm-Schwelle für den dritten Rang bei 40 Lesarten ist 0,00132. Der Bericht sagt bisher „bleibt nach Holm signifikant“; v0.4
    sagt es vorsichtig: nicht mehr klar. Ebenso: N30 H2 „beats MIT“ (p = 0,026, einseitig) ist unkorrigiert; H2 war nicht Primär-
    Endpunkt (Dave am 09.11. abgelehnt), also übersteht es Holm nicht. Beides steht im Erratum.
  - Erratum-Entwurf EN und DE: veroeffentlichung/v0.4/ERRATUM_v0.4.md, mit fünf offenen Punkten für Dave. Die Ersetzungsliste für
    die Zahlen im Text erstellt ein Hilfs-Agent nur lesend; Claude prüft jede Ersetzung maschinell (genau einmal im Text) und gegen
    die Belege.
- 12.11. 14:09 – **v0.4: Daves Antworten zu den offenen Punkten des Erratums.**
  - Denkzettel neutral formuliert („Einfach Neutral formulieren.“). Datum: heute, anzupassen am Tag der Veröffentlichung.
  - […]
  - N13: Dave bittet um eine genauere Erklärung. Claudes Vorschlag (Lesart A, vorsichtig): „an der Holm-Schwelle, nicht mehr klar
    robust“, ohne die Familie jetzt nachträglich genau abzuzählen. Grund: Die „~40“ von v0.3 waren eine Schätzung, eine
    Rechnung dazu gibt es nicht; die Zahl jetzt festzulegen, nachdem p bekannt ist, wäre ein Freiheitsgrad nach dem Ergebnis.
  - […]
  - Code-Reparatur: wird getrennt von eval/03_eval.py vorbereitet (die laufenden und die […] Messungen behalten
    ihr eingefrorenes Werkzeug), Probe unter Linux nach dem Ende von […].
- 12.11. 14:14 – **v0.4: Lesart zu N13 entschieden** (Dave: „Ja, so“): „an der Holm-Schwelle, nicht mehr klar robust“, ohne die Familie
  nachträglich abzuzählen; der Effekt (−19 Punkte, 7 : 26) wird weiter berichtet.
- 12.11. 14:17 – **Code-Reparatur vorbereitet, getrennt vom laufenden Werkzeug** (eval/03_eval.py bleibt unverändert für […]):
  - Reparierte Fassung veroeffentlichung/v0.4/staging/eval/03_eval.py (SHA 878a9c8181364d48…): Generierung in Threads, Bewertung und Schreiben im
    Haupt-Thread; korrekt() verweigert mit Zeitgrenze außerhalb des Haupt-Threads (RuntimeError); ein Scheitern von math-verify steht
    laut im Log, im Datensatz ("bewertung": "text-rueckfall") und als Zähler in der Zusammenfassung; ohne math-verify kein Lauf.
    03b und 03c laden 03_eval.py als Modul und erben das.
  - Eigener Fehler, offen benannt: Der Kommentar im alten Programm verweist auf eine frühere Prüfung „Laptop = MiniPC: 0
    Abweichungen“. Sie lief im Haupt-Thread und konnte den Fehler in Arbeits-Threads nicht finden. Das steht jetzt als Nachtrag im
    Kommentar.
  - Eichung (paket/137_bewertung_eichen.py, SHA e474e4817b707ab9…) auf dem Laptop bestanden: 8 bekannte Paare richtig; Arbeits-Thread ohne
    Zeitgrenze gleich; Ablauf Threads → Haupt-Thread gleich; Eichliste 315 Abgaben aus 6 Ordnern, alt = neu, 0 Text-Rückfälle,
    Fingerabdruck cac7e091b1705009. Auf dem MiniPC nach dem Ende von […] dieselbe Eichung; der Fingerabdruck muss gleich sein,
    und der Aufruf aus einem Arbeits-Thread muss dort laut scheitern.
- 12.11. 14:33 – **v0.4: Ersetzungsliste geprüft, ein fünftes Urteil ändert sich, Upload vorbereitet** (Dave: „jap ok und den Upload vorbereiten
  für die korrigierte Veröffentlichung“; vorbereitet heißt bereitgestellt, nicht hochgeladen):
  - Ersetzungsliste des Hilfs-Agenten (131 Stellen je Sprache, jede genau einmal im Text, ohne Überlappung) von Claude geprüft und mit
    veroeffentlichung/v0.4/korrekturen_claude.py ergänzt (jetzt 134 je Sprache; Liste ae11a970f88ba542…). Belegte Korrekturen:
    - **N24, zweite Lesart** (vorab 08.11. 15:40: „schnell bestätigt“ bei AUC ≤ 2.000 Tokens ≥ 0,75 und ≥ +0,10 über der Grundlinie):
      0,827 gegen 0,670 (+0,157) → **„schnell bestätigt“** (v0.3-Daten: 0,823 gegen 0,736, +0,087 → offen). [pre-registered,
      berichtigt] Damit ändern sich fünf Urteile, alle zugunsten unserer Methode. Die zweite Lesart für N26b bleibt widerlegt.
    - ERGORE-Intervall wie in v0.3 aus Skript 73 (Wald): −18,9 bis −4,0 (statt des Bootstraps aus 135).
    - N21, schnelle Teilmenge [descriptive]: 0,756 / 0,591 / 0,641, „26 von 29“ unverändert (Nachrechnung wie bestaetigen() in 103;
      trifft auf den alten Daten 0,794 / 0,629 / 0,627 und 26 von 29).
    - 3.9 Deutung: „5–8 Punkte“ statt „5–7“ (Seed 1 auf dem Block −5,0, Mittel beider Seeds −8,2; alte Rechnung −5,0 und −7,9);
      MITs Schwankung (24 → 18) ist zwei Drittel des Block-Abstands (9).
    - „unadjusted“ bei N30 H2 in Zusammenfassung, Kurzfassung 12 und 3.11.
    - Unverändert bestätigt: Mediane der Kaskade (+3,4; +1,9 bis +2,6), 96 AUC 0,48–0,54 (96 im Spiegel), Schiedsrichter-Intervall.
    - Nachzählungen des Agenten (Set B zu 72: 32 gegen 26, 11 : 5, p = 0,21; N15 62,5 %) stammen aus einer nur lesenden Zählung,
      deren Selbsttest auf den alten Daten jeden v0.3-Wert trifft; beschreibend.
  - Suche nach übrig gebliebenen alten Kennzahlen im gebauten v0.4: nur unberührte Werte (Laptop-Daten, andere Größen).
  - Bereitgestellt in veroeffentlichung/v0.4/staging/ (nicht im Repo): Bericht v0.4 EN/DE (md, PDF; 30 und 32 Seiten), 23 Lauf-Tabellen,
    26 Urteilsdateien, berichtigtes 03_eval.py, Release-Kopien von 133–137 (in 133 und 136 Interna anderer Arbeit bzw. ein privater
    Rechnername aus Mustern entfernt, Logik gleich), Protokoll-Auszug v0.4 (Kürzungen nur mit „[…]“).
  - Vor dem Release offen: Eichung auf dem MiniPC nach dem Ende von […]; Daves Durchsicht; Geheimnis-Scan; Daves Go.
- 12.11. 14:35 – **v0.4: Upload bereitgestellt, Geheimnis-Scan sauber.** In veroeffentlichung/v0.4/staging/: Bericht v0.4 (md, PDF; EN 30, DE 32
  Seiten), results/runs (23), results/verdicts (26), eval/03_eval.py (repariert), paket/133–137 (Release-Kopien), prereg/
  ANNAHMEN_excerpt_v0.4_de.md (11 Einträge, 7 Aufzählungspunkte und einzelne Stellen mit „[…]“ gekürzt), README.md, CITATION.cff.
  Release-Texte (GitHub, HF #4, Commit): veroeffentlichung/v0.4/ENTWUERFE_RELEASE_v0.4.md. Geheimnis-Scan
  (veroeffentlichung/v0.4/geheimnis_scan.py, auch über den PDF-Text): 2 Treffer, beide 127.0.0.1 im Auswertungsprogramm (lokaler
  Standard-Server, schon in v0.3 veröffentlicht), sonst nichts. Nichts im Repo, nichts hochgeladen.
- 12.11. 14:41 – **v0.4: Gutachter-Paket für Argon und WREN** (Dave: „Ja den Entwurf lesen sie dann gegen mit kurzer Begründung, damit sie
  wissen, warums jetzt ne Version 0.4 gibt“). veroeffentlichung/v0.4/gutachter_paket/: PRUEFAUFTRAG_v0.4.md (Warum v0.4, was sich
  ändert, fünf Prüfpunkte, Form der Rückmeldung), Bericht v0.4 EN und DE, v0.3 EN zum Vergleich. Scan: keine Rechnernamen, Pfade,
  Zugangsdaten oder E-Mail-Adressen; […]. Weitergeben tut Dave.
  - […]
- 12.11. 14:44 – **Freigabe: MiniPC-Eichung direkt nach […]** (Frage: „Darf ich die MiniPC-Eichung direkt nach dem Ende von […] selbst
  starten?“ – Dave: „Ja, direkt danach“). Gilt nur für diese Eichung (paket/137, nur CPU, ~1 min, eigener Ordner, kein Modell, kein
  Server) und nur, wenn […] sauber fertig ist (Endzeile, Kette und Server weg); sonst nicht starten und Dave melden. Skript
  minipc/eichung_v04_minipc.sh (SHA d389d695a3ddc16a…, LF): prüft den Zustand, vermerkt in der Koordinationsnotiz, kopiert reparierte und alte
  Fassung, 137 und die sechs Vergleichsordner (SHA-Abgleich), rechnet, holt das Ergebnis nach logs/137_eichung_minipc.*.
  Bestanden heißt: 8 bekannte Paare richtig, Aufruf aus einem Arbeits-Thread scheitert laut, alt = neu, 0 Text-Rückfälle,
  Fingerabdruck cac7e091b1705009 wie auf dem Laptop.
- 12.11. 17:49 – **Plan für den Abend und die Nacht 12./13.11.; […]** (Dave):
  - Release v0.4: „Morgen Vormittag machen ohne stress und wenn ich wieder am Laptop bin“. Datum und Fassungszeile gehen dann auf
    den 13.11.; Protokoll-Auszug, PDFs und Geheimnis-Scan neu. Dave schickt das Gutachter-Paket heute an Argon und WREN (Anschreiben
    veroeffentlichung/v0.4/ANSCHREIBEN_GUTACHTER_v0.4.md).
  - […]
  - **Eichung v0.4 umgestellt:** Statt minipc/eichung_v04_minipc.sh vom Laptop aus (das bräuchte den Laptop um Mitternacht) rechnet
    jetzt die Nachtkette. Der Kopierteil lief schon 17:46–17:47 mit minipc/eichung_v04_vorbereiten.sh (SHA-256 e31a7b5315c261e1…):
    reparierte und alte Fassung, 137 und die sechs Vergleichsordner nach [Pfad], mit SHA256SUMS; alle Kopien
    gleich. Die Kette prüft die Liste vor dem Rechnen noch einmal. Bestanden heißt weiter dasselbe wie um 14:44. Das Ergebnis hole
    ich morgen früh auf den Laptop.
- 12.11. 17:59 – **Gutachten zu v0.4 eingegangen** (von Dave eingefügt; abgelegt in recherche/gutachter/2026-11-12/, INDEX ergänzt):
  Argon „nach Korrektur eines inhaltlichen Folgesatzes … publikationsreif“, WREN „publikationsreif, … zwei optionale … Feinheiten“.
  Sechs Funde, alle am Text von v0.4 geprüft und zutreffend; nichts davon berührt eine Zahl oder ein Urteil, es sind Folgesätze aus
  v0.3. Vorschläge mit eigenen Formulierungen in veroeffentlichung/v0.4/EINARBEITUNG_GUTACHTEN_v0.4.md; eingearbeitet wird nach
  Daves Entscheidung.
- 12.11. 18:17 – **Daves Entscheidungen** […] und zu den Gutachten:
  - […]
  - Gutachten v0.4: „ja bitte alle sechs Korrekturen in der v0.4 einarbeiten“ (Vorschläge in veroeffentlichung/v0.4/EINARBEITUNG_GUTACHTEN_v0.4.md).
- 12.11. 18:22 – **v0.4: sechs Gutachten-Korrekturen eingearbeitet** (Dave 18:17), dazu Datum 13.11. und Dank:
  - Über die Bau-Skripte, nicht in den fertigen Dateien: korrekturen_claude.py Schritt 6 (Argon 1–4), baue_v04.py (WREN 1, Datum,
    Dank „drafts of versions 0.3 and 0.4“), ERRATUM_v0.4.md (WREN 2, Kasten EN und DE), readme_citation_v04.py (WREN 2 im README,
    date-released 2026-11-13), ENTWUERFE_RELEASE_v0.4.md (WREN 2 im Release-Text und im HF-Hinweis; Datum und Gegenlesen als
    erledigt). Sicherung vorher im Scratchpad (sicherung_v04_1817).
  - Neu gebaut: Jede Ersetzung passt genau einmal, keine Überlappung (EN 142, DE 142 Änderungen). Diff gegen den Stand im
    Gutachter-Paket: nur die sechs Stellen, Datum, Dank, und der Absatz zur Nachvollziehbarkeit. Der stand im Paket noch mit
    „re-grading scripts (132–136)“; richtig und schon vorher im Bau-Skript: „re-grading and calibration scripts (133–137), a
    corrected evaluation client“. Die Gutachter haben also an dieser Stelle einen älteren Bau gesehen (Versäumnis von Claude: staging
    war nach der Änderung nicht neu gebaut).
  - reste_suchen.py: nur die bekannten, legitimen Treffer. PDFs neu (EN 30, DE 33 Seiten); die neuen Sätze stehen darin, „apparent
    edge“, „scheinbarer Vorsprung“ und „lower precision“ nicht mehr. Geheimnis-Scan über staging: dieselben bekannten Treffer
    (127.0.0.1 im Auswertungsprogramm, […]).
  - SHA-256 (erste 16): EN md cd44ef4fb62aba8a, DE md 9cff542f805def52, EN pdf 43971548725906e2, DE pdf 676f334df9451bce, README
    ebc53446dd3d14ca, CITATION b6bdabb193bdd66a.
- 12.11. 19:23 – **v0.4: Satz in 3.8 umformuliert; Kopfzeile der PDFs berichtigt**:
  - […]
  - **Eigener Fehler:** Die PDFs von v0.4 (Bau 14:30, 18:21, 19:00) trugen auf jeder Seite die Kopfzeile „interim report v0.2“ bzw.
    „Zwischenbericht v0.2“. build_pdf.py setzt ohne --kopf die von v0.2; bei v0.3 war --kopf gesetzt, bei v0.4 habe ich es
    vergessen. Die Gutachter hatten nur die Markdown-Fassungen, Dave die PDFs von 14:30 und 18:21. Neu: baue_pdf_v04.py setzt die
    Kopfzeile immer und prüft sie (EN auf 29 von 30 Seiten, DE auf 32 von 33; die Titelseite hat keine). Checkliste ergänzt.
  - SHA-256 (erste 16): EN md 5e9e32ef6e04a396, DE md 1a710475041d4ac0, EN pdf e92979a866670b25, DE pdf 50f8538cd24f6677. Scan: nur
    127.0.0.1 im Auswertungsprogramm.
- 13.11. 01:26 – **[…]; Eichung v0.4 auf dem MiniPC bestanden**:
  - […]
  - Eichung (paket/137, Nachtkette 01:24:58–01:24:59, Rückgabe 0; Kopien vorher per SHA256SUMS geprüft). Ausgabe nach
    logs/137_eichung_minipc.txt und .json geholt. Plattform linux, Zeitgrenze aktiv. Die 8 bekannten Paare sind richtig. Der Aufruf aus
    einem Arbeits-Thread scheitert laut. Ablauf Threads → Haupt-Thread gleich. Eichliste: 315 Abgaben aus 6 Ordnern, alt ≠ neu 0,
    Text-Rückfälle 0, **Fingerabdruck cac7e091b1705009, gleich dem Laptop**. Damit ist die Code-Reparatur auf beiden Rechnern geeicht
    (WRENs Hinweis: der Vergleicher im Haupt-Thread gegen beide Rechner).
  - […]
