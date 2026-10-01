"""Fast ffmpeg-based 9:16 Telugu ad videos for Dhruva Foundation."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

ROOT = Path(r"D:\Sadhi\Dhruva")
POSTERS = ROOT / "posters"
OUT = ROOT / "videos"
AUDIO = OUT / "audio"
PREP = OUT / "prep"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:] if proc.stderr else "ffmpeg failed")


def audio_duration(path: Path) -> float:
    proc = subprocess.run([FFMPEG, "-i", str(path), "-f", "null", "-"], capture_output=True, text=True)
    for line in (proc.stderr or "").splitlines():
        if "Duration:" in line:
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 24.0


def to_vertical(src: Path, dst: Path) -> None:
    img = Image.open(src).convert("RGB")
    scale = max(W / img.width, H / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    img.crop((left, top, left + W, top + H)).save(dst, quality=95)


def make_clip(img: Path, out: Path, seconds: float, zoom_in: bool) -> None:
    frames = max(int(seconds * 30), 30)
    if zoom_in:
        zexpr = f"min(1.0+0.0012*on,1.12)"
    else:
        zexpr = f"max(1.12-0.0012*on,1.0)"
    vf = (
        f"scale=1200:2133,zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s={W}x{H}:fps=30,format=yuv420p"
    )
    run([
        FFMPEG, "-y", "-loop", "1", "-i", str(img),
        "-vf", vf, "-t", f"{seconds:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", str(out),
    ])


def concat_clips(clips: list[Path], out: Path) -> None:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", str(out),
    ])


def mux(video: Path, audio: Path, out: Path, duration: float) -> None:
    duration = min(duration, 29.5)
    run([
        FFMPEG, "-y",
        "-i", str(video), "-i", str(audio),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-t", f"{duration:.2f}",
        "-movflags", "+faststart",
        str(out),
    ])


def build(name: str, audio: Path, images: list[Path], zoom_in: bool) -> None:
    PREP.mkdir(parents=True, exist_ok=True)
    dur = min(audio_duration(audio), 29.5)
    print(f"Building {name} ({dur:.1f}s)...")
    n = len(images)
    seg = dur / n
    verts, clips = [], []
    for i, src in enumerate(images):
        vimg = PREP / f"{name}_img{i}.jpg"
        clip = PREP / f"{name}_clip{i}.mp4"
        to_vertical(src, vimg)
        make_clip(vimg, clip, seg, zoom_in=(zoom_in if i % 2 == 0 else not zoom_in))
        verts.append(vimg)
        clips.append(clip)
    silent = PREP / f"{name}_silent.mp4"
    concat_clips(clips, silent)
    out = OUT / f"{name}.mp4"
    mux(silent, audio, out, dur)
    print(f"  -> {out} ({out.stat().st_size/1024/1024:.1f} MB)")


def main() -> None:
    build(
        "dhruva-ad1-idea-to-business",
        AUDIO / "ad1.mp3",
        [
            POSTERS / "dhruva-poster-14-admissions-story.jpg",
            POSTERS / "dhruva-poster-13-admissions-startup-school.jpg",
            POSTERS / "dhruva-poster-11-four-pillars-story.jpg",
            POSTERS / "dhruva-poster-17-apply-admissions.jpg",
        ],
        True,
    )
    build(
        "dhruva-ad2-dream-start",
        AUDIO / "ad2.mp3",
        [
            POSTERS / "dhruva-poster-02-dream-starts-story.jpg",
            POSTERS / "dhruva-poster-07-emotional-hook-story.jpg",
            POSTERS / "dhruva-poster-15-journey-start-admissions.jpg",
            POSTERS / "dhruva-poster-12-final-cta.jpg",
        ],
        False,
    )
    build(
        "dhruva-ad3-where-to-start",
        AUDIO / "ad3.mp3",
        [
            POSTERS / "dhruva-poster-11-four-pillars-story.jpg",
            POSTERS / "dhruva-poster-16-facebook-admissions.jpg",
            POSTERS / "dhruva-poster-05-idea-action-business.jpg",
            POSTERS / "dhruva-poster-09-bold-join-now.jpg",
        ],
        True,
    )
    print("Done.")


if __name__ == "__main__":
    main()
