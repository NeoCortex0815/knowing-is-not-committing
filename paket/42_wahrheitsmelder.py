"""Innerer Wahrheitsmelder (Nutzer 06.11. ~11:55: „Ja, danach bauen“). Bedingung des Nutzers: „Das Modell zuckt, aber das Ergebnis
kann nur falsch sein, weil es keine Hinweise auf eine Wahrheit gibt wie bei den bisher gelösten Aufgaben.“
Sonde wie Zhang et al. 2025 (arXiv 2504.05419, „Reasoning Models Know When They're Right“); NUR Übungsdaten.

sammeln: An jeder Kandidaten-Stelle im Denken (\\boxed{…} oder „answer is …“) den Residual Stream am letzten Token des Kandidaten
         lesen (Ausgang der Schichten --schichten). Etikett = Kandidat richtig (math-verify gegen gold). Ein Vorwärtslauf je
         Transkript mit dem eigen-vL-Modell (bis Schicht 15 identisch mit ERGORE/β 5,2); Abbruch nach der tiefsten Schicht,
         Eingabe endet am letzten Kandidaten.
pruefen: L2-logistische Sonde je Schicht (torch, standardisiert), 5-fach Kreuzvalidierung nach Aufgabe gruppiert (keine Aufgabe in
         Training UND Test). Kennzahlen: AUC zurückgehalten; dazu Mittelwert-Differenz-Richtung als einfache Vergleichs-Sonde;
         gepaarte Trefferquote in Läufen mit richtigen UND falschen Kandidaten (gleiche Aufgabe, gleicher Lauf).
  python 42_wahrheitsmelder.py sammeln --laeufe ergebnisse/tag2-kw75-s0/ergebnisse.jsonl ... --aus ergebnisse/wahrheit_sammlung.npz
  python 42_wahrheitsmelder.py pruefen --sammlung ergebnisse/wahrheit_sammlung.npz
"""
import argparse
import importlib.util
import json
import os
import re

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Stopp(Exception):
    pass


def kandidaten_mit_ende(text):
    """Wie 23_klingel_regel.kandidaten, aber mit Endposition (Zeichen nach dem Kandidaten)."""
    out, i = [], 0
    while True:
        j = text.find("\\boxed{", i)
        if j < 0:
            break
        k, tiefe = j + 7, 1
        while k < len(text) and tiefe:
            tiefe += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        out.append((j, k, text[j + 7:k - 1]))
        i = k
    for m in re.finditer(r"answer is[:\s]*\$?([^\n$]{1,40}?)\$?(?:[.\n]|$)", text):
        out.append((m.start(), m.end(1), m.group(1)))
    return sorted(out)


FUELLWOERTER = (r"^(?:(?:is|likely|probably|simply|just|exactly|indeed|actually|clearly|definitely|still|then|therefore|thus|so|"
                r"now|the|number|value|answer|final|result|equal to|equals|approximately)\b[\s,:]+)+")


def bereinige_kandidat(c):
    """Kandidaten-Text ohne Füllwörter/Satzzeichen außen (06.11. 15:20, nach dem Zünder-Test gefunden: 'likely -125', '"3"?').
    Nur für die BEWERTUNG; die Lese-Position bleibt gleich. In sammeln nur mit --bereinigt (Standard aus = alte Ergebnisse
    reproduzierbar)."""
    c0 = c.strip().strip("\"'“”‘’`*").strip()
    c2 = re.sub(FUELLWOERTER, "", c0, flags=re.I).strip()
    c2 = c2.strip("\"'“”‘’`*").rstrip("?!.,;:").strip().strip("\"'“”‘’`").strip()
    return c2 or c0


