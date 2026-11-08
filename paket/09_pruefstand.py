"""Schnell-Prüfstand: viele Kandidaten-Edits (Schichten x Stärke alpha x Anzahl Neuronen) in EINEM schichtweisen
Durchlauf per Teacher-Forcing bewerten – Sekunden/Minuten statt Stunden-Messung je Kandidat.

  python 09_pruefstand.py --modell MODELLE/Qwen3.5-0.8B --ergebnisse diagnose/ergebnisse.jsonl --nur-zurueckgehalten 4 \
      --richtung ergebnisse/eigene_richtung.npz --schicht-sets "15,19;14,19;10,14" --alphas 2,4,6,8 --top-ks 32,64,128 \
      --zufall --referenz mit=ergebnisse/mit_richtung.npz:15,19:6 --geraet cuda --aus ergebnisse/pruefstand.json

Was gemessen wird (auf Transkripten, die die Richtungssuche NICHT gesehen hat: 04s --halte-zurueck N / hier
--nur-zurueckgehalten N):
  Klasse A (Schleifen- bzw. Fehler-Tokens): Delta log p des tatsächlich folgenden Tokens  -> soll stark sinken
  Klasse B (produktiv bzw. korrekt):        KL(Basis || Kandidat) und Delta log p         -> soll ~0 bleiben
  --zufall: je Kandidat eine Zufallsrichtung (orthogonal zu u, gleiche Neuronen) mit GLEICHER Gewichtsänderung
            -> "netto" = Wirkung(eigen) - Wirkung(zufall): was die Richtung leistet, nicht bloß die Störung.
Rangfolge: Wirkung auf A (netto, wenn --zufall) unter der Nebenbedingung KL_B <= --max-kl.

Ablauf: alle Kandidaten teilen sich die Rechnung bis zu ihrer ersten Edit-Schicht; ab dort eigener Strang.
Jede Schicht wird nur EINMAL geladen (35B-tauglich). Edits werden im Speicher angewendet und exakt zurückgesetzt.
Dicht (down_proj) und MoE (experts.down_proj + shared_expert.down_proj) wie 05_patch.py / 05m_patch_moe.py.
"""
import argparse
import importlib
import json
import os
import sys
import time

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
S = importlib.import_module("04s_richtung_schichtweise")


# ------------------------------------------------------------------ Kandidaten

def _auswahl(R, L, top_k, top_k_shared):
    """Neuronen-Auswahl je Schicht aus einer Richtungsdatei: dicht -> spalten; MoE -> paare + shared."""
    if f"exp_spalten_{L}" in R or f"exp_score_{L}" in R:
        if top_k and f"exp_score_{L}" in R:
            sc = R[f"exp_score_{L}"]
            fl = np.argsort(-sc.ravel())[:top_k]
            paare = np.stack(np.unravel_index(fl, sc.shape), 1)
        else:
            paare = R[f"exp_spalten_{L}"]
        ks = top_k_shared if top_k_shared is not None else top_k
        if ks and f"shared_score_{L}" in R:
            shared = np.sort(np.argsort(-R[f"shared_score_{L}"])[:ks])
        else:
            shared = R.get(f"shared_spalten_{L}", np.zeros(0, np.int64))
        return {"typ": "moe", "paare": np.asarray(paare, np.int64), "shared": np.asarray(shared, np.int64)}
    if top_k and f"score_{L}" in R:
        sp = np.sort(np.argsort(-R[f"score_{L}"])[:top_k])
    elif f"spalten_{L}" in R:
        sp = R[f"spalten_{L}"]
    else:
        raise SystemExit(f"Schicht {L}: weder score_{L} noch spalten_{L} in der Richtungsdatei "
                         f"(04s mit --edit-schichten, die diese Schicht enthalten, laufen lassen)")
    return {"typ": "dicht", "spalten": np.asarray(sp, np.int64)}


def _zufall_u(u, seed):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(u.shape)
    z -= (z @ u) * u
    return z / np.linalg.norm(z)


