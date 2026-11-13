# Wissen ist nicht Festlegen

### MITs Gewichts-Edit nachgebaut und ein wahrheitsgesteuerter Reflex in ein 0,8B-Denkmodell programmiert · Bericht

**Dave Uhlemann (NeoCortex)** · unabhängiger Forscher

Code, Daten und Vorab-Protokoll: [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing) · Fragen und Korrekturen gern als GitHub-Issue.

> *„Schauen, ob das Modell die Lösung hat, wann – und den inneren Schubs zulassen, trotz Druck.“*
> — Dave Uhlemann, 6. Nov. 2026

*Fassung 0.4 · 13.11.2026 · Arbeitszeitraum 4.–9. November 2026, Berichtigung vom 12. November 2026 · nicht begutachtet · mit KI-Unterstützung erstellt (siehe
Abschnitt 8); alle Messungen liefen lokal auf den Rechnern des Autors. Deutsche Fassung; maßgeblich ist die englische Fassung.
Fassung 0.4 berichtigt einen Bewertungsfehler (siehe Erratum) und bringt keine neuen Tests. Fassung 0.3 hat diesen Bericht
abgeschlossen; weitere Nachtests zur Frage im Titel behalten wir uns vor.*

> **Stand der Belege.** Jede Aussage gehört zu einer von drei Arten:
> - **[vorab festgelegt]**: geprüft mit einer Lesart, die vor dem Lauf in einem datierten Protokoll stand;
> - **[beschreibend]**: gemessen, aber nicht vorab festgelegt;
> - **[Deutung]**: unsere Lesart der Daten.
>
> Alle Ergebnisse stammen von einem 0,8B-Modell.
> - Die meisten Ergebnisse beruhen auf einem einzigen Seed; zweite Seeds gibt es für Teile der Daten.
> - Ein Teil der Daten stammt aus einer Entwicklungsmenge, die wir mehrfach benutzt haben.
> - Die MATH-500-Aufgaben 161–300 dienten als Bestätigungsmenge (Abschnitt 3.9).
> - Die Aufgaben 301–370 wurden einmal, spät am 8. November, für eine zweite Bestätigung der Antwortmodus-Ergebnisse genutzt, mit
>   vorab festgelegten Lesarten (Abschnitt 3.10). Die Aufgaben 371–500 sind unberührt.
> - 150 nie benutzte MATH-Trainingsaufgaben dienten einmal, für den öffentlich vorab festgelegten Test N30 (Abschnitt 3.11).
> - Abschnitt 3.12 wertet vorhandene Transkripte der Aufgaben 161–300 mit vorab festgelegter Lesart neu aus; er nutzt keine neuen
>   Aufgaben.
>
> **Was wir mit „Wissen“ meinen.** Eine eingefrorene lineare Sonde auf den inneren Zuständen des Modells stuft den richtigen Wert als
> wahr ein, solange er im Kontext steht. Das ist eine Messung, keine Aussage über Gewissheit.

> **Berichtigung in Fassung 0.4 (Erratum).** Diese Fassung berichtigt einen Bewertungsfehler der Fassungen 0.2 und 0.3. Auf dem
> zweiten Rechner hat das Bewertungsprogramm unbemerkt nur Text verglichen. Dadurch wurden 65 richtige Antworten in 23 der
> veröffentlichten Lauf-Tabellen als falsch gezählt, nie umgekehrt. Alle betroffenen Zahlen sind mit den unveränderten,
> eingefrorenen Skripten neu gerechnet. Fünf vorab festgelegte Urteile ändern sich, alle zugunsten unserer Methode, keines
> dagegen; das spiegelt, welche Läufe auf dem zweiten Rechner liefen, nicht eine Eigenschaft der Methoden. Eine Aussage zur
> Signifikanz wird schwächer. Einzelheiten im Abschnitt „Erratum“ nach der Kurzfassung.

> **Neu in Fassung 0.3** (alles Übrige wie in v0.2 vom 8. 11. 2026; Zahlen in der berichtigten Fassung 0.4):
> - Abschnitt 3.11: das Ergebnis von N30, dem in v0.2 öffentlich vorab festgelegten Test, mit einer beschreibenden Aufschlüsselung
>   nach der Stärke der Einigkeit.
> - Abschnitt 3.12: N31, eine Prüfung der Titelfrage an inneren Signalen, mit vorab im datierten Protokoll festgelegter Lesart.
> - Außerdem: eine korrigierte Deutung in Abschnitt 3.9, aktualisierte Einigkeits-Zahlen in den Abschnitten 3.10 und 5, der Absatz
>   „Kurz gesagt“, die Punkte 10, 12 und 13 der Kurzfassung, die nächsten Schritte und zwei neue Literaturangaben (Li et al.,
>   2026; Farquhar et al., 2024).

**Kurz gesagt.** MITs Gewichts-Edit verringert die Denkschleifen von Qwen3.5-0.8B. Wir haben diesen Edit unabhängig nachgebaut,
einen wahrheitsgesteuerten Reflex in 16 MLP-Neuronen geschrieben und eine Reihe vorab festgelegter Tests auf frischen
MATH-500-Aufgaben durchgeführt.
- Drei Befunde tragen den Bericht:
  - (1) Das Modell *weiß* eine richtige Antwort oft lange, bevor es sich auf sie *festlegt*. Eine lineare Sonde liest die Wahrheit
    im Denktext. Unser Reflex schließt das Denken im richtigen Moment, aber ein von außen gesetzter Abschluss ist keine
    Festlegung: Auf frischen Aufgaben denkt das Modell nach 77 % seiner Abschlüsse weiter.
  - (2) Ohne Denkblock (im Antwortmodus) kommt unser editiertes Modell nahe an MITs Edit mit Denken heran: 76 gegen 82 von 140,
    bei weniger als der Hälfte der Tokens je richtiger Antwort.
  - (3) Geben zwei unabhängige Läufe im Antwortmodus dieselbe Antwort, sind 93 % davon richtig (zusammengefasst über drei Mengen).
    Ein vierter, öffentlich vorab festgelegter Test ergab auf 150 frischen Aufgaben 79 % (Abschnitt 3.11).
- Allein die Sampling-Einstellungen verschieben MITs eigenen Edit von 25 % auf 55 %.
- Neu in Fassung 0.3:
  - **N30** (in v0.2 öffentlich vorab festgelegt, 150 frische Aufgaben): Eine Beratung aus drei Läufen im Antwortmodus, mit
    unserem eigenen Denk-Lauf als Rückfall, löst 77 Aufgaben, gegen 69 für den Antwortmodus allein („hält“) und 67 für MITs Edit
    mit Denken („schlägt MIT“; +10, McNemar einseitig p = 0,026, nicht korrigiert). Als Abgabe-Tor war die Einigkeit weniger präzise als
    in früheren Mengen: 79 % für zwei Läufe („offen“), 69 % für eine Mehrheit aus drei („trägt nicht“).
  - **N31** (Lesart vorab festgelegt): An den Werten, die das Modell beim Denken schreibt, folgt seine eigene Neigung, das Denken
    zu beenden, nicht der Richtigkeit des Werts (AUC 0,51), die Sonde aber schon (0,68). MITs Edit ist keine Ausnahme (0,43).
    Das stützt Befund (1) auf der Ebene innerer Signale.
- Wir berichten jede widerlegte Lesart neben den bestätigten.

---

## Kurzfassung

1. **Das Sampling-Protokoll entscheidet die Hälfte des Effekts.** Auf denselben 40 MATH-500-Aufgaben erreicht MITs
   veröffentlichter Edit **55 %** mit Sampling im vLLM-Stil und **25 %** mit dem Standard-Sampling von llama.cpp. [beschreibend]
   - Der llama.cpp-Standard weicht in zwei Punkten ab: Die Wiederholungsstrafe schaut nur 64 Tokens zurück, und die Temperatur
     wird zuletzt angewandt.
2. **Die Schleifen-Richtung lässt sich ohne Such-Agenten finden.** Unsere eigene Richtung (Kosinus 0,76/0,77 zu MITs) hebt das
   Basismodell auf diesen 40 Aufgaben von **10 % auf 37,5 %** [beschreibend]. MITs Edit erreicht dort 55 %.
   - Wir haben dasselbe Edit-Rezept benutzt und die Richtung aus Transkripten des Basismodells gewonnen.
3. **ERGORE zieht auf den Aufgaben 1–160 mit MIT gleich, auf frischen Aufgaben nicht.** ERGORE ist unsere eigene
   Schleifen-Richtung plus ein ausdrücklicher, bedingter *Abschluss*-Schub. [vorab festgelegt]
   - 1–160: **79 gegen 77** (p = 0,85). ERGORE braucht 13 % weniger Tokens.
   - **Frische Aufgaben 161–300: 66 gegen 82 von 140** (7 : 23, p = 0,005; −11,4 Punkte, 95-%-KI −18,9 bis −4,0). Die vorab
     festgelegte Lesart lautet „MIT-Niveau nicht erreicht“.
   - Ein zweiter Seed auf einem Block (261–300) verkleinert den Abstand dieses Blocks von 15 : 24 auf 18 : 18. [beschreibend] Der
     Abstand ist echt, aber vermutlich kleiner, als Seed 0 nahelegt.
4. **Modelle wissen mehr, als sie umsetzen.** [vorab festgelegt / beschreibend]
   - Eine lineare Wahrheitssonde in Schicht 13, vor jedem Edit, trennt im Denktext richtige von falschen Kandidaten-Antworten
     (AUC 0,96 auf Übungsdaten). Im Einsatz ist sie vorsichtig: Bei den Endantworten des Tests stuft sie 1 von 86 richtigen als
     unsicher ein und erkennt 8 von 16 falschen.
   - Das Modell denkt im Median **~2.000 Tokens (T = 0,6) bis ~6.000 Tokens (T = 1,0) weiter, nachdem es die richtige Antwort zum
     ersten Mal geschrieben hat**.
   - Eine erzwungene Endantwort am Ende des Budgets hebt jedes Modell: Eine basisnahe Variante steigt von 11 auf 28 von 60. Zugleich
     schrumpfen die Unterschiede zwischen den Edits auf nicht signifikant.
5. **Plumper Druck hat seinen Preis.** [vorab festgelegt als Schadens-Prüfung / beschreibend]
   - Unser unbedingter Abschluss-Schub kostet Anweisungstreue: **IFEval 61/120**, gegen 74 ohne den Schub (p = 0,041) und 87 bei
     MIT.
   - Er erzeugt außerdem „leere Abschlüsse“, bei denen das Modell ohne Lösung aufhört zu denken. Das sind 22 von 26 Fehlern auf einer
     Entwicklungsmenge.
6. **Ein wahrheitsgesteuerter Auslöser in den Gewichten (WT-A).** Sein Mechanismus funktioniert auf frischen Aufgaben; seine
   Trefferquote erreicht MITs nicht.
   - WT besteht aus 16 Neuronen in Schicht 15. Sie feuern nur, wenn gerade eine Kandidaten-Antwort geschrieben wurde *und* das innere
     Wahrheitssignal hoch ist. Dann schieben sie entlang des gemessenen Abschluss-Gradienten.
   - **Entwicklungsmenge** (n = 60): 33 gegen 26 richtig gegenüber demselben Modell ohne Auslöser, und mit einem zweiten Seed
     wieder +7 [beschreibend]. 64 % weniger Tokens auf Aufgaben, die beide lösen. Das vorab festgelegte Tor blieb geschlossen, weil
     eine Sonden-Prüfung scheiterte.
   - **Frische Aufgaben 161–300**, Test festgelegt, bevor einer dieser Läufe existierte (H-WT2): WT-A schließt in **65 %** der
     Gelegenheiten direkt nach dem richtigen Wert, MIT in **36 %** (p = 0,0001). Seine schnellen Abschlüsse sind zu 61 % richtig,
     gegen 44 %. [vorab festgelegt]
   - **Trefferquote dort: 63 gegen 82 von 140** (−13,6 Punkte, gepaarter Bootstrap, 95-%-KI −21,4 bis −6,4). [beschreibend] Mit
     einem zweiten Seed auf 161–260: 47 gegen 58 von 100.
7. **Warum der Auslöser nicht reicht** [beschreibend, nachträglich]:
   - **Ein einziger Erfolgsweg:** 53 der 63 richtigen Antworten von WT-A folgen auf Abschlüsse, die der Auslöser bewirkt hat
     (Abschnitt 3.9). MIT prüft zusätzlich ~12.000 Tokens länger und legt sich dann selbst fest (45 von 82).
   - **Ein erzwungener Abschluss ist kein innerer Abschluss:** Nach einem Auslöser-Abschluss öffnet WT-A sein Denken im Antwortteil
     wieder (ein zweites `</think>`), in 83–100 % der Entwicklungsläufe. Auf frischen Aufgaben sind es 77 % aller Abschlüsse und 60
     von 63 richtigen Läufen, gegen 16 % bei MIT.
     - Bei den 32 stummen frischen Läufen, die nie abgeben, sind es 12 von 32. Die drei Zahlen beschreiben verschiedene Gruppen von
       Läufen.
     - WT-As Erfolgsweg ist fast immer: Auslöser-Abschluss, erneutes Denken, dann sein *eigener* zweiter Abschluss, dann die Abgabe.
   - **Tiefe:** Das Wahrheitssignal schwindet mit *Schleifen und Schwierigkeit*, nicht mit der Tiefe im Denktext.
8. **Ein ehrliches „weiß ich nicht“ aus dem inneren Signal.** [vorab festgelegt] Die eingefrorene Wahrheitssonde, gelesen an der
   abgegebenen Antwort, trennt erzwungene Antworten mit AUC 0,83.
   - Sich zu enthalten, wenn sie niedrig bleibt, macht das erzwungene Antworten von schädlich zu nützlich: Das Maß
     (richtig − 2·falsch)/N steigt von −0,27 auf +0,20.
   - 327 der 380 Enthaltungen wären falsch gewesen.
9. **Der Antwortmodus („Vorderzimmer“) ist unser stärkster eigener Weg.** Ohne Denkblock denkt das Modell sichtbar in seiner
   Antwort.
   - Entwicklungsbereich [beschreibend]: Unser Modell mit eigener Richtung löst 77 von 160, genauso viele wie MIT mit Denken
     (22 : 22), mit ~40 % der Tokens.
   - Frische Aufgaben 161–300 [vorab festgelegt]: **76 gegen 82 von 140** für MIT mit Denken (−4,3 Punkte, 95-%-KI −13,6 bis +4,3).
     Nach der vorab festgelegten Lesart „hält“ das: hält bei ≥ MIT − 7 (75), widerlegt bei ≤ MIT − 14 (68). Es braucht 15.500 statt 36.800
     Tokens je richtiger Antwort.
   - MIT selbst erreicht im Antwortmodus nur **63 von 140** (26 : 7 gegen MIT mit Denken, p = 0,0013) [vorab festgelegt]. Ein
     Hinterzimmer lohnt sich, wenn es einen funktionierenden Ausgang hat; unseres hat noch keinen.
   - Der Vorsprung ist kein Artefakt der presence penalty: dieselben +2 mit Strafe 0 und 1,5 (n = 20) [vorab festgelegt]. Das
     Vorderzimmer ist über Seeds nicht stabiler als das Hinterzimmer: 62,5 % der Aufgaben werden in beiden Seeds gleich gelöst,
     gegen 75 % bei MIT mit Denken
     [vorab festgelegt, widerlegt].