def sammeln(a):
    import torch
    import transformers as tf
    ev = lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    geraet = a.geraet
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    schichten = [int(x) for x in a.schichten.split(",")]
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    speicher = {}
    model = lesemodell(a.modell, geraet, schichten, speicher)
    notfall = {"cpu": None, "probe": os.environ.get("WSP_OOM_PROBE") == "1"}
    X = {L: [] for L in schichten}
    y, aufgabe, lauf, kand, bereich, final, tpos, geraete = [], [], [], [], [], [], [], []
    n_laeufe = 0
    for pfad in a.laeufe:
        tag = os.path.basename(os.path.dirname(pfad))
        for z in open(pfad, encoding="utf-8"):
            if a.max_laeufe and n_laeufe >= a.max_laeufe:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zu_c = text.find("</think>")
            ks = kandidaten_mit_ende(text)          # Denken UND Antwortteil (Nutzer: auch die Endantwort beurteilen)
            if not ks:
                continue
            ber = [1 if (zu_c >= 0 and s0 > zu_c) else 0 for s0, _, _ in ks]
            boxed_antw = [i for i, (s0, _, c) in enumerate(ks) if ber[i] == 1 and text.startswith("\\boxed{", s0)]
            fin = [i == (boxed_antw[-1] if boxed_antw else -1) for i in range(len(ks))]
            grenzen = np.cumsum([len(s) for s in stuecke])
            pos = [min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1) for _, e, _ in ks]
            letzt = max(pos)
            g_r = vorwaerts(model, r["prompt_ids"] + gen[:letzt + 1], geraet, speicher, notfall, a.modell, schichten)
            p0 = len(r["prompt_ids"])
            for (_, _, c), ti, b_, f_ in zip(ks, pos, ber, fin):
                for L in schichten:
                    X[L].append(speicher[L][p0 + ti].numpy())
                y.append(bool(ev.korrekt(c, r["gold"])) or (a.bereinigt and bool(ev.korrekt(bereinige_kandidat(c), r["gold"]))))
                aufgabe.append(r["id"])
                lauf.append(f"{tag}/{r['id']}")
                kand.append(c[:40])
                bereich.append(b_)
                final.append(f_)
                tpos.append(ti)               # Token-Index des Kandidaten-Endes im generierten Teil (für Token-Ersparnis)
                geraete.append(g_r)
            n_laeufe += 1
            print(f"{tag} {r['id']}: {len(ks)} Kandidaten, davon richtig {sum(y[-len(ks):])}"
                  f"{' [CPU-Notausgang]' if g_r != geraet else ''}", flush=True)
    np.savez_compressed(a.aus, y=np.array(y), aufgabe=np.array(aufgabe), lauf=np.array(lauf), kand=np.array(kand),
                        bereich=np.array(bereich), final=np.array(final), schichten=np.array(schichten),
                        tpos=np.array(tpos), geraet=np.array(geraete),
                        **{f"X_{L}": np.stack(X[L]).astype(np.float32) for L in schichten})
    print(f"gespeichert: {a.aus} – {n_laeufe} Läufe, {len(y)} Kandidaten-Stellen ({sum(y)} richtig)")


