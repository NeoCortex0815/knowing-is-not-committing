# Wissen ist nicht Festlegen

### MITs Gewichts-Edit nachgebaut und ein wahrheitsgesteuerter Reflex in ein 0,8B-Denkmodell programmiert · Zwischenbericht

**Dave Uhlemann (NeoCortex)** · unabhängiger Forscher

Code, Daten und Vorab-Protokoll: [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing) · Fragen und Korrekturen gern als GitHub-Issue.

> *„Schauen, ob das Modell die Lösung hat, wann – und den inneren Schubs zulassen, trotz Druck.“*
> — Dave Uhlemann, 6. Nov. 2026

*Entwurf v0.2 · 08.11.2026 · Arbeitszeitraum 4.–8. November 2026 · nicht begutachtet · mit KI-Unterstützung erstellt (siehe
Abschnitt 8); alle Messungen liefen lokal auf den Rechnern des Autors. Deutsche Fassung; maßgeblich ist die englische Fassung.*

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
>
> **Was wir mit „Wissen“ meinen.** Eine eingefrorene lineare Sonde auf den inneren Zuständen des Modells stuft den richtigen Wert als
> wahr ein, solange er im Kontext steht. Das ist eine Messung, keine Aussage über Gewissheit.

**Kurz gesagt.** MITs Gewichts-Edit verringert die Denkschleifen von Qwen3.5-0.8B. Wir haben diesen Edit unabhängig nachgebaut,
einen wahrheitsgesteuerten Reflex in 16 MLP-Neuronen geschrieben und eine Reihe vorab festgelegter Tests auf frischen
MATH-500-Aufgaben durchgeführt.
- Drei Befunde tragen den Bericht:
  - (1) Das Modell *weiß* eine richtige Antwort oft lange, bevor es sich auf sie *festlegt*. Eine lineare Sonde liest die Wahrheit
    im Denktext. Unser Reflex schließt das Denken im richtigen Moment, aber ein von außen gesetzter Abschluss ist keine
    Festlegung: Auf frischen Aufgaben denkt das Modell nach 77 % seiner Abschlüsse weiter.
  - (2) Ohne Denkblock (im Antwortmodus) kommt unser editiertes Modell nahe an MITs Edit mit Denken heran: 71 gegen 80 von 140,
    bei weniger als der Hälfte der Tokens je richtiger Antwort.
  - (3) Geben zwei unabhängige Läufe im Antwortmodus dieselbe Antwort, sind 91 % davon richtig (zusammengefasst über drei Mengen).
- Allein die Sampling-Einstellungen verschieben MITs eigenen Edit von 25 % auf 55 %.
- Wir berichten jede widerlegte Lesart neben den bestätigten und legen den nächsten Test öffentlich vorab fest.

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
   - **Frische Aufgaben 161–300: 65 gegen 80 von 140** (7 : 22, p = 0,008; −10,7 Punkte, 95-%-KI −18,0 bis −3,4). Die vorab
     festgelegte Lesart lautet „MIT-Niveau nicht erreicht“.
   - Ein zweiter Seed auf einem Block (261–300) verkleinert den Abstand dieses Blocks von 14 : 22 auf 16 : 16. [beschreibend] Der
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
   - **Entwicklungsmenge** (n = 60): 31 gegen 23 richtig gegenüber demselben Modell ohne Auslöser, und mit einem zweiten Seed
     wieder +8 [beschreibend]. 64 % weniger Tokens auf Aufgaben, die beide lösen. Das vorab festgelegte Tor blieb geschlossen, weil
     eine Sonden-Prüfung scheiterte.
   - **Frische Aufgaben 161–300**, Test festgelegt, bevor einer dieser Läufe existierte (H-WT2): WT-A schließt in **65 %** der
     Gelegenheiten direkt nach dem richtigen Wert, MIT in **36 %** (p = 0,0001). Seine schnellen Abschlüsse sind zu 61 % richtig,
     gegen 44 %. [vorab festgelegt]
   - **Trefferquote dort: 61 gegen 80 von 140** (−13,6 Punkte, gepaarter Bootstrap, 95-%-KI −21,4 bis −5,7). [beschreibend] Mit
     einem zweiten Seed auf 161–260: 47 gegen 58 von 100.
7. **Warum der Auslöser nicht reicht** [beschreibend, nachträglich]:
   - **Ein einziger Erfolgsweg:** 51 der 61 richtigen Antworten von WT-A folgen auf Abschlüsse, die der Auslöser bewirkt hat
     (Abschnitt 3.9). MIT prüft zusätzlich ~12.000 Tokens länger und legt sich dann selbst fest (44 von 80).
   - **Ein erzwungener Abschluss ist kein innerer Abschluss:** Nach einem Auslöser-Abschluss öffnet WT-A sein Denken im Antwortteil
     wieder (ein zweites `</think>`), in 83–100 % der Entwicklungsläufe. Auf frischen Aufgaben sind es 77 % aller Abschlüsse und 58
     von 61 richtigen Läufen, gegen 16 % bei MIT.
     - Bei den 32 stummen frischen Läufen, die nie abgeben, sind es 12 von 32. Die drei Zahlen beschreiben verschiedene Gruppen von
       Läufen.
     - WT-As Erfolgsweg ist fast immer: Auslöser-Abschluss, erneutes Denken, dann sein *eigener* zweiter Abschluss, dann die Abgabe.
   - **Tiefe:** Das Wahrheitssignal schwindet mit *Schleifen und Schwierigkeit*, nicht mit der Tiefe im Denktext.
