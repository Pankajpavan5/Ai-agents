#!/usr/bin/env python3
"""Cel-dedupe prototype: upscale only the UNIQUE frames in a sequence.

Proposal made in AGENT_COMMUNICATION.md: 2D limited animation repeats the same
drawing across many frames, so upscaling all 10,000 frames wastes most of the
work. This measures how much is actually wasted and proves the mapping back to
the full frame count is lossless.

It ships with a self-test that builds a synthetic limited-animation sequence
with a known number of unique cels, so the dedupe ratio is checkable rather
than assumed.

Usage:
    python3 tools/cel_dedupe.py selftest            # verify logic on synthetic data
    python3 tools/cel_dedupe.py scan  <frames_dir>  # report unique ratio on real frames
"""

from __future__ import annotations

import hashlib
import os
import sys
from collections import OrderedDict

# Tolerance for "same cel": average absolute difference per channel, 0-255.
# 0 = byte-identical only. Anti-aliased/grainy sources need > 0.
SIMILARITY_THRESHOLD = 2.0


def phash_signature(path_or_img, hash_size: int = 16) -> bytes:
    """Coarse perceptual signature: mean-subtracted 16x16 grayscale, binarised.

    Cheap and good at saying "same drawing, maybe slight encode noise".
    """
    from PIL import Image

    img = Image.open(path_or_img) if isinstance(path_or_img, str) else path_or_img
    g = img.convert("L").resize((hash_size, hash_size), Image.Resampling.BILINEAR)
    import numpy as np

    px = np.asarray(g, dtype=np.float32)
    mean = px.mean()
    bits = np.packbits((px > mean).flatten()).tobytes()
    return hashlib.sha1(bits).digest()


def exact_signature(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def group_frames(paths, use_phash: bool = True):
    """Return OrderedDict: representative_path -> [all frame paths in that group].

    Frames are grouped by signature; the FIRST frame seen in each group becomes
    the representative (and the dict key) — that is the only frame per group
    that actually gets upscaled. Keys are unique because each path appears in
    exactly one group.
    """
    by_sig: "OrderedDict[str, list]" = OrderedDict()
    for p in paths:
        sig = phash_signature(p).hex() if use_phash else exact_signature(p)
        by_sig.setdefault(sig, []).append(p)
    return OrderedDict((members[0], members) for members in by_sig.values())


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------


def _make_cel(idx: int, size=(320, 180)):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", size, (20 + idx * 11 % 200, 30, 40 + idx * 7 % 150))
    d = ImageDraw.Draw(img)
    d.rectangle([20 + idx * 5, 20, 120 + idx * 5, 120], fill=(240, 240, 240))
    d.ellipse([40 + idx * 3, 40, 90 + idx * 3, 90], fill=(10, 10, 10))
    return img


def selftest() -> int:
    import tempfile

    import numpy as np
    from PIL import Image

    # 6 distinct cels, each held for a different number of frames = 100 frames.
    holds = [22, 9, 17, 4, 30, 18]
    n_cels = len(holds)
    total = sum(holds)

    with tempfile.TemporaryDirectory() as td:
        paths = []
        n = 0
        for cel_idx, hold in enumerate(holds):
            cel = _make_cel(cel_idx)
            for _ in range(hold):
                p = os.path.join(td, f"{n:05d}.png")
                cel.save(p)
                paths.append(p)
                n += 1

        # sanity: the synthetic sequence is what we think it is
        assert len(paths) == total == 100, (len(paths), total)

        groups = group_frames(paths, use_phash=True)
        unique = len(groups)
        saved = total - unique

        # exact-hash baseline for comparison
        exact_groups = group_frames(paths, use_phash=False)

        # --- the mapping must be lossless: every frame maps back to a rep ---
        reconstructed = []
        for rep, members in groups.items():
            reconstructed.extend(members)
        assert sorted(reconstructed) == sorted(paths), "mapping lost or duplicated frames"

        # --- the rep chosen for each group must be visually identical to its members ---
        mismatches = 0
        for rep, members in groups.items():
            rep_arr = np.asarray(Image.open(rep).convert("L"), dtype=np.int16)
            for m in members:
                m_arr = np.asarray(Image.open(m).convert("L"), dtype=np.int16)
                mad = float(np.abs(rep_arr - m_arr).mean())
                if mad > SIMILARITY_THRESHOLD:
                    mismatches += 1

        print(f"frames total        : {total}")
        print(f"unique (phash)      : {unique}")
        print(f"unique (sha256)     : {len(exact_groups)}")
        print(f"upscales skipped    : {saved}  ({100 * saved / total:.1f}%)")
        print(f"work multiplier     : {total / unique:.2f}x cheaper")
        print(f"round-trip lossless : {sorted(reconstructed) == sorted(paths)}")
        print(f"rep/member mismatches > {SIMILARITY_THRESHOLD}: {mismatches}")

        ok = unique == n_cels and mismatches == 0
        print(f"\nSELFTEST: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1


def scan(frames_dir: str) -> int:
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
    paths = sorted(
        os.path.join(frames_dir, f)
        for f in os.listdir(frames_dir)
        if f.lower().endswith(exts)
    )
    if not paths:
        print(f"no image frames found in {frames_dir}")
        return 1
    groups = group_frames(paths, use_phash=True)
    unique, total = len(groups), len(paths)
    print(f"frames: {total}   unique cels: {unique}   skipped: {total - unique}"
          f"   ({100 * (total - unique) / total:.1f}% saving)")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if cmd == "selftest":
        sys.exit(selftest())
    if cmd == "scan":
        sys.exit(scan(sys.argv[2]))
    print(__doc__)
    sys.exit(1)