def baue_kandidaten(a):
    K = []
    if a.richtung:
        R = dict(np.load(a.richtung))
        sets = ([[int(x) for x in s.split(",")] for s in a.schicht_sets.split(";")] if a.schicht_sets else
                [sorted({int(k.split("_")[-1]) for k in R if k.startswith(("score_", "spalten_", "exp_score_"))})])
        alphas = [float(x) for x in a.alphas.split(",")]
        tks = [int(x) for x in a.top_ks.split(",")]
        for sset in sets:
            for tk in tks:
                for al in alphas:
                    edits = {}
                    for L in sset:
                        u = R[f"u_{L}"].astype(np.float64)
                        u /= np.linalg.norm(u)
                        edits[L] = dict(_auswahl(R, L, tk, a.top_k_shared), u=u, alpha=al)
                    name = f"eigen L{','.join(map(str, sset))} k{tk or 'datei'} a{al:g}"
                    K.append({"name": name, "art": "eigen", "edits": edits})
                    if a.zufall:
                        ze = {L: dict(e, u=_zufall_u(e["u"], 1000 * L + int(10 * al) + tk), u_ref=e["u"])
                              for L, e in edits.items()}
                        K.append({"name": name.replace("eigen", "zufall"), "art": "zufall", "edits": ze,
                                  "partner": name})
    for ref in a.referenz or []:
        nm, rest = ref.split("=", 1)
        pfad, sch, al = rest.rsplit(":", 2)
        R = dict(np.load(pfad))
        edits = {}
        for L in [int(x) for x in sch.split(",")]:
            u = R[f"u_{L}"].astype(np.float64)
            u /= np.linalg.norm(u)
            edits[L] = dict(_auswahl(R, L, 0, 0), u=u, alpha=float(al))
        name = f"{nm} L{sch} a{float(al):g}"
        K.append({"name": name, "art": "referenz", "edits": edits})
        if a.zufall:
            ze = {L: dict(e, u=_zufall_u(e["u"], 7000 + L), u_ref=e["u"]) for L, e in edits.items()}
            K.append({"name": name.replace(nm, nm + "-zufall"), "art": "zufall", "edits": ze, "partner": name})
    if not K:
        raise SystemExit("keine Kandidaten (--richtung und/oder --referenz angeben)")
    return K


# ------------------------------------------------------------------ Edit im Speicher anwenden / zurücksetzen

def wende_an(layer, e):
    """Wendet den Rang-1-Edit auf die geladene Schicht an. Gibt (zuruecksetzen(), rel_aenderung) zurück.
    Zufall mit u_ref: alpha so skaliert, dass die Gewichtsänderung so groß ist wie mit der echten Richtung."""
    import torch
    dev = next(layer.parameters()).device
    u = torch.tensor(e["u"], dtype=torch.float32, device=dev)
    u_ref = torch.tensor(e["u_ref"], dtype=torch.float32, device=dev) if "u_ref" in e else None
    ziele = []  # (tensor, index-tupel, spalten-als-zeilen?)
    if e["typ"] == "dicht":
        Wt = layer.mlp.down_proj.weight.data
        ziele.append((Wt, (slice(None), torch.tensor(e["spalten"], device=dev)), False))
    else:
        D = layer.mlp.experts.down_proj.data                    # [E, H, I]
        p = torch.tensor(e["paare"], device=dev)
        if len(p):
            ziele.append((D, (p[:, 0], slice(None), p[:, 1]), True))   # -> [n, H]
        if len(e["shared"]):
            Ws = layer.mlp.shared_expert.down_proj.weight.data
            ziele.append((Ws, (slice(None), torch.tensor(e["shared"], device=dev)), False))
    orig = [(T, idx, T[idx].clone()) for T, idx, _ in ziele]
    spalten = [(o.float() if zeilen else o.float().T) for (_, _, o), (_, _, zeilen) in zip(orig, ziele)]  # [n, H]
    alpha = e["alpha"]
    if u_ref is not None:
        n_ref = sum(float((c @ u_ref).pow(2).sum()) for c in spalten) ** 0.5
        n_z = sum(float((c @ u).pow(2).sum()) for c in spalten) ** 0.5
        alpha = alpha * n_ref / max(n_z, 1e-12)
    d2, w2 = 0.0, 0.0
    for (T, idx, o), c, (_, _, zeilen) in zip(orig, spalten, ziele):
        neu = c - alpha * (c @ u)[:, None] * u[None, :]
        d2 += float((neu - c).pow(2).sum())
        T[idx] = (neu if zeilen else neu.T).to(T.dtype)
    for T, _, _ in ziele:
        w2 += float(T.float().pow(2).sum())

    def zurueck():
        for T, idx, o in orig:
            T[idx] = o
    return zurueck, (d2 ** 0.5) / max(w2 ** 0.5, 1e-12), alpha