8. **Ein ehrliches „weiß ich nicht“ aus dem inneren Signal.** [vorab festgelegt] Die eingefrorene Wahrheitssonde, gelesen an der
   abgegebenen Antwort, trennt erzwungene Antworten mit AUC 0,83.
   - Sich zu enthalten, wenn sie niedrig bleibt, macht das erzwungene Antworten von schädlich zu nützlich: Das Maß
     (richtig − 2·falsch)/N steigt von −0,30 auf +0,17.
   - 327 der 380 Enthaltungen wären falsch gewesen.
9. **Der Antwortmodus („Vorderzimmer“) ist unser stärkster eigener Weg.** Ohne Denkblock denkt das Modell sichtbar in seiner
   Antwort.
   - Entwicklungsbereich [beschreibend]: Unser Modell mit eigener Richtung löst 77 von 160, genauso viele wie MIT mit Denken
     (22 : 22), mit ~40 % der Tokens.
   - Frische Aufgaben 161–300 [vorab festgelegt]: **71 gegen 80 von 140** für MIT mit Denken (−6,4 Punkte, 95-%-KI −15,0 bis +2,1).
     Nach der vorab festgelegten Lesart ist das „offen“: hält bei ≥ 73, widerlegt bei ≤ 66. Es braucht 16.600 statt 37.700 Tokens
     je richtiger Antwort.
   - MIT selbst erreicht im Antwortmodus nur **59 von 140** (27 : 6 gegen MIT mit Denken, p = 0,0003) [vorab festgelegt]. Ein
     Hinterzimmer lohnt sich, wenn es einen funktionierenden Ausgang hat; unseres hat noch keinen.
   - Der Vorsprung ist kein Artefakt der presence penalty: dieselben +2 mit Strafe 0 und 1,5 (n = 20) [vorab festgelegt]. Das
     Vorderzimmer ist über Seeds nicht stabiler als das Hinterzimmer: 75 % der Aufgaben werden in beiden Seeds gleich gelöst
     [vorab festgelegt, widerlegt].
10. **Das Vorderzimmer weiß, wann es sicher ist: eine Beratung der Intuitionen.** Mehrere Läufe im Antwortmodus antworten
    unabhängig. Sind sie sich einig, gibt das Modell ab; nur strittige Fälle gehen ins Hinterzimmer.
    - **Zwei Intuitionen** [vorab festgelegt, drei Bestätigungen]. Geben zwei Läufe mit verschiedenen Seeds dieselbe Antwort, ist
      sie richtig in **37 von 38** Fällen auf 161–260, in 13 von 17 auf 40 neuen Trainingsaufgaben und in **28 von 31 auf den
      unberührten Aufgaben 301–370**. Zusammengefasst über die drei Mengen sind 78 von 86 richtig (91 %); die zusammengefasste
      Zahl ist beschreibend, weil jede Menge einzeln vorab festgelegt war. Sind die Läufe uneinig, hat der erste Lauf nur in 13–32 %
      recht.
    - **Drei Intuitionen** [vorab festgelegt, „offen“ um einen Punkt]. Eine Mehrheit aus drei gibt auf 62 von 100 Aufgaben ab statt
      auf 38, und 89 % davon sind richtig (Ziel: 90 %). Das Maß (richtig − 2·falsch)/N steigt von +0,35 auf +0,41. Sind sich alle
      drei einig, sind 29 von 29 richtig.
    - **Eine auf Antworttexten trainierte Sonde** [vorab festgelegt; in allen drei Tests „offen“]. Sie liest die Richtigkeit an der
      abgegebenen Antwort mit AUC 0,76–0,85 auf neuen Daten; die auf Denktexten trainierte Sonde erreicht 0,68.
      - Sie bringt nur +0,01 bis +0,05 über Antwortlänge und Schwierigkeit hinaus.
      - Ihr scheinbarer Vorsprung bei schnellen Antworten hat sich auf unberührten Aufgaben nicht wiederholt (0,61 gegen 0,60).
      - Als zusätzliches Abgabe-Tor schadet sie: Maß +0,13 statt +0,31 mit Einigkeit allein.
      - Als **Schiedsrichterin** zwischen zwei uneinigen Intuitionen hilft sie [vorab festgelegt]: 11 statt 7 richtige Antworten.
        Die einigen Fälle berührt sie nicht. Mit nur 18 entscheidenden Aufgaben ist das zerbrechlich: Das Bootstrap-95-%-Intervall
        für den Gewinn reicht von −1 bis +10.
    - **Zimmerwechsel** [vorab festgelegt / beschreibend].
      - Mit zwei Intuitionen verliert der Rückgriff auf WT-As Hinterzimmer: 54 gegen 57 von 100 für den Antwortmodus allein
        [vorab festgelegt].
      - Mit drei Intuitionen gewinnt er: 62 gegen 57 [beschreibend].
      - Mit MITs Hinterzimmer als Rückfall: 63 (zwei Intuitionen) und 66 (drei), gegen 58 für MIT allein [beschreibend].
      - Auf den unberührten Aufgaben 301–370 [vorab festgelegt]: „zwei einig → Antwortmodus, sonst MITs Hinterzimmer“ löst **40
        von 70**. MIT allein löst 38, der Antwortmodus allein 35. Die Präzision der Einigkeit liegt bei 90 %, aber die Regel kostet
        mehr Tokens je richtiger Antwort als MIT (56.800 gegen 41.000). Die Lesart ist deshalb **offen**. Der Gewinn kommt aus
        beiden Zimmern: vorne die Präzision (28 gegen 26 auf den einigen Aufgaben), hinten MITs Ausgang (12 gegen 7 auf dem Rest).
    - **Zwei Betriebsarten, zwei Kosten.**
      - Ein *einzelner* Lauf im Antwortmodus ist der effiziente Weg: 16.600 statt 37.700 Tokens je richtiger Antwort (Punkt 9).
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

