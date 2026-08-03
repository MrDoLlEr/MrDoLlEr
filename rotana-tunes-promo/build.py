"""Build the film: voice-over -> frames -> score -> mux.

    python3 build.py            # full build, reusing a cached voice-over
    python3 build.py --revoice  # re-synthesise the voice-over first
    python3 build.py --preview  # every 3rd frame, half size, for a fast look
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from multiprocessing import Process

import numpy as np

from config import BUILD, FPS, H, OUT, W

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def ensure_voice(force: bool) -> None:
    if force or not (BUILD / "vo_timing.json").exists() or not (BUILD / "vo_raw.wav").exists():
        import vo

        t = vo.synthesize()
        print(f"[vo] {t['duration']:.2f}s, {len(t['lines'])} lines")
    else:
        print("[vo] reusing cached take")


def _segment(idx: int, first: int, last: int, scale: int, step: int, path: str) -> None:
    import storyboard as sb  # imported per process so caches stay local

    w, h = W // scale, H // scale
    cmd = [
        FFMPEG, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS / step), "-i", "-",
        "-an", "-vf", f"unsharp=5:5:0.45:5:5:0.0,scale={w}:{h}:flags=lanczos",
        "-c:v", "libx264", "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p",
        path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for n in range(first, last):
        arr = sb.frame(n * step / FPS, n * step)
        proc.stdin.write((np.clip(arr, 0, 1) * 255).astype(np.uint8).tobytes())
        if idx == 0 and (n - first) % 20 == 0:
            done = n - first + 1
            rate = done / max(1e-3, time.time() - t0)
            eta = (last - first - done) / max(rate, 1e-3)
            print(f"[render] worker0 {done}/{last - first} frames  {rate:.2f} fps  eta {eta:.0f}s",
                  flush=True)
    proc.stdin.close()
    proc.wait()


def render_video(duration: float, workers: int, step: int, scale: int) -> str:
    frames = int(round(duration * FPS)) // step
    seg_dir = BUILD / "segments"
    if seg_dir.exists():
        shutil.rmtree(seg_dir)
    seg_dir.mkdir(parents=True)

    bounds = [round(i * frames / workers) for i in range(workers + 1)]
    procs = []
    for i in range(workers):
        p = Process(target=_segment, args=(i, bounds[i], bounds[i + 1], scale, step,
                                           str(seg_dir / f"seg_{i:02d}.mp4")))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
        if p.exitcode:
            raise RuntimeError(f"render worker failed with code {p.exitcode}")

    listing = seg_dir / "segments.txt"
    listing.write_text("".join(f"file '{seg_dir / f'seg_{i:02d}.mp4'}'\n" for i in range(workers)))
    silent = BUILD / "picture.mp4"
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(silent)],
        check=True,
    )
    return str(silent)


def mux(picture: str, audio: str, dest: str, vertical: bool = True) -> None:
    if vertical:
        vf = "null"
    else:
        # 16:9 re-frame: blurred fill behind the pillarboxed master
        vf = (
            "split[a][b];"
            "[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            "gblur=sigma=42,eq=brightness=-0.16:saturation=0.7[bg];"
            "[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0"
        )
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", picture, "-i", audio,
         "-filter_complex" if not vertical else "-vf", vf,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-level", "4.1", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "224k", "-ar", "48000", "-ac", "2",
         "-shortest", dest],
        check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--revoice", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4)))
    ap.add_argument("--skip-wide", action="store_true")
    args = ap.parse_args()

    ensure_voice(args.revoice)

    import storyboard as sb

    duration = sb.TIMING["duration"]
    cuts = sb.cut_times()
    print(f"[edit] {duration:.2f}s, {len(sb.SHOTS)} shots, {len(cuts)} cuts")

    import mix as mixer

    sections = {
        "open": sb.SHOTS[1].start,
        "groove": sb.SHOTS[4].start,
        "full": sb.SHOTS[7].start,
        "peak": sb.SHOTS[12].start,
        "break": sb.SHOTS[14].start,
        "cta": sb.SHOTS[17].start,
    }
    t0 = time.time()
    audio = mixer.build_mix(duration, cuts, sections)
    print(f"[audio] mixed in {time.time() - t0:.1f}s -> {audio}")

    t0 = time.time()
    picture = render_video(duration, args.workers, 3 if args.preview else 1,
                           2 if args.preview else 1)
    print(f"[render] {time.time() - t0:.1f}s -> {picture}")

    vertical = OUT / ("preview_9x16.mp4" if args.preview else "rotana_tunes_promo_9x16.mp4")
    mux(picture, str(audio), str(vertical), vertical=True)
    print(f"[out] {vertical}")

    if not args.preview and not args.skip_wide:
        wide = OUT / "rotana_tunes_promo_16x9.mp4"
        mux(picture, str(audio), str(wide), vertical=False)
        print(f"[out] {wide}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