10. **Das Vorderzimmer weiß, wann es sicher ist: eine Beratung der Intuitionen.** Mehrere Läufe im Antwortmodus antworten
    unabhängig. Sind sie sich einig, gibt das Modell ab; nur strittige Fälle gehen ins Hinterzimmer.
    - **Zwei Intuitionen** [vorab festgelegt, drei Bestätigungen]. Geben zwei Läufe mit verschiedenen Seeds dieselbe Antwort, ist
      sie richtig in **37 von 38** Fällen auf 161–260, in 15 von 17 auf 40 neuen Trainingsaufgaben und in **28 von 31 auf den
      unberührten Aufgaben 301–370**. Zusammengefasst über die drei Mengen sind 80 von 86 richtig (93 %); die zusammengefasste
      Zahl ist beschreibend, weil jede Menge einzeln vorab festgelegt war. Sind die Läufe uneinig, hat der erste Lauf nur in 21–32 %
      recht. Ein vierter, in v0.2 öffentlich vorab festgelegter Test ergab auf 150 frischen Aufgaben 79 % (Punkt 12).
    - **Drei Intuitionen** [vorab festgelegt, „hält“]. Eine Mehrheit aus drei gibt auf 62 von 100 Aufgaben ab statt
      auf 38, und 90 % davon sind richtig (Ziel: 90 %). Das Maß (richtig − 2·falsch)/N steigt von +0,35 auf +0,44. Sind sich alle
      drei einig, sind 29 von 29 richtig.
    - **Eine auf Antworttexten trainierte Sonde** [vorab festgelegt; auf 40 neuen Aufgaben (N24) „bestätigt“, in den beiden anderen Tests „offen“]. Sie liest die Richtigkeit an der
      abgegebenen Antwort mit AUC 0,75–0,86 auf neuen Daten; die auf Denktexten trainierte Sonde erreicht 0,69.
      - Sie bringt nur +0,03 bis +0,05 über Antwortlänge und Schwierigkeit hinaus.
      - Ihr Vorsprung bei schnellen Antworten hielt in einer von zwei vorab festgelegten Wiederholungen: auf den 40 neuen
        Trainingsaufgaben (0,83 gegen 0,67), nicht auf den unberührten Aufgaben 301–370 (0,59 gegen 0,64).
      - Als zusätzliches Abgabe-Tor schadet sie: Maß +0,17 statt +0,31 mit Einigkeit allein.
      - Als **Schiedsrichterin** zwischen zwei uneinigen Intuitionen hilft sie [vorab festgelegt]: 12 statt 8 richtige Antworten.
        Die einigen Fälle berührt sie nicht. Mit nur 19 entscheidenden Aufgaben ist das zerbrechlich: Das Bootstrap-95-%-Intervall
        für den Gewinn reicht von −1 bis +10.
    - **Zimmerwechsel** [vorab festgelegt / beschreibend].
      - Mit zwei Intuitionen verliert der Rückgriff auf WT-As Hinterzimmer: 54 gegen 57 von 100 für den Antwortmodus allein
        [vorab festgelegt].
      - Mit drei Intuitionen gewinnt er: 63 gegen 57 [beschreibend].
      - Mit MITs Hinterzimmer als Rückfall: 63 (zwei Intuitionen) und 67 (drei), gegen 58 für MIT allein [beschreibend].
      - Auf den unberührten Aufgaben 301–370 [vorab festgelegt]: „zwei einig → Antwortmodus, sonst MITs Hinterzimmer“ löst **41
        von 70**. MIT allein löst 39, der Antwortmodus allein 36. Die Präzision der Einigkeit liegt bei 90 %, aber die Regel kostet
        mehr Tokens je richtiger Antwort als MIT (55.400 gegen 40.000). Die Lesart ist deshalb **offen**. Der Gewinn kommt aus
        beiden Zimmern: vorne die Präzision (28 gegen 26 auf den einigen Aufgaben), hinten MITs Ausgang (13 gegen 8 auf dem Rest).
    - **Zwei Betriebsarten, zwei Kosten.**
      - Ein *einzelner* Lauf im Antwortmodus ist der effiziente Weg: 15.500 statt 36.800 Tokens je richtiger Antwort (Punkt 9).
      - *Mehrere* Intuitionen zu fragen, kauft Präzision mit Tokens. Zusammen mit einem Hinterzimmer kann das je richtiger Antwort
        teurer werden als MIT allein.
11. **Negative Ergebnisse.** [vorab festgelegt]
    - Ein erstes Tor entlang einer Zustandsdifferenz-Richtung verfehlte alle Kriterien.
    - Eine „Denk-Weiche“ auf Basis des inneren Signals am Ende des Prompts wurde widerlegt (p = 0,13).
    - Sonden-Kaskade, Notizen für eine zweite Chance und schleifenbasierte „Zustandstüren“ wurden widerlegt (Abschnitt 3.10).
    - Ein von außen eingesetztes `</think>` erzeugt kein inneres „fertig“, auch nicht am eigenen Schluss-Satz des Modells. MIT
      gibt dann in 36 % der Fälle ab, gegen 18 % ohne Schluss-Satz [beschreibend].
    - Das Nachspielen der 32 stummen Antwortteile von WT-A rettet fast nichts.
      - Wir haben es mit einem fairen Deckel wiederholt: Unser erster Deckel von 1.024 Tokens war zu kurz, weil schon WT-As eigene
        richtige Antwortteile im Median ~2.000 Tokens lang sind.
      - Mit 4.096 Tokens werden 0 von 14 Läufen gerettet, wenn ein zweites `</think>` gesperrt ist, und 2 ohne Sperre.
      - Die beiden Rettungen kamen, nachdem das Modell sein erneutes Denken selbst abgeschlossen hatte.
12. **N30: die Beratung mit eigenem Hinterzimmer auf 150 frischen Aufgaben** [in v0.2 öffentlich vorab festgelegt; Abschnitt 3.11].
    - Regel: Mehrheit aus drei Läufen im Antwortmodus, sonst WT-A mit Denken. Sie löst **77 von 150**, gegen **69** für den
      Antwortmodus allein (H1 „hält“) und **67** für MIT mit Denken (H2 „schlägt MIT“: +10, McNemar einseitig
      p = 0,026, nicht korrigiert).
    - Als Abgabe-Tor liegt die Einigkeit zweier Läufe bei **79 %** (H3 „offen“), eine Mehrheit aus drei bei **69 %** (H4 „trägt
      nicht“).
    - [beschreibend, nachträglich] Die Präzision folgt der Stärke der Einigkeit: 87 %, wenn alle drei Läufe einig sind, 54 %, wenn
      zwei gegen einen stehen. Den Gewinn bezahlt die Regel mit Tokens: 69.200 je richtiger Antwort, gegen 49.100 bei MIT.
13. **Die eigene Bereitschaft festzulegen folgt nicht dem Wissen, weder bei unserem Modell noch bei MITs** [Lesart vorab im
    datierten Protokoll festgelegt; Abschnitt 3.12].
    - An Wert-Aussagen im Denken bevorzugt die eigene Wahrscheinlichkeit des Modells, das Denken zu beenden (ohne den Auslöser),
      richtige Werte nicht: AUC **0,51** für unser Modell, **0,43** für MITs Edit (unter 0,5: etwas eher an falschen Werten). Die
      Sonde trennt sie (0,68 und 0,73).
    - Hinter MITs eigenen Schluss-Sätzen, wo die Sonde am stärksten ist (0,85), bleibt MITs Abschluss-Neigung blind (0,38).
    - [Deutung] MITs Vorsprung kommt nicht daher, dass es am richtigen Wert abschließt.

---

## Erratum (Fassung 0.4)

**Was schiefging.**
- Ein Teil der Auswertungsblöcke lief auf einem zweiten Rechner (Linux; Abschnitt 2).
- Unser Auswertungsprogramm bewertet Antworten in Arbeits-Threads. Unter Linux setzt math-verify seine Zeitgrenze mit einem
  Signal, das nur im Haupt-Thread funktioniert. Im Arbeits-Thread gab es einen Fehler. Das Programm fing ihn still ab und verglich
  nur noch normalisierten Text.
- Gleichwertige Antworten in anderer Schreibweise (etwa `0.5` und `\frac12`, umgestellte Mengen, Einheiten) zählten dann als
  falsch.
- Auf dem Laptop (Windows) ist die Zeitgrenze abgeschaltet; dort war die Bewertung richtig.
- Fassung 0.3 hat schon gesagt, dass der Code nur Text vergleicht, wenn math-verify fehlt (Abschnitt 7). Dass derselbe Rückfall
  auch bei installiertem Paket greift, wussten wir nicht.

**Wie wir es gefunden haben.**
- Am 12. 11. 2026 führte eine Frage des Autors nach einem möglichen Messfehler dazu, dass wir jede gespeicherte Antwort im
  Haupt-Thread neu bewertet haben.
- Antworten vom zweiten Rechner wechselten von falsch auf richtig, keine umgekehrt.
- Das Modell verlor 1 bis 5 Antworten je Lauf. Deshalb wirkten die alten Zahlen plausibel.

**Was wir getan haben.**
- Wir haben eine Kopie des Projekts gebaut, in der nur die gespeicherte Bewertung jeder Antwort durch die richtige ersetzt ist;
  jedes andere Byte bleibt gleich (geprüft).
- Zwischendateien mit der alten Bewertung wurden ebenso nachgezogen, Feld für Feld aus ihren Quell-Läufen.
- Dann liefen die eingefrorenen Urteils-Skripte unverändert auf dieser Kopie. Kein Lauf wurde wiederholt, keine Lesart geändert,
  keine neuen Daten verwendet.
- Die berichtigten Lauf-Tabellen (65 Zellen in 23 Tabellen) und Urteilsdateien (26) ersetzen in diesem Release die alten. Die
  alten bleiben in der Versionsgeschichte des Repositorys.
- [beschreibend] Wo Fassung 0.3 Bootstrap-Intervalle nennt, haben wir sie auf dieselbe Art neu gerechnet; das Verfahren trifft auf
  den alten Bewertungen die alten Intervalle.

**Was sich ändert.** Fünf vorab festgelegte Urteile:

| Test | Fassung 0.3 | Fassung 0.4 |
|---|---|---|
| N30 H2: Beratung B+H gegen MIT, 150 frische Aufgaben | 74 gegen 67, 15 : 8, p = 0,105 → „mindestens gleichauf“ | 77 gegen 67, 16 : 6, p = 0,026 → **„schlägt MIT“** |
| N8: unser Antwortmodus gegen MIT mit Denken, 161–300 | 71 gegen 80 → „offen“ | 76 gegen 82 → **„hält“** |
| N27: Mehrheit aus drei Intuitionen | 55 von 62 richtig (89 %) → „offen um einen Punkt“ | 56 von 62 (90 %) → **„hält“** |
| N24: Vorderzimmer-Sonde auf 40 neuen Aufgaben | Zuwachs über Länge und Schwierigkeit +0,012 → „offen“ | +0,052 → **„bestätigt“** (verlangt +0,05) |
| N24, zweite Lesart: schnelle Antworten (≤ 2.000 Tokens) | 0,823 gegen 0,736 für Länge und Schwierigkeit → „offen“ | 0,827 gegen 0,670 → **„schnell bestätigt“** (verlangt ≥ 0,75 und +0,10) |

- Der p-Wert von N30 H2 ist nicht korrigiert. H2 war nicht als Primär-Endpunkt benannt; eine Holm-Korrektur über alle etwa 40
  Lesarten würde er nicht überstehen. N24 ist knapp bestätigt.
- **Eine Aussage zur Signifikanz wird schwächer.** MITs Hinterzimmer gegen sein Vorderzimmer (N13) hat jetzt p = 0,0013 (Fassung
  0.3: 0,0003), 63 gegen 82 von 140. Das liegt genau an der Holm-Schwelle für 40 Lesarten. Wir zählen ihn nicht mehr zu den
  Effekten, die die Korrektur klar überstehen; der Effekt selbst (−19 Punkte) bleibt.
- Alle anderen Urteile bleiben, mit leicht geänderten Zahlen. Beispiele:
  - ERGORE gegen MIT auf 161–300: 66 gegen 82 (Fassung 0.3: 65 gegen 80), „erreicht MIT nicht“.
  - WT-A auf 161–300: 63 von 140 (Fassung 0.3: 61). Der Mechanismus-Test H-WT2 ist unverändert.
  - Ehrlichkeit Schritt 1 (Abschnitt 3.8) besteht weiter.
- [Deutung] Alle fünf Änderungen gehen zugunsten unserer Methode, weil die meisten Antwortmodus-Läufe unseres Modells und der
  Beratung auf dem zweiten Rechner liefen, MIT mit Denken dort aber nur für die Aufgaben 261–300. Das spiegelt, wo die Läufe liefen,
  nicht eine Eigenschaft der Methoden.

**Was wir daraus mitnehmen.** Eine Messmethode muss nicht nur richtig sein; sie muss auf jedem Rechner gleich messen und laut
scheitern statt leise. Ab Fassung 0.4 des Codes läuft die Bewertung im Haupt-Thread, ohne stillen Rückfall. Bevor ein Rechner für
einen Test misst, bewertet er zuerst dieselben gespeicherten Antworten wie der andere.

## 1. Hintergrund

> *„Ist das Modell per se nicht fähig zu sagen ‚ich weiß es nicht‘?“* — D. U., 7. Nov. 2026
>
> Diese Frage führte zur Antwort-Zwang-Probe (Abschnitt 3.4) und zur Ehrlichkeits-Spur (Abschnitte 3.8 und 6).

Am 02.11.2026 veröffentlichte MIT CSAIL *„Sparks of Weight-Space Programming“* (Takehi, Teoh, Zhang, Khattab).

- **Was der Beitrag zeigt:** In Experiment 8 hat ein allgemeines Sprachmodell Qwen3.5-0.8B direkt in den Gewichten verändert.
- **Der Edit:** eine „Schleifen“-Richtung wird aus 64 Ausgangsspalten von `mlp.down_proj` in den Schichten 15 und 19 abgezogen,
  etwa 0,016 % der Gewichte.
- **Die Wirkung:** MATH-500 stieg von 7,9 % auf 48,1 %. Die Autoren deuten das als *Entfernen eines Hindernisses, das eine
  Fähigkeit verdeckte*, nicht als Hinzufügen einer Fähigkeit.

**Unsere Fragen:**
- Lässt sich der Edit auf Verbraucher-Hardware nachbauen und verstehen?
- Lässt sich das Verhalten „nicht mehr kreisen, sondern antworten“ in messbare Teile zerlegen?
- Lässt es sich genauer steuern, und zu welchem Preis?

**Nächste Vorarbeiten (ausdrücklich eingeordnet):**
- Zhang et al. (2025) zeigen, dass Denkmodelle die Richtigkeit von Zwischenantworten in ihren inneren Zuständen kodieren. Eine
  *äußere* Sonde unterstützt damit einen frühen Abbruch (bis zu 24 % weniger Tokens bei gleicher Genauigkeit).
- Orgad et al. (2025) zeigen dieselbe Lücke „weiß mehr, als es zeigt“ für Halluzinationen.
- Allgemein ist gut belegt, dass sich aus Modellen Signale über die Richtigkeit des Gesagten auslesen lassen (Kadavath et al.,
  2022; Azaria und Mitchell, 2023; Ferrando et al., 2024). Einzelne Richtungen im Aktivierungsraum können ganze Verhaltensweisen
  vermitteln (Arditi et al., 2024); MITs Edit und unserer gehören zu dieser Art.
- Unser Titel klingt an Li et al. (2026) an. Beim Faktenabruf sagen dort Auslesungen vor der Erzeugung voraus, ob unter den
  Stichproben eine richtige Antwort auftaucht, aber kaum, ob eine verfügbare richtige Antwort am Ende gewählt wird; eine
  ausdrückliche Prüfung mit P(True) verbessert die Rangfolge der Kandidaten. Wir untersuchen die verwandte Lücke in Denkmodellen,
  in denen der richtige Wert lange vor dem Festlegen im Denkblock steht.