---

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
- Unser Beitrag ist nicht die Lücke selbst:
  - Wir zerlegen einen veröffentlichten Gewichts-Edit auf Verbraucher-Hardware. Das Sampling-Protokoll macht die Hälfte seiner
    Wirkung aus, und die Schleifen-Richtung lässt sich ohne Such-Agenten finden.
  - Wir zeigen, dass der Engpass das Festlegen ist, nicht das Wissen (Wahrheitssonde, Antwort-Zwang).
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
  Auswertungsblöcke mit identischen Modelldateien (per Prüfsumme kontrolliert) und identischen Einstellungen.
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
  - IFEval: 120 Prompts, strenge Bewertung auf Prompt-Ebene.
- **Vorab-Festlegung:** Vor jedem entscheidenden Lauf steht die Lesart (Kriterien, Schwellen) in einem datierten Protokoll.
  Spätere Änderungen werden mit Begründung eingetragen, und nur, bevor die zugehörigen Daten existieren.
- **Statistik:**
  - Die meisten vorab festgelegten Lesarten sind Schwellenregeln („hält / offen / widerlegt“). Wo ein Test auch einen p-Wert hat
    (exakter McNemar-Test für gepaarte Trefferquoten, Fisher-Test für Raten), berichten wir ihn unkorrigiert.
  - Die drei Haupteffekte mit p-Wert bleiben nach Holm-Korrektur über alle ~30 vorab festgelegten Lesarten dieses Projekts
    signifikant:
    - die Abschlüsse des Auslösers nach dem richtigen Wert (H-WT2), p = 0,0001;
    - MITs Hinterzimmer gegen sein Vorderzimmer, p = 0,0003;
    - die Einigkeit zweier Intuitionen, p ≈ 10⁻¹¹.
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
| K1 kein Schaden gegenüber demselben Modell ohne WT | erfüllt: 31 gegen 23 richtig (nur WT-A 9, nur ohne WT 1; p = 0,021) |
| K2 Abschlüsse ≤ 64 Tokens nach einem richtigen Kandidaten | **nicht auswertbar**: 2 Gelegenheiten (siehe unten) |
| K3 Token-Ersparnis auf Aufgaben, die beide lösen | erfüllt: Mittel 5.248 gegen 14.776 (−64 %) |
| K4 Wahrheitssonde auf den neuen Transkripten intakt | **nicht erfüllt**: AUC 0,82 / 0,94 gegen 0,99 / 0,996 (zwei Blöcke) |

Nach der vorab festgelegten Lesart **blieb das Tor zu einer bestätigenden Aussage geschlossen**. Alle späteren WT-A-Zahlen sind
beschreibend, außer H-WT2 (Abschnitt 3.9).
- **Warum K2 nicht messbar war.** WT-A schließt direkt nach Ergebnissätzen (`So $\binom{10}{8} = 45$.`), *bevor* das Modell
  `\boxed{…}` oder „the answer is“ schreibt. Unser alter Kandidaten-Erkenner suchte nur danach.
- **Die Korrektur.** Wir schrieben einen breiteren Erkenner (alte Kandidaten plus Wert-Aussagen „= X“, „is X“). Damit legten wir
  einen neuen Test (H-WT2) fest, bevor ein Lauf auf frischen Aufgaben existierte.
- **Ein zweiter Seed** wiederholt das Ergebnis der Entwicklungsmenge: 33 gegen 25 (wieder +8). [beschreibend]

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

Alle Skripte liegen im veröffentlichten Code. Ob das Rezept auf größere Modelle übertragbar ist, ist die Frage von Phase 2.

**Lehre aus WT-A** [beschreibend]: Der Effektor muss zur *Phase* passen, und er muss einen *Zustand* hinterlassen, nicht nur ein
Token.
- Nach einem Auslöser-Abschluss öffnet WT-A sein Denken im Antwortteil wieder (ein zweites `</think>`), in 83–100 % der Läufe,
  selbst wenn der Wert vorher sechsmal oder öfter genannt worden war. Das erzeugte 46 % aller Tokens auf der Entwicklungsmenge.
  - Auf frischen Aufgaben (161–300) sind es 77 % aller Abschlüsse und 58 von 61 richtigen Läufen; MIT denkt nach 16 % seiner
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
| offizielle Antworten | 592 | – | – | +0,20 |
| erzwungene Antworten | 726 | 552 | – | −0,30 |
| **erzwungen + Enthaltung nach Sonde** | 673 | 225 | 380 | **+0,17** |

- **Beide Kriterien erfüllt:** AUC auf erzwungenen Antworten 0,83 (gefordert ≥ 0,75), und die Regel schlägt das Erzwingen beim Maß
  S₂.
- 327 der 380 Enthaltungen wären falsch gewesen; 53 richtige Antworten gingen verloren.
- **Risiko und Abdeckung:** Nur die 50 % sichersten zu beantworten ergibt 87 % Treffer, die 30 % sichersten ergeben 95 %.
- Nur auf den frischen Aufgaben: AUC 0,83 (erzwungene Antworten 0,80), S₂ +0,13 mit der Regel gegen −0,24 erzwungen.
- [Deutung] Das innere Wahrheitssignal stößt nicht nur das Festlegen an; es sagt auch, wann man sich *nicht* festlegen sollte. Die
  Enthaltung selbst in die Gewichte zu schreiben, ist der nächste Schritt.

### 3.9 Frische Aufgaben: MATH-500 161–300

> *„Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen.“* — D. U., 8. Nov. 2026

