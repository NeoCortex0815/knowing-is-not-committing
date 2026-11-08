"""WSP-Werkzeugkasten: safetensors lesen/patchen ohne torch, bf16-Helfer, Rang-1-Edits.

Skaliert auf große Modelle: Tensoren werden per memmap gelesen, beim Patchen werden nur die
Shards kopiert, die einen geänderten Tensor enthalten (alle anderen Dateien werden verlinkt).

bf16-Rundung und safetensors-Format wie in st_numpy.py aus RikiyaT/lm_understand-logs (MIT-Lizenz).
"""
import glob
import hashlib
import json
import os
import re
import shutil
import struct

import numpy as np

DT = {"BF16": np.uint16, "F16": np.float16, "F32": np.float32, "F64": np.float64, "I64": np.int64,
      "I32": np.int32, "I16": np.int16, "I8": np.int8, "U8": np.uint8, "BOOL": np.bool_}


# ---------------------------------------------------------------- safetensors

def header(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n)), 8 + n


def tensor_index(model_dir):
    """{tensor_name: shard_dateiname} aus model.safetensors.index.json oder durch Scannen der Shards."""
    idx = os.path.join(model_dir, "model.safetensors.index.json")
    if os.path.exists(idx):
        return dict(json.load(open(idx))["weight_map"])
    out = {}
    for p in sorted(glob.glob(os.path.join(model_dir, "*.safetensors"))):
        h, _ = header(p)
        for k in h:
            if k != "__metadata__":
                out[k] = os.path.basename(p)
    return out


def tensor_lesen(model_dir, name, index=None):
    """(dtype, read-only memmap). BF16 kommt als uint16-Bitmuster."""
    index = index or tensor_index(model_dir)
    path = os.path.join(model_dir, index[name])
    h, off = header(path)
    info = h[name]
    a, b = info["data_offsets"]
    dt = DT[info["dtype"]]
    arr = np.memmap(path, mode="r", dtype=dt, offset=off + a, shape=tuple(info["shape"]))
    assert arr.nbytes == b - a
    return info["dtype"], arr


def tensor_f32(model_dir, name, index=None):
    dt, arr = tensor_lesen(model_dir, name, index)
    if dt == "BF16":
        return bf16_to_f32(np.asarray(arr))
    return np.asarray(arr, dtype=np.float32)


def sha256(arr):
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()


# ---------------------------------------------------------------- bf16

def bf16_bits(x32):
    """float32 -> bfloat16-Bitmuster, round-to-nearest-even (wie torch .to(bfloat16) für endliche Werte)."""
    u = np.ascontiguousarray(x32, dtype=np.float32).view(np.uint32).astype(np.uint64)
    u = u + 0x7FFF + ((u >> 16) & 1)
    return (u >> 16).astype(np.uint16)


def bf16_to_f32(bits):
    return (np.asarray(bits).astype(np.uint32) << 16).view(np.float32)


# ---------------------------------------------------------------- Patch schreiben

def modell_mit_patch(src_dir, dst_dir, patches, meta=None):
    """Legt dst_dir als Kopie von src_dir an, in der die Tensoren aus `patches` ersetzt sind.

    patches: {tensor_name: numpy-Array im Original-Dtype (BF16 als uint16-Bits), gleiche Form}.
    Unveränderte Dateien werden symbolisch verlinkt, betroffene Shards kopiert und an Ort und
    Stelle überschrieben (Header und Offsets bleiben identisch).
    """
    src_dir, dst_dir = os.path.abspath(src_dir), os.path.abspath(dst_dir)
    if os.path.exists(dst_dir):
        raise SystemExit(f"Zielordner existiert schon: {dst_dir} (bitte löschen oder anderen Namen wählen)")
    os.makedirs(dst_dir)
    index = tensor_index(src_dir)
    betroffen = {}
    for name in patches:
        if name not in index:
            raise KeyError(f"Tensor nicht im Modell: {name}")
        betroffen.setdefault(index[name], []).append(name)
    for fn in sorted(os.listdir(src_dir)):
        if fn.startswith("."):
            continue
        s, d = os.path.join(src_dir, fn), os.path.join(dst_dir, fn)
        if fn in betroffen:
            shutil.copyfile(s, d)
        else:
            try:
                os.symlink(s, d)
            except OSError:  # Windows ohne Symlink-Recht: Hardlink (gleiche Platte), sonst Kopie
                try:
                    os.link(s, d)
                except OSError:
                    shutil.copyfile(s, d)
    for shard, names in betroffen.items():
        path = os.path.join(dst_dir, shard)
        h, off = header(path)
        with open(path, "r+b") as f:
            for name in names:
                info = h[name]
                neu = np.ascontiguousarray(patches[name])
                assert neu.dtype == DT[info["dtype"]], (name, neu.dtype, info["dtype"])
                assert list(neu.shape) == info["shape"], (name, neu.shape, info["shape"])
                a, b = info["data_offsets"]
                assert neu.nbytes == b - a
                f.seek(off + a)
                f.write(neu.tobytes())
    info = {"basis": src_dir, "geaendert": {n: sha256(a) for n, a in patches.items()}}
    if meta:
        info.update(meta)
    ziel = os.path.join(dst_dir, "wsp_patch.json")
    if os.path.lexists(ziel):  # 07.11.: aus der Basis verlinkte wsp_patch.json (Hardlink!) nicht durchschreiben – nur den Link im Ziel lösen
        os.remove(ziel)
    with open(ziel, "w") as f:
        json.dump(info, f, indent=1)
    return dst_dir


# ---------------------------------------------------------------- Rang-1-Edits

def rang1_edit(W0, u, spalten, alpha):
    """W = W0 - alpha * outer(u, maske * (u @ W0))  (Formel des MIT-Edits p50c, alpha=6).

    W0: [d_model, d_ff] float32 (down_proj-Gewicht), u: Einheitsvektor im Residual Stream,
    spalten: Neuron-Indizes, die geändert werden. alpha=1 projiziert u exakt heraus, alpha>1
    kehrt die Komponente um.
    """
    W0 = np.asarray(W0, dtype=np.float64)
    u = np.asarray(u, dtype=np.float64)
    u = u / np.linalg.norm(u)
    spalten = np.asarray(spalten, dtype=np.int64)
    W = W0.copy()
    p = u @ W0[:, spalten]
    W[:, spalten] = W0[:, spalten] - alpha * np.outer(u, p)
    return W.astype(np.float32)


def richtung_aus_diff(W0, W1):
    """Rekonstruiert u, Spalten und alpha aus einem Rang-1-Edit W1 = W0 - alpha*u*(u^T W0)[spalten]."""
    D = np.asarray(W1, dtype=np.float64) - np.asarray(W0, dtype=np.float64)
    spalten = np.where(np.any(D != 0, axis=0))[0]
    Ds = D[:, spalten]
    U, S, _ = np.linalg.svd(Ds, full_matrices=False)
    u = U[:, 0]
    rang1_anteil = float(S[0] ** 2 / np.sum(S ** 2))
    b = Ds.T @ u
    p = u @ np.asarray(W0, dtype=np.float64)[:, spalten]
    alpha = float(-(b @ p) / (p @ p))
    return u, spalten, alpha, rang1_anteil


def schicht_aus_name(name):
    m = re.search(r"layers\.(\d+)\.", name)
    return int(m.group(1)) if m else None


def tensorname(muster, schicht):
    return muster.format(L=schicht)
