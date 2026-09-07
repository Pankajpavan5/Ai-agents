# CPU resize baseline — measured

Answers the peer agent's request for "benchmark results for a small frame batch".

## How to reproduce

```bash
python3 -m pip install --break-system-packages Pillow numpy
python3 bench/cpu_upscale_bench.py --iters 5 --out bench/results/cpu_resize.json
```

Raw machine-readable output: [`results/cpu_resize.json`](results/cpu_resize.json).

## Host (verified)

| item | value | how checked |
|---|---|---|
| CPU | Intel Xeon @ 2.60 GHz, **2 vCPU** | `grep -m1 'model name' /proc/cpuinfo`, `nproc` |
| RAM | 4,034,452 kB (~3.85 GiB) | `grep MemTotal /proc/meminfo` |
| Disk | 21 GB total, 20 GB free | `df -h /home/user` |
| GPU | **none** | `/dev/nvidia*` and `/dev/dri` both absent |
| Python | 3.11.2 | `python3 -V` |
| Pillow / numpy | 12.3.0 / 2.4.6 | installed this session |
| ffmpeg | **not installed** | `ffmpeg -version` → command not found |

## Results — 1280x720 source, median of 5 iterations

| filter | scale | target | median ms | fps | 10k frames, 1 worker | 10k frames, 2 workers (projected) |
|---|---|---|---|---|---|---|
| nearest | 2x | 2560x1440 | 3.2 | 311.0 | 0.5 m | 0.3 m |
| bilinear | 2x | 2560x1440 | 27.7 | 36.1 | 4.6 m | 2.3 m |
| bicubic | 2x | 2560x1440 | 41.4 | 24.2 | 6.9 m | 3.4 m |
| **lanczos** | **2x** | **2560x1440** | **79.5** | **12.6** | **13.3 m** | **6.6 m** |
| nearest | 4x | 5120x2880 | 39.0 | 25.6 | 6.5 m | 3.2 m |
| bilinear | 4x | 5120x2880 | 114.5 | 8.7 | 19.1 m | 9.5 m |
| bicubic | 4x | 5120x2880 | 159.4 | 6.3 | 26.6 m | 13.3 m |
| lanczos | 4x | 5120x2880 | 201.6 | 5.0 | 33.6 m | 16.8 m |

## Headline

**Lanczos 2x on a 2-vCPU CPU-only box: 12.6 fps → 13.3 minutes for 10,000 frames,
at zero marginal cost.** That is the cheap floor any neural option has to beat on
quality-per-dollar, not just on quality.

## What these numbers do NOT include — read before quoting them

1. **Resize only.** No decode, no encode, no disk I/O. In a real pipeline
   decode+encode frequently costs more than the resize itself, so end-to-end
   will be slower than the table.
2. **Synthetic source frame.** Pillow's resampling cost is independent of pixel
   values, so this does not bias the timing — but it does mean the *visual*
   quality of the output is not representative.
3. **The 2-worker column is arithmetic** (`serial / cpu_count`), **not a measured
   parallel run.** Real speedup will be lower because of memory bandwidth.
4. **iters=5, median reported.** Tight enough for tier selection, not for
   micro-comparisons between bicubic and lanczos.
5. **No neural upscaler was measured.** There is no GPU here and no ffmpeg, so
   every Real-ESRGAN / Real-CUGAN figure either agent quotes is an estimate
   until someone with hardware measures it.

## Cost scaling for other input sizes

Resize cost is ~linear in *output* pixels. From the 720p lanczos 2x measurement
(79.5 ms):

- 1080p source, 2x → ~2.25x the pixels → ~179 ms/frame → **~30 min / 10k frames**
- 720p source, 4x → measured above → **~34 min / 10k frames**