**Aufbau.**
- Die Aufgaben 161–300 waren bis zu diesem Schritt unberührt.
- Der Laptop rechnete 161–260, der zweite Rechner 261–300. Jeder paarweise Vergleich läuft auf demselben Rechner.
- Gleiches Protokoll für alle Modelle, Seed 0; ein zweiter Seed für Teile der Daten.

**Hauptbefund** [vorab festgelegt]. ERGORE erreicht MIT-Niveau nicht: 65 gegen 80 von 140 (7 : 22, p = 0,008).

| Block | ERGORE | MIT | Anmerkung |
|---|---|---|---|
| 161–260 (Laptop) | 51 | 58 | Seed 0 |
| 261–300 (zweiter Rechner), Seed 0 | 14 | 22 | 3 : 11 |
| 261–300, Seed 1 [beschreibend] | 16 | 16 | 6 : 6 |

[Deutung] Der Gleichstand aus dem Entwicklungsbereich hat sich nicht übertragen. Auf einem Block ist MITs eigene Schwankung von Seed
zu Seed (22 → 16) so groß wie der Abstand. Der Abstand ist echt, liegt aber vermutlich eher bei 5–7 Punkten als bei 11.

**WT-A auf frischen Aufgaben.**

| | WT-A Seed 0 | WT-A Seed 1 (nur 161–260) | MIT |
|---|---|---|---|
| richtig [beschreibend] | 61/140 (161–260: 44/100) | 47/100 | 80/140 (161–260: 58/100) |
| **H-WT2: Abschlüsse ≤ 64 Tokens nach dem richtigen Wert, je Gelegenheit** [vorab festgelegt] | **65 % (55/85)** | 54 % | 36 % (37/102), p = 0,0001 |
| **H-WT2: schnelle Abschlüsse, die richtig sind** [vorab festgelegt] | **61 % (55/90)** | 57 % | 44 % (37/85) |
| Tokens auf Aufgaben, die beide lösen | 7.146 | – | 13.233 |

**Blick nach innen: ein Auslöser-Audit mit Teacher-Forcing** [beschreibend; Lesarten vorab festgelegt]. Wir haben alle 140
WT-A-Transkripte mit und ohne die 16 Neuronen nachgespielt und an jeder Stelle das Tor, den Kontext-Term, den Schub und die
gesampelte Abschluss-Wahrscheinlichkeit gelesen.
- **Der Auslöser trägt WT-As Erfolge.**
  - 69 von 102 ersten Abschlüssen gehen auf den Auslöser zurück: Die gesampelte Abschluss-Wahrscheinlichkeit liegt ohne die
    Neuronen unter 2 % und mit ihnen bei mindestens 20 %.
  - 46 dieser 69 folgen auf den richtigen Wert, 18 auf einen falschen, 5 woanders. Aus ihnen kommen **51 der 61 richtigen
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
| … schließt direkt daran | 55 → 48 richtig abgegeben | 37 → 33 |
| … schließt nicht direkt daran | 30 → **7** richtig | 65 → **44** richtig |
| Tokens vom ersten richtigen Wert bis zum Abschluss (Median) | 1.018 | 12.289 |

- **Wann der Auslöser zündet:** bei frühen, klar formulierten Lösungen leichterer Aufgaben.
  - Erster richtiger Wert im Median nach 719 gegen 1.963 Tokens.
  - Stufen 1–3: 75 % dieser Läufe schließen am Wert; Stufen 4–5: 50 %.
- **Schweigen ist oft ein Abgabefehler.** 32 WT-A-Läufe schließen das Denken ohne `\boxed`-Antwort. In 14 davon erscheint der
  richtige Wert früh im Antwortteil und geht dann verloren.
  - Wie oft öffnet WT-A sein Denken nach einem Abschluss wieder (ein zweites `</think>`)? Das hängt davon ab, welche Läufe man
    zählt:
    - in 83–100 % der Entwicklungsläufe;
    - in 77 % aller seiner Abschlüsse auf diesen frischen Aufgaben (58 seiner 61 richtigen Läufe);
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
    seine Grundlage: +8 in beiden Seeds). Er lohnt sich nicht, wo das Modell schon gut prüft und sich festlegt.
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
  - Set B: 32 gegen 23 für dasselbe Modell mit Denken (14 : 5, p = 0,064).
  - Alle 109 Treffer im Antwortmodus enden regulär (Ende des Zugs). Keiner stammt aus einer Schleife oder einem Budget-Abbruch;
    es ist also kein Bewertungs-Artefakt.
- **Taugt der Antwortmodus nur für leichte Aufgaben?** [beschreibend, Entwicklungsdaten] Nein.
  - Nach offizieller Schwierigkeit (1–160): Antwortmodus 26 gegen MIT mit Denken 22 auf den Stufen 4–5, und 33 gegen 37 auf den
    Stufen 1–2.
  - Dasselbe Modell in beiden Betriebsarten (Set B, zwei Seeds fürs Denken): Bei Aufgaben, die das Modell schnell beantwortet
    (< 1.000 Tokens), erreicht der Antwortmodus 21 und das Denken 19 und 19 von 26.
  - Bei Aufgaben, deren Antwort lange dauert (> 8.000 Tokens), erreicht der Antwortmodus 8, das Denken 2 und 3 von 25.
  - Das Bild des Autors dafür ist ein Haus. Der Antwortmodus ist das *Vorderzimmer*, der Denkblock das *Hinterzimmer*; dazwischen
    liegt ein *Flur*, dessen Ausgänge zum „Feierabend“ (abgeben und aufhören) oder in den „Pausenraum“ führen (innehalten,
    enthalten, neu ansetzen).
  - [Deutung] Für dieses 0,8B-Modell ist das Hinterzimmer nicht der Ort, an dem schwere Aufgaben gelöst werden; es ist der Ort, an
    dem sich das Modell verliert.
  - Auch der Antwortmodus zeigt ein eigenes Tempo-Signal: Antworten innerhalb von 1.000 Tokens sind zu ~75 % richtig, Antworten
    jenseits von 8.000 Tokens zu ~25 %.
