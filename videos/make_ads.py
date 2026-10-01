"""Create 3 vertical 9:16 Telugu ad videos for Dhruva Foundation Business Startup School."""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image

ROOT = Path(r"D:\Sadhi\Dhruva")
POSTERS = ROOT / "posters"
OUT = ROOT / "videos"
AUDIO = OUT / "audio"
FRAMES = OUT / "frames"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

W, H = 1080, 1920
FPS = 30


def cover_resize(img: Image.Image, size=(W, H)) -> Image.Image:
    tw, th = size
    scale = max(tw / img.width, th / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th)).convert("RGB")


def audio_duration(path: Path) -> float:
    cmd = [
        FFMPEG,
        "-i",
        str(path),
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    for line in (proc.stderr or "").splitlines():
        if "Duration:" in line:
            # Duration: 00:00:24.98,
            part = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 25.0


def render_ken_burns(
    images: list[Path],
    out_mp4: Path,
    duration: float,
    zoom_in: bool = True,
) -> None:
    """Render a Ken Burns slideshow matching audio duration (capped at 30s)."""
    duration = min(duration, 29.5)
    n = len(images)
    seg = duration / n
    frames_dir = FRAMES / out_mp4.stem
    frames_dir.mkdir(parents=True, exist_ok=True)

    # clear old frames
    for old in frames_dir.glob("*.jpg"):
        old.unlink()

    total_frames = int(duration * FPS)
    frames_per_seg = [total_frames // n] * n
    for i in range(total_frames % n):
        frames_per_seg[i] += 1

    frame_idx = 0
    for img_i, img_path in enumerate(images):
        base = cover_resize(Image.open(img_path))
        # slightly larger canvas for zoom
        canvas = base.resize((int(W * 1.12), int(H * 1.12)), Image.Resampling.LANCZOS)
        cw, ch = canvas.size
        segs = frames_per_seg[img_i]
        for f in range(segs):
            t = f / max(segs - 1, 1)
            if zoom_in:
                z = 1.0 + 0.10 * t
            else:
                z = 1.10 - 0.10 * t
            # slight pan
            pan_x = (0.02 * math.sin(t * math.pi)) if img_i % 2 == 0 else (-0.02 * t)
            pan_y = -0.015 * t
            vw, vh = int(W * z), int(H * z)
            cx = cw // 2 + int(pan_x * cw)
            cy = ch // 2 + int(pan_y * ch)
            left = max(0, min(cw - vw, cx - vw // 2))
            top = max(0, min(ch - vh, cy - vh // 2))
            crop = canvas.crop((left, top, left + vw, top + vh)).resize(
                (W, H), Image.Resampling.LANCZOS
            )
            crop.save(frames_dir / f"f{frame_idx:05d}.jpg", quality=92)
            frame_idx += 1

    pattern = str(frames_dir / "f%05d.jpg")
    tmp_video = out_mp4.with_suffix(".silent.mp4")
    cmd_v = [
        FFMPEG,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "medium",
        "-crf",
        "18",
        str(tmp_video),
    ]
    subprocess.run(cmd_v, check=True, capture_output=True)

    return tmp_video


def mux(video_silent: Path, audio: Path, out: Path, duration: float) -> None:
    duration = min(duration, 29.5)
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        str(video_silent),
        "-i",
        str(audio),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-t",
        f"{duration:.2f}",
        "-movflags",
        "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    video_silent.unlink(missing_ok=True)


def main() -> None:
    ads = [
        {
            "name": "dhruva-ad1-idea-to-business",
            "audio": AUDIO / "ad1.mp3",
            "images": [
                POSTERS / "dhruva-poster-14-admissions-story.jpg",
                POSTERS / "dhruva-poster-13-admissions-startup-school.jpg",
                POSTERS / "dhruva-poster-11-four-pillars-story.jpg",
                POSTERS / "dhruva-poster-17-apply-admissions.jpg",
            ],
            "zoom_in": True,
        },
        {
            "name": "dhruva-ad2-dream-start",
            "audio": AUDIO / "ad2.mp3",
            "images": [
                POSTERS / "dhruva-poster-02-dream-starts-story.jpg",
                POSTERS / "dhruva-poster-07-emotional-hook-story.jpg",
                POSTERS / "dhruva-poster-15-journey-start-admissions.jpg",
                POSTERS / "dhruva-poster-12-final-cta.jpg",
            ],
            "zoom_in": False,
        },
        {
            "name": "dhruva-ad3-where-to-start",
            "audio": AUDIO / "ad3.mp3",
            "images": [
                POSTERS / "dhruva-poster-11-four-pillars-story.jpg",
                POSTERS / "dhruva-poster-16-facebook-admissions.jpg",
                POSTERS / "dhruva-poster-05-idea-action-business.jpg",
                POSTERS / "dhruva-poster-09-bold-join-now.jpg",
            ],
            "zoom_in": True,
        },
    ]

    for ad in ads:
        missing = [p for p in ad["images"] if not p.exists()]
        if missing:
            raise SystemExit(f"Missing images: {missing}")
        dur = audio_duration(ad["audio"])
        print(f"Building {ad['name']} ({dur:.1f}s)...")
        out = OUT / f"{ad['name']}.mp4"
        silent = render_ken_burns(ad["images"], out, dur, zoom_in=ad["zoom_in"])
        mux(silent, ad["audio"], out, dur)
        size_mb = out.stat().st_size / (1024 * 1024)
        print(f"  -> {out.name} ({size_mb:.1f} MB)")

    print("Done.")


if __name__ == "__main__":
    main()