# ------------------------------------------------------------------ Hauptprogramm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modell", required=True)
    ap.add_argument("--ergebnisse", required=True)
    ap.add_argument("--nur-zurueckgehalten", type=int, default=0,
                    help="N: nur Transkripte mit Index %% N == 0 (die 04s --halte-zurueck N nicht gesehen hat)")
    ap.add_argument("--kontrast", action="store_true")
    ap.add_argument("--richtung")
    ap.add_argument("--schicht-sets", default="", help='z. B. "15,19;14,19" (leer: Edit-Schichten der Datei)')
    ap.add_argument("--alphas", default="2,4,6")
    ap.add_argument("--top-ks", default="64", help="0 = Neuronen aus der Datei (spalten_L / exp_spalten_L)")
    ap.add_argument("--top-k-shared", type=int, default=None, help="MoE: Shared-Neuronen (Standard = top-k)")
    ap.add_argument("--referenz", action="append", help="name=pfad.npz:schichten:alpha (feste Spalten, z. B. MIT)")
    ap.add_argument("--zufall", action="store_true")
    ap.add_argument("--max-len", type=int, default=4096)
    ap.add_argument("--pos-je-text", type=int, default=200)
    ap.add_argument("--min-lauf", type=int, default=32)
    ap.add_argument("--max-texte", type=int, default=64)
    ap.add_argument("--eintritt", type=int, default=32, help="Schleifen-Modus: Tokens ab Schleifenbeginn (Klasse E)")
    ap.add_argument("--max-kl", type=float, default=0.05, help="Nebenwirkungs-Grenze (KL auf Klasse B, nats)")
    ap.add_argument("--geraet", default="cpu")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=256)
    ap.add_argument("--rohdaten", help=".npz mit Positionen und log p je Strang (für Tests)")
    ap.add_argument("--aus", required=True)
    a = ap.parse_args()

    import torch
    if a.threads:
        torch.set_num_threads(a.threads)
    dev = torch.device(a.geraet)
    t0 = time.time()
    K = baue_kandidaten(a)
    model, tpfad, tm, dt = S.geruest(a.modell, "bf16", False)
    praefix, layers = tpfad + ".", tm.layers
    nL = len(layers)
    texte = [json.loads(z) for z in open(a.ergebnisse, encoding="utf-8")]
    jobs = S.positionen(texte, a, np.random.default_rng(a.seed))
    if not jobs:
        raise SystemExit("keine verwertbaren Transkripte")
    for j in jobs:  # Ziel-Token muss existieren: Position p sagt ids[p+1] voraus
        n = len(j["ids"])
        j["ir"] = [p for p in j["ir"] if p + 1 < n]
        j["ip"] = [p for p in j["ip"] if p + 1 < n]
        # Schleifen-EINTRITT: die ersten --eintritt Tokens der ersten Schleife (dort fällt die Entscheidung)
        if a.kontrast:   # Kontrast: Eintritts-Positionen aus klasse_e (z. B. Wechsel Deutsch -> Englisch)
            j["ie"] = [p for p in j.get("ke", []) if p + 1 < n]
        else:
            j["ie"] = ([j["P"] + j["onset"] - 1 + t for t in range(a.eintritt) if j["P"] + j["onset"] + t < n]
                       if j["onset"] < j["n_gen"] else [])
        j["ids"] = j["ids"][:max(j["ir"] + j["ip"] + j["ie"]) + 2]
    tok = sum(len(j["ids"]) for j in jobs)
    erste = [min(k["edits"]) for k in K]
    print(f"{len(K)} Kandidaten, {len(jobs)} Transkripte, {tok} Tokens, A {sum(len(j['ir']) for j in jobs)} / "
          f"B {sum(len(j['ip']) for j in jobs)} Positionen, Gerät {dev}", flush=True)

    lader = S.Lader(a.modell)
    with torch.no_grad():
        if type(tm.embed_tokens) is torch.nn.Embedding:   # nur benötigte Zeilen (spart RAM)
            Hb = [lader.zeilen(praefix + "embed_tokens.weight", j["ids"]).to(dt)[None] for j in jobs]
        else:
            lader.lade(tm.embed_tokens, praefix + "embed_tokens.", dt)
            Hb = [tm.embed_tokens(torch.tensor([j["ids"]])) for j in jobs]
            tm.embed_tokens.to("meta")
    tm.rotary_emb.to(dev)
    Hk = [None] * len(K)
    rel = {i: {} for i in range(len(K))}

    for L in range(nL):
        tL = time.time()
        layer = layers[L]
        lader.lade(layer, f"{praefix}layers.{L}.", dt, dev)
        layer.to(dev)
        with torch.no_grad():
            for i in range(len(K)):
                if erste[i] == L:
                    Hk[i] = list(Hb)          # Strang zweigt hier ab (Tensoren werden ersetzt, nie verändert)
            for k in range(len(jobs)):
                Hb[k] = S.schicht_vorwaerts(layer, Hb[k].to(dev), tm, L).to("cpu")
            for i, c in enumerate(K):
                if Hk[i] is None:
                    continue
                zurueck = None
                if L in c["edits"]:
                    zurueck, r_, al = wende_an(layer, c["edits"][L])
                    rel[i][L] = {"rel_aenderung": round(r_, 6), "alpha_eff": round(al, 4)}
                for k in range(len(jobs)):
                    Hk[i][k] = S.schicht_vorwaerts(layer, Hk[i][k].to(dev), tm, L).to("cpu")
                if zurueck:
                    zurueck()
        layer.to("meta")
        if dev.type == "cuda":
            torch.cuda.empty_cache()
        aktiv = sum(h is not None for h in Hk)
        print(f"Schicht {L}/{nL - 1}: {aktiv} Stränge aktiv ({time.time() - tL:.1f} s, gesamt {time.time() - t0:.0f} s)",
              flush=True)

    # Endnorm + LM-Kopf nur an den Messpositionen
    lader.lade(tm.norm, praefix + "norm.", dt, dev)
    tm.norm.to(dev)
    kopf = "lm_head.weight" if "lm_head.weight" in lader.index else praefix + "embed_tokens.weight"
    Wk = (lader.tensor_mmap(kopf) if dev.type == "cuda" else lader.tensor(kopf)).to(dev, torch.bfloat16)
    posA = [torch.tensor(j["ir"], dtype=torch.long) for j in jobs]
    posE = [torch.tensor(j["ie"], dtype=torch.long) for j in jobs]
    zielE = torch.cat([torch.tensor(j["ids"])[torch.tensor(j["ie"], dtype=torch.long) + 1] for j in jobs])
    posB = [torch.tensor(j["ip"], dtype=torch.long) for j in jobs]
    zielA = torch.cat([torch.tensor(j["ids"])[torch.tensor(j["ir"], dtype=torch.long) + 1] for j in jobs]) if posA else None
    zielB = torch.cat([torch.tensor(j["ids"])[torch.tensor(j["ip"], dtype=torch.long) + 1] for j in jobs])

    def sammle(H, pos):
        return torch.cat([H[k][0, pos[k]] for k in range(len(jobs))])

    with torch.no_grad():
        hA_b, hB_b, hE_b = sammle(Hb, posA), sammle(Hb, posB), sammle(Hb, posE)
        hA = [sammle(H, posA) for H in Hk]
        hE = [sammle(H, posE) for H in Hk]
        hB = [sammle(H, posB) for H in Hk]
        del Hk, Hb

        def lsm(h):
            return torch.log_softmax((tm.norm(h.to(dev)) @ Wk.T).float(), dim=-1)

        def logp_ziel(h, ziel):
            out = []
            for s in range(0, len(h), a.chunk):
                out.append(lsm(h[s:s + a.chunk]).gather(1, ziel[s:s + a.chunk, None].to(dev))[:, 0].cpu())
            return torch.cat(out) if out else torch.zeros(0)

        lpA_b, lpB_b = logp_ziel(hA_b, zielA), logp_ziel(hB_b, zielB)
        lpA = [logp_ziel(h, zielA) for h in hA]
        lpE_b = logp_ziel(hE_b, zielE)
        lpE = [logp_ziel(h, zielE) for h in hE]
        lpB = [logp_ziel(h, zielB) for h in hB]
        kl = [0.0] * len(K)
        for s in range(0, len(hB_b), a.chunk):
            base = lsm(hB_b[s:s + a.chunk])
            pb = base.exp()
            for i in range(len(K)):
                kl[i] += float((pb * (base - lsm(hB[i][s:s + a.chunk]))).sum())
        kl = [x / max(len(hB_b), 1) for x in kl]

    erg = []
    for i, c in enumerate(K):
        dA = float((lpA[i] - lpA_b).mean())
        erg.append({"name": c["name"], "art": c["art"], "partner": c.get("partner"),
                    "delta_logp_A": round(dA, 4), "p_A_basis": round(float(lpA_b.exp().mean()), 4),
                    "p_A_kandidat": round(float(lpA[i].exp().mean()), 4),
                    "anteil_A_gesenkt": round(float((lpA[i] < lpA_b).float().mean()), 3),
                    "delta_logp_B": round(float((lpB[i] - lpB_b).mean()), 4), "kl_B": round(kl[i], 5),
                    "delta_logp_E": round(float((lpE[i] - lpE_b).mean()), 4) if len(lpE_b) else None,
                    "p_E_kandidat": round(float(lpE[i].exp().mean()), 4) if len(lpE_b) else None,
                    "schichten": {str(L): v for L, v in rel[i].items()}})
    nach_name = {e["name"]: e for e in erg}
    for e in erg:
        if e["art"] != "zufall":
            z = next((x for x in erg if x.get("partner") == e["name"]), None)
            if z:
                e["netto_delta_logp_A"] = round(e["delta_logp_A"] - z["delta_logp_A"], 4)
                if e["delta_logp_E"] is not None:
                    e["netto_delta_logp_E"] = round(e["delta_logp_E"] - z["delta_logp_E"], 4)
                e["zufall_kl_B"] = z["kl_B"]
    def schluessel(e):
        return e.get("netto_delta_logp_A", e["delta_logp_A"])
    gueltig = sorted([e for e in erg if e["art"] != "zufall" and e["kl_B"] <= a.max_kl], key=schluessel)
    zu_stark = sorted([e for e in erg if e["art"] != "zufall" and e["kl_B"] > a.max_kl], key=schluessel)
    bericht = {"modell": a.modell, "transkripte": len(jobs), "tokens": tok,
               "positionen": {"A": int(len(lpA_b)), "B": int(len(lpB_b)), "E": int(len(lpE_b))}, "max_kl": a.max_kl,
               "p_A_basis": round(float(lpA_b.exp().mean()), 4),
               "p_E_basis": round(float(lpE_b.exp().mean()), 4) if len(lpE_b) else None, "laufzeit_s": round(time.time() - t0, 1),
               "rangfolge": [e["name"] for e in gueltig], "ueber_kl_grenze": [e["name"] for e in zu_stark],
               "kandidaten": erg}
    os.makedirs(os.path.dirname(os.path.abspath(a.aus)), exist_ok=True)
    json.dump(bericht, open(a.aus, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if a.rohdaten:
        np.savez(a.rohdaten, lpA_b=lpA_b.numpy(), lpB_b=lpB_b.numpy(),
                 **{f"lpA_{i}": lpA[i].numpy() for i in range(len(K))},
                 **{f"lpB_{i}": lpB[i].numpy() for i in range(len(K))},
                 namen=np.array([c["name"] for c in K]),
                 posA=np.array(json.dumps([j["ir"] for j in jobs])), posB=np.array(json.dumps([j["ip"] for j in jobs])))

    print(f"\nBasis: p(nächstes Token) A = {bericht['p_A_basis']}, E = {bericht['p_E_basis']}   "
          f"(A = Schleife/Fehler, E = Schleifen-Eintritt, B = produktiv/korrekt)")
    print(f"{'Kandidat':34s} {'ΔlogpA':>8s} {'nettoA':>8s} {'ΔlogpE':>8s} {'nettoE':>8s} {'KL_B':>8s}  rel.Änd.")
    for e in gueltig + zu_stark + [x for x in erg if x["art"] == "zufall"]:
        ra = ",".join(f"{v['rel_aenderung']:.3f}" for v in e["schichten"].values())
        mark = "  > KL-Grenze" if e in zu_stark else ""
        nan = float("nan")
        dE = e["delta_logp_E"] if e["delta_logp_E"] is not None else nan
        print(f"{e['name']:34s} {e['delta_logp_A']:8.3f} {e.get('netto_delta_logp_A', nan):8.3f} "
              f"{dE:8.3f} {e.get('netto_delta_logp_E', nan):8.3f} {e['kl_B']:8.4f}  {ra}{mark}")
    print(f"\nlaufzeit {bericht['laufzeit_s']} s -> {a.aus}")


if __name__ == "__main__":
    main()