- **Frische Aufgaben 161–300** [vorab festgelegt: hält bei ≥ MIT − 7 von 140, widerlegt bei ≤ MIT − 14]: Antwortmodus **71**,
  MIT mit Denken **80**. Das Ergebnis ist **offen**.
  - Auf 161–260 57 gegen 58; auf 261–300 14 gegen 22.
  - Alle Läufe im Antwortmodus enden regulär. Je richtiger Antwort brauchen sie 14.800 statt 36.600 Tokens (161–260).
- **MIT im Vorderzimmer** [vorab festgelegt]: MITs Edit ohne Denkblock erreicht **59 von 140** (6 : 27 gegen MIT mit Denken,
  p = 0,0003). Die Lesart „das Hinterzimmer lohnt sich bei MIT“ hält.
  - Unser Vorderzimmer (71) schlägt MITs Vorderzimmer (14 : 26, p = 0,08).
  - [Deutung] Ein Hinterzimmer lohnt sich nur, wenn es einen funktionierenden Ausgang hat. MITs Edit baut diesen Ausgang; unserer
    baut ein stärkeres Vorderzimmer.
- **Prüfungen** [vorab festgelegt]:
  - Presence penalty: Der Vorsprung des Antwortmodus auf Set B 1–20 beträgt +2, sowohl mit Strafe 0 als auch mit 1,5. Kein
    Artefakt.
  - Stabilität von Tag zu Tag: Mit einem zweiten Seed auf 261–300 geht der Antwortmodus von 14 auf 16, aber nur 75 % der Aufgaben
    werden gleich gelöst. MIT mit Denken erreicht ebenfalls 75 %. Die Vermutung des Autors, das Vorderzimmer sei stabiler, ist
    widerlegt.
- **Kaskade „Antwortmodus → Wahrheitssonde → Denklauf → weiß ich nicht“** [vorab festgelegt; Vorbedingung nicht erfüllt, daher
  beschreibend].
  - **Vorbedingung:** Die eingefrorene Wahrheitssonde muss Antworten im Antwortmodus auf 161–300 mit AUC ≥ 0,75 trennen. Sie
    erreicht 0,68 (0,76 auf 1–160). Die Kaskade wird deshalb nur beschreibend berichtet.
  - **Hauptvariante:** Schwellen auf 1–160 geeicht, MIT als Rückfall. Auf 161–300 erreicht sie S₂ +0,32 gegen +0,27 für MIT
    allein, aber nur 67 richtige Antworten (MIT: 80). Die Lesart verlangte S₂ ≥ +0,25 *und* mindestens 75 richtige Antworten und
    galt als widerlegt bei S₂ ≤ +0,19 *oder* weniger als 75 richtigen. Sie ist deshalb trotz des höheren S₂ **widerlegt**.
  - **Kosten:** Die Tokens steigen eher, als dass sie fallen, weil die meisten Aufgaben im Denkzweig landen.
  - **Grund:** Im Antwortmodus ist die Sonde weit nach oben verschoben. Richtige Antworten haben einen Median-Wert von +3,4, falsche
    +1,9 bis +2,6, gegen eine eingefrorene Schwelle von −1,2.
  - [Deutung] Die Sonde wurde auf Denktext trainiert. Im Vorderzimmer klingt jede Aussage wie eine Behauptung. Eine Kaskade im
    Vorderzimmer braucht eine Sonde, die auf Antworttext trainiert ist.
- **Zweite Chance („Morgengrauen“)** [vorab festgelegt]. Die 69 WT-A-Läufe, die nichts abgegeben hatten, wurden im Antwortmodus mit
  Notizen wiederholt. Die Notizen waren die Sätze um die stärksten eigenen Wahrheits-Blitze des Modells, ausgewählt ohne Zugriff
  auf die Lösung. Die Kontrolle war der Antwortmodus ohne Notizen auf denselben Aufgaben.
  - Notizen 22, Kontrolle 25 (p = 0,66). Die Wirkung der Notizen ist **widerlegt**.
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
  - **40 neue Trainingsaufgaben** (nie zuvor benutzt): gleiche Antwort bei 17, 13 richtig (76 %); verschieden bei 23, 13 % richtig.
    Das Kriterium hält mit +63 Punkten, aber mit deutlich geringerer Präzision.
  - **Unberührte Aufgaben 301–370:** gleiche Antwort bei 31, **28 richtig (90 %)**; verschieden bei 39, 18 % richtig. Das
    Kriterium hält mit +72 Punkten.
  - [beschreibend, zusammengefasst] Über die drei Bestätigungen sind 78 von 86 einigen Antworten richtig (91 %). Die 97 % des
    ersten Tests sind das obere Ende. Jede Menge war einzeln vorab festgelegt, die zusammengefasste Zahl nicht.
  - [Deutung] Das ist Selbstkonsistenz (Wang et al., 2022), eingesetzt an der Stelle des Festlegens. Die Einigkeit stimmt nicht über
    die Antwort ab; sie entscheidet, *ob* abgegeben wird.
  - [beschreibend] Auf dem schon gesehenen Block 261–300 zeigt sich dasselbe Muster: 10 von 12 gegen 4 von 28.