def auc(s, y):
    s, y = np.asarray(s), np.asarray(y, bool)
    pos, neg = s[y], s[~y]
    if not len(pos) or not len(neg):
        return float("nan")
    rang = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1
    return float((rang[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def logreg(Xtr, ytr, lam):
    import torch
    X = torch.tensor(Xtr, dtype=torch.float64)
    yt = torch.tensor(ytr, dtype=torch.float64)
    w = torch.zeros(X.shape[1], dtype=torch.float64, requires_grad=True)
    b = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([w, b], max_iter=200, line_search_fn="strong_wolfe")

    def schritt():
        opt.zero_grad()
        z = X @ w + b
        verlust = torch.nn.functional.binary_cross_entropy_with_logits(z, yt) + lam * (w @ w) / len(yt)
        verlust.backward()
        return verlust
    opt.step(schritt)
    return w.detach().numpy(), float(b.detach())


def pruefen(a):
    Z = np.load(a.sammlung)
    y = Z["y"].astype(bool)
    aufgabe, lauf = Z["aufgabe"], Z["lauf"]
    schichten = [int(L) for L in Z["schichten"]]
    eind = sorted(set(aufgabe))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    falte = {t: i % 5 for i, t in enumerate(eind)}
    f = np.array([falte[t] for t in aufgabe])
    gemischt = [l for l in set(lauf) if y[lauf == l].any() and (~y[lauf == l]).any()]
    print(f"{len(y)} Kandidaten-Stellen ({y.sum()} richtig), {len(eind)} Aufgaben, {len(set(lauf))} Läufe, "
          f"{len(gemischt)} Läufe mit richtigen UND falschen Kandidaten")
    bereich = Z["bereich"] if "bereich" in Z.files else np.zeros(len(y), int)
    final = Z["final"].astype(bool) if "final" in Z.files else np.zeros(len(y), bool)
    print(f"Bereiche: Denken {(bereich == 0).sum()}, Antwortteil {(bereich == 1).sum()}, davon Endantworten {final.sum()} "
          f"({(final & ~y).sum()} falsch)")
    print(f"{'Schicht':>7s} {'AUC Sonde':>10s} {'AUC Mittel-Diff':>16s} {'gepaart richtig>falsch':>24s}   "
          f"AUC Denken / Antwort | Schwelle (≤5 % richtige markiert): Fehlalarm / falsche erkannt")
    ergebnis = {}
    for L in schichten:
        X = Z[f"X_{L}"].astype(np.float64)
        s_log = np.zeros(len(y))
        s_md = np.zeros(len(y))
        markiert = np.zeros(len(y), bool)
        for k in range(5):
            tr, te = f != k, f == k
            mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
            Xtr, Xte = (X[tr] - mu) / sd, (X[te] - mu) / sd
            w, b = logreg(Xtr, y[tr].astype(float), a.lam)
            s_log[te] = Xte @ w + b
            d = Xtr[y[tr]].mean(0) - Xtr[~y[tr]].mean(0)
            s_md[te] = Xte @ d
            # VORAB FESTGELEGT (Nutzer: „darf keine richtigen Antworten beeinflussen“): Schwelle = 5 %-Quantil der Werte
            # richtiger Kandidaten im TRAININGS-Teil; „unsicher“ = darunter
            thr = np.quantile((Xtr @ w + b)[y[tr]], 0.05)
            markiert[te] = s_log[te] < thr
        paare = treffer = 0
        for l in gemischt:
            m = lauf == l
            sr, sf = s_log[m & y], s_log[m & ~y]
            paare += len(sr) * len(sf)
            treffer += sum((x > z) for x in sr for z in sf)
        fa = float((markiert & y).sum() / max(1, y.sum()))
        tr_ = float((markiert & ~y).sum() / max(1, (~y).sum()))
        fa_end = float((markiert & y & final).sum() / max(1, (y & final).sum()))
        tr_end = float((markiert & ~y & final).sum() / max(1, (~y & final).sum()))
        ergebnis[L] = {"auc_sonde": round(auc(s_log, y), 3), "auc_mitteldiff": round(auc(s_md, y), 3),
                       "gepaart": round(treffer / max(1, paare), 3), "paare": int(paare),
                       "auc_denken": round(auc(s_log[bereich == 0], y[bereich == 0]), 3),
                       "auc_antwort": round(auc(s_log[bereich == 1], y[bereich == 1]), 3),
                       "fehlalarm_richtig": round(fa, 3), "falsch_erkannt": round(tr_, 3),
                       "endantwort_fehlalarm": round(fa_end, 3), "endantwort_falsch_erkannt": round(tr_end, 3)}
        e = ergebnis[L]
        print(f"{L:7d} {e['auc_sonde']:10.3f} {e['auc_mitteldiff']:16.3f} {e['gepaart']:18.3f} ({paare} Paare)   "
              f"{e['auc_denken']:.3f} / {e['auc_antwort']:.3f} | {100 * fa:.1f} % / {100 * tr_:.1f} %  "
              f"(Endantworten: {100 * fa_end:.1f} % / {100 * tr_end:.1f} %)")
    json.dump(ergebnis, open(os.path.splitext(a.sammlung)[0] + "_pruefung.json", "w"), indent=1)


def einfrieren(a):
    """Sonde für die einmalige Test-Anwendung einfrieren (06.11. ~13:45, vor jedem Blick auf Testdaten): Schicht --schicht,
    Training auf ALLEN Übungs-Kandidaten; Schwelle = 5-%-Quantil der zurückgehaltenen (5-fach nach Aufgabe gruppiert) Werte
    richtiger Kandidaten – die nachträglich korrigierte Kalibrierung (vorab-Variante aus Trainingswerten fiel durch)."""
    Z = np.load(a.sammlung)
    y = Z["y"].astype(bool)
    aufgabe = Z["aufgabe"]
    X = Z[f"X_{a.schicht}"].astype(np.float64)
    eind = sorted(set(aufgabe))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    falte = {t: i % 5 for i, t in enumerate(eind)}
    f = np.array([falte[t] for t in aufgabe])
    oof = np.zeros(len(y))
    for k in range(5):
        tr, te = f != k, f == k
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
        w, b = logreg((X[tr] - mu) / sd, y[tr].astype(float), a.lam)
        oof[te] = ((X[te] - mu) / sd) @ w + b
    thr = float(np.quantile(oof[y], 0.05))
    mu, sd = X.mean(0), X.std(0) + 1e-6
    w, b = logreg((X - mu) / sd, y.astype(float), a.lam)
    np.savez(a.aus, w=w, b=b, mu=mu, sd=sd, thr=thr, schicht=a.schicht)
    print(f"eingefroren: Schicht {a.schicht}, Schwelle {thr:.3f}, AUC (zurückgehalten) {auc(oof, y):.3f} → {a.aus}")


def lesemodell(pfad, geraet, schichten, speicher):
    """Lesemodell mit Haken am Ausgang der Schichten (speicher[L]); Abbruch nach der tiefsten. cuda → bf16, cpu → fp32."""
    import torch
    import transformers as tf
    dt = torch.bfloat16 if geraet == "cuda" else torch.float32
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(pfad, dtype=dt)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=dt)
    model.to(geraet).eval()
    tiefste = max(schichten)
    for n, m in model.named_modules():
        for L in schichten:
            if re.search(rf"(language_model|model)\.layers\.{L}$", n) and "visual" not in n:
                def hook(mod, inp, out, L=L):
                    speicher[L] = (out[0] if isinstance(out, tuple) else out)[0].detach().float().cpu()
                    if L == tiefste:
                        raise Stopp()
                m.register_forward_hook(hook)
    return model


def vorwaerts(model, ids, geraet, speicher, notfall, pfad, schichten):
    """Ein Vorwärtslauf bis zur tiefsten Schicht. Reicht der Grafikspeicher nicht, wird GENAU DIESER Lauf auf der CPU (fp32)
    gelesen (notfall = {"cpu": Modell oder None}); Rückgabe: tatsächlich benutztes Gerät."""
    import torch
    speicher.clear()
    oom = False
    try:
        if notfall.get("probe"):
            notfall["probe"] = False
            raise torch.OutOfMemoryError("simuliert (WSP_OOM_PROBE)")
        with torch.no_grad():
            model(input_ids=torch.tensor([ids], device=geraet))
    except Stopp:
        pass
    except torch.OutOfMemoryError:
        oom = True
    if not oom:
        return geraet
    speicher.clear()  # außerhalb des except-Blocks, damit der Speicher des Fehlversuchs frei ist
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    if notfall.get("cpu") is None:
        print("Speicher reicht nicht: Notausgang CPU (fp32) wird geladen", flush=True)
        notfall["cpu"] = lesemodell(pfad, "cpu", schichten, speicher)
    try:
        with torch.no_grad():
            notfall["cpu"](input_ids=torch.tensor([ids]))
    except Stopp:
        pass
    return "cpu"


def anwenden(a):
    """Eingefrorene Sonde GENAU EINMAL auf die Endantworten von Testläufen anwenden (Lesemodell wie beim Sammeln).
    Technischer Notausgang (06.11. ~14:00, vor dem Testlauf eingebaut): Reicht der Grafikspeicher für einen langen Lauf (bis 33k
    Tokens) nicht, wird GENAU DIESER Lauf auf der CPU (fp32) gelesen; Sonde und Schwelle bleiben unverändert, der Lauf wird im
    Ergebnis mit "geraet": "cpu" gekennzeichnet. WSP_OOM_PROBE=1 simuliert den Speicherfehler beim ersten Lauf (nur Trockentest)."""
    import torch
    import transformers as tf
    S = np.load(a.sonde)
    L = int(S["schicht"])
    geraet = a.geraet
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    speicher = {}
    model = lesemodell(a.modell, geraet, [L], speicher)
    notfall = {"cpu": None, "probe": os.environ.get("WSP_OOM_PROBE") == "1"}
    erg = []
    for spec in a.laeufe:
        name, pfade = spec.split("=", 1)
        laeufe = []
        for pfad in pfade.split("+"):
            laeufe += [json.loads(z) for z in open(pfad, encoding="utf-8")]
        if a.max_laeufe:
            laeufe = sorted(laeufe, key=lambda r: len(r["gen_ids"]))[:a.max_laeufe]
        for r in laeufe:
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            zu_c = text.find("</think>")
            fin = [(s0, e) for s0, e, _ in kandidaten_mit_ende(text) if zu_c >= 0 and s0 > zu_c and text.startswith("\\boxed{", s0)]
            if not fin:
                erg.append({"modell": name, "id": r["id"], "korrekt": bool(r["korrekt"]), "endantwort": False})
                continue
            grenzen = np.cumsum([len(s) for s in stuecke])
            ti = min(int(np.searchsorted(grenzen, fin[-1][1] - 1, side="right")), len(stuecke) - 1)
            ids = r["prompt_ids"] + gen[:ti + 1]
            geraet_r = vorwaerts(model, ids, geraet, speicher, notfall, a.modell, [L])
            h = speicher[L][len(r["prompt_ids"]) + ti].numpy().astype(np.float64)
            s = float(((h - S["mu"]) / S["sd"]) @ S["w"] + S["b"])
            erg.append({"modell": name, "id": r["id"], "korrekt": bool(r["korrekt"]), "endantwort": True,
                        "wert": round(s, 3), "unsicher": s < float(S["thr"]), "laenge": len(ids), "geraet": geraet_r})
            print(f"{name} {r['id']}: korrekt {r['korrekt']}, Wert {s:.2f}, unsicher {s < float(S['thr'])}, "
                  f"{len(ids)} Tokens{' [CPU-Notausgang]' if geraet_r != geraet else ''}", flush=True)
    json.dump(erg, open(a.aus, "w"), indent=1)
    for name in sorted({e["modell"] for e in erg}):
        g = [e for e in erg if e["modell"] == name and e["endantwort"]]
        r_ = [e for e in g if e["korrekt"]]
        f_ = [e for e in g if not e["korrekt"]]
        ohne = sum(1 for e in erg if e["modell"] == name and not e["endantwort"])
        print(f"== {name}: Endantworten {len(g)} (ohne Endantwort {ohne}) | richtige als unsicher markiert "
              f"{sum(e['unsicher'] for e in r_)}/{len(r_)} | falsche als unsicher markiert {sum(e['unsicher'] for e in f_)}/{len(f_)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e_ = sub.add_parser("einfrieren")
    e_.add_argument("--sammlung", required=True); e_.add_argument("--schicht", type=int, default=13)
    e_.add_argument("--lam", type=float, default=50.0); e_.add_argument("--aus", required=True)
    w_ = sub.add_parser("anwenden")
    w_.add_argument("--sonde", required=True); w_.add_argument("--laeufe", nargs="+", required=True, help="name=pfad1+pfad2")
    w_.add_argument("--modell", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    w_.add_argument("--geraet", default="cuda"); w_.add_argument("--max-laeufe", type=int, default=0)
    w_.add_argument("--aus", required=True)
    s = sub.add_parser("sammeln")
    s.add_argument("--laeufe", nargs="+", required=True)
    s.add_argument("--modell", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    s.add_argument("--schichten", default="8,11,13,15,17,19,21,23")
    s.add_argument("--geraet", default="cuda")
    s.add_argument("--max-laeufe", type=int, default=0)
    s.add_argument("--bereinigt", action="store_true", help="Etiketten mit bereinigtem Kandidaten-Text (ab 06.11. 15:20)")
    s.add_argument("--aus", required=True)
    p = sub.add_parser("pruefen")
    p.add_argument("--sammlung", required=True)
    p.add_argument("--lam", type=float, default=50.0)
    a = ap.parse_args()
    {"sammeln": sammeln, "pruefen": pruefen, "einfrieren": einfrieren, "anwenden": anwenden}[a.cmd](a)


if __name__ == "__main__":
    main()