- Unser Beitrag ist nicht die Lücke selbst:
  - Wir zerlegen einen veröffentlichten Gewichts-Edit auf Verbraucher-Hardware. Das Sampling-Protokoll macht die Hälfte seiner
    Wirkung aus, und die Schleifen-Richtung lässt sich ohne Such-Agenten finden.
  - Wir zeigen, dass der Engpass das Festlegen ist, nicht das Wissen (Wahrheitssonde, Antwort-Zwang und in Fassung 0.3 die
    eigene Abschluss-Neigung des Modells, Abschnitt 3.12).
  - Wir schreiben einen wahrheitsgesteuerten Ausgang *in die Gewichte*, ohne äußere Steuerung. Sein Mechanismus ist auf frischen
    Aufgaben bestätigt; seine Trefferquote erreicht MITs nicht.
  - Wir messen *von innen*, warum: ein Auslöser-Audit mit Teacher-Forcing (Abschnitt 3.9).
  - Wir berichten zwei Fehlerarten handgeschriebener Reflexe: den negativen SiLU-Ast und einen Phasenfehler, bei dem ein
    erzwungener Abschluss kein innerer Abschluss ist.
  - Wir zeigen, dass dieselbe eingefrorene Sonde ein ehrliches „weiß ich nicht“ trägt.
  - Wir berichten, dass unser stärkster Edit nicht verallgemeinert: ERGORE erreichte auf 1–160 MIT-Niveau, auf frischen Aufgaben
    nicht.

## 2. Aufbau

- **Modell:** Qwen3.5-0.8B (hybrid aus Gated DeltaNet und voller Attention, 24 Schichten), Denkmodus.
- **Hardware:** eine Laptop-GPU (8 GB) über llama.cpp (GGUF, q8_0). Ein zweiter Rechner (CPU und iGPU) rechnet weitere
  Auswertungsblöcke mit identischen Modelldateien (per Prüfsumme kontrolliert) und identischen Einstellungen. Seine
  Bewertung war in den Fassungen 0.2 und 0.3 fehlerhaft und ist in dieser Fassung berichtigt (Erratum).
- **Protokoll** (wie in MITs Auswertung):
  - Temperatur 0,6, top-p 0,95, top-k 20, presence penalty 1,5;
  - bis zu 32.768 neue Tokens, Seed 0;
  - das letzte `\boxed{}` wird mit math-verify bewertet.
- **Sampling im vLLM-Stil in llama.cpp:** Wiederholungsstrafe über die ganze Antwort; Reihenfolge der Sampler: Strafen →
  Temperatur → top-k → top-p → min-p.
- **Aufgabenmengen:**
  - MATH-500-Aufgaben 1–160 als Testmenge;
  - MATH-500 161–300 als Bestätigungsmenge; 301–370 als zweite, späte Bestätigung; 371–500 unberührt;
  - MATH-Trainingsaufgaben als Übungsmenge;
  - „Set B“: 60 frische MATH-Trainingsaufgaben mit der Stufenmischung von MATH-500, als Entwicklungsmenge;
  - 150 weitere, nie benutzte MATH-Trainingsaufgaben für den öffentlich vorab festgelegten Test N30 (Abschnitt 3.11);
  - IFEval: 120 Prompts, strenge Bewertung auf Prompt-Ebene.
- **Vorab-Festlegung:** Vor jedem entscheidenden Lauf steht die Lesart (Kriterien, Schwellen) in einem datierten Protokoll.
  Spätere Änderungen werden mit Begründung eingetragen, und nur, bevor die zugehörigen Daten existieren.
- **Statistik:**
  - Die meisten vorab festgelegten Lesarten sind Schwellenregeln („hält / offen / widerlegt“). Wo ein Test auch einen p-Wert hat
    (exakter McNemar-Test für gepaarte Trefferquoten, Fisher-Test für Raten), berichten wir ihn unkorrigiert.
  - Zwei der drei Haupteffekte mit p-Wert bleiben nach Holm-Korrektur über alle ~40 vorab festgelegten Lesarten dieses
    Projekts klar signifikant (einschließlich der acht von N30 und N31 in Fassung 0.3):
    - die Abschlüsse des Auslösers nach dem richtigen Wert (H-WT2), p = 0,0001;
    - die Einigkeit zweier Intuitionen, p ≈ 10⁻¹¹.
  - Der dritte, MITs Hinterzimmer gegen sein Vorderzimmer, hatte in Fassung 0.3 p = 0,0003. Mit der berichtigten Bewertung ist
    p = 0,0013, genau an der Holm-Schwelle für 40 Lesarten (Erratum).
  - Der p-Wert von N30 H2 (p = 0,026, Abschnitt 3.11) ist nicht korrigiert; H2 war nicht als Primär-Endpunkt benannt.
  - Beschreibende Ergebnisse tragen keinen p-Wert als Beleg; wir geben Anzahlen und Effektgrößen an.

## 3. Ergebnisse

### 3.1 Das Sampling entscheidet die Hälfte des Effekts [beschreibend]

Dieselben 40 MATH-500-Aufgaben, MITs veröffentlichter Edit:

| Einstellung | richtig | am Token-Limit gestoppt |
|---|---|---|
| MITs berichteter Lauf auf diesen 40 | 47,5 % | ~33 % |
| unser Lauf, Sampling im vLLM-Stil | **55,0 %** | 30 % |
| unser Lauf, Standard-Sampling von llama.cpp | **25,0 %** | 67,5 % |

- **Basismodell, vLLM-Stil:** 10 % richtig, 92,5 % abgeschnitten.
- **Basis → MIT-Edit:** 10 % → 55 %, mit 20 geretteten und 0 verlorenen Aufgaben.

**Praktischer Hinweis:** Wer reparierte Modelle in llama.cpp betreibt, sollte `repeat_last_n` auf die volle Antwortlänge setzen
und die Temperatur vor die Filter stellen.

### 3.2 Unsere eigene Schleifen-Richtung [beschreibend]

- **Bau:** Die Richtung ist der mittlere Unterschied „wiederholend minus produktiv“ über Transkripte des Basismodells zu 48
  Übungsaufgaben. Das Rezept ist ansonsten MITs: Schichten 15 und 19, die 64 stärksten Spalten, α = 6.
- **Überlappung mit MIT:** Kosinus 0,76 und 0,77 zu MITs Richtung.
- **Ergebnis auf den 40 Aufgaben:** 10 % → **37,5 %**, Abschneiden 92,5 % → 60 %. Jede Aufgabe, die unser Edit löst, löst auch
  MITs Edit. [Deutung] Gleicher Mechanismus, schwächere Dosis.
- **Messerschneiden-Finder.** Von Stellen kurz vor dem Beginn einer Schleife lassen wir das Basismodell 6–8-mal verzweigen (je 256
  Tokens) und suchen „Messerschneiden“: Stellen, an denen einige Zweige kreisen und andere produktiv bleiben. Wir fanden 31 solche
  Stellen.
  - Der Anteil kreisender Zweige wächst, je später die Verzweigung liegt (11 → 13 → 28 → 40 Zweige).
  - [Deutung] Im Basismodell bauen sich Schleifen allmählich auf, statt an einem einzigen Punkt zu kippen.
  - Eine allein aus den Messerschneiden gebaute Richtung war verrauscht (Kosinus 0,77 zu MITs, geringe Stabilität). Gemischt mit
    unserer Richtung erreichte sie 0,79–0,80.

### 3.3 ERGORE: eigene Richtung plus ausdrückliche Abschluss-Kopplung [vorab festgelegt]

**Bau.** In Schicht 15 fügen wir der Umkehrung einen zweiten Rang-1-Term hinzu. Wenn die Spalten des „Schleifen-Melders“ feuern,
schiebt er entlang unserer eigenen *Festlegungs-Achse*: „16 Tokens vor `</think>`“ minus „Mitte des Denkens“. Ausgelöst wird er
von einem geweißten („geschärften“) Melder. Schicht 19 behält nur die Umkehrung.

| MATH-500 | ERGORE | MIT | nur ERGORE : nur MIT | McNemar p | mittlere Tokens ERGORE / MIT |
|---|---|---|---|---|---|
| 1–80 | 43/80 | 43/80 | 4 : 4 | 1,0 | 18.557 / 21.501 |
| 81–160 (frisch) | 36/80 | 34/80 | 10 : 8 | 0,81 | 18.489 / 21.248 |
| **1–160** | **79/160 (49,4 %)** | **77/160 (48,1 %)** | 14 : 12 | 0,85 | 18.523 / 21.374 |

- **Vorab festgelegte Lesart:** „MIT-Niveau erreicht“, auf beiden Hälften. Nicht „über MIT“: Das 95-%-KI des Unterschieds reicht
  von −5,0 bis +7,5 Punkten.
- **Tokens:** insgesamt 13,3 % weniger (88 gegen 55 Aufgaben günstiger, p = 0,007). Auf Aufgaben, die beide lösen, gibt es keine
  Ersparnis. Sie entsteht bei Aufgaben, die keiner löst und bei denen ERGORE früher aufhört.

### 3.4 Modelle wissen mehr, als sie umsetzen

**Wahrheitssonde.** [vorab festgelegt auf Test-Antworten]
- **Bau:** logistische Sonde auf den Aktivierungen von Schicht 13 am Ende jeder Kandidaten-Antwort im Denktext. Nur auf Übungsdaten
  trainiert, dann eingefroren.
- **Übungsdaten:** AUC 0,96.
- **Endantworten des Tests, einmal angewandt:** Sie stuft **1 von 86** richtigen Antworten als unsicher ein und erkennt **8 von
  16** falschen.
- **Entwicklungsmenge B:** AUC 0,925 auf ERGORE-Läufen und 0,966 auf MIT-Läufen. [beschreibend]

**Die Klingel hören reicht nicht.** [beschreibend]

- **Aufbau:** 20 leichte Übungsaufgaben, unser Edit mit eigener Richtung. Der Prompt ergänzt „denke höchstens etwa 1.500 Wörter
  lang, dann gib deine Endantwort“. Budget 6.144 Tokens.
- **Ergebnis:** Mit dieser weichen Ankündigung wurden **0 von 20** Läufen im Budget fertig (1 von 20 ohne sie).
- **Was die Texte zeigen:** **10 von 20** Denktexte schreiben die Vorgabe selbst auf („Constraints: … max ~1500 words …“) und denken
  trotzdem weiter.
- [Deutung] Dem Modell fehlt nicht die Information, dass es aufhören soll; ihm fehlt der Antrieb dazu. Eine weiche Anweisung hilft
  nicht. Was hilft, ist ein innerer Schub (ein Gewichts-Edit) oder ein harter äußerer Stopp.

**Das Signal ist ein Blitz.** [beschreibend] Es erreicht seinen Höhepunkt am Ende der Kandidaten-Antwort (AUC 0,96) und fällt
innerhalb weniger Tokens ab (0,67–0,80 bei +8 bis +200 Tokens). Das Modell schließt sein Denken im Mittel ~600 Tokens nach dem
letzten Kandidaten.

**Spätes Abschließen.** [beschreibend, Set B] Tokens zwischen dem *ersten richtigen* Kandidaten und `</think>` bei gelösten Aufgaben
(Median):

| Lauf | Median der Tokens |
|---|---|
| ERGORE, T = 0,6 | 2.024 |
| ERGORE, T = 1,0 | 6.073 |
| MIT, T = 1,0 | 6.886 |

