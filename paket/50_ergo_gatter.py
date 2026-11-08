"""ERGO-Gatter („Sicherheit ERGO gib ab“ als Gewichts-Eingriff; Schritt 2, Entwurf paket/SCHRITT2_ENTWURF_ERGO_GATTER.md).
Nutzer 06.11. ~22:55: „Ja, vorbereiten“. Nur Übungsdaten.

sammeln: MLP-Eingang x von Schicht 15 (= post_attention_layernorm, für denselben Text bei eigen/ERGORE/MIT gleich) an allen
         Kandidaten-Enden (Etikett bereinigt: roh ODER bereinigt richtig) und an zufälligen gewöhnlichen Tokens je Lauf; dazu
         die Aktivierungs-Statistik aller 3.584 Neuronen von Schicht 15 (Summe, Quadratsumme, Maximum von |a|).
lernen:  (a) Wahrheitssonde w_T (richtig gegen falsch, nur Kandidaten) und (b) Gatter-Sonde w_TC (Ende eines RICHTIGEN Kandidaten
         gegen alles andere: falsche Kandidaten + gewöhnliche Tokens), beide zurückgehalten nach Aufgabe geprüft; Bias-Ersatz v
         (Kleinste Quadrate: vᵀx ≈ 1); Wahl der K ruhigsten Neuronen außerhalb der 64 Schleifen-Spalten.
bauen:   eigen-vL + Gatter-Neuronen G in Schicht 15: gate_proj[G] = κ_g·(w_TC + (b − τ)·v), up_proj[G] = v (≈ 1),
         down_proj[:, G] = κ_d·e⊥. Kein Laufzeit-Hook nötig.
pruefen: zurückgehaltene Feuerrate des Gatters an richtigen/falschen Kandidaten-Enden und an gewöhnlichen Tokens.
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
sys.path.insert(0, HIER)
L = 15


def lade(name, pfad):
    s = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


wm = lade("wm", os.path.join(HIER, "42_wahrheitsmelder.py"))


class Stopp(Exception):
    pass


def sammeln(a):
    import torch
    import transformers as tf
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    torch.set_num_threads(int(os.environ.get("WSP_THREADS", 2)))
    geraet = a.geraet
    dt = torch.bfloat16 if geraet == "cuda" else torch.float32
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(a.modell, dtype=dt)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(a.modell, dtype=dt)
    model.to(geraet).eval()
    sp = {}
    stat = {"n": 0, "s": None, "q": None, "m": None}

    def hook_mlp(mod, inp):
        sp["x"] = inp[0][0].detach().float()

    def hook_down(mod, inp):
        A = inp[0][0].detach().float()
        sp["a_n"] = A.shape[0]
        s, q, m = A.abs().sum(0), (A * A).sum(0), A.abs().max(0).values
        stat["s"] = s if stat["s"] is None else stat["s"] + s
        stat["q"] = q if stat["q"] is None else stat["q"] + q
        stat["m"] = m if stat["m"] is None else torch.maximum(stat["m"], m)
        stat["n"] += A.shape[0]
        raise Stopp()
    for n, m in model.named_modules():
        if "visual" in n:
            continue
        if re.search(rf"(language_model|model)\.layers\.{L}\.mlp$", n):
            m.register_forward_pre_hook(hook_mlp)
        if re.search(rf"(language_model|model)\.layers\.{L}\.mlp\.down_proj$", n):
            m.register_forward_pre_hook(hook_down)
    rng = np.random.default_rng(0)
    Xk, yk, lk, ak, endk, Xn, ln_, an_ = [], [], [], [], [], [], [], []
    for pfad in a.laeufe:
        tag = os.path.basename(os.path.dirname(pfad))
        n_l = 0
        for z in open(pfad, encoding="utf-8"):
            if a.max_laeufe and n_l >= a.max_laeufe:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            grenzen = np.cumsum([len(s) for s in stuecke])
            ks = wm.kandidaten_mit_ende(text)
            pos = [min(int(np.searchsorted(grenzen, e - 1, side="right")), len(stuecke) - 1) for _, e, _ in ks]
            sp.clear()
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([r["prompt_ids"] + gen], device=geraet))
            except Stopp:
                pass
            except torch.OutOfMemoryError:
                print(f"Speicher reicht nicht – Lauf übersprungen: {tag}/{r['id']}", flush=True)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                continue
            X = sp["x"][len(r["prompt_ids"]):].cpu().numpy()
            kpos = set()
            for (_, _, c), ti in zip(ks, pos):
                Xk.append(X[ti])
                yk.append(bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"])))
                lk.append(f"{tag}/{r['id']}")
                ak.append(r["id"])
                endk.append(ti)
                kpos.update(range(max(0, ti - 2), ti + 3))
            frei = [t for t in range(len(gen)) if t not in kpos]
            for t in rng.choice(frei, size=min(a.normal_je_lauf, len(frei)), replace=False) if frei else []:
                Xn.append(X[int(t)])
                ln_.append(f"{tag}/{r['id']}")
                an_.append(r["id"])
            n_l += 1
            print(f"{tag} {r['id']}: {len(ks)} Kandidaten, {len(gen)} Tokens", flush=True)
    n = max(1, stat["n"])
    mittel = (stat["s"] / n).cpu().numpy()
    streu = np.sqrt(np.maximum((stat["q"] / n).cpu().numpy() - mittel ** 2, 0))
    np.savez_compressed(a.aus, Xk=np.stack(Xk).astype(np.float32), yk=np.array(yk), lk=np.array(lk), ak=np.array(ak),
                        endk=np.array(endk), Xn=np.stack(Xn).astype(np.float32), ln=np.array(ln_), an=np.array(an_),
                        neuron_mittel_abs=mittel, neuron_rms=np.sqrt((stat["q"] / n).cpu().numpy()), neuron_streu=streu,
                        neuron_max_abs=stat["m"].cpu().numpy(), tokens=n)
    print(f"gespeichert: {a.aus} – {len(yk)} Kandidaten ({sum(yk)} richtig), {len(Xn)} gewöhnliche Tokens, {n} Tokens Statistik")


def falten(aufgaben):
    eind = sorted(set(aufgaben))
    rng = np.random.default_rng(0)
    rng.shuffle(eind)
    return {t: i % 5 for i, t in enumerate(eind)}


def sonde_oof(X, y, f, lam):
    """Logistische Sonde: zurückgehaltene Werte (Faltungen f) und endgültige Sonde auf allen Daten in rohen x-Koordinaten."""
    oof = np.zeros(len(y))
    for k in range(5):
        tr = f != k
        if not (f == k).any():
            continue
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6
        w, b = wm.logreg((X[tr] - mu) / sd, y[tr].astype(float), lam)
        oof[f == k] = ((X[f == k] - mu) / sd) @ w + b
    mu, sd = X.mean(0), X.std(0) + 1e-6
    w, b = wm.logreg((X - mu) / sd, y.astype(float), lam)
    return oof, w / sd, b - float((w * mu / sd).sum())


def lernen(a):
    """Gatter „Kandidat × Wahrheit“ (06.11. ~23:05, umgedreht gegenüber dem ersten Entwurf):
    gate (gleichgerichtet) = Kandidaten-Ende-Melder s_C → an gewöhnlichen Tokens aus (kein Zucken mitten im Text);
    up (mit Vorzeichen) = Wahrheitssonde s_T → richtiger Kandidat: Schub zum Abgeben, falscher: Schub zum Weiterdenken.
    Schwellen (vorab als Regel): τ_C = (1 − fehl_normal)-Quantil der zurückgehaltenen s_C an gewöhnlichen Tokens;
    Nullpunkt τ_T = Mitte zwischen den Medianen richtiger und falscher Kandidaten (zurückgehalten)."""
    Z = np.load(a.sammlung)
    Xk, yk, ak = Z["Xk"].astype(np.float64), Z["yk"].astype(bool), Z["ak"].astype(str)
    Xn, an_ = Z["Xn"].astype(np.float64), Z["an"].astype(str)
    f = falten(list(ak) + list(an_))
    fk, fn = np.array([f[t] for t in ak]), np.array([f[t] for t in an_])
    # Wahrheitssonde s_T: nur Kandidaten (richtig gegen falsch)
    oof_T, wT, bT = sonde_oof(Xk, yk, fk, a.lam)
    print(f"Wahrheitssonde s_T (MLP-Eingang Schicht 15): AUC zurückgehalten {wm.auc(oof_T, yk):.3f} ({len(yk)} Kandidaten, {yk.sum()} richtig)")
    # Kandidaten-Ende-Melder s_C: alle Kandidaten-Enden gegen gewöhnliche Tokens
    X = np.vstack([Xk, Xn])
    yC = np.concatenate([np.ones(len(Xk), bool), np.zeros(len(Xn), bool)])
    fC = np.concatenate([fk, fn])
    oof_C, wC, bC = sonde_oof(X, yC, fC, a.lam)
    print(f"Kandidaten-Ende-Melder s_C: AUC zurückgehalten {wm.auc(oof_C, yC):.4f} ({len(Xn)} gewöhnliche Tokens)")
    sC_k, sC_n = oof_C[:len(Xk)], oof_C[len(Xk):]
    tau_C = float(np.quantile(sC_n, 1 - a.fehl_normal))
    print(f"τ_C = {tau_C:.3f}: Gate offen an Kandidaten-Enden {100 * float((sC_k > tau_C).mean()):.1f} %, an gewöhnlichen Tokens "
          f"{100 * float((sC_n > tau_C).mean()):.3f} %")
    med_r, med_f = float(np.median(oof_T[yk])), float(np.median(oof_T[~yk]))
    tau_T = 0.5 * (med_r + med_f)
    print(f"Wahrheit: Median richtig {med_r:.2f}, falsch {med_f:.2f} → Nullpunkt τ_T = {tau_T:.2f} | richtige über τ_T "
          f"{100 * float((oof_T[yk] > tau_T).mean()):.1f} %, falsche über τ_T {100 * float((oof_T[~yk] > tau_T).mean()):.1f} %")
    # Wahrheitssonde an gewöhnlichen Tokens (nur zur Information: dort ist das Gate zu)
    sT_n = Xn @ wT + bT
    print(f"   (s_T an gewöhnlichen Tokens, nur Info: Median {np.median(sT_n):.2f})")
    # Simulation der Gatter-Ausgabe (zurückgehalten): a = SiLU(z_C) · (s_T − τ_T)/(med_r − τ_T)
    offen = sC_k[sC_k > tau_C]                     # typische GEÖFFNETE Kandidaten-Enden → z = z_ziel
    kC = a.z_ziel / (float(np.median(offen)) - tau_C) if len(offen) else a.z_ziel
    silu = lambda z: z / (1 + np.exp(-np.clip(z, -60, 60)))  # noqa: E731
    gk = silu(kC * (sC_k - tau_C)) * (oof_T - tau_T) / (med_r - tau_T)
    gn = silu(kC * (sC_n - tau_C)) * (sT_n - tau_T) / (med_r - tau_T)
    ref = silu(a.z_ziel)
    for name, x in (("richtige Kandidaten", gk[yk]), ("falsche Kandidaten", gk[~yk]), ("gewöhnliche Tokens", gn)):
        print(f"   Ausgabe/Ziel {name:20s}: Median {np.median(x) / ref:+.2f} | Anteil > +0,5: {100 * float((x / ref > 0.5).mean()):.2f} % | "
              f"Anteil < −0,5: {100 * float((x / ref < -0.5).mean()):.2f} %")
    # Bias-Ersatz v: vᵀx ≈ 1 (kleinste Quadrate auf gewöhnlichen Tokens)
    lam_v = 1e-3 * len(Xn)
    v = np.linalg.solve(Xn.T @ Xn + lam_v * np.eye(X.shape[1]), Xn.T @ np.ones(len(Xn)))
    vx = X @ v
    print(f"Bias-Ersatz vᵀx: Mittel {vx.mean():.4f}, Streuung {vx.std():.4f}")
    # ruhigste Neuronen außerhalb der 64 Schleifen-Spalten
    R = dict(np.load(a.richtung))
    S = set(int(s) for s in R[f"spalten_{L}"])
    rms = Z["neuron_rms"]
    G = np.array([j for j in np.argsort(rms) if int(j) not in S][:a.k], dtype=np.int64)
    print(f"ruhigste {a.k} Neuronen: {G.tolist()} | RMS {rms[G].min():.2e}–{rms[G].max():.2e} (Median aller {np.median(rms):.2e})")
    np.savez(a.aus, wT=wT, bT=bT, wC=wC, bC=bC, tau_C=tau_C, tau_T=tau_T, med_r=med_r, med_f=med_f, kC=kC, v=v, G=G,
             med_sC_k=float(np.median(sC_k)), auc_T=wm.auc(oof_T, yk), auc_C=wm.auc(oof_C, yC), oof_T=oof_T, yk=yk,
             sC_k=sC_k, sC_n=sC_n, sT_n=sT_n)
    print(f"gespeichert: {a.aus}")


def bauen(a):
    """eigen-vL + Gatter-Neuronen G in Schicht 15. Gesamtschub an einem typischen richtigen Kandidaten-Ende = --schub
    (Richtung e⊥, Entschluss-Achse orthogonal zu u_e, wie bei ERGORE); z(x) = κ_g·(w_rohᵀx + b_roh − τ) über vᵀx ≈ 1."""
    import wsp_lib as W
    Lz = np.load(a.lern)
    wT, bT, wC, bC = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"])
    tau_C, tau_T, med_r, kC, v = float(Lz["tau_C"]), float(Lz["tau_T"]), float(Lz["med_r"]), float(Lz["kC"]), Lz["v"]
    G = Lz["G"].astype(np.int64)
    if med_r <= tau_T:
        raise SystemExit(f"Median richtiger Kandidaten {med_r:.3f} liegt nicht über dem Nullpunkt {tau_T:.3f} – Abbruch")
    kappa_g = kC                                   # z_C = κ_C·(s_C − τ_C), Median Kandidaten-Ende → z_ziel
    kappa_u = 1.0 / (med_r - tau_T)                # up = (s_T − τ_T)/(med_r − τ_T): richtiger Median → +1
    silu = a.z_ziel / (1 + np.exp(-a.z_ziel))
    kappa_d = a.schub / (len(G) * silu)
    zeile_gate = kappa_g * (wC + (bC - tau_C) * v)
    zeile_up = kappa_u * (wT + (bT - tau_T) * v)
    R = dict(np.load(a.richtung))
    u = R[f"u_{L}"].astype(np.float64)
    u /= np.linalg.norm(u)
    e = dict(np.load(a.achse))[f"u_{L}"].astype(np.float64)
    e -= (e @ u) * u
    e /= np.linalg.norm(e)
    patches, info = {}, {}
    # 1) Umkehr wie eigen-vL auf Schicht 15 und 19 (aus dem GRUNDmodell gerechnet, Kontrolle: bitgleich mit eigen-vL)
    #    – bewusst nicht von eigen-vL kopiert: dessen wsp_patch.json ist hart verlinkt und würde überschrieben.
    down = {}
    for Ls in (15, 19):
        name = f"model.language_model.layers.{Ls}.mlp.down_proj.weight"
        _, bits = W.tensor_lesen(a.basis, name)
        W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
        u_l = R[f"u_{Ls}"].astype(np.float64)
        u_l /= np.linalg.norm(u_l)
        S_l = np.asarray(R[f"spalten_{Ls}"], dtype=np.int64)
        W1 = np.asarray(W.rang1_edit(W0, u_l, S_l, a.alpha), dtype=np.float64)
        if a.vergleich:
            _, ref = W.tensor_lesen(a.vergleich, name)
            gleich = float(np.mean(np.asarray(ref) == W.bf16_bits(W1)))
            info[f"umkehr_{Ls}_bitgleich_wie_vergleich"] = round(gleich, 6)
            print(f"Umkehr Schicht {Ls}: bitgleich mit Vergleich zu {100 * gleich:.4f} %", flush=True)
        down[Ls] = (name, W0, W1)
    # 2) Gatter-Neuronen G in Schicht 15 (gate/up aus dem Grundmodell, down nach der Umkehr; G ∩ S = ∅)
    S15 = set(int(s) for s in R[f"spalten_{L}"])
    assert not (set(G.tolist()) & S15), "Gatter-Neuronen überschneiden sich mit den Schleifen-Spalten"
    for k in ("gate", "up"):
        name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
        _, bits = W.tensor_lesen(a.basis, name)
        T = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64).copy()
        alt = T.copy()
        T[G, :] = (zeile_gate if k == "gate" else zeile_up)[None, :]
        patches[name] = W.bf16_bits(T)
        info[name] = {"zeilen": int(len(G)), "relative_aenderung": round(float(np.linalg.norm(T - alt) / np.linalg.norm(alt)), 5)}
        print(name, info[name], flush=True)
    for Ls, (name, W0, W1) in down.items():
        if Ls == L:
            W1 = W1.copy()
            W1[:, G] = (kappa_d * e)[:, None]
        patches[name] = W.bf16_bits(W1)
        info[name] = {"relative_aenderung": round(float(np.linalg.norm(W1 - W0) / np.linalg.norm(W0)), 5)}
        print(name, info[name], flush=True)
    meta = {"art": "ERGO-Gatter: gate = Kandidaten-Ende (gleichgerichtet), up = Wahrheit (mit Vorzeichen), down = e_perp",
            "basis": os.path.abspath(a.basis), "lern": os.path.abspath(a.lern), "neuronen": G.tolist(), "tau_C": tau_C,
            "tau_T": tau_T, "kappa_g": kappa_g, "kappa_u": kappa_u, "kappa_d": kappa_d, "schub": a.schub, "z_ziel": a.z_ziel,
            "median_richtig_oof": med_r, "achse": os.path.abspath(a.achse), "alpha": a.alpha, "tensoren": info}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Modell: {a.aus} | κ_g {kappa_g:.3f}, κ_u {kappa_u:.3f}, κ_d {kappa_d:.4f}, τ_C {tau_C:.3f}, τ_T {tau_T:.3f}")


def bauen_zig(a):
    """V2.1 „Zünder im Gewicht“ (07.11. ~05:05, nach den Nachuntersuchungen 53–57): eigen + Gatter-Neuronen G in Schicht 15 mit
    gate (gleichgerichtet) = WAHRHEIT mit hoher Schwelle (höchstens --fehl-falsch der falschen Kandidaten darüber, zurückgehalten),
    up (mit Vorzeichen) = Kandidaten-Ende (95 % der Enden positiv), down = κ_d·ĝ (Abschluss-Gradient: sofortiges `</think>`).
    Gesamtanstoß an einem typischen sicher-richtigen Kandidaten-Ende = --kappa (Residual-Einheiten; Probe: κ 5 → p ≈ 0,95)."""
    import wsp_lib as W
    Lz = np.load(a.lern)
    wT, bT, wC, bC, v = Lz["wT"], float(Lz["bT"]), Lz["wC"], float(Lz["bC"]), Lz["v"]
    G = Lz["G"].astype(np.int64)
    oof_T, yk, sC_k = Lz["oof_T"], Lz["yk"].astype(bool), Lz["sC_k"]
    tau_T = float(np.quantile(oof_T[~yk], 1 - a.fehl_falsch))
    ueber = oof_T[yk & (oof_T > tau_T)]
    if not len(ueber):
        raise SystemExit("Keine richtigen Kandidaten über der Wahrheits-Schwelle – Abbruch")
    kappa_g = a.z_ziel / (float(np.median(ueber)) - tau_T)
    tau_C = float(np.quantile(sC_k, 0.05))
    kappa_u = 1.0 / (float(np.median(sC_k)) - tau_C)
    silu = a.z_ziel / (1 + np.exp(-a.z_ziel))
    kappa_d = a.kappa / (len(G) * silu)
    g = np.load(a.gradient)["g_15"].astype(np.float64)
    g /= np.linalg.norm(g)
    print(f"Wahrheits-Schwelle τ_T {tau_T:.3f}: richtige darüber {100 * float((oof_T[yk] > tau_T).mean()):.1f} %, falsche darüber "
          f"{100 * float((oof_T[~yk] > tau_T).mean()):.1f} % (zurückgehalten) | τ_C {tau_C:.3f}", flush=True)
    zeile_gate = kappa_g * (wT + (bT - tau_T) * v)
    zeile_up = kappa_u * (wC + (bC - tau_C) * v)
    R = dict(np.load(a.richtung))
    patches, info = {}, {}
    down = {}
    for Ls in (15, 19):
        name = f"model.language_model.layers.{Ls}.mlp.down_proj.weight"
        _, bits = W.tensor_lesen(a.basis, name)
        W0 = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64)
        u_l = R[f"u_{Ls}"].astype(np.float64)
        u_l /= np.linalg.norm(u_l)
        W1 = np.asarray(W.rang1_edit(W0, u_l, np.asarray(R[f"spalten_{Ls}"], dtype=np.int64), a.alpha), dtype=np.float64)
        if a.vergleich:
            _, ref = W.tensor_lesen(a.vergleich, name)
            info[f"umkehr_{Ls}_bitgleich"] = round(float(np.mean(np.asarray(ref) == W.bf16_bits(W1))), 6)
            print(f"Umkehr Schicht {Ls}: bitgleich mit Vergleich zu {100 * info[f'umkehr_{Ls}_bitgleich']:.4f} %", flush=True)
        down[Ls] = (name, W0, W1)
    assert not (set(G.tolist()) & set(int(s) for s in R[f"spalten_{L}"]))
    for k in ("gate", "up"):
        name = f"model.language_model.layers.{L}.mlp.{k}_proj.weight"
        _, bits = W.tensor_lesen(a.basis, name)
        T = np.asarray(W.bf16_to_f32(np.asarray(bits)), dtype=np.float64).copy()
        T[G, :] = (zeile_gate if k == "gate" else zeile_up)[None, :]
        patches[name] = W.bf16_bits(T)
    for Ls, (name, W0, W1) in down.items():
        if Ls == L:
            W1 = W1.copy()
            W1[:, G] = (kappa_d * g)[:, None]
        patches[name] = W.bf16_bits(W1)
    meta = {"art": "V2.1 Zünder im Gewicht: gate = Wahrheit (hohe Schwelle), up = Kandidaten-Ende, down = Abschluss-Gradient",
            "basis": os.path.abspath(a.basis), "lern": os.path.abspath(a.lern), "gradient": os.path.abspath(a.gradient),
            "neuronen": G.tolist(), "tau_T": tau_T, "tau_C": tau_C, "kappa_g": kappa_g, "kappa_u": kappa_u, "kappa_d": kappa_d,
            "kappa": a.kappa, "z_ziel": a.z_ziel, "fehl_falsch": a.fehl_falsch, "alpha": a.alpha, "tensoren": info}
    W.modell_mit_patch(a.basis, a.aus, patches, meta)
    print(f"Modell: {a.aus} | κ_g {kappa_g:.3f}, κ_u {kappa_u:.3f}, κ_d {kappa_d:.4f}")


def q8_0(m):
    """Quantisieren/Dequantisieren wie GGUF q8_0 (Blöcke zu 32 entlang der letzten Achse, Skala max|w|/127)."""
    m = np.asarray(m, dtype=np.float64)
    form = m.shape
    b = m.reshape(-1, 32)
    d = np.abs(b).max(1, keepdims=True) / 127.0
    d[d == 0] = 1.0
    d = d.astype(np.float16).astype(np.float64)
    return (np.round(b / d).clip(-127, 127) * d).reshape(form)


def quantprobe(a):
    """Verträgt das Gatter die q8_0-Umwandlung? Vergleicht z(x) mit exakten und mit q8_0-Gewichten UND q8_0-Aktivierungen
    (so rechnet llama.cpp) auf den gesammelten Stellen."""
    Z, Lz = np.load(a.sammlung), np.load(a.lern)
    X = np.vstack([Z["Xk"], Z["Xn"]]).astype(np.float64)
    art = np.array(["richtig" if v else "falsch" for v in Z["yk"]] + ["normal"] * len(Z["Xn"]))
    v = Lz["v"]
    zg = float(Lz["kC"]) * (Lz["wC"] + (float(Lz["bC"]) - float(Lz["tau_C"])) * v)
    zu = (Lz["wT"] + (float(Lz["bT"]) - float(Lz["tau_T"])) * v) / (float(Lz["med_r"]) - float(Lz["tau_T"]))
    silu = lambda z: z / (1 + np.exp(-np.clip(z, -60, 60)))  # noqa: E731
    out_e = silu(X @ zg) * (X @ zu)
    Xq = q8_0(X)
    out_q = silu(Xq @ q8_0(zg)) * (Xq @ q8_0(zu))
    ref = silu(a.z_ziel)
    for name in ("richtig", "falsch", "normal"):
        m = art == name
        e_, q_ = out_e[m] / ref, out_q[m] / ref
        print(f"   {name:8s} n={m.sum():6d} | Ausgabe/Ziel Median exakt {np.median(e_):+.3f}, q8_0 {np.median(q_):+.3f} | "
              f"|Δ| 99%-Quantil {np.quantile(np.abs(e_ - q_), 0.99):.4f} | Vorzeichen gleich {100 * float((np.sign(e_) == np.sign(q_)).mean()):.2f} %")


def pruefen(a):
    """Liest im GEBAUTEN Modell die Gatter-Neuronen (Eingang down_proj, Schicht 15) entlang von Läufen: feuern sie an richtigen
    Kandidaten-Enden und schweigen sonst? (Funktionsprobe der eingeschriebenen Gewichte.)"""
    import torch
    import transformers as tf
    ev = wm.lade("ev", os.path.join(WURZEL, "eval", "03_eval.py"))
    meta = json.load(open(os.path.join(a.modell, "wsp_patch.json"), encoding="utf-8")) if os.path.exists(
        os.path.join(a.modell, "wsp_patch.json")) else None
    G = torch.tensor(np.load(a.lern)["G"].astype(np.int64))
    tok = tf.AutoTokenizer.from_pretrained(a.modell)
    cls = getattr(tf, "AutoModelForImageTextToText", None) or tf.AutoModelForCausalLM
    try:
        model = cls.from_pretrained(a.modell, dtype=torch.bfloat16)
    except Exception:  # noqa: BLE001
        model = tf.AutoModelForCausalLM.from_pretrained(a.modell, dtype=torch.bfloat16)
    model.to(a.geraet).eval()
    sp = {}

    def hook(mod, inp):
        sp["g"] = inp[0][0][:, G.to(inp[0].device)].detach().float().sum(1).cpu().numpy()
        raise Stopp()
    for n, m in model.named_modules():
        if re.search(rf"(language_model|model)\.layers\.{L}\.mlp\.down_proj$", n) and "visual" not in n:
            m.register_forward_pre_hook(hook)
    r_w, f_w, n_w = [], [], []
    n_l = 0
    speicher_runs, meta_runs = {}, []
    for pfad in a.laeufe:
        for z in open(pfad, encoding="utf-8"):
            if a.max_laeufe and n_l >= a.max_laeufe:
                break
            r = json.loads(z)
            gen = r["gen_ids"]
            stuecke = [tok.decode([t]) for t in gen]
            text = "".join(stuecke)
            grenzen = np.cumsum([len(s) for s in stuecke])
            try:
                with torch.no_grad():
                    model(input_ids=torch.tensor([r["prompt_ids"] + gen], device=a.geraet))
            except Stopp:
                pass
            g = sp["g"][len(r["prompt_ids"]):]
            kpos = set()
            kand_meta = []
            for (_, e_, c) in wm.kandidaten_mit_ende(text):
                ti = min(int(np.searchsorted(grenzen, e_ - 1, side="right")), len(stuecke) - 1)
                kpos.update(range(max(0, ti - 2), ti + 3))
                ok = bool(ev.korrekt(c, r["gold"])) or bool(ev.korrekt(wm.bereinige_kandidat(c), r["gold"]))
                (r_w if ok else f_w).append(float(g[ti]))
                kand_meta.append({"t": int(ti), "richtig": ok})
            n_w += [float(x) for t, x in enumerate(g) if t not in kpos]
            if a.aus:
                tag = os.path.basename(os.path.dirname(pfad))
                speicher_runs[f"{tag}|{r['id']}"] = np.asarray(g, dtype=np.float16)
                zu_t = r["gen_ids"].index(248069) if 248069 in r["gen_ids"] else -1
                meta_runs.append({"lauf": f"{tag}/{r['id']}", "korrekt": bool(r["korrekt"]), "ende": r["ende"],
                                  "zu_token": zu_t, "tokens": len(gen), "kandidaten": kand_meta})
            n_l += 1
    r_w, f_w, n_w = np.array(r_w), np.array(f_w), np.array(n_w)
    schw = 0.5
    print(f"Gatter-Summe (Eingang down_proj, {len(G)} Neuronen) über {n_l} Läufe:")
    for name, x in (("richtige Kandidaten-Enden", r_w), ("falsche Kandidaten-Enden", f_w), ("gewöhnliche Tokens", n_w)):
        if len(x):
            print(f"   {name:26s} n={len(x):6d} | Median {np.median(x):8.3f} | 99%-Quantil {np.quantile(x, 0.99):8.3f} | "
                  f"Anteil > {schw}: {100 * float((x > schw).mean()):.2f} %")
    if meta:
        print("Patch:", {k: meta[k] for k in ("tau_C", "tau_T", "kappa_g", "kappa_u", "kappa_d", "schub") if k in meta})
    if a.aus:
        np.savez_compressed(a.aus + ".npz", **speicher_runs)
        json.dump(meta_runs, open(a.aus + ".json", "w", encoding="utf-8"), indent=0, ensure_ascii=False)
        print(f"Gatter-Aktivität gespeichert: {a.aus}.npz/.json ({len(meta_runs)} Läufe)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bauen")
    b.add_argument("--basis", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    b.add_argument("--vergleich", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    b.add_argument("--alpha", type=float, default=6.0)
    b.add_argument("--lern", required=True)
    b.add_argument("--richtung", default=os.path.join(ERG, "eigene_richtung-vL.npz"))
    b.add_argument("--achse", default=os.path.join(ERG, "richtung-entschluss.npz"))
    b.add_argument("--schub", type=float, default=1.0); b.add_argument("--z-ziel", type=float, default=3.0)
    b.add_argument("--aus", required=True)
    z = sub.add_parser("bauen_zig")
    z.add_argument("--basis", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B"))
    z.add_argument("--vergleich", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    z.add_argument("--alpha", type=float, default=6.0); z.add_argument("--lern", required=True)
    z.add_argument("--gradient", default=os.path.join(ERG, "abschluss_gradient.npz"))
    z.add_argument("--richtung", default=os.path.join(ERG, "eigene_richtung-vL.npz"))
    z.add_argument("--kappa", type=float, default=7.0); z.add_argument("--z-ziel", type=float, default=3.0)
    z.add_argument("--fehl-falsch", type=float, default=0.02); z.add_argument("--aus", required=True)
    qp = sub.add_parser("quantprobe")
    qp.add_argument("--sammlung", required=True); qp.add_argument("--lern", required=True)
    qp.add_argument("--z-ziel", type=float, default=3.0)
    p = sub.add_parser("pruefen")
    p.add_argument("--modell", required=True); p.add_argument("--lern", required=True)
    p.add_argument("--laeufe", nargs="+", required=True); p.add_argument("--max-laeufe", type=int, default=20)
    p.add_argument("--geraet", default="cuda"); p.add_argument("--aus", default="", help="Pfad ohne Endung: Gatter-Summe je Token speichern")
    s = sub.add_parser("sammeln")
    s.add_argument("--laeufe", nargs="+", required=True)
    s.add_argument("--modell", default=os.path.join(WURZEL, "modelle", "Qwen3.5-0.8B-eigen-vL"))
    s.add_argument("--geraet", default="cuda"); s.add_argument("--max-laeufe", type=int, default=0)
    s.add_argument("--normal-je-lauf", type=int, default=40); s.add_argument("--aus", required=True)
    le = sub.add_parser("lernen")
    le.add_argument("--sammlung", required=True); le.add_argument("--lam", type=float, default=50.0)
    le.add_argument("--richtung", default=os.path.join(ERG, "eigene_richtung-vL.npz"))
    le.add_argument("--k", type=int, default=16)
    le.add_argument("--fehl-normal", type=float, default=0.001); le.add_argument("--z-ziel", type=float, default=3.0)
    le.add_argument("--aus", required=True)
    a = ap.parse_args()
    {"sammeln": sammeln, "lernen": lernen, "bauen": bauen, "bauen_zig": bauen_zig, "pruefen": pruefen, "quantprobe": quantprobe}[a.cmd](a)


if __name__ == "__main__":
    main()
