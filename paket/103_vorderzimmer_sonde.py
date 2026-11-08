"""(N21) Vorderzimmer-Sonde (08.11.; Nutzer „Ja, mit einplanen“; Lesart vorab in ANNAHMEN 08.11. 13:12).
Frage: Gibt es an der Abgabe im Vorderzimmer (Antwortmodus, INT) eine lineare Wahrheits-Information, die die eingefrorene
Hinterzimmer-Sonde nicht sieht? Oder sind die Fehler dort wirklich selbstsicher?
Teil A (--sammeln, GPU): Zustand am letzten Token des letzten \\boxed{…} (Stelle wie 89 Teil A), Ausgang der Schichten
  4, 6, 8, 10, 11, 12, 13, 14. Bis dorthin sind alle unsere Modelle bei gleichem Text identisch (Edits ab Schicht 15); gelesen mit
  eigen, ohne Generierung. Je Lauf-Satz eine Datei ergebnisse/vorderzimmer/<satz>.npz (fortsetzbar: fertige Sätze werden
  übersprungen, solange die Laufzahl gleich ist).
Teil B (--auswerten, CPU): Training auf Set B + 1–160 (5-fach-Kreuzvalidierung, nach Aufgabe gruppiert, wählt Schicht und
  L2-Stärke), danach eingefroren und einmal getestet auf INT Seed 0 161–300. Grundlinie log(Tokens) + Stufe. Urteil N21.
  python 103_vorderzimmer_sonde.py --sammeln [--geraet cuda] [--nur SATZ ...]
  python 103_vorderzimmer_sonde.py --auswerten
"""
import argparse
import importlib.util
import json
import os
import re
import sys

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
ERG = os.path.join(WURZEL, "ergebnisse")
ORDNER = os.path.join(ERG, "vorderzimmer")
SCHICHTEN = [4, 6, 8, 10, 11, 12, 13, 14]
TRAIN = ["setB60-ohne-eigen-t06", "setB20-p0-eigen-antwort", "m500-001-080-ohne-eigen-t06", "m500-081-160-ohne-eigen-t06"]
TEST = ["s3-int-eigen-161-210", "s3-int-eigen-211-260", "s3-int-eigen-261-300"]
EXTRA = {"MIT im Vorderzimmer": ["s3-mitint-161-210", "s3-mitint-211-260", "s3-mitint-261-300"],
         "INT Seed 1": ["s3-int-eigen-161-185-s1", "s3-int-eigen-186-210-s1", "s3-int-eigen-211-260-s1", "s3-int-eigen-261-300-s1"]}
LAMBDAS = [1.0, 10.0, 100.0, 1000.0, 10000.0]


class Stopp(Exception):
    pass