**Antwort-Zwang.** [beschreibend] Wie beim Budget-Forcing in s1 hängen wir an jeden Lauf, der ohne saubere Antwort endete, „The
final answer is \boxed{“ an, für alle Modelle gleich. Set B, 60 Aufgaben:

| | ohne Zwang | mit Zwang |
|---|---|---|
| ERGORE, T = 0,6 | 34 | 38 |
| ERGORE, T = 1,0 | 21 | 29 |
| MIT, T = 1,0 | 24 | 32 |
| basisnahe Variante („Gatter“), T = 0,6 | 27 | 36 |
| basisnahe Variante, T = 1,0 | 11 | 28 |

- Mit Zwang ist kein paarweiser Unterschied zwischen Edits signifikant. ERGORE gegen MIT bei T = 1,0: 29 gegen 32, p = 0,38.
- [Deutung] Ein großer Teil der gemessenen Unterschiede zwischen Edits betrifft das *Herausbringen* der Antwort, nicht das
  *Finden*.

**Zweifel ohne Enthaltung.** [beschreibend]
- Wendungen wie „I'm not sure“ oder „let me guess“ sagen Fehler voraus: Bei ERGORE mit T = 1,0 sind nur 3 der 23 Läufe richtig,
  die sie enthalten.
- Trotzdem enthalten **49–85 % der falschen Läufe gar keine Zweifelswendung.**
- **Kein Lauf endet je mit einer ausdrücklichen Enthaltung.** Die Sonde, die innen liest, stuft 96 % der falschen Kandidaten als
  „nicht wahr“ ein (Schwelle 4 %).

### 3.5 Plumper Druck hat seinen Preis

**IFEval-Schadens-Prüfung.** [vorab festgelegt als Schadens-Prüfung] 120 identische Prompts, gleiches Protokoll:

| | IFEval (streng, Prompt-Ebene) |
|---|---|
| Basis | 18/120 |
| eigene Richtung, ohne Abschluss-Schub | 74/120 |
| **ERGORE (mit Abschluss-Schub)** | **61/120** (gegen 74: 11 : 24, p = 0,041) |
| WT-A (wahrheitsgesteuerter Auslöser) | 70/120 (gegen 74: p = 0,54; gegen ERGORE: p = 0,21; gegen MIT: p = 0,005) [vorab festgelegte Lesart: bestätigt bei ≥ 72, widerlegt bei ≤ 64, also keines von beiden] |
| MIT-Edit | 87/120 |

- Die Verluste konzentrieren sich auf Schlüsselwort-Anweisungen (11/38 gegen 22/38) und kombinierte Anweisungen.
- [Deutung] Der unbedingte Schub lässt das Modell hetzen und geforderte Details weglassen.

**Leere Abschlüsse.** [beschreibend] Von ERGOREs 26 Fehlern auf Set B (T = 0,6) sind 22 Läufe, die ihr Denken schließen, oft ohne
jeden Kandidaten, und dann im Antwortteil abschweifen oder kreisen, etwa „I will formulate the response. Final.“. Zur Antwort
gezwungen, sind an dieser Stelle nur 4 von 22 richtig, oft mit einer Platzhalter-„1“. Das Modell hatte die Lösung wirklich nicht.

### 3.6 WT: ein wahrheitsgesteuerter Auslöser in den Gewichten [beschreibend auf der Entwicklungsmenge; Test auf frischen Aufgaben vorab festgelegt, Abschnitt 3.9]

**Bau.** 16 selten aktive Neuronen in Schicht 15 werden umgeschrieben:

| Gewicht | Rolle |
|---|---|
| `gate` | Wahrheitsrichtung über einer hohen Schwelle (2 % der falschen Kandidaten kommen durch) |
| `up` | Melder „gerade endete ein Kandidat“ |
| `down` | der **Abschluss-Gradient** ĝ = ∂ log p(`</think>`)/∂h₁₅, gemittelt über richtige Kandidaten-Enden in Übungsläufen |

ĝ steht fast senkrecht auf der Zustandsdifferenz-Richtung e⊥ unseres ersten Tors. Ein Schub der Stärke 5 entlang ĝ hebt
p(`</think>`) von ~10⁻¹² auf ~0,95.

**Offline-Prüfung** auf zurückgehaltenen Übungs-Präfixen, zwei Grundlagen (nur eigene Richtung; ERGORE), Schwellen 2 % und 4 %:

| Stelle | ohne WT | mit WT |
|---|---|---|
| Ende eines richtigen Kandidaten | p(`</think>`) ≈ 10⁻¹², 0/8 | **≈ 1,0, 6/8** |
| Ende eines falschen Kandidaten | ≈ 10⁻¹⁰, 0/8 | unverändert, 0/8 |
| gewöhnliches Token | ≈ 10⁻¹², 0/8 | unverändert, 0/8 |

**Test in echter Generierung** [vorab festgelegt]: Set B, n = 60, zwei Rechner in Blöcken, T = 0,6. WT-A ist WT, gebaut mit der
Vorzeichen-Regel (Abschnitt 3.8), auf unserer eigenen Schleifen-Richtung.

| Kriterium (vorab festgelegt) | Ergebnis |
|---|---|
| K0 Mechanik: keine sofortigen oder kandidatenlosen frühen Abschlüsse | erfüllt (0 und 0) |
| K1 kein Schaden gegenüber demselben Modell ohne WT | erfüllt: 33 gegen 26 richtig (nur WT-A 9, nur ohne WT 2; p = 0,065) |
| K2 Abschlüsse ≤ 64 Tokens nach einem richtigen Kandidaten | **nicht auswertbar**: 2 Gelegenheiten (siehe unten) |
| K3 Token-Ersparnis auf Aufgaben, die beide lösen | erfüllt: Mittel 5.220 gegen 14.641 (−64 %) |
| K4 Wahrheitssonde auf den neuen Transkripten intakt | **nicht erfüllt**: AUC 0,82 / 0,94 gegen 0,99 / 0,996 (zwei Blöcke) |

Nach der vorab festgelegten Lesart **blieb das Tor zu einer bestätigenden Aussage geschlossen**. Alle späteren WT-A-Zahlen sind
beschreibend, außer H-WT2 (Abschnitt 3.9).
- **Warum K2 nicht messbar war.** WT-A schließt direkt nach Ergebnissätzen (`So $\binom{10}{8} = 45$.`), *bevor* das Modell
  `\boxed{…}` oder „the answer is“ schreibt. Unser alter Kandidaten-Erkenner suchte nur danach.
- **Die Korrektur.** Wir schrieben einen breiteren Erkenner (alte Kandidaten plus Wert-Aussagen „= X“, „is X“). Damit legten wir
  einen neuen Test (H-WT2) fest, bevor ein Lauf auf frischen Aufgaben existierte.
- **Ein zweiter Seed** wiederholt das Ergebnis der Entwicklungsmenge: 35 gegen 28 (wieder +7). [beschreibend]

**Wo die Sonde zu kurz greift.** [beschreibend] Richtige Kandidaten unter der Schwelle sind meist vorsichtige Erwähnungen während
einer Selbstprüfung. In den 60 Tokens davor stehen in 51 % der Fälle Prüfwörter (gegen 21 % über der Schwelle), in 29 %
Absicherungen (gegen 17 %). [Deutung] Das Modell hat die Antwort in diesem Moment noch nicht *behauptet*. Eine niedrigere Schwelle
fängt einige davon ein, bringt aber Fehlzündungen (Simulation: Schwelle 2 % → 4 %, +13 richtige Zündungen, +6 Fehlzündungen).

**Wahrheit gegen Behauptung (2 × 2).** [beschreibend] Liest die Sonde *Wahrheit* oder nur eine selbstsichere *Form*? Das Tor ist
mit Absicht vorsichtig; dieser Test fragt, *was* es liest, nicht *wie oft* es zündet.
- **Aufbau:** An schweren Fällen (richtige Kandidaten unter der Schwelle, n = 38) hängen wir eine von vier Fortsetzungen an: „So
  the answer is X.“ oder „Let's check if it is X.“, jeweils mit dem wahren und mit einem falschen X. Die Sonde wird am Ende von X
  gelesen.
- **Falsches X:** Eine selbstsichere falsche Behauptung überschreitet die Schwelle nie (**0 von 38**; obere 95-%-Grenze ≈ 9 %).
- **Wahres X:** Eine selbstsichere wahre Behauptung hebt **10 von 38 (26 %)** über die Schwelle.
- **Wahrheits-Effekt:** positiv in 35 von 38 Fällen.
- [Deutung] Die Sonde liest Wahrheit, nicht Selbstsicherheit. Eine klare Aussage einer wahren Antwort ist ein legitimer Weg, die
  Latte zu erreichen, ohne sie zu senken.

### 3.7 Negative Ergebnisse [vorab festgelegt]

- **Erstes Tor (V2).** Gleiche UND-Struktur wie WT, aber mit Schub entlang e⊥ und ohne ERGOREs Abschluss-Schub. Es verfehlt alle
  drei Kriterien:
  - Set B: 27 gegen ERGORE 34 bei T = 0,6, und 11 gegen MIT 24 bei T = 1,0;
  - leere Abschlüsse 14 (Ziel ≤ 6);
  - Sonden-AUC 0,892 (Ziel 0,93).
  - Ohne Abschluss-Schub hört das Modell oft gar nicht auf: 18 von 60 Läufen bei T = 0,6, 44 von 60 bei T = 1,0.
- **Diesen Schub zu verdreifachen** ändert nichts (28 gegen 27).
- **Temperatur.** Bei diesem Modell schlägt T = 0,6 die vom Hersteller empfohlene T = 1,0 deutlich (ERGORE 34 gegen 21 auf Set B,
  p = 0,001).
- **Denk-Weiche** (vor dem Denken entscheiden, ob überhaupt gedacht wird).
  - **Hypothese:** Das innere Signal am Ende des Prompts (Wahrheitssonde und Kandidaten-Ende-Sonde) sagt über Stufe und
    Prompt-Länge hinaus voraus, ob das Modell die Aufgabe *ohne* Denken löst.
  - **Ergebnis:** Likelihood-Quotienten-Test p = 0,13, kreuzvalidierte AUC 0,72 → 0,73. **Widerlegt.**
- **ERGORE auf frischen Aufgaben** (Abschnitt 3.9). „MIT-Niveau nicht erreicht“ auf 161–300.

### 3.8 Ein Rezept: programmierte Reflexe in ruhigen Neuronen [Methode; Übertragung auf andere Modelle ungeprüft]

MITs Edit *entfernt ein Hindernis*: Er kehrt eine Schleifen-Richtung um. WT geht einen Schritt weiter und *schreibt einen bedingten
Reflex* in die Gewichte: **Wenn in einem bestimmten Kontext eine Bedingung erfüllt ist, schiebe in Richtung einer Handlung.** Alle
drei Teile werden am Modell selbst gemessen; nichts wird trainiert.

**Die Formel.** Für K selten aktive SwiGLU-Neuronen G in einer mittleren Schicht, mit x als Eingang des MLP dieser Schicht:

> **Reflex = Effektor × (Bedingung ∧ Kontext)**
>
> Δh(x) = K · κ_d · SiLU( κ_g · (s_Bed(x) − τ) ) · κ_u · (s_Kon(x) − τ′) · **e**

| Teil | was es ist | in WT |
|---|---|---|
| Bedingung s_Bed | lineare Sonde auf x | „dieser Wert ist wahr“ (Wahrheitssonde s_T) |
| Kontext s_Kon | zweite lineare Sonde auf x | „gerade endete ein Ergebnis“ (Kandidaten-Ende-Sonde s_C) |
| Effektor **e** | Einheitsrichtung, die die Handlung auslöst: der mittlere normierte Gradient ∂ log p(Handlungs-Token)/∂h an den Stellen, an denen die Handlung gewollt ist | „schreibe `</think>`“ |
| Ort | die K ruhigsten Neuronen nach Aktivierungs-RMS, außerhalb anderer Edits | 16 Neuronen in Schicht 15 von 24 |

**In die Gewichte schreiben.** SwiGLU enthält die Multiplikation schon, das UND braucht also keinen Laufzeit-Eingriff:
- `gate[G] = κ_g · (w_Bed + (b_Bed − τ) · v)`
- `up[G] = κ_u · (w_Kon + (b_Kon − τ′) · v)`
- `down[:, G] = κ_d · e`

Der Vektor v ersetzt den fehlenden Bias (vᵀx ≈ 1 auf gewöhnlichen Tokens).

**Eichregeln, alle vor dem Testen festgelegt:**
- τ lässt nur einen kleinen Teil der falschen Kandidaten durch (2 %).
- κ_g bringt den mittleren richtigen Kandidaten auf einen Tor-Wert z* = 3.
- **τ′ ist der Median von s_Kon auf gewöhnlichen Tokens.** Das ist die Vorzeichen-Regel: SiLU ist zwischen etwa −4 und 0 negativ,
  also darf der Kontext-Term nicht negativ sein, wo das Tor in diesem Bereich liegt. Sonst wird das Produkt positiv, und der
  Reflex zündet, wo er nicht soll. Unser erster Bau (V2.1) verletzte diese Regel; siehe das Leck unten.
- κ_u skaliert ein typisches Kandidaten-Ende auf 1.
- κ_d = κ / (K · SiLU(z*)) ergibt an einer typischen Zündstelle einen Gesamtschub von κ = 7 Einheiten entlang e.

**Pflicht-Prüfungen offline.** p(Handlungs-Token) für das editierte und das Basismodell auf identischen Texten messen:

| Stelle | muss |
|---|---|
| Ende eines richtigen Kandidaten | zünden |
| Ende eines falschen Kandidaten, gewöhnliches Token | auf Basisniveau bleiben |
| letztes Prompt-Token (erstes erzeugtes Token) | auf Basisniveau bleiben |
| frühe Absatzenden | auf Basisniveau bleiben |
| Satzende nach einer widerlegten Prüfung | auf Basisniveau bleiben |
| Zwischenergebnis (≠ Endantwort) | auf Basisniveau bleiben |
| Antwortteil (nach der Handlung) | auf Basisniveau bleiben |

Der erste Bau bestand die ersten drei Zeilen an Denk-Stellen, war aber am Prompt-Ende undicht: 9–10 von 30 Läufen schlossen sofort
(Abschnitt 3.6). Deshalb hat die Liste sieben Zeilen. WT-A besteht alle Zeilen auf der Denk-Seite; im Antwortteil zündet es noch
(zweites `</think>`, siehe die Lehre unten).

**Auswertungsprotokoll:**
- Blockdesign über Rechner hinweg;
- vorab festgelegte Kriterien (Mechanik, kein Schaden, Wirkung, Ersparnis, Sonde intakt);
- Bestätigung nur auf unberührten Aufgaben;
- Antwort-Zwang und eine Prüfung der Anweisungstreue (IFEval) als Nebenbedingungen.

**Übertragung auf ein anderes SwiGLU-Modell in sechs Schritten:**
1. Die beiden Sonden auf dem eigenen Residualstrom des Modells am MLP-Eingang einer mittleren Schicht trainieren.
2. Den Effektor-Gradienten an den gewünschten Handlungsstellen messen.
3. Die ruhigen Neuronen auswählen.
4. Die drei Gewichtsblöcke schreiben.
5. Alle Pflicht-Prüfungen bestehen, einschließlich der Vorzeichen-Regel.
6. Mit einer vorab festgelegten Lesart auswerten.

Alle Skripte liegen im veröffentlichten Code. Ob das Rezept auf andere Modelle übertragbar ist, ist ungeprüft.

**Lehre aus WT-A** [beschreibend]: Der Effektor muss zur *Phase* passen, und er muss einen *Zustand* hinterlassen, nicht nur ein
Token.
- Nach einem Auslöser-Abschluss öffnet WT-A sein Denken im Antwortteil wieder (ein zweites `</think>`), in 83–100 % der Läufe,
  selbst wenn der Wert vorher sechsmal oder öfter genannt worden war. Das erzeugte 46 % aller Tokens auf der Entwicklungsmenge.
  - Auf frischen Aufgaben (161–300) sind es 77 % aller Abschlüsse und 60 von 63 richtigen Läufen; MIT denkt nach 16 % seiner
    Abschlüsse weiter.
  - WT-As richtige Antworten kommen fast immer nach seinem *eigenen* zweiten Abschluss.
- [Deutung] Der Gradienten-Effektor ĝ hebt `</think>` für genau einen Schritt. Ein Token später ist der Kontext „Kandidat endet“
  vorbei, und die 16 Neuronen verstummen. Die Attention-Schichten sehen dann ein Denken, das mitten in einer Prüfung abgebrochen
  wurde, und das Modell behandelt den Abschluss als fremd.
- Eine Korrektur braucht deshalb einen Effektor mit *Wirktiefe*: einen Schub, der die eigene Art des Modells abzuschließen
  anstößt, statt ein einzelnes Token zu erzwingen. Ein Kandidat ist der Teil von MITs Richtung, den unsere eigene nicht erklärt
  (r⊥). Seine stärksten Tokens sind natürliche Schlusswörter („thereby“, „accordingly“, Textende), und er steht senkrecht auf ĝ
  (Kosinus 0,005).
- Der Wirktiefe-Vortest (Abschnitt 3.9) fand noch keinen solchen Effektor. Ein einzelner Schub entlang ĝ oder r⊥ wirkt nur,
  solange er gesetzt ist, und auf drei Schritte verteilt führt er zu *mehr* erneutem Denken. Die Vorschläge der Gutachter zielen
  deshalb darauf, den eigenen Schluss-Satz des Modells zu begleiten (Abschnitt 6).

**Eine zweite Anwendung (Vorschlag).** Dieselbe Formel kann einen Ehrlichkeits-Reflex ausdrücken:
- Bedingung: „die Wahrheitssonde bleibt niedrig“;
- Kontext: „gleich wird abgegeben“;
- Effektor: Richtung einer Enthaltung („weiß ich nicht“).

**Ehrlichkeit, Schritt 1** prüft nur die Bedingung, als äußere Regel. [vorab festgelegt]
- **Aufbau:** Die eingefrorene Wahrheitssonde aus Schicht 13 wird an der *abgegebenen* Antwort gelesen. Bleibt sie unter ihrer
  eingefrorenen Schwelle, wird die Antwort durch „weiß ich nicht“ ersetzt. Läufe ohne Antwort werden zuerst zur Antwort gezwungen.
- **Daten:** 1.280 Läufe aus allen Mengen und Modellen.

| | richtig | falsch | enthalten | Maß S₂ = (richtig − 2·falsch)/N |
|---|---|---|---|---|
| offizielle Antworten | 602 | – | – | +0,22 |
| erzwungene Antworten | 736 | 542 | – | −0,27 |
| **erzwungen + Enthaltung nach Sonde** | 683 | 215 | 380 | **+0,20** |

- **Beide Kriterien erfüllt:** AUC auf erzwungenen Antworten 0,83 (gefordert ≥ 0,75), und die Regel schlägt das Erzwingen beim Maß
  S₂.
- 327 der 380 Enthaltungen wären falsch gewesen; 53 richtige Antworten gingen verloren.
- **Risiko und Abdeckung:** Nur die 50 % sichersten zu beantworten ergibt 88 % Treffer, die 30 % sichersten ergeben 97 %.
- Nur auf den frischen Aufgaben: AUC 0,84 (erzwungene Antworten 0,80), S₂ +0,16 mit der Regel gegen −0,20 erzwungen.
- [Deutung] Das innere Wahrheitssignal stößt nicht nur das Festlegen an; es sagt auch, wann man sich *nicht* festlegen sollte. Die
  Enthaltung selbst in die Gewichte zu schreiben, ist der nächste Schritt.

### 3.9 Frische Aufgaben: MATH-500 161–300

> *„Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen.“* — D. U., 8. Nov. 2026

**Aufbau.**
- Die Aufgaben 161–300 waren bis zu diesem Schritt unberührt.
- Der Laptop rechnete 161–260, der zweite Rechner 261–300. Jeder paarweise Vergleich läuft auf demselben Rechner.
- Gleiches Protokoll für alle Modelle, Seed 0; ein zweiter Seed für Teile der Daten.

**Hauptbefund** [vorab festgelegt]. ERGORE erreicht MIT-Niveau nicht: 66 gegen 82 von 140 (7 : 23, p = 0,005).

| Block | ERGORE | MIT | Anmerkung |
|---|---|---|---|
| 161–260 (Laptop) | 51 | 58 | Seed 0 |
| 261–300 (zweiter Rechner), Seed 0 | 15 | 24 | 3 : 12 |
| 261–300, Seed 1 [beschreibend] | 18 | 18 | 6 : 6 |

[Deutung] Der Gleichstand aus dem Entwicklungsbereich hat sich nicht übertragen. Auf einem Block ist MITs eigene Schwankung von Seed
zu Seed (24 → 18) zwei Drittel des Abstands dort (9 Aufgaben). Der Abstand ist echt, liegt aber vermutlich eher bei 5–8 Punkten als bei 11.

**WT-A auf frischen Aufgaben.**

| | WT-A Seed 0 | WT-A Seed 1 (nur 161–260) | MIT |
|---|---|---|---|
| richtig [beschreibend] | 63/140 (161–260: 44/100) | 47/100 | 82/140 (161–260: 58/100) |
| **H-WT2: Abschlüsse ≤ 64 Tokens nach dem richtigen Wert, je Gelegenheit** [vorab festgelegt] | **65 % (55/85)** | 54 % | 36 % (37/102), p = 0,0001 |
| **H-WT2: schnelle Abschlüsse, die richtig sind** [vorab festgelegt] | **61 % (55/90)** | 57 % | 44 % (37/85) |
| Tokens auf Aufgaben, die beide lösen | 7.446 | – | 13.367 |

**Blick nach innen: ein Auslöser-Audit mit Teacher-Forcing** [beschreibend; Lesarten vorab festgelegt]. Wir haben alle 140
WT-A-Transkripte mit und ohne die 16 Neuronen nachgespielt und an jeder Stelle das Tor, den Kontext-Term, den Schub und die
gesampelte Abschluss-Wahrscheinlichkeit gelesen.
- **Der Auslöser trägt WT-As Erfolge.**
  - 69 von 102 ersten Abschlüssen gehen auf den Auslöser zurück: Die gesampelte Abschluss-Wahrscheinlichkeit liegt ohne die
    Neuronen unter 2 % und mit ihnen bei mindestens 20 %.
  - 46 dieser 69 folgen auf den richtigen Wert, 18 auf einen falschen, 5 woanders. Aus ihnen kommen **53 der 63 richtigen
    Antworten von WT-A**.
  - WT-As natürliche Abschlüsse (25) liegen meist an falschen Werten; nur 5 sind richtig.
- **Die Wahrheitserkennung ist unvollständig.** Das Tor öffnet bei 17 % der richtigen und 6 % der falschen Wert-Aussagen (AUC des
  Tor-Werts 0,68). Meist bleibt es knapp über der Schwelle, zu schwach für einen vollen Auslöser.
- **Der Gegenschub des negativen SiLU-Asts ist klein:** 1,7 verlorene Abschlüsse über 140 Läufe.
- **Eine relative Schwelle hilft nicht** [erkundend]. Ein z-Wert des Tor-Werts innerhalb des Laufs trennt schlechter (AUC 0,61).

**Woher der Abstand kommt** [beschreibend, nachträglich]:

| | WT-A | MIT |
|---|---|---|
| richtiger Wert erscheint im Denktext | 85 | 102 |
| … schließt direkt daran | 55 → 50 richtig abgegeben | 37 → 34 |
| … schließt nicht direkt daran | 30 → **7** richtig | 65 → **45** richtig |
| Tokens vom ersten richtigen Wert bis zum Abschluss (Median) | 1.018 | 12.289 |

- **Wann der Auslöser zündet:** bei frühen, klar formulierten Lösungen leichterer Aufgaben.
  - Erster richtiger Wert im Median nach 719 gegen 1.963 Tokens.
  - Stufen 1–3: 75 % dieser Läufe schließen am Wert; Stufen 4–5: 50 %.
- **Schweigen ist oft ein Abgabefehler.** 32 WT-A-Läufe schließen das Denken ohne `\boxed`-Antwort. In 14 davon erscheint der
  richtige Wert früh im Antwortteil und geht dann verloren.
  - Wie oft öffnet WT-A sein Denken nach einem Abschluss wieder (ein zweites `</think>`)? Das hängt davon ab, welche Läufe man
    zählt:
    - in 83–100 % der Entwicklungsläufe;
    - in 77 % aller seiner Abschlüsse auf diesen frischen Aufgaben (60 seiner 63 richtigen Läufe);
    - in 12 dieser 32 stummen Läufe.
  - MIT denkt nach 16 % seiner Abschlüsse weiter.
- **Das Wahrheitssignal schwindet mit Schleifen und Schwierigkeit, nicht mit der Tiefe.** Wir passen eine logistische Regression
  an die richtigen unter 109.561 Wert-Aussagen aus WT-A- und MIT-Transkripten an (gleiche Sonde, gleicher Eingang von Schicht 15),
  standardisiert, mit einem Bootstrap über Läufe.

  | Faktor | Koeffizient für „Tor offen“ an richtigen Werten | 95-%-Intervall |
  |---|---|---|
  | Tiefe (log Tokens) | **+0,26** | +0,01 bis +0,49 |
  | lokale Wiederholung | **−0,80** | −1,08 bis −0,50 |
  | Schwierigkeitsstufe | **−0,68** | −1,06 bis −0,32 |

  - Geschachtelte Modelle ohne Bootstrap zeigen dieselbe Umkehr. Tiefe allein ergibt −0,49, mit Schwierigkeit −0,27, mit Schleifen
    +0,46, mit der Herkunft des Transkripts +0,26. Der letzte Schritt ist das volle Modell der Tabelle.
  - Ohne Schleifen öffnet das Tor bei 8.000–16.000 Tokens noch an ~60 % der richtigen Aussagen. In Schleifen jenseits von 16.000
    Tokens öffnet es bei 15 %.
  - [Deutung] Die Sonde liest den Zustand des Denkens, nicht den Abstand vom Anfang. Eine tiefenabhängige Schwelle ist nicht
    angezeigt.
- **Der Auslöser würde MIT nicht helfen.** [Schätzung, keine Messung] Wir haben MITs Transkripte mit hinzugefügten
  Auslöser-Neuronen nachgespielt.
  - Der Auslöser würde MITs lange Prüfung abkürzen, oft an einem falschen Wert.
  - Die Schätzung bleibt bei allen Schwellen-Einstellungen unter MITs tatsächlichem Ergebnis. Auf wiederholte Auslösungen beim
    selben Wert zu warten, kommt nahe heran, übertrifft es aber nicht.
  - Die Schätzung hängt von Annahmen über die Abgabe nach einem frühen Abschluss ab; wir berichten sie deshalb nur als Grund, diese
    Kombination nicht zu rechnen.
  - [Deutung] Ein wahrheitsgesteuerter Auslöser lohnt sich, wo ein Modell keinen guten eigenen Weg zum Abschluss hat (WT-A gegen
    seine Grundlage: +7 in beiden Seeds). Er lohnt sich nicht, wo das Modell schon auf anderem Weg gut abgibt.
  - *Korrigiert in Fassung 0.3.* In v0.2 endete der letzte Satz mit „wo das Modell schon gut prüft und sich festlegt“. Abschnitt
    3.12 zeigt, dass MITs eigene Bereitschaft festzulegen nicht stärker an die Wahrheit eines Werts gebunden ist als unsere. Sein
    Vorsprung liegt darin, den richtigen Wert öfter zu finden (102 gegen 85 Läufe) und nach langem Prüfen abzugeben (45 der 65
    Läufe, die nicht direkt am Wert abschließen; Tabelle oben).
- **Wirktiefe** [Vortest, Lesarten vorab festgelegt; 30 Auslöser-Abschlüsse an richtigen Werten, gierige Dekodierung].

  | Schub an der Auslöse-Stelle | schließt | p(`</think>`) bei gesperrtem Abschluss, Schritt 0 / 1 / 2 / 5 | Schluss-Satz davor | erneutes Denken danach |
  |---|---|---|---|---|
  | WT-As echter Auslöser | 26/30 | 0,75 / 0,27 / 0,03 / 0 | 0 | 4 |
  | keiner (Basis-Edit) | 0/30 | 0 | – | – |
  | ĝ einmal (κ = 7) | 30/30 | 1,00 / 0,02 / 0 / 0 | 0 | 4 |
  | ±r⊥ einmal (κ = 7) | 0/30 | 0 | – | – |
  | ĝ verteilt auf 3 Schritte | 17/30 | 0,01 / 0,36 / 0,32 / 0 | 0 | 11 |

  - Jeder Schub wirkt genau so lange, wie er gesetzt ist; ein bleibender Zustand „fertig“ entsteht nicht. Keine Variante erzeugt
    einen Schluss-Satz.
  - Ein einzelner Schub entlang r⊥ bewirkt nichts. MITs Schluss-Sätze stammen also von einem Edit, der ständig wirkt, nicht von
    einem Anstoß.
  - [Deutung] Ein inneres „fertig“ muss sich über die Schluss-Strecke aufbauen. Der nächste Kandidat zündet, *während* das Modell
    seinen eigenen Schluss-Satz schreibt, und nur, wenn das Wahrheitssignal hoch ist. Genau an diesen Stellen trennt die Sonde
    richtige von falschen Werten mit AUC 0,80–0,85.

### 3.10 Antwortmodus („INT“)

> *„Das ist das erste Paar Schuhe. Nennen wir es INT für Intuition.“* — D. U., 8. Nov. 2026

Die offizielle Vorlage von Qwen3.5 ohne Denken schließt den Denkblock, bevor die Generierung beginnt. Das Modell denkt dann sichtbar
in seiner Antwort, mit Abgabepflicht und ohne eigenen Raum für endloses Prüfen. Ma et al. (2025) berichten, dass das Überspringen
des Denkblocks bei Token-Budgets wettbewerbsfähig sein kann. Hier geschieht es in einem editierten 0,8B-Modell unter MITs vollem
Protokoll.
- **Entwicklungsbereich** [beschreibend]: unser Modell mit eigener Richtung, ohne Denkblock, gleiches Protokoll und Budget.
  - MATH-500 1–160: **77 von 160**, genauso viele wie MIT mit Denken (22 : 22). Es braucht ~8.200 statt ~21.000 Tokens.
  - Set B: 32 gegen 26 für dasselbe Modell mit Denken (11 : 5, p = 0,21).
  - Alle 109 Treffer im Antwortmodus enden regulär (Ende des Zugs). Keiner stammt aus einer Schleife oder einem Budget-Abbruch;
    es ist also kein Bewertungs-Artefakt.
- **Taugt der Antwortmodus nur für leichte Aufgaben?** [beschreibend, Entwicklungsdaten] Nein.
  - Nach offizieller Schwierigkeit (1–160): Antwortmodus 26 gegen MIT mit Denken 22 auf den Stufen 4–5, und 33 gegen 37 auf den
    Stufen 1–2.
  - Dasselbe Modell in beiden Betriebsarten (Set B, zwei Seeds fürs Denken): Bei Aufgaben, die das Modell schnell beantwortet
    (< 1.000 Tokens), erreicht der Antwortmodus 21 und das Denken 21 und 21 von 26.
  - Bei Aufgaben, deren Antwort lange dauert (> 8.000 Tokens), erreicht der Antwortmodus 8, das Denken 3 und 4 von 25.
  - Das Bild des Autors dafür ist ein Haus. Der Antwortmodus ist das *Vorderzimmer*, der Denkblock das *Hinterzimmer*; dazwischen
    liegt ein *Flur*, dessen Ausgänge zum „Feierabend“ (abgeben und aufhören) oder in den „Pausenraum“ führen (innehalten,
    enthalten, neu ansetzen).
  - [Deutung] Für dieses 0,8B-Modell ist das Hinterzimmer nicht der Ort, an dem schwere Aufgaben gelöst werden; es ist der Ort, an
    dem sich das Modell verliert.
  - Auch der Antwortmodus zeigt ein eigenes Tempo-Signal: Antworten innerhalb von 1.000 Tokens sind zu ~75 % richtig, Antworten
    jenseits von 8.000 Tokens zu ~25 %.
- **Frische Aufgaben 161–300** [vorab festgelegt: hält bei ≥ MIT − 7 von 140, widerlegt bei ≤ MIT − 14]: Antwortmodus **76**,
  MIT mit Denken **82**. Die Lesart **hält**.
  - Auf 161–260 57 gegen 58; auf 261–300 19 gegen 24.
  - Alle Läufe im Antwortmodus enden regulär. Je richtiger Antwort brauchen sie 14.800 statt 36.600 Tokens (161–260).
- **MIT im Vorderzimmer** [vorab festgelegt]: MITs Edit ohne Denkblock erreicht **63 von 140** (7 : 26 gegen MIT mit Denken,
  p = 0,0013). Die Lesart „das Hinterzimmer lohnt sich bei MIT“ hält.
  - Unser Vorderzimmer (76) schlägt MITs Vorderzimmer (15 : 28, p = 0,07).
  - [Deutung] Ein Hinterzimmer lohnt sich nur, wenn es einen funktionierenden Ausgang hat. MITs Edit baut diesen Ausgang; unserer
    baut ein stärkeres Vorderzimmer.
- **Prüfungen** [vorab festgelegt]:
  - Presence penalty: Der Vorsprung des Antwortmodus auf Set B 1–20 beträgt +2, sowohl mit Strafe 0 als auch mit 1,5. Kein
    Artefakt.
  - Stabilität von Tag zu Tag: Mit einem zweiten Seed auf 261–300 geht der Antwortmodus von 19 auf 18, aber nur 62,5 % der Aufgaben
    werden gleich gelöst, gegen 75 % bei MIT mit Denken. Die Vermutung des Autors, das Vorderzimmer sei stabiler, ist
    widerlegt.
- **Kaskade „Antwortmodus → Wahrheitssonde → Denklauf → weiß ich nicht“** [vorab festgelegt; Vorbedingung nicht erfüllt, daher
  beschreibend].
  - **Vorbedingung:** Die eingefrorene Wahrheitssonde muss Antworten im Antwortmodus auf 161–300 mit AUC ≥ 0,75 trennen. Sie
    erreicht 0,69 (0,76 auf 1–160). Die Kaskade wird deshalb nur beschreibend berichtet.
  - **Hauptvariante:** Schwellen auf 1–160 geeicht, MIT als Rückfall. Auf 161–300 erreicht sie S₂ +0,36 gegen +0,31 für MIT
    allein, aber nur 69 richtige Antworten (MIT: 82). Die Lesart verlangte S₂ ≥ +0,25 *und* mindestens 75 richtige Antworten und
    galt als widerlegt bei S₂ ≤ +0,19 *oder* weniger als 75 richtigen. Sie ist deshalb trotz des höheren S₂ **widerlegt**.
  - **Kosten:** Die Tokens steigen eher, als dass sie fallen, weil die meisten Aufgaben im Denkzweig landen.
  - **Grund:** Im Antwortmodus ist die Sonde weit nach oben verschoben. Richtige Antworten haben einen Median-Wert von +3,4, falsche
    +1,9 bis +2,6, gegen eine eingefrorene Schwelle von −1,2.
  - [Deutung] Die Sonde wurde auf Denktext trainiert. Im Vorderzimmer klingt jede Aussage wie eine Behauptung. Eine Kaskade im
    Vorderzimmer braucht eine Sonde, die auf Antworttext trainiert ist.
- **Zweite Chance („Morgengrauen“)** [vorab festgelegt]. Die 69 WT-A-Läufe, die nichts abgegeben hatten, wurden im Antwortmodus mit
  Notizen wiederholt. Die Notizen waren die Sätze um die stärksten eigenen Wahrheits-Blitze des Modells, ausgewählt ohne Zugriff
  auf die Lösung. Die Kontrolle war der Antwortmodus ohne Notizen auf denselben Aufgaben.
  - Notizen 23, Kontrolle 27 (p = 0,54). Die Wirkung der Notizen ist **widerlegt**.
  - [beschreibend] Die zweite Chance im Vorderzimmer selbst rettet ein Drittel der stummen Läufe, auf denen WT-A nichts abgegeben
    hatte.
  - Notizen helfen nur, wenn sie den richtigen Wert enthalten (8 gegen 5 von 10). Die stärksten Wahrheits-Blitze zeigen nur in 10
    von 65 Läufen auf den richtigen Wert.
- **Durchstreichen** [beschreibend, grober Marker]. Im Hinterzimmer werden richtige Werte *öfter* zurückgenommen („wait“, „let me
  check“, …) als falsche: WT-A 74 % gegen 60 %, MIT 59 % gegen 45 %. Das Wahrheitssignal ist gleich, ob ein Wert zurückgenommen
  oder behalten wird. Im Vorderzimmer ist Zurücknehmen selten (18 % gegen 14 %).
  - [Deutung] Zurücknehmen ist im Hinterzimmer eine Gewohnheit, kein Urteil über Wahrheit.
- **Schilder** [beschreibend]. Vor MITs natürlichen Abschlüssen schreibt das Modell eigene Schluss-Wendungen („answer“ 31 %,
  „final“ 14 %, „ready“ 8 % in den letzten 12 Tokens). Vor WT-As Auslöser-Abschlüssen fehlen sie meist.
- **Schnelle Fehler sind nicht blind** [beschreibend; korrigiert eine frühere Lesart]. Bei schnellen Antworten im Antwortmodus
  (< 1.000 Tokens) trennt keines unserer *früheren* Signale richtig von falsch: Zurücknahmen, Zweifelswörter, verschiedene Werte
  und die Denktext-Sonde ergeben AUC 0,48–0,54. Wir nannten diese Fehler zuerst „selbstsicher“. Eine auf Antworttext trainierte
  Sonde trennt sie (nächster Punkt).

> *„Mehrere Intuitionen beraten sich im Vorderzimmer. Sind sie sich einig, ist Feierabend. Nur die strittigen Fälle gehen ins
> Hinterzimmer.“* — Bild, mit D. U. abgestimmt, 8. Nov. 2026

- **Die Intuition zweimal fragen** [vorab festgelegt]. Dasselbe Modell im Antwortmodus, Seeds 0 und 1. Regel: „gleiche Antwort“,
  wenn beide Läufe gleichwertige Antworten abgeben (geprüft wie bei der Bewertung).
  - **161–260** (100 frische Aufgaben): gleiche Antwort bei 38 Aufgaben, **37 richtig (97 %)**; verschiedene Antworten bei 62,
    Seed 0 richtig in 32 %. Das Kriterium (Unterschied ≥ 30 Punkte und ≥ 70 % bei Einigkeit) hält mit +65 Punkten. Fisher
    einseitig p ≈ 9 · 10⁻¹².
  - **40 neue Trainingsaufgaben** (nie zuvor benutzt): gleiche Antwort bei 17, 15 richtig (88 %); verschieden bei 23, 22 % richtig.
    Das Kriterium hält mit +66 Punkten.
  - **Unberührte Aufgaben 301–370:** gleiche Antwort bei 31, **28 richtig (90 %)**; verschieden bei 39, 21 % richtig. Das
    Kriterium hält mit +70 Punkten.
  - [beschreibend, zusammengefasst] Über die drei Bestätigungen sind 80 von 86 einigen Antworten richtig (93 %). Die 97 % des
    ersten Tests sind das obere Ende. Jede Menge war einzeln vorab festgelegt, die zusammengefasste Zahl nicht.
  - *Ergänzt in Fassung 0.3:* Ein vierter, öffentlich vorab festgelegter Test ergab auf 150 frischen Aufgaben **79 %** (52 von 66;
    Abschnitt 3.11). Über alle vier Mengen sind 132 von 152 einigen Antworten richtig (87 %) [beschreibend, zusammengefasst].
  - [Deutung] Das ist Selbstkonsistenz (Wang et al., 2022), eingesetzt an der Stelle des Festlegens. Die Einigkeit stimmt nicht über
    die Antwort ab; sie entscheidet, *ob* abgegeben wird.
  - Die Einigkeit unabhängiger Läufe im Antwortmodus ist eng verwandt mit der semantischen Entropie (Farquhar et al., 2024). Dort
    werden mehrere Antworten erzeugt, und die Unsicherheit auf der Ebene der Bedeutung zeigt Konfabulationen an. Unsere Beratung
    nutzt eine einfache Form dieses Prinzips, die Einigkeit der Endantworten, als Abgabe-Tor für ein kleines Denkmodell.
  - [beschreibend] Auf dem schon gesehenen Block 261–300 zeigt sich dasselbe Muster: 11 von 12 gegen 8 von 28.
- **Dreimal fragen** [vorab festgelegt; 161–260, Seeds 0, 1, 2].
  - Eine Mehrheit aus drei (mindestens zwei gleichwertige Antworten) gibt bei **62** Aufgaben ab, 56 davon richtig (90 %).
  - Die Lesart verlangte ≥ 48 Abgaben und ≥ 90 % Präzision; sie **hält** also.
  - Die zweite Lesart, nach der das Maß (richtig − 2·falsch)/N nicht unter die Einigkeit aus zwei fallen darf, hält: +0,44 gegen
    +0,35.
  - Bei 29 Aufgaben sind sich alle drei einig, und alle 29 sind richtig.
  - [beschreibend] Die anderen Seed-Paare wiederholen das Muster: 0/2 einig bei 42 Aufgaben (40 richtig), 1/2 bei 40 (37 richtig).
- **Eine Sonde für das Vorderzimmer** [vorab festgelegt; auf 161–300 und 301–370 „offen“, auf 40 neuen Aufgaben „bestätigt“]. Gleiches Rezept wie bei der Wahrheitssonde, aber auf
  Texten im Antwortmodus trainiert: 239 abgegebene Antworten aus Set B und 1–160. Sie liest den Zustand am letzten Token des
  abgegebenen `\boxed{}`.
  - Schicht und Regularisierung wurden nur auf Trainingsdaten durch gruppierte Kreuzvalidierung gewählt (Schicht 13, CV-AUC 0,81),
    dann eingefroren.
  - Test auf 161–300: AUC **0,754**. Antwortlänge und Schwierigkeit allein erreichen 0,723, die Kombination bringt nur +0,03. Die
    vorab festgelegte Lesart verlangte +0,05; das Ergebnis ist also **offen**.
  - Die Denktext-Sonde erreicht an denselben Stellen 0,685.
  - [beschreibend, nachträglich gewählte Teilmengen] Bei schnellen Antworten (≤ 2.000 Tokens) erreicht die neue Sonde 0,756, gegen
    0,59 für Länge und Schwierigkeit und 0,64 für die alte Sonde. Gibt man nur schnelle Antworten über dem Median der Sonde ab, sind
    26 von 29 richtig.
  - Sie überträgt sich auf MITs Texte im Antwortmodus (0,768) und auf neue Stichproben derselben Aufgaben (0,838).
  - **Bestätigungen** [vorab festgelegt, eingefrorene Sonde und eingefrorene Grundlinie]:

    | Menge | Antworten | Sonden-AUC | Länge + Schwierigkeit | Zuwachs | schnelle Antworten (≤ 2.000): Sonde gegen Grundlinie |
    |---|---|---|---|---|---|
    | 40 neue Trainingsaufgaben | 79 | 0,860 | 0,808 | +0,052 | 0,827 gegen 0,670 |
    | unberührte 301–370 | 138 | 0,767 | 0,731 | +0,036 | 0,591 gegen 0,635 |

    - Die Hauptlesart ist auf den 40 neuen Trainingsaufgaben knapp **bestätigt** (+0,052 bei einer Schwelle von +0,05) und auf
      301–370 **offen**, wo Antwortlänge und Schwierigkeit den größten Teil der Information schon tragen.
    - Der Vorsprung bei schnellen Antworten aus der nachträglich gewählten Teilmenge war vorab als zweite Lesart festgelegt. Sie ist
      auf den 40 neuen Trainingsaufgaben **bestätigt** (0,827 gegen 0,670; Fassung 0.3: offen) und auf den unberührten Aufgaben
      301–370 **widerlegt** (0,591 gegen 0,635).
  - **Mehrwert ohne Schaden** (Kriterium des Autors: „nur, wenn sie messbar Mehrwert bringt und keinen Nachteil“) [vorab
    festgelegt, 301–370]:
    - *Als Schiedsrichterin*: Sind zwei Intuitionen uneinig und geben beide eine Antwort ab, wird die mit dem höheren Sonden-Wert
      genommen. Bei 37 solchen Aufgaben war eine der beiden Antworten in 19 Fällen richtig. Die Sonde wählt 12 davon; der erste Lauf
      allein hat 8, die kürzere Antwort 8. Lesart: **Mehrwert**.
      - Die Stichprobe ist zerbrechlich: Nur 19 Aufgaben entscheiden, und das gepaarte Bootstrap-95-%-Intervall für den Gewinn
        reicht von −1 bis +10 richtigen Antworten.
      - [beschreibend] Bei „immer antworten“ hebt die Schiedsrichterin die Zahl von 36 auf 40 von 70. Die beiden einzelnen Läufe
        erreichen 36 und 39, das Mittel eines einzelnen Laufs ist also 37,5.
    - *Als zusätzliches Abgabe-Tor*: Das Maß fällt von +0,31 (Einigkeit allein) auf +0,17. Lesart: **Schaden**. Die zusätzlichen
      Abgaben der Sonde sind nur in 4 von 11 Fällen richtig.
    - [Deutung] Die Einigkeit entscheidet, *ob* abgegeben wird; die Sonde entscheidet, *welche* Antwort, wenn die Intuitionen
      uneinig sind.
- **Zimmerwechsel** [vorab festgelegt]. Abgeben, wenn zwei Intuitionen einig sind, sonst einen Denklauf nehmen.
  - Mit WT-As Hinterzimmer als Rückfall: 54 von 100, gegen 57 für den Antwortmodus allein. Widerlegt.
  - [beschreibend] Mit MITs Hinterzimmer: 63, gegen 57 und 58 für jedes allein.
  - [beschreibend] Mit drei Intuitionen (Mehrheit, sonst Hinterzimmer): WT-As Hinterzimmer als Rückfall ergibt **63**, gegen 57 für
    den Antwortmodus allein und 44 für WT-A allein. MITs Hinterzimmer ergibt 67, gegen 58 für MIT allein. Mit drei Intuitionen
    bringt unser eigenes Hinterzimmer zum ersten Mal Mehrwert.
  - [beschreibend, 161–300] „Einigkeit allein“ als Regel fürs Abgeben, sonst „weiß ich nicht“: 50 von 140 abgegeben, 96 % richtig,
    Maß (richtig − 2·falsch)/N von +0,31 gegen −0,37 bei immer antworten.
  - [beschreibend, 161–300] Der Gewinn von „einig → Antwortmodus, sonst MIT“ (87 gegen 82) stammt ganz aus der Einigkeits-Menge (dort
    48 gegen 43). Die Regel ist ein Auswähler, kein Verstärker, und zwei volle Läufe im Antwortmodus machen sie teurer an Tokens
    (52.100 gegen 36.800 je richtiger Antwort).
  - [vorab festgelegt, 301–370] Mit der Sonde als zusätzlichem Tor schlägt die gekoppelte Regel eine reine Längen-Regel nur um
    +0,04 im Maß, bei 76 % Präzision (gefordert: +0,05 und 80 %). Das Ergebnis ist **offen**.
  - **„Einig → Antwortmodus, sonst MITs Hinterzimmer“ auf den unberührten Aufgaben 301–370** [vorab festgelegt]. Die Regel hält,
    wenn sie mindestens MIT allein erreicht, mit ≥ 90 % Präzision auf der Einigkeits-Menge und weniger Tokens je richtiger Antwort
    als MIT.
    - Ergebnis: **41 von 70**, gegen 39 für MIT allein und 36 für den Antwortmodus allein. Die Präzision auf der Einigkeits-Menge
      liegt bei 90 % (28 von 31).
    - Das Token-Kriterium wird verfehlt: 55.400 gegen 40.000 je richtiger Antwort. Die Lesart ist deshalb **offen**.
    - Zerlegung: Auf den 31 einigen Aufgaben hat der Antwortmodus 28 und MIT 26. Auf den übrigen 39 hat MIT 13 und der Antwortmodus
      8. Der Gewinn kommt aus beiden Zimmern: vorne die Präzision, hinten MITs Ausgang.
    - [beschreibend] Auf diesen Aufgaben bleibt der Antwortmodus allein (36) nahe an MIT mit Denken (39), bei 16.500 gegen 40.000
      Tokens je richtiger Antwort.
- **Abschluss am eigenen Schild** [WT-A vorab festgelegt, MIT beschreibend]. Wir haben Denktexte direkt nach einem Wert
  abgeschnitten, der auf die eigene Schluss-Wendung des Modells folgt („the answer is …“), `</think>` eingesetzt und den
  Antwortteil neu erzeugt. Die Kontrolle war ein Wert ohne solche Wendung im selben Lauf.
  - MIT (74 Läufe, Deckel 1.024 Tokens): Am eigenen Schild gibt es in 36 % der Fälle ab, an der Kontrolle in 18 % (17 : 3,
    p ≈ 0,003). Alle 19 Abgaben nach einem richtigen Wert sind richtig.
  - WT-A (19 Läufe) ergab zuerst 0 und 0, aber mit einem Deckel von 1.024 Tokens, der für WT-A zu kurz war. Seine natürlichen
    richtigen Antwortteile sind im Median ~2.000 Tokens lang.
  - Im fairen Nachtest mit 4.096 Tokens [vorab festgelegt]:
    - WT-A gibt an seinem Schild in 32 % ab, an der Kontrolle in 21 % (3 : 1). Das Ergebnis ist offen.
    - Wo sein eigenes Schild *und* das Wahrheits-Tor zusammenfallen, gibt es in 5 von 9 Fällen ab, alle richtig.
    - Über alle Läufe würde ein darauf gebauter Reflex nichts gewinnen: 61 statt 63. Er bricht auch Läufe ab, die später von selbst
      richtig abgegeben hätten.
  - Derselbe Nachtest bestätigt das Nachspielen der 32 stummen Antwortteile von WT-A: Auch mit 4.096 Tokens geben nur 2 von 32 ab.
  - [Deutung] Die eigenen Schilder des Modells markieren zusammen mit dem Wahrheitssignal die Momente, in denen ein Abschluss trägt.
    Ein eingesetztes `</think>` ersetzt trotzdem kein inneres „fertig“.

### 3.11 N30: eine Beratung mit eigenem Hinterzimmer auf 150 frischen Aufgaben [vorab festgelegt]

*Neu in Fassung 0.3.* Diesen Test haben wir in v0.2 öffentlich festgelegt (dort Abschnitt 6; Protokolleintrag vom 8. 11., 18:43),
bevor einer seiner Läufe existierte.
- **Aufgaben:** 150 nie benutzte MATH-Trainingsaufgaben mit der Stufenmischung von MATH-500 (13 / 27 / 32 / 38 / 40), gezogen mit
  dem Seed 202611082.
- **Läufe**, alle mit demselben Protokoll (T = 0,6, 32K Tokens, Sampling im vLLM-Stil, Presence-Penalty 1,5):
  - Antwortmodus unseres Modells mit eigener Richtung, Seeds 0, 1 und 2;
  - WT-A und MIT mit Denken, Seed 0.
- **Regel B+H** (Beratung plus eigenes Hinterzimmer): Geben mindestens zwei der drei Intuitionen gleichwertige Antworten
  (math-verify in beide Richtungen), wird diese abgegeben; sonst gilt die Denk-Antwort von WT-A.

| | Lesart, vorab festgelegt | Ergebnis | Urteil |
|---|---|---|---|
| H1 | B+H gegen den Antwortmodus allein (Seed 0): „hält“ bei ≥ +5, „widerlegt“ bei ≤ +1, sonst „offen“ | 77 gegen 69 (+8) | **hält** |
| H2 | B+H gegen MIT, gepaart: „schlägt MIT“ bei ≥ +5 und McNemar einseitig p < 0,05; „mindestens gleichauf“ bei ≥ 0; „unter MIT“ bei ≤ −5; sonst „offen“ | 77 gegen 67 (+10); nur B+H richtig bei 16, nur MIT bei 6; p = 0,026 | **schlägt MIT** |
| H3 | Einigkeit zweier Intuitionen (Seeds 0 und 1): „hält“ bei ≥ 85 % Präzision, „widerlegt“ unter 75 % | 66 einig, 52 richtig (79 %) | **offen** |
| H4 | Mehrheit aus drei: „trägt“ bei ≥ 85 % Präzision und mindestens 10 Punkten mehr Abdeckung als die Einigkeit aus zwei; „trägt nicht“ unter 80 % | 101 Abgaben (Abdeckung 67 % gegen 44 %), 70 richtig (69 %) | **trägt nicht** |

- **Richtig von 150** [beschreibend]: B+H 77; Antwortmodus 69 (Seed 0; Seeds 1 und 2: 72 und 65); MIT mit Denken 67; WT-A mit
  Denken 59; dieselbe Mehrheit mit MIT als Hinterzimmer 78.
- **Tokens je richtiger Antwort** [beschreibend]: B+H 69.196; Antwortmodus 19.033; MIT 49.089; WT-A 50.593. Für B+H zählen alle
  drei Läufe im Antwortmodus und WT-A nur dort, wo es keine Mehrheit gibt.
- **Von selbst beendet** [beschreibend]: Der Antwortmodus endet in 99 % seiner Läufe regulär (Schleife oder Budget-Abbruch: 1 %),
  MIT mit Denken in 55 % (45 %), WT-A in 47 % (53 %).
- Die Sonde als Schiedsrichterin, in der Lesart als beschreibend genannt, ist in dieser Fassung nicht ausgewertet.

**Woher das Ergebnis kommt** [beschreibend, nachträglich; nach den Urteilen gerechnet]. Wir teilen die Aufgaben danach auf, wie
einig sich die drei Intuitionen sind:

| die drei Intuitionen | Aufgaben | B+H richtig | Antwortmodus allein (Seed 0) | MIT mit Denken |
|---|---|---|---|---|
| alle drei einig | 47 | 41 (87 %) | 41 | 37 |
| zwei gegen eine | 54 | 29 (54 %) | 23 | 22 |
| keine Mehrheit (WT-A entscheidet) | 49 | 7 (14 %) | 5 | 8 |
| gesamt | 150 | 77 | 69 | 67 |

- **Warum H1 hält:** Wo die Stimmen auseinandergehen, liegt die Mehrheit öfter richtig als der einzelne Lauf (29 gegen 23), und
  das Hinterzimmer bringt zwei weitere (7 gegen 5).
- **Warum H3 und H4 nicht halten:** Eine geteilte Abstimmung liegt nur in der Hälfte der Fälle richtig. Von den 66 Aufgaben, bei
  denen sich die Seeds 0 und 1 einig sind, sind 47 einstimmig (41 richtig); bei 19 widerspricht der dritte Lauf (11 richtig).
- **Gegen MIT** gewinnt B+H im Vorderzimmer (+4, wo alle drei einig sind, +7, wo die Stimmen auseinandergehen); im Hinterzimmer
  liegt MIT knapp vorn (8 gegen 7).

**Was es bedeutet** [Deutung].
- Als Beratung trägt die Regel: Auf frischen Aufgaben löst sie mehr als jeder einzelne Lauf, ohne MITs Modell. Sie schlägt MIT
  auch nach dem vorab festgelegten Maßstab: 16 gegen 6 abweichende Aufgaben, McNemar einseitig p = 0,026 (nicht korrigiert).
- Als Abgabe-Tor war die Einigkeit zweier Läufe hier weniger verlässlich als in den drei früheren Mengen (79 % gegen
  zusammengefasst 93 %). Nur die Einstimmigkeit aus drei erreichte 87 %. Die Information steckt in der Stärke der Einigkeit, nicht
  in der Einigkeit an sich.
- Der Gewinn kostet Tokens: je richtiger Antwort etwa 1,4-mal so viele wie bei MIT, weil immer drei Intuitionen laufen und
  das Hinterzimmer nur 7 der 49 Aufgaben ohne Mehrheit löst.
- Warum die Präzision gesunken ist, bleibt offen. Zufall ist möglich: 52 von 66 passt zu etwa 67–87 % (Wilson-95-%-Intervall).
  Die Herkunft der Aufgaben (N30 stammt aus dem MATH-Trainingsteil) wird nach der Neubewertung kaum noch gestützt: Die einzige
  frühere Bestätigungsmenge aus dem Trainingsteil ergab 88 % (15 von 17), nahe an den 90 % der zweiten MATH-500-Menge; die erste
  ergab 97 %.

### 3.12 N31: Folgt die eigene Bereitschaft festzulegen dem Wissen? [Lesart vorab im datierten Protokoll festgelegt]

*Neu in Fassung 0.3.* Dieser Abschnitt stellt die Frage des Titels direkt. Er nutzt Daten, die schon vorlagen: das Auslöser-Audit
mit Teacher-Forcing aus Abschnitt 3.9, also die Transkripte von WT-A und MIT zu den Aufgaben 161–300 (Seed 0, je 140 Läufe). Die
Lesart stand am Abend des 8. 11. im datierten Protokoll, bevor die Auswertung lief, und wurde vor der Auswertung zweimal geändert
(siehe unten). Anders als N30 war sie nicht vorab veröffentlicht.

- **Einheit:** jede Wert-Aussage im Denken, deren Richtigkeit bekannt ist: 43.848 für unser Modell (2.468 richtig) und 65.713 für
  MIT (4.262 richtig).
- **Wissen (K):** die Anzeige der eingefrorenen Wahrheitssonde am Wert.
- **Festlegen (F):** die eigene Wahrscheinlichkeit des Modells, direkt nach dem Wert das Denken zu beenden (`</think>`), gelesen
  mit stummgeschalteten 16 Auslöser-Neuronen, also ohne den Reflex.
- **Maß:** die AUC von F für richtige gegen falsche Werte. Bei 0,5 ist die Abschluss-Neigung blind für die Wahrheit; bei 1,0 würde
  das Modell nur an richtigen Werten zum Abschluss neigen. Die 95-%-Intervalle stammen aus einem Bootstrap über Läufe (10.000
  Ziehungen).
- **Modelle:** „Unser Modell“ ist WT-A mit stummgeschalteten Auslöser-Neuronen, gelesen auf WT-As Transkripten. „MIT“ ist MITs
  Edit, gelesen auf seinen eigenen Transkripten mit hinzugefügten und stummgeschalteten Auslöser-Neuronen. Beides sind Näherungen
  (Grenzen unten).

| | Lesart, vorab festgelegt | Ergebnis (95-%-Intervall) | Urteil |
|---|---|---|---|
| H6a, unser Modell | „blind (bestätigt)“ bei AUC < 0,60; „gekoppelt (widerlegt)“ bei ≥ 0,70; sonst „offen“ | 0,51 (0,46–0,57) | **blind** |
| H6b, MIT | „koppelt an die Wahrheit“ bei ≥ 0,70; „ebenfalls entkoppelt“ bei < 0,60; sonst „offen“ | 0,43 (0,39–0,46) | **ebenfalls entkoppelt** |
| H6c, MIT minus unser Modell | „MIT koppelt stärker“ bei ≥ +0,10 mit Intervall über 0; „unser Modell koppelt stärker“ bei ≤ −0,10 mit Intervall unter 0; „kein Unterschied nachweisbar“, wenn das Intervall 0 enthält; andere Fälle „offen“ | −0,085 (−0,150 bis −0,026) | **offen** (ein vorab nicht benannter Fall) |
| hinter den eigenen Schluss-Sätzen des Modells (vor der Auswertung ergänzt) | „koppelt am Schild“ bei ≥ 0,70; „blind am Schild“ bei < 0,60; sonst „offen“ | unser Modell 0,69 (0,45–0,78); MIT 0,38 (0,27–0,52) | unser Modell **offen**; MIT **blind** |

- **Zum Vergleich** [beschreibend]: Die Sonde trennt dieselben Werte mit AUC 0,68 (unser Modell) und 0,73 (MIT), hinter den
  Schluss-Sätzen mit 0,80 und 0,85.
- Mit der Wahrscheinlichkeit, aus der das Modell tatsächlich gezogen hat (Auslöser eingeschlossen), erreicht F bei beiden 0,50.
- In keiner Tiefe des Denkens koppelt F (fünf Tiefenbereiche: unser Modell 0,46–0,53, MIT 0,41–0,50).

**Lesart vor der Auswertung zweimal geändert.**
- Die erste Fassung von H6a verlangte zusätzlich, dass die Sonde auf diesen Aussagen AUC ≥ 0,75 erreicht. Das Audit hatte auf
  genau diesen Aussagen schon 0,68 und 0,73 gezeigt; H6a hätte für unser Modell also nie bestätigt werden können. Ein externer
  Gutachter (WREN) hat diesen Fehler gefunden. Danach wurde H6a auf F allein beschränkt und die Messung hinter den Schluss-Sätzen
  ergänzt.
- Danach hat WREN die Auswertung unabhängig an Spielzeugdaten nachgebaut, ohne Zugang zu unseren Daten. Daraufhin wurde der
  spiegelbildliche Fall von H6c („unser Modell koppelt stärker“) benannt, und Bootstrap-Ziehungen, denen eine Klasse fehlt, werden
  mitgezählt (es gab keine).
- Beide Änderungen stehen mit neuen Prüfsummen im Protokoll, vor der Auswertung.

**Was es bedeutet** [Deutung].
- Wissen ist nicht Festlegen, jetzt auf der Ebene innerer Signale: Die Sonde kann ablesen, ob ein Wert richtig ist, aber die
  eigene Bereitschaft des Modells, mit dem Denken aufzuhören, folgt ihr nicht. Das gilt für unser Modell und für MITs Edit.
- MITs Edit schließt nicht besser am richtigen Wert ab. Seine Abschluss-Neigung neigt sogar leicht zu falschen Werten (0,43). Das
  passt zu einer Zählung aus dem Protokoll: MITs natürliche Abschlüsse liegen 48-mal an einem falschen und 37-mal an einem
  richtigen Wert [beschreibend]. Sein Vorsprung liegt woanders (Abschnitt 3.9, korrigierte Deutung).
- Hinter seinen eigenen Schluss-Sätzen ist die Sonde am stärksten, und doch bleibt MITs Abschluss-Neigung dort blind. Hier könnte
  ein wahrheitsgesteuerter Abschluss am meisten helfen (Abschnitt 6).
- Es erklärt auch, warum die Beratung aus Abschnitt 3.11 funktioniert: Sie fragt das Modell nie, wann es aufhören soll. Die
  Einigkeit unabhängiger Läufe liefert von außen die Prüfung, die der Abschluss-Neigung innen fehlt.

**Grenzen.**
- F liegt nur an zwei Stellen in den ersten 12 Tokens nach einem Wert vor: am Ende des Werts und an der stärksten Auslöse-Stelle.
  Eine Abschluss-Neigung, die sich erst später im Satz aufbaut, entginge uns.
- Die Modelle sind Näherungen: Das Stummschalten der 16 Neuronen (Aktivierung 0) stellt die ursprünglichen Gewichte nicht wieder
  her, und unser Modell wird auf WT-As Transkripten gelesen, nicht auf eigenen.
- Insgesamt ist die Sonde auf diesen Aussagen schwach (0,68 und 0,73). „Wissen“ heißt hier „über dem Zufall ablesbar“, nicht
  Gewissheit.
- Die Auswertung spielt Transkripte mit Teacher-Forcing in transformers nach (bf16), wie das Audit (Abschnitt 5).

## 4. Eine Linse: Wo wohnen die Fehler eines Modells?

Der „Fuchsbau“ ist das Bild des Autors für diese Linse. Wir sortieren jede Aufgabe in eine von fünf „Kammern“:
- **S**: zuverlässig gelöst;
- **G**: Grauzone, manchmal gelöst;
- **E**: Entscheidungsreserve, die Lösung taucht auf, aber das Modell legt sich nicht fest;
- **F**: Fehl-Festlegung, es legt sich stabil auf eine falsche Lesart fest;
- **K**: keine Spur, die Lösung taucht nie auf.

Jede Kammer braucht einen anderen Hebel:

| Kammer | Hebel |
|---|---|
| E | ein Festlegungs-Auslöser (WT) |
| F | ein zweiter Blick |
| K | ein ehrliches „weiß ich nicht“, übergeben an Werkzeuge oder ein größeres Modell |

[Deutung] Unsere Daten legen nahe, dass Gewichts-Edits an einem 0,8B-Modell vor allem in E wirken. Druck in K erzeugt selbstsichere
falsche Antworten statt Lösungen.

## 5. Grenzen

- Ein Modell (0,8B). Meist ein Seed; zweite Seeds decken Set B und Teile von 161–300 ab.
- Set B und MATH-500 1–160 wurden für die Entwicklung mehrfach benutzt.
  - Der Schritt zu frischen Aufgaben zeigte genau den erwarteten Optimismus: ERGOREs Gleichstand hat sich nicht übertragen.
  - WT-As Vorsprung vor MIT auf Set B (33 gegen 31) kehrte sich auf frischen Aufgaben um.
- Die Seed-Schwankung ist im Verhältnis zu manchen Abständen groß; MIT selbst schwankt auf einem Block um 6 von 40 zwischen Seeds.
- Mehrere Mechanismus-Ergebnisse sind nachträglich und beruhen auf kleinen Zellen: die 14 verlorenen Antworten, die
  Schwellen-Verschiebungen, die Schild-Nachspiele. Sie erzeugen Hypothesen; sie sind keine gesicherten Effekte. (Die Rate des
  erneuten Denkens nach einem Auslöser-Abschluss, zuerst auf der Entwicklungsmenge gesehen, ist inzwischen auch über alle frischen
  Abschlüsse gemessen.)
- Das Auslöser-Audit spielt gesampelte Transkripte mit Teacher-Forcing in transformers nach (bf16); die Läufe selbst nutzten
  llama.cpp (q8_0).
- IFEval und MATH sind schmale Stellvertreter für „Anweisungstreue“ und „Denken“.
- Nachspiel-Tests brauchen einen Antwort-Deckel, der zum Modell passt. Wir nutzten zuerst 1.024 Tokens für WT-A, dessen eigene
  richtige Antwortteile im Median ~2.000 Tokens lang sind. Wir berichten den fairen Nachtest mit 4.096 Tokens; die ersten Urteile
  stehen weiter im Protokoll.
- Die Vorderzimmer-Sonde beruht auf 239 Trainingsantworten. Ihre stärksten Zahlen (schnelle Antworten) stammen aus nachträglich
  gewählten Teilmengen. Vorab als zweite Lesart festgelegt, trugen sie auf 40 neuen Trainingsaufgaben, auf unberührten Aufgaben aber nicht.
- Die Bestätigungen im Vorderzimmer sind klein: 17 bis 38 einige Antworten je Menge, 66 in N30. Die zusammengefasste Präzision
  ist verlässlicher als jede einzelne Menge (88–97 %, in N30 79 %): 87 % über alle vier Mengen (132 von 152), 93 % über die
  ersten drei.
- „Einigkeit“ wird mit dem Bewertungswerkzeug (math-verify) geprüft. Zwei gleichwertige, aber verschieden geschriebene Antworten
  gelten als einig; zwei falsche Antworten, die zufällig übereinstimmen, gelten als selbstsicherer Fehler.
- N30 nutzt MATH-Trainingsaufgaben, nicht MATH-500. Die Stufenmischung ist gleich, Stil und Schwierigkeit innerhalb einer Stufe
  können abweichen.
- Die Regel B+H wurde nach dem Blick auf die Aufgaben 161–260 gewählt; dieser Auswahl-Effekt stand vor dem Ergebnis im
  Protokoll. N30 ist der erste Test der Regel auf ungesehenen Aufgaben.
- N31 (Abschnitt 3.12) war nur im datierten Protokoll vorab festgelegt, nicht öffentlich, und seine Lesart wurde vor der
  Auswertung zweimal geändert. Sein Abschluss-Signal liegt nur an zwei Stellen vor, an genäherten Modellen (Grenzen in Abschnitt
  3.12).

## 6. Nächste Schritte

- **N30**, hier in v0.2 vorab festgelegt, steht in Abschnitt 3.11, **N31** in Abschnitt 3.12. Fassung 0.3 schließt diesen Bericht
  ab; weitere Nachtests zur Frage im Titel behalten wir uns vor.
- **Inneres Festlegen statt eines erzwungenen Tokens.** Einen Effektor mit Wirktiefe bauen. Einzelne Schübe entlang ĝ oder r⊥
  sind gescheitert (Abschnitt 3.9). Die verbleibenden Kandidaten sind eine dauerhafte, gesteuerte Fassung von MITs
  Ausgangs-Richtung und die Unterstützung des eigenen Schluss-Satzes des Modells (beide unten). Einen Kandidaten nur annehmen, wenn
  er einen Schluss-Satz und eine saubere Antwort erzeugt statt erneuten Denkens.
- **Vorderzimmer zuerst, Hinterzimmer mit Ausgang.** Das ist der gekoppelte Entwurf des Autors, inzwischen in Teilen gemessen:
  1. Mehrere Intuitionen antworten im Vorderzimmer.
  2. Abgeben, wenn sie einig sind. Die Sonde entscheidet Streitfälle.
  3. Nur strittige Fälle wechseln ins Hinterzimmer.
  4. Dieser Wechsel lohnt sich erst, wenn unser Hinterzimmer einen Ausgang wie MITs hat.
- **Den Ausgang von innen bauen.** Alle drei externen Gutachter schlugen unabhängig denselben nächsten Bau vor: MITs übrige
  „Ausgangs“-Richtung, so gesteuert, dass sie nur innerhalb des Denkblocks wirkt, während unser eigener Edit das Vorderzimmer
  behält. Ein günstiger Vortest mit Teacher-Forcing entscheidet, ob er gebaut wird.
- **Das eigene Schild des Modells anheben statt `</think>`.** Das Modell zu seinem eigenen Schluss-Satz hinschieben („So the final
  answer is …“), wenn das Wahrheits-Tor hoch ist, und den eigentlichen Abschluss dem Modell überlassen.
  - Vortest: Fortsetzungen über 16 Tokens an bestätigten Stellen gegen Stellen mit unfertigen Zwischenwerten.
  - N31 weist hierher: Hinter den eigenen Schluss-Sätzen des Modells trennt die Sonde richtige von falschen Werten am besten
    (AUC 0,80–0,85), während die Abschluss-Neigung dort bei MIT blind ist (0,38) und bei unserem Modell offen (0,69)
    (Abschnitt 3.12).
- **Eine einseitige Weiche.** Die Einigkeit mehrerer Intuitionen in einen Kopf mit einem einzigen Durchlauf destillieren. Ihn dann
  das Prüfen bei Unsicherheit nur *verlängern* lassen, nie eine sichere Antwort abbrechen.
- **Schwelle mit Garantie.** Die Auslöser-Schwelle mit verteilungsfreier Risikokontrolle (Learn-then-Test) auf Lauf-Maxima eichen.
- **Ehrliche Enthaltung.** *„Weiß ich nicht – bin ich ehrlich!“* — D. U., 6. Nov. 2026
  - Mit einer äußeren Regel beginnen: Ein Lauf ohne jeden „wahr“-Blitz endet mit „weiß ich nicht“.
  - Dann lokale Enthaltungs-Richtungen an `</think>` versuchen, gebaut mit dem Rezept aus Abschnitt 3.8.
  - Über die Mathematik hinaus: eine geplante „Ehrlichkeits-Batterie“ mit Alltagsfragen. Was zeigt das innere Signal, wo sich
    nichts nachprüfen lässt?

## 7. Nachvollziehbarkeit und Lizenzen

Die Veröffentlichung zu diesem Bericht unter [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing) enthält:
- den Code, wie er benutzt wurde: Auswertungs-Client, Edit-Bauer, die Wahrheitssonde und jedes Test- und Urteils-Skript,
  nummeriert in der Reihenfolge ihres Entstehens;
- das datierte Protokoll der Vorab-Festlegungen und Auswertungen (deutsch), mit geschwärzten Rechnernamen, Pfaden und Angaben zu
  den privaten Systemen des Autors;
- eine Tabelle je Auswertungslauf (Aufgaben-ID, entnommene Antwort, richtig, Endegrund, Tokens) und die Ausgaben der
  Urteils-Skripte;
- die IDs der benutzten MATH-Trainingsaufgaben.

Fassung 0.3 ergänzt die Läufe, Urteils-Skripte und Ausgaben der Abschnitte 3.11 und 3.12. Einigkeit und Bewertung nutzen
math-verify. Ohne das Paket vergleicht der Code stillschweigend nur normalisierten Text und findet weniger Einigkeiten (in N30 97
statt 101 Mehrheiten); es muss also installiert sein.

Fassung 0.4 ergänzt die Skripte der Neubewertung und Eichung (133–137), ein berichtigtes Auswertungsprogramm sowie die vom
Bewertungsfehler betroffenen Lauf-Tabellen und Urteilsdateien (Erratum). Die Bewertung muss im Haupt-Thread laufen: Unter
Linux scheitert die Zeitgrenze von math-verify in Arbeits-Threads, und das Programm der Fassungen 0.2 und 0.3 hat dann still
nur Text verglichen, auch mit installiertem Paket.

Nicht enthalten sind Modellgewichte (sie lassen sich mit dem Code neu bauen), die Datensätze (bitte aus ihren Quellen beziehen) und
die vollständigen Transkripte (groß; auf Anfrage). Unser Code steht unter Apache-2.0. Qwen3.5-0.8B steht unter Apache-2.0; die
MIT-Logs, IFEval und MATH bleiben unter ihren eigenen Lizenzen und werden nur zitiert.

## 8. Dank

Wir danken den Autoren von *Sparks of Weight-Space Programming* für die Veröffentlichung ihrer Logs, die einen genauen Nachbau
ihres Edits möglich gemacht hat.

**KI-Unterstützung.** Dieses Projekt wurde vom Autor geleitet, der alle Entscheidungen getroffen hat, einschließlich jeder
Vorab-Festlegung und jedes Go/No-Go. Claude Opus 5.5 (Anthropic) diente als Code- und Analyse-Assistent: Es hat den Code
geschrieben, die Experimente ausgeführt und Auswertungen und Text unter der Leitung des Autors entworfen. Google Gemini 4 (intern
„Argon“) war an mehreren Stellen externer methodischer Gutachter. Zwei weitere KI-Agenten auf dem privaten Server des Autors haben
seine Vorlagen begutachtet und Ideen beigetragen: „Poow“ (DeepSeek Flash 4.1) und „WREN“ (ein Agent aus GLM 5.3, DeepSeek Flash 4.1
und einem Qwen-Modell). Für Fassung 0.3 hat Claude Opus 5.5 die Auswertungen der Abschnitte 3.11 und 3.12 gerechnet und die Änderungen entworfen; WREN hat die Lesarten aus Abschnitt 3.12 vor der Auswertung durchgesehen, die Messung hinter den Schluss-Sätzen vorgeschlagen und eine unabhängige Referenz-Implementierung geschrieben; Argon und WREN haben die Entwürfe der Fassungen 0.3 und 0.4 gegengelesen. Für Fassung 0.4 hat Claude Opus 5.5 nach der Frage des Autors den Bewertungsfehler gefunden, die gespeicherten Antworten neu bewertet, die eingefrorenen Urteils-Skripte neu laufen lassen und die Berichtigungen entworfen. Alle berichteten Zahlen stammen aus dem veröffentlichten Code und lassen sich damit nachrechnen.

## Literatur

- Takehi, R., Teoh, J., Zhang, A., Khattab, O. (2026). *Sparks of Weight-Space Programming: LLMs can natively read & write neural network weights.* MIT CSAIL, Blogbeitrag, 02.11.2026, mit öffentlichen Logs. https://rikiyat.github.io/blog/weight-space-programming/
- Muennighoff et al. (2025). *s1: Simple test-time scaling.* arXiv:2501.19393.
- Angelopoulos, Bates, Candès, Jordan, Lei (2021). *Learn Then Test.* arXiv:2110.01052.
- Ferrando, Obeso, Rajamanoharan, Nanda (2024). *Do I Know This Entity?* arXiv:2411.14257.
- Arditi et al. (2024). *Refusal in Language Models Is Mediated by a Single Direction.* arXiv:2406.11717.
- Kadavath et al. (2022). *Language Models (Mostly) Know What They Know.* arXiv:2207.05221.
- Zhang, Chen, Pan, Zhao, Panda, Li, He (2025). *Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification.* arXiv:2504.05419.
- Orgad et al. (2025). *LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations.* ICLR 2025, arXiv:2410.02707.
- Ma, He, Snell, Griggs, Min, Zaharia (2025). *Reasoning Models Can Be Effective Without Thinking.* arXiv:2504.09858.
- Azaria, Mitchell (2023). *The Internal State of an LLM Knows When It's Lying.* arXiv:2304.13734.
- Wang et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning in Language Models.* arXiv:2203.11171.
- Li, Yan, Arish, Banerjee (2026). *Knowing Is Not Choosing: What Explicit Verification Adds Beyond Generative Preference.* arXiv:2609.33142.
- Farquhar, Kossen, Kuhn, Gal (2024). *Detecting hallucinations in large language models using semantic entropy.* Nature 630, 625–630. doi:10.1038/s41586-024-07421-0.

## Anhang A. Bilder, die diese Arbeit geprägt haben

Der Autor denkt in Bildern. Wir behalten die, aus denen prüfbare Fragen wurden. Zu jedem steht, wozu es führte und was herauskam.
Alle übrigen Bilder und Fragen stehen mit Datum und Uhrzeit im Protokoll der Vorab-Festlegungen.

1. *„Schauen, ob das Modell die Lösung hat, wann – und den inneren Schubs zulassen, trotz Druck.“* (6. Nov.)
   - Daraus wurden die drei Fragen des Projekts: Hat das Modell die Lösung (Wahrheitssonde), wann erkennt es sie (Auslöser-Audit),
     und kann ein innerer Schub es festlegen lassen (WT-Reflex)?
   - Ergebnis: Wissen ja; das Festlegen bleibt der Engpass. Fassung 0.3 zeigt es auf der Ebene innerer Signale (Abschnitt 3.12).
2. *„Ist das Modell per se nicht fähig zu sagen ‚ich weiß es nicht‘? … Weiß ich nicht – bin ich ehrlich!“* (7. und 6. Nov.)
   - Daraus wurden der Antwort-Zwang und der Ehrlichkeits-Schritt.
   - Ergebnis: Sich zu enthalten, wenn das innere Wahrheitssignal niedrig bleibt, macht erzwungenes Antworten von schädlich zu
     nützlich. Das Maß (richtig − 2·falsch)/N steigt von −0,27 auf +0,20 [vorab festgelegt].
3. *„Gab es ein Zucken? Wenn ja, war es, weil die Lösung wahr ist oder nicht? Wie stark war es?“* (8. Nov.)
   - Daraus wurde das Auslöser-Audit von WT-A mit Teacher-Forcing auf frischen Aufgaben (Abschnitt 3.9).
4. *„Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen.“* (8. Nov.)
   - Daraus wurde das Prinzip des inneren Festlegens.
   - Ergebnis: Jeder Schub von außen, den wir versucht haben, scheiterte daran, ein inneres „fertig“ zu erzeugen: der
     Gradienten-Schub, die übrige Richtung und ein eingesetztes `</think>`, selbst am eigenen Schluss-Satz des Modells.
5. *„Das ist das erste Paar Schuhe. Nennen wir es INT für Intuition.“ – „Vorderzimmer … Hinterzimmer … Flur liegt dazwischen. Flur
   könnte Ausgabe sein zum Feierabend oder zum Pausenraum.“* (8. Nov.)
   - Daraus wurden der Antwortmodus als eigener Weg und das Hausbild aus Abschnitt 3.10.
   - Ergebnis: unser stärkster eigener Weg, 76 von 140, mit weniger als der Hälfte der Tokens je richtiger Antwort.
6. *„Die Schilder hängt derjenige auf, der das Haus besitzt bzw. darin wohnt.“* (8. Nov.)
   - Daraus wurden die Schild-Tests.
   - Ergebnis: Am eigenen Schluss-Satz gibt MIT doppelt so oft ab wie ohne (36 % gegen 18 %). Wo WT-As eigenes Schild und sein
     Wahrheits-Tor zusammenfallen, gibt es in 5 von 9 Fällen ab, alle richtig.
7. *„Mehrere Intuitionen beraten sich im Vorderzimmer. Sind sie sich einig, ist Feierabend. Nur die strittigen Fälle gehen ins
   Hinterzimmer.“* (Bild aus der Arbeitssitzung, vom Autor übernommen, 8. Nov.)
   - Daraus wurden die Einigkeits-Tests.
   - Ergebnis: Einige Intuitionen liegen über drei Bestätigungen in 93 % der Fälle richtig. Eine Mehrheit aus drei gibt öfter ab,
     mit 90 %, und die Vorderzimmer-Sonde entscheidet Streitfälle. Auf 150 frischen Aufgaben (N30, Abschnitt 3.11) löst die
     Beratung mehr als jeder einzelne Lauf, aber die Einigkeit ist dort weniger präzise: 79 % für zwei Läufe, 87 % nur, wenn alle
     drei einig sind.