- **Dreimal fragen** [vorab festgelegt; 161–260, Seeds 0, 1, 2].
  - Eine Mehrheit aus drei (mindestens zwei gleichwertige Antworten) gibt bei **62** Aufgaben ab, 55 davon richtig (89 %).
  - Die Lesart verlangte ≥ 48 Abgaben und ≥ 90 % Präzision; sie ist also um einen Punkt **offen**.
  - Die zweite Lesart, nach der das Maß (richtig − 2·falsch)/N nicht unter die Einigkeit aus zwei fallen darf, hält: +0,41 gegen
    +0,35.
  - Bei 29 Aufgaben sind sich alle drei einig, und alle 29 sind richtig.
  - [beschreibend] Die anderen Seed-Paare wiederholen das Muster: 0/2 einig bei 42 Aufgaben (40 richtig), 1/2 bei 40 (35 richtig).
- **Eine Sonde für das Vorderzimmer** [vorab festgelegt; Ergebnis „offen“]. Gleiches Rezept wie bei der Wahrheitssonde, aber auf
  Texten im Antwortmodus trainiert: 239 abgegebene Antworten aus Set B und 1–160. Sie liest den Zustand am letzten Token des
  abgegebenen `\boxed{}`.
  - Schicht und Regularisierung wurden nur auf Trainingsdaten durch gruppierte Kreuzvalidierung gewählt (Schicht 13, CV-AUC 0,81),
    dann eingefroren.
  - Test auf 161–300: AUC **0,763**. Antwortlänge und Schwierigkeit allein erreichen 0,723, die Kombination bringt nur +0,04. Die
    vorab festgelegte Lesart verlangte +0,05; das Ergebnis ist also **offen**.
  - Die Denktext-Sonde erreicht an denselben Stellen 0,681.
  - [beschreibend, nachträglich gewählte Teilmengen] Bei schnellen Antworten (≤ 2.000 Tokens) erreicht die neue Sonde 0,794, gegen
    0,63 für Länge und Schwierigkeit und 0,63 für die alte Sonde. Gibt man nur schnelle Antworten über dem Median der Sonde ab, sind
    26 von 29 richtig.
  - Sie überträgt sich auf MITs Texte im Antwortmodus (0,776) und auf neue Stichproben derselben Aufgaben (0,836).
  - **Bestätigungen** [vorab festgelegt, eingefrorene Sonde und eingefrorene Grundlinie]:

    | Menge | Antworten | Sonden-AUC | Länge + Schwierigkeit | Zuwachs | schnelle Antworten (≤ 2.000): Sonde gegen Grundlinie |
    |---|---|---|---|---|---|
    | 40 neue Trainingsaufgaben | 79 | 0,852 | 0,841 | +0,012 | 0,823 gegen 0,736 |
    | unberührte 301–370 | 138 | 0,765 | 0,717 | +0,048 | 0,606 gegen 0,599 |

    - Beide Hauptlesarten sind **offen**: Die Sonde liest Richtigkeit gut, aber Antwortlänge und Schwierigkeit tragen den größten
      Teil dieser Information schon.
    - Der Vorsprung bei schnellen Antworten aus der nachträglich gewählten Teilmenge hat sich auf den unberührten Aufgaben **nicht
      wiederholt**. Er war vorab als zweite Lesart festgelegt, und diese Lesart ist widerlegt.
  - **Mehrwert ohne Schaden** (Kriterium des Autors: „nur, wenn sie messbar Mehrwert bringt und keinen Nachteil“) [vorab
    festgelegt, 301–370]:
    - *Als Schiedsrichterin*: Sind zwei Intuitionen uneinig und geben beide eine Antwort ab, wird die mit dem höheren Sonden-Wert
      genommen. Bei 37 solchen Aufgaben war eine der beiden Antworten in 18 Fällen richtig. Die Sonde wählt 11 davon; der erste Lauf
      allein hat 7, die kürzere Antwort 7. Lesart: **Mehrwert**.
      - Die Stichprobe ist zerbrechlich: Nur 18 Aufgaben entscheiden, und das gepaarte Bootstrap-95-%-Intervall für den Gewinn
        reicht von −1 bis +10 richtigen Antworten.
      - [beschreibend] Bei „immer antworten“ hebt die Schiedsrichterin die Zahl von 35 auf 39 von 70. Die beiden einzelnen Läufe
        erreichen 35 und 39, das Mittel eines einzelnen Laufs ist also 37.
    - *Als zusätzliches Abgabe-Tor*: Das Maß fällt von +0,31 (Einigkeit allein) auf +0,13. Lesart: **Schaden**. Die zusätzlichen
      Abgaben der Sonde sind nur in 3 von 11 Fällen richtig.
    - [Deutung] Die Einigkeit entscheidet, *ob* abgegeben wird; die Sonde entscheidet, *welche* Antwort, wenn die Intuitionen
      uneinig sind.