def lade_mod(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def laufe(d):
    p = os.path.join(ERG, d, "ergebnisse.jsonl")
    return [json.loads(z) for z in open(p, encoding="utf-8")] if os.path.exists(p) else []


def stufen():
    st = {}
    for z in open(os.path.join(WURZEL, "daten", "math500.jsonl"), encoding="utf-8"):
        d = json.loads(z)
        st[d["unique_id"]] = int(d["level"])
    for z in (z for f in ("math_train_setB60.jsonl", "math_train_neu40.jsonl")
              for z in open(os.path.join(WURZEL, "daten", "practice", f), encoding="utf-8")):
        d = json.loads(z)
        m = re.search(r"\d", str(d.get("level", "")))
        st[d["id"]] = int(m.group()) if m else 3
    return st


def lesemodell(pfad, geraet, speicher):
    """Haken am Ausgang der Schichten; gespeichert wird nur die LETZTE Stelle; Abbruch nach der tiefsten Schicht."""
    import torch
    import transformers as tf
    dt = torch.bfloat16 if geraet == "cuda" else torch.float32
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(pfad, dtype=dt)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(pfad, dtype=dt)
    model.to(geraet).eval()
    tiefste = max(SCHICHTEN)
    n_haken = 0
    for n, m in model.named_modules():
        for L in SCHICHTEN:
            if re.search(rf"(language_model|model)\.layers\.{L}$", n) and "visual" not in n:
                def hook(mod, inp, out, L=L):
                    h = out[0] if isinstance(out, tuple) else out
                    speicher[L] = h[0, -1].detach().float().cpu().numpy()
                    if L == tiefste:
                        raise Stopp()
                m.register_forward_hook(hook)
                n_haken += 1
    assert n_haken == len(SCHICHTEN), f"nur {n_haken} Haken gesetzt"
    return model


def sammeln(a):
    import torch
    wm = lade_mod("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))
    import transformers as tf
    tok = tf.AutoTokenizer.from_pretrained(os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    os.makedirs(ORDNER, exist_ok=True)
    pfad = os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL")
    saetze = a.nur or (TRAIN + TEST + [d for v in EXTRA.values() for d in v])
    model, speicher = None, {}
    for d in saetze:
        R = laufe(d)
        ziel = os.path.join(ORDNER, d + ".npz")
        if not R:
            print(f"FEHLT (noch): {d}", flush=True)
            continue
        if os.path.exists(ziel) and int(np.load(ziel)["n_laeufe"]) == len(R):
            print(f"{d}: schon gesammelt ({len(R)} Läufe)", flush=True)
            continue
        X, meta = [], []
        for r in R:
            st = [tok.decode([t]) for t in r["gen_ids"]]
            text = "".join(st)
            boxed = [(s0, e) for s0, e, _ in wm.kandidaten_mit_ende(text) if text.startswith("\\boxed{", s0)]
            m = {"id": r["id"], "korrekt": bool(r["korrekt"]), "tokens": int(r["tokens"]), "ende": r["ende"], "antwort": bool(boxed)}
            if boxed:
                gr = np.cumsum([len(s) for s in st])
                ti = min(int(np.searchsorted(gr, boxed[-1][1] - 1, side="right")), len(st) - 1)
                ids = r["prompt_ids"] + r["gen_ids"][:ti + 1]
                if model is None:
                    model = lesemodell(pfad, a.geraet, speicher)
                speicher.clear()
                try:
                    with torch.no_grad():
                        model(input_ids=torch.tensor([ids], device=a.geraet), use_cache=False)
                except Stopp:
                    pass
                except torch.OutOfMemoryError:
                    speicher.clear()
                    torch.cuda.empty_cache()
                    m["oom"] = True
                if len(speicher) == len(SCHICHTEN):
                    X.append(np.stack([speicher[L] for L in SCHICHTEN]).astype(np.float16))
                    m["zeile"] = len(X) - 1
            meta.append(m)
        np.savez_compressed(ziel, X=np.array(X) if X else np.zeros((0, len(SCHICHTEN), 1), np.float16),
                            meta=json.dumps(meta), n_laeufe=len(R), schichten=np.array(SCHICHTEN))
        print(f"{d}: {len(R)} Läufe, {len(X)} Zustände, ohne \\boxed {sum(not m['antwort'] for m in meta)}, "
              f"Speicher-Abbruch {sum(1 for m in meta if m.get('oom'))}", flush=True)


def lade_satz(d, st):
    p = os.path.join(ORDNER, d + ".npz")
    if not os.path.exists(p):
        return None
    z = np.load(p)
    meta = json.loads(str(z["meta"]))
    M = [m for m in meta if "zeile" in m]
    if not M:
        return None
    X = z["X"].astype(np.float32)[[m["zeile"] for m in M]]
    return {"X": X, "y": np.array([1.0 if m["korrekt"] else 0.0 for m in M]), "ids": [m["id"] for m in M],
            "tokens": np.array([m["tokens"] for m in M], float), "stufe": np.array([st.get(m["id"], 3) for m in M], float),
            "n_ohne": sum(1 for m in meta if "zeile" not in m)}


def verbinden(teile):
    teile = [t for t in teile if t is not None]
    if not teile:
        return None
    return {"X": np.concatenate([t["X"] for t in teile]), "y": np.concatenate([t["y"] for t in teile]),
            "ids": sum((t["ids"] for t in teile), []), "tokens": np.concatenate([t["tokens"] for t in teile]),
            "stufe": np.concatenate([t["stufe"] for t in teile]), "n_ohne": sum(t["n_ohne"] for t in teile)}


def auc(s, y):
    """Paarweise AUC, Gleichstände zählen 0,5."""
    s, y = np.asarray(s, float), np.asarray(y)
    p, n = s[y == 1], s[y == 0]
    if len(p) == 0 or len(n) == 0:
        return float("nan")
    d = p[:, None] - n[None, :]
    return float(((d > 0).sum() + 0.5 * (d == 0).sum()) / d.size)


def ridge_logreg(X, y, lam, iters=30):
    """L2-logistische Regression (Newton/IRLS); Achsenabschnitt unbestraft. Rückgabe (w, b).
    Bei mehr Merkmalen als Beispielen wird exakt im Zeilenraum gerechnet (die L2-Lösung liegt dort), das spart Rechenzeit."""
    n, d = X.shape
    if d > n:
        Vt = np.linalg.svd(X, full_matrices=False)[2]
        beta, b = ridge_logreg(X @ Vt.T, y, lam, iters)
        return Vt.T @ beta, b
    A = np.hstack([X, np.ones((n, 1))])
    P = np.eye(d + 1) * lam
    P[-1, -1] = 0.0
    w = np.zeros(d + 1)
    for _ in range(iters):
        z = np.clip(A @ w, -30, 30)
        p = 1.0 / (1.0 + np.exp(-z))
        g = A.T @ (p - y) + P @ w
        H = (A * (p * (1 - p))[:, None]).T @ A + P + 1e-6 * np.eye(d + 1)
        schritt = np.linalg.solve(H, g)
        w -= schritt
        if np.max(np.abs(schritt)) < 1e-6:
            break
    return w[:-1], w[-1]


def standard(Xtr, *andere):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    return [(Xtr - mu) / sd] + [(X - mu) / sd for X in andere]


def faltungen(ids, k=5, seed=0):
    aufgaben = sorted(set(ids))
    rng = np.random.default_rng(seed)
    rng.shuffle(aufgaben)
    fach = {a: i % k for i, a in enumerate(aufgaben)}
    return np.array([fach[i] for i in ids])


def auswerten(a):
    sys.stdout.reconfigure(encoding="utf-8")
    st = stufen()
    T = verbinden([lade_satz(d, st) for d in TRAIN])
    P = verbinden([lade_satz(d, st) for d in TEST])
    if T is None or P is None:
        print("Zustände fehlen – erst --sammeln")
        return
    print(f"Training: {len(T['y'])} Abgaben ({int(T['y'].sum())} richtig; ohne \\boxed/abgebrochen {T['n_ohne']}) | "
          f"Test INT Seed 0 161–300: {len(P['y'])} ({int(P['y'].sum())} richtig; ohne {P['n_ohne']})")
    f = faltungen(T["ids"])
    B = {"cv": {}}
    beste = (-1.0, None, None)
    for k, L in enumerate(SCHICHTEN):
        zeile = []
        for lam in LAMBDAS:
            oof = np.zeros(len(T["y"]))
            for fo in range(5):
                tr, te = f != fo, f == fo
                Xa, Xb = standard(T["X"][tr, k], T["X"][te, k])
                w, b = ridge_logreg(Xa, T["y"][tr], lam)
                oof[te] = Xb @ w + b
            A = auc(oof, T["y"])
            B["cv"][f"L{L} λ{lam:g}"] = A
            zeile.append(f"λ {lam:g}: {A:.3f}")
            if A > beste[0]:
                beste = (A, (k, L, lam), oof.copy())
        print(f"   CV Schicht {L:2d}: " + " | ".join(zeile))
    A_cv, (k, L, lam), oof = beste
    print(f"Gewählt (nur Training): Schicht {L}, λ {lam:g}, CV-AUC {A_cv:.3f} → eingefroren")
    Xa, Xp = standard(T["X"][:, k], P["X"][:, k])
    w, b = ridge_logreg(Xa, T["y"], lam)

    def sonde(D):
        return standard(T["X"][:, k], D["X"][:, k])[1] @ w + b

    def grund(D):
        return np.stack([np.log1p(D["tokens"]), D["stufe"]], 1)
    G = standard(grund(T), grund(P))
    wg, bg = ridge_logreg(G[0], T["y"], 1e-3)
    s_p = sonde(P)
    g_p = G[1] @ wg + bg
    # kombiniert: Grundlinie + Sonden-Wert; im Training mit den Out-of-fold-Werten (kein Durchsickern)
    Kt = np.column_stack([G[0], oof])
    Kp = np.column_stack([G[1], s_p])
    mu, sd = Kt.mean(0), Kt.std(0) + 1e-6
    wk, bk = ridge_logreg((Kt - mu) / sd, T["y"], 1e-3)
    k_p = ((Kp - mu) / sd) @ wk + bk
    A_s, A_g, A_k = auc(s_p, P["y"]), auc(g_p, P["y"]), auc(k_p, P["y"])
    print(f"\n== Test INT Seed 0 161–300 (n {len(P['y'])}): Sonde AUC {A_s:.3f} | Grundlinie (log Tokens + Stufe) {A_g:.3f} | "
          f"kombiniert {A_k:.3f} (Zuwachs {A_k - A_g:+.3f})")
    schnell = P["tokens"] <= 2000
    print(f"   nur schnelle Läufe (≤ 2.000 Tokens, n {int(schnell.sum())}, richtig {int(P['y'][schnell].sum())}): "
          f"Sonde AUC {auc(s_p[schnell], P['y'][schnell]):.3f}")
    # eingefrorene Hinterzimmer-Sonde an denselben Stellen (89 Teil A)
    alt = {}
    pa = os.path.join(ERG, "int_sonde.jsonl")
    if os.path.exists(pa):
        for z in open(pa, encoding="utf-8"):
            e = json.loads(z)
            if e.get("satz") == "161–300" and "wert" in e:
                alt[e["id"]] = e["wert"]
    J = [i for i, x in enumerate(P["ids"]) if x in alt]
    if J:
        sa = np.array([alt[P["ids"][i]] for i in J])
        print(f"   Hinterzimmer-Sonde (eingefroren) an denselben Stellen (n {len(J)}): AUC {auc(sa, P['y'][J]):.3f}; "
              f"neue Sonde auf denselben {auc(s_p[J], P['y'][J]):.3f}")
    for name, dirs in EXTRA.items():
        D = verbinden([lade_satz(d, st) for d in dirs])
        if D is not None:
            print(f"   beschreibend {name} (n {len(D['y'])}, richtig {int(D['y'].sum())}): Sonde AUC {auc(sonde(D), D['y']):.3f}")
    urteil = ("Vorderzimmer-Sonde trägt" if (A_s >= 0.70 and A_k - A_g >= 0.05) else
              ("selbstsichere Fehler bestätigt" if A_s <= 0.60 else "offen"))
    print(f"\nURTEIL N21 (vorab): Test-AUC {A_s:.3f}, Zuwachs über Grundlinie {A_k - A_g:+.3f} → {urteil}")
    B.update({"schicht": L, "lambda": lam, "cv_auc": A_cv, "test_auc": A_s, "grundlinie_auc": A_g, "kombiniert_auc": A_k,
              "urteil": urteil, "n_train": int(len(T["y"])), "n_test": int(len(P["y"]))})
    np.savez(os.path.join(ERG, "vorderzimmer_sonde_eingefroren.npz"), w=w, b=b, schicht=L, lam=lam,
             mu=T["X"][:, k].mean(0), sd=T["X"][:, k].std(0) + 1e-6)
    json.dump(B, open(os.path.join(ERG, "vorderzimmer_sonde.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def bestaetigen(name, saetze):
    """N24 / N26 (b): eingefrorene Sonde und eingefrorene Grundlinie auf neuen Abgaben (Lesart vorab in ANNAHMEN)."""
    sys.stdout.reconfigure(encoding="utf-8")
    st = stufen()
    T = verbinden([lade_satz(d, st) for d in TRAIN])
    D = verbinden([lade_satz(d, st) for d in saetze])
    fehlt = [d for d in saetze if lade_satz(d, st) is None]
    if D is None:
        print(f"{name}: keine Zustände ({fehlt})")
        return
    F = np.load(os.path.join(ERG, "vorderzimmer_sonde_eingefroren.npz"))
    k = SCHICHTEN.index(int(F["schicht"]))
    s_t = ((T["X"][:, k] - F["mu"]) / F["sd"]) @ F["w"] + F["b"]
    s_d = ((D["X"][:, k] - F["mu"]) / F["sd"]) @ F["w"] + F["b"]
    median = float(np.median(s_t))

    def grund(X):
        return np.stack([np.log1p(X["tokens"]), X["stufe"]], 1)
    G = standard(grund(T), grund(D))
    wg, bg = ridge_logreg(G[0], T["y"], 1e-3)
    g_d = G[1] @ wg + bg
    schnell = D["tokens"] <= 2000
    A, Ag = auc(s_d, D["y"]), auc(g_d, D["y"])
    As, Ags = auc(s_d[schnell], D["y"][schnell]), auc(g_d[schnell], D["y"][schnell])
    frei = s_d >= median
    print(f"== {name}: {len(D['y'])} Abgaben ({int(D['y'].sum())} richtig; ohne Zustand {D['n_ohne']})" + (f"; FEHLT {fehlt}" if fehlt else ""))
    print(f"   alle: Sonde AUC {A:.3f} | Grundlinie {Ag:.3f} | Zuwachs {A - Ag:+.3f}")
    print(f"   schnell (≤ 2.000 Tokens, n {int(schnell.sum())}, richtig {int(D['y'][schnell].sum())}): Sonde {As:.3f} | Grundlinie {Ags:.3f} | "
          f"Zuwachs {As - Ags:+.3f}")
    print(f"   Freigabe über dem Trainings-Median ({median:.4f}): {int(frei.sum())} Abgaben, richtig {int(D['y'][frei].sum())} "
          f"({100 * D['y'][frei].mean() if frei.any() else float('nan'):.0f} %); schnell und frei: {int((frei & schnell).sum())}, "
          f"richtig {int(D['y'][frei & schnell].sum())}")
    urteil = ("bestätigt" if (A >= 0.70 and As >= 0.70 and A - Ag >= 0.05 and As - Ags >= 0.05) else
              ("widerlegt" if A <= 0.60 else "offen"))
    print(f"URTEIL {name} (vorab): {urteil}")
    json.dump({"auc": A, "auc_grund": Ag, "auc_schnell": As, "auc_grund_schnell": Ags, "n": int(len(D["y"])), "urteil": urteil,
               "frei": [int(frei.sum()), int(D["y"][frei].sum())]},
              open(os.path.join(ERG, f"sonde_bestaetigung_{name}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sammeln", action="store_true")
    ap.add_argument("--auswerten", action="store_true")
    ap.add_argument("--geraet", default="cuda")
    ap.add_argument("--nur", nargs="*")
    ap.add_argument("--bestaetigen", nargs="+", metavar=("NAME", "SATZ"))
    a = ap.parse_args()
    if a.bestaetigen:
        bestaetigen(a.bestaetigen[0], a.bestaetigen[1:])
    elif a.sammeln:
        sammeln(a)
    elif a.auswerten:
        auswerten(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
