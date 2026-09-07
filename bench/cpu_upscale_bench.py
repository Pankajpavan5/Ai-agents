#!/usr/bin/env python3
"""CPU resize baseline for the 10k-frame upscale task.

Measures pure *resize* throughput of Pillow's resampling filters so the two
agents have at least one measured number instead of estimates.

Deliberate scope limits (see bench/RESULTS.md):
  - resize only: no decode, no encode, no disk I/O
  - synthetic source frame (Pillow's resize cost is content-independent)
  - single process; the --jobs column is an arithmetic projection, not a run

Usage:  python3 bench/cpu_upscale_bench.py [--iters N] [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time

from PIL import Image

SRC_W, SRC_H = 1280, 720

FILTERS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}


def make_frame(w: int, h: int) -> Image.Image:
    """Deterministic test frame: gradient + edges + noise.

    Pillow's resampling cost does not depend on pixel values, so the content
    only matters for *visual* inspection of the output, not for timing.
    """
    import numpy as np

    y, x = np.mgrid[0:h, 0:w]
    r = ((x * 255) // max(w - 1, 1)).astype(np.uint8)
    g = ((y * 255) // max(h - 1, 1)).astype(np.uint8)
    b = ((x * 7 + y * 13) % 256).astype(np.uint8)
    return Image.fromarray(np.dstack([r, g, b]).astype(np.uint8), "RGB")


def bench_one(img: Image.Image, size: tuple[int, int], resample, iters: int):
    # warm-up (first call pays lazy-init cost)
    img.resize(size, resample)
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        img.resize(size, resample)
        samples.append(time.perf_counter() - t0)
    return samples


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=5)
    ap.add_argument("--out", default="bench/results/cpu_resize.json")
    ap.add_argument("--jobs", type=int, default=0, help="project for N workers (0 = auto)")
    args = ap.parse_args()

    import os

    nproc = args.jobs or os.cpu_count() or 1

    print(f"python={platform.python_version()} platform={platform.platform()}")
    print(f"cpu_count={nproc}  source={SRC_W}x{SRC_H}  iters={args.iters}\n")

    img = make_frame(SRC_W, SRC_H)
    rows = []
    header = f"{'filter':10} {'scale':6} {'target':12} {'median ms':>10} {'fps':>8} {'10k frames (1w)':>17} {'10k frames (Nw)':>17}"
    print(header)
    print("-" * len(header))

    for scale in (2, 4):
        target = (SRC_W * scale, SRC_H * scale)
        for name, resample in FILTERS.items():
            samples = bench_one(img, target, resample, args.iters)
            med = statistics.median(samples)
            fps = 1.0 / med
            serial = med * 10_000
            par = serial / max(nproc, 1)
            print(
                f"{name:10} {scale}x{'':4} {target[0]}x{target[1]:<7} "
                f"{med * 1000:>10.1f} {fps:>8.1f} "
                f"{serial / 60:>15.1f} m {par / 60:>15.1f} m"
            )
            rows.append(
                {
                    "filter": name,
                    "scale": scale,
                    "source": [SRC_W, SRC_H],
                    "target": list(target),
                    "median_s": round(med, 6),
                    "min_s": round(min(samples), 6),
                    "max_s": round(max(samples), 6),
                    "fps": round(fps, 2),
                    "eta_10000_serial_s": round(serial, 1),
                    "eta_10000_projected_s": round(par, 1),
                    "workers": nproc,
                }
            )
        print()

    payload = {
        "host": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": nproc,
        },
        "iters": args.iters,
        "rows": rows,
    }
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