- **Zimmerwechsel** [vorab festgelegt]. Abgeben, wenn zwei Intuitionen einig sind, sonst einen Denklauf nehmen.
  - Mit WT-As Hinterzimmer als Rückfall: 54 von 100, gegen 57 für den Antwortmodus allein. Widerlegt.
  - [beschreibend] Mit MITs Hinterzimmer: 63, gegen 57 und 58 für jedes allein.
  - [beschreibend] Mit drei Intuitionen (Mehrheit, sonst Hinterzimmer): WT-As Hinterzimmer als Rückfall ergibt **62**, gegen 57 für
    den Antwortmodus allein und 44 für WT-A allein. MITs Hinterzimmer ergibt 66, gegen 58 für MIT allein. Mit drei Intuitionen
    bringt unser eigenes Hinterzimmer zum ersten Mal Mehrwert.
  - [beschreibend, 161–300] „Einigkeit allein“ als Regel fürs Abgeben, sonst „weiß ich nicht“: 50 von 140 abgegeben, 94 % richtig,
    Maß (richtig − 2·falsch)/N von +0,29 gegen −0,48 bei immer antworten.
  - [beschreibend, 161–300] Der Gewinn von „einig → Antwortmodus, sonst MIT“ (84 gegen 80) stammt ganz aus der Einigkeits-Menge (dort
    47 gegen 43). Die Regel ist ein Auswähler, kein Verstärker, und zwei volle Läufe im Antwortmodus machen sie teurer an Tokens
    (54.000 gegen 37.700 je richtiger Antwort).
  - [vorab festgelegt, 301–370] Mit der Sonde als zusätzlichem Tor schlägt die gekoppelte Regel eine reine Längen-Regel nur um
    +0,04 im Maß, bei 74 % Präzision (gefordert: +0,05 und 80 %). Das Ergebnis ist **offen**.
  - **„Einig → Antwortmodus, sonst MITs Hinterzimmer“ auf den unberührten Aufgaben 301–370** [vorab festgelegt]. Die Regel hält,
    wenn sie mindestens MIT allein erreicht, mit ≥ 90 % Präzision auf der Einigkeits-Menge und weniger Tokens je richtiger Antwort
    als MIT.
    - Ergebnis: **40 von 70**, gegen 38 für MIT allein und 35 für den Antwortmodus allein. Die Präzision auf der Einigkeits-Menge
      liegt bei 90 % (28 von 31).
    - Das Token-Kriterium wird verfehlt: 56.800 gegen 41.000 je richtiger Antwort. Die Lesart ist deshalb **offen**.
    - Zerlegung: Auf den 31 einigen Aufgaben hat der Antwortmodus 28 und MIT 26. Auf den übrigen 39 hat MIT 12 und der Antwortmodus
      7. Der Gewinn kommt aus beiden Zimmern: vorne die Präzision, hinten MITs Ausgang.
    - [beschreibend] Auf diesen Aufgaben bleibt der Antwortmodus allein (35) nahe an MIT mit Denken (38), bei 17.000 gegen 41.000
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
    - Über alle Läufe würde ein darauf gebauter Reflex nichts gewinnen: 59 statt 61. Er bricht auch Läufe ab, die später von selbst
      richtig abgegeben hätten.
  - Derselbe Nachtest bestätigt das Nachspielen der 32 stummen Antwortteile von WT-A: Auch mit 4.096 Tokens geben nur 2 von 32 ab.
  - [Deutung] Die eigenen Schilder des Modells markieren zusammen mit dem Wahrheitssignal die Momente, in denen ein Abschluss trägt.
    Ein eingesetztes `</think>` ersetzt trotzdem kein inneres „fertig“.

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
  - WT-As Vorsprung vor MIT auf Set B (31 gegen 27) kehrte sich auf frischen Aufgaben um.
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
  gewählten Teilmengen und haben sich auf unberührten Aufgaben nicht wiederholt.
- Die Bestätigungen im Vorderzimmer sind klein: 17 bis 38 einige Antworten je Menge. Die zusammengefasste Präzision (91 %) ist
  verlässlicher als jede einzelne Menge (76–97 %).
- „Einigkeit“ wird mit dem Bewertungswerkzeug (math-verify) geprüft. Zwei gleichwertige, aber verschieden geschriebene Antworten
  gelten als einig; zwei falsche Antworten, die zufällig übereinstimmen, gelten als selbstsicherer Fehler.

## 6. Nächste Schritte

- **Läuft, während dieser Bericht erscheint (öffentliche Vorab-Festlegung).** Wir testen die Beratung der Intuitionen mit *unserem
  eigenen* Hinterzimmer auf 150 frischen MATH-Trainingsaufgaben, die nie benutzt wurden. Sie haben dieselbe Stufenmischung wie
  MATH-500.
  - Läufe: Antwortmodus mit den Seeds 0, 1 und 2, dazu WT-A und MIT mit Denken.
  - Regel: Sind mindestens zwei der drei Intuitionen einig, wird diese Antwort abgegeben; sonst gilt WT-As Antwort mit Denken.
  - Lesarten, festgelegt, bevor einer dieser Läufe existierte:
    - (H1) Die Regel „hält“, wenn sie ≥ 5 Aufgaben mehr löst als der Antwortmodus allein, und ist „widerlegt“ bei ≤ +1;
    - (H2) gegen MIT: „schlägt MIT“ bei ≥ +5 mit einseitigem McNemar p < 0,05, „mindestens gleichauf“ bei ≥ 0, „unter MIT“ bei
      ≤ −5;
    - (H3) die Einigkeit zweier Intuitionen „hält“ bei ≥ 85 % Präzision und ist „widerlegt“ unter 75 %;
    - (H4) eine Mehrheit aus drei „trägt“ bei ≥ 85 % Präzision mit ≥ 10 Punkten mehr Abdeckung als die Einigkeit aus zwei.
  - Das Ergebnis berichten wir in der nächsten Fassung, wie auch immer es ausfällt.
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
- **Eine einseitige Weiche.** Die Einigkeit mehrerer Intuitionen in einen Kopf mit einem einzigen Durchlauf destillieren. Ihn dann
  das Prüfen bei Unsicherheit nur *verlängern* lassen, nie eine sichere Antwort abbrechen.
