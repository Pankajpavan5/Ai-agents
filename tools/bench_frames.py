#!/usr/bin/env python3
"""100-frame benchmark harness — the step both agents agreed on.

Samples frames EVENLY across the whole sequence (not the first N — opening
frames are usually title cards and understate motion), upscales them, and
reports the numbers we agreed to exchange:

    wall clock, peak RSS, output bytes, PSNR and SSIM (round-trip)

Quality metric needs no eyeballs: the upscaled frame is downscaled back to the
source size and compared against the original. Round-trip fidelity is not a
perfect proxy for perceptual quality, but it is cheap and it is comparable
between two different machines.

Usage:
    python3 tools/bench_frames.py selftest
    python3 tools/bench_frames.py run <frames_dir> [--n 100] [--scale 2] [--filter lanczos]
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time

import numpy as np
from PIL import Image

FILTERS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}
IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")


def sample_evenly(paths, n: int):
    """Pick n frames spread evenly over the sequence, always including both ends."""
    total = len(paths)
    if total <= n:
        return list(paths)
    idx = [round(i * (total - 1) / (n - 1)) for i in range(n)]
    return [paths[i] for i in sorted(set(idx))]


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    if mse == 0.0:
        return float("inf")
    return float(10.0 * np.log10((255.0**2) / mse))


def block_ssim(a: np.ndarray, b: np.ndarray, win: int = 8) -> float:
    """Mean SSIM over non-overlapping win x win blocks, luminance only.

    Simplified (block-based, not the sliding-window reference implementation),
    but monotonic and comparable across runs, which is what we need here.
    """
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    h, w = a.shape
    h -= h % win
    w -= w % win
    a, b = a[:h, :w], b[:h, :w]
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2

    def blocks(x):
        return x.reshape(h // win, win, w // win, win).transpose(0, 2, 1, 3).reshape(-1, win * win)

    A, B = blocks(a), blocks(b)
    mu_a, mu_b = A.mean(1), B.mean(1)
    va = A.var(1)
    vb = B.var(1)
    cov = ((A - mu_a[:, None]) * (B - mu_b[:, None])).mean(1)
    num = (2 * mu_a * mu_b + c1) * (2 * cov + c2)
    den = (mu_a**2 + mu_b**2 + c1) * (va + vb + c2)
    return float(np.mean(num / den))


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


# ---------------------------------------------------------------------------


def selftest() -> int:
    rng = np.random.default_rng(0)
    img = (rng.random((64, 64)) * 255).astype(np.uint8)
    same = img.copy()
    noisy = np.clip(img.astype(np.int16) + 10, 0, 255).astype(np.uint8)

    p_same = psnr(img, same)
    s_same = block_ssim(img, same)
    p_noisy = psnr(img, noisy)
    s_noisy = block_ssim(img, noisy)

    # sampling must cover the ends and never exceed n
    paths = [f"f{i:04d}" for i in range(1000)]
    s100 = sample_evenly(paths, 100)
    s_all = sample_evenly(paths[:10], 100)

    checks = [
        ("psnr(identical) == inf", p_same == float("inf")),
        ("ssim(identical) == 1.0", abs(s_same - 1.0) < 1e-9),
        ("psnr(noisy) is finite", np.isfinite(p_noisy)),
        ("noisy psnr < identical psnr", p_noisy < p_same),
        ("noisy ssim < 1.0", s_noisy < 1.0),
        ("noisy ssim still high", s_noisy > 0.5),
        ("sample_evenly returns exactly n", len(s100) == 100),
        ("sample_evenly includes first frame", s100[0] == "f0000"),
        ("sample_evenly includes last frame", s100[-1] == "f0999"),
        ("sample_evenly returns all when n > total", s_all == paths[:10]),
    ]
    print(f"psnr identical={p_same}  noisy={p_noisy:.2f} dB")
    print(f"ssim identical={s_same:.6f}  noisy={s_noisy:.4f}\n")
    bad = 0
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        bad += 0 if ok else 1
    print(f"\nSELFTEST: {'PASS' if bad == 0 else f'FAIL ({bad} checks)'}")
    return 0 if bad == 0 else 1


def run(frames_dir: str, n: int, scale: int, filt: str) -> int:
    if filt not in FILTERS:
        print(f"unknown filter {filt!r}; choose from {sorted(FILTERS)}")
        return 1
    resample = FILTERS[filt]

    paths = sorted(
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith(IMG_EXTS)
    )
    if not paths:
        print(f"no image frames in {frames_dir}")
        return 1

    picked = sample_evenly(paths, n)
    out_dir = os.path.join("bench", "out")
    os.makedirs(out_dir, exist_ok=True)

    t0 = time.perf_counter()
    out_bytes = 0
    psnrs, ssims = [], []
    for i, p in enumerate(picked):
        src = Image.open(p).convert("RGB")
        up = src.resize((src.width * scale, src.height * scale), resample)
        # round-trip: back down to source size, compare with original
        back = up.resize(src.size, Image.Resampling.LANCZOS)
        a = np.asarray(src.convert("L"), dtype=np.uint8)
        b = np.asarray(back.convert("L"), dtype=np.uint8)
        psnrs.append(psnr(a, b))
        ssims.append(block_ssim(a, b))
        out_path = os.path.join(out_dir, f"{i:05d}.png")
        up.save(out_path)
        out_bytes += os.path.getsize(out_path)
    wall = time.perf_counter() - t0

    finite = [v for v in psnrs if np.isfinite(v)]
    report = {
        "frames_available": len(paths),
        "frames_sampled": len(picked),
        "scale": scale,
        "filter": filt,
        "wall_clock_s": round(wall, 3),
        "fps": round(len(picked) / wall, 2),
        "peak_rss_mb": round(peak_rss_mb(), 1),
        "output_bytes": out_bytes,
        "output_mb": round(out_bytes / 1e6, 1),
        "eta_10000_frames_min": round(wall / len(picked) * 10000 / 60, 1),
        "roundtrip_psnr_mean_db": round(float(np.mean(finite)), 2) if finite else None,
        "roundtrip_ssim_mean": round(float(np.mean(ssims)), 4),
    }
    print(json.dumps(report, indent=2))
    os.makedirs("bench/results", exist_ok=True)
    with open(f"bench/results/frames_{filt}_{scale}x.json", "w") as fh:
        json.dump(report, fh, indent=2)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["selftest", "run"])
    ap.add_argument("frames_dir", nargs="?")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--filter", default="lanczos")
    a = ap.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    if not a.frames_dir:
        ap.error("run needs a frames directory")
    sys.exit(run(a.frames_dir, a.n, a.scale, a.filter))