- **Schwelle mit Garantie.** Die Auslöser-Schwelle mit verteilungsfreier Risikokontrolle (Learn-then-Test) auf Lauf-Maxima eichen.
- **Ehrliche Enthaltung.** *„Weiß ich nicht – bin ich ehrlich!“* — D. U., 6. Nov. 2026
  - Mit einer äußeren Regel beginnen: Ein Lauf ohne jeden „wahr“-Blitz endet mit „weiß ich nicht“.
  - Dann lokale Enthaltungs-Richtungen an `</think>` versuchen, gebaut mit dem Rezept aus Abschnitt 3.8.
  - Über die Mathematik hinaus: eine geplante „Ehrlichkeits-Batterie“ mit Alltagsfragen. Was zeigt das innere Signal, wo sich
    nichts nachprüfen lässt?
- **Größere Modelle.** Übertragung auf ein 35B-Modell mit Mixture-of-Experts.

## 7. Nachvollziehbarkeit und Lizenzen

Die Veröffentlichung zu diesem Bericht unter [github.com/NeoCortex0815/knowing-is-not-committing](https://github.com/NeoCortex0815/knowing-is-not-committing) enthält:
- den Code, wie er benutzt wurde: Auswertungs-Client, Edit-Bauer, die Wahrheitssonde und jedes Test- und Urteils-Skript,
  nummeriert in der Reihenfolge ihres Entstehens;
- das datierte Protokoll der Vorab-Festlegungen und Auswertungen (deutsch), mit geschwärzten Rechnernamen, Pfaden und Angaben zu
  den privaten Systemen des Autors;
- eine Tabelle je Auswertungslauf (Aufgaben-ID, entnommene Antwort, richtig, Endegrund, Tokens) und die Ausgaben der
  Urteils-Skripte;
- die IDs der benutzten MATH-Trainingsaufgaben.

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
und einem Qwen-Modell). Alle berichteten Zahlen stammen aus dem veröffentlichten Code und lassen sich damit nachrechnen.

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

## Anhang A. Bilder, die diese Arbeit geprägt haben

Der Autor denkt in Bildern. Wir behalten die, aus denen prüfbare Fragen wurden. Zu jedem steht, wozu es führte und was herauskam.
Alle übrigen Bilder und Fragen stehen mit Datum und Uhrzeit im Protokoll der Vorab-Festlegungen.

1. *„Schauen, ob das Modell die Lösung hat, wann – und den inneren Schubs zulassen, trotz Druck.“* (6. Nov.)
   - Daraus wurden die drei Fragen des Projekts: Hat das Modell die Lösung (Wahrheitssonde), wann erkennt es sie (Auslöser-Audit),
     und kann ein innerer Schub es festlegen lassen (WT-Reflex)?
   - Ergebnis: Wissen ja; das Festlegen bleibt der Engpass.
2. *„Ist das Modell per se nicht fähig zu sagen ‚ich weiß es nicht‘? … Weiß ich nicht – bin ich ehrlich!“* (7. und 6. Nov.)
   - Daraus wurden der Antwort-Zwang und der Ehrlichkeits-Schritt.
   - Ergebnis: Sich zu enthalten, wenn das innere Wahrheitssignal niedrig bleibt, macht erzwungenes Antworten von schädlich zu
     nützlich. Das Maß (richtig − 2·falsch)/N steigt von −0,30 auf +0,17 [vorab festgelegt].
3. *„Gab es ein Zucken? Wenn ja, war es, weil die Lösung wahr ist oder nicht? Wie stark war es?“* (8. Nov.)
   - Daraus wurde das Auslöser-Audit von WT-A mit Teacher-Forcing auf frischen Aufgaben (Abschnitt 3.9).
4. *„Ein Prüfer gibt dem Prüfling auch keinen Schubs von außen.“* (8. Nov.)
   - Daraus wurde das Prinzip des inneren Festlegens.
   - Ergebnis: Jeder Schub von außen, den wir versucht haben, scheiterte daran, ein inneres „fertig“ zu erzeugen: der
     Gradienten-Schub, die übrige Richtung und ein eingesetztes `</think>`, selbst am eigenen Schluss-Satz des Modells.
5. *„Das ist das erste Paar Schuhe. Nennen wir es INT für Intuition.“ – „Vorderzimmer … Hinterzimmer … Flur liegt dazwischen. Flur
   könnte Ausgabe sein zum Feierabend oder zum Pausenraum.“* (8. Nov.)
   - Daraus wurden der Antwortmodus als eigener Weg und das Hausbild aus Abschnitt 3.10.
   - Ergebnis: unser stärkster eigener Weg, 71 von 140, mit weniger als der Hälfte der Tokens je richtiger Antwort.
6. *„Die Schilder hängt derjenige auf, der das Haus besitzt bzw. darin wohnt.“* (8. Nov.)
   - Daraus wurden die Schild-Tests.
   - Ergebnis: Am eigenen Schluss-Satz gibt MIT doppelt so oft ab wie ohne (36 % gegen 18 %). Wo WT-As eigenes Schild und sein
     Wahrheits-Tor zusammenfallen, gibt es in 5 von 9 Fällen ab, alle richtig.
7. *„Mehrere Intuitionen beraten sich im Vorderzimmer. Sind sie sich einig, ist Feierabend. Nur die strittigen Fälle gehen ins
   Hinterzimmer.“* (Bild aus der Arbeitssitzung, vom Autor übernommen, 8. Nov.)
   - Daraus wurden die Einigkeits-Tests.
   - Ergebnis: Einige Intuitionen liegen über drei Bestätigungen in 91 % der Fälle richtig. Eine Mehrheit aus drei gibt öfter ab,
     mit 89 %, und die Vorderzimmer-Sonde entscheidet Streitfälle.
