# SI-assisted: cfable (Claude Sonnet 5.5)
"""Build the 30-second pitch video: the presenter on the left, the slides inside an app
window on the right, English subtitles, and the narration track.

    python scripts/build_pitch_video.py <presenter.mp4> <narration.mp3> [--out docs/demo/Huiracocha_AI_pitch_30s.mp4]

Inputs (both supplied by the team, 2026-11-15):
  * the presenter video (portrait, 36 s) says the same script as the narration, starting at 3.12 s;
  * the narration (English, 30.2 s) is an AI-generated voice (ElevenLabs), so the video carries a
    visible label (project rule: AI-generated media is declared and watermarked).

Alignment: the word timestamps of both tracks were measured with faster-whisper (large-v3) and the
presenter's video is re-timed segment by segment so his lips follow the narration. Seven of the eight
segments need a speed change of 6 % or less; only the first sentence needs 22 %.

Needs: ffmpeg on PATH and Playwright with Chrome (frames are rendered from HTML, like the slides).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SLIDES_HTML = ROOT / "docs" / "demo" / "slides.html"

# Sentence starts, in seconds. A: narration. V: presenter video. The last value is the end.
A = [0.0, 2.66, 7.20, 10.88, 16.54, 19.94, 24.36, 26.00, 29.95]
V = [3.12, 6.37, 10.89, 14.61, 19.94, 23.34, 27.80, 29.44, 33.37]

SUBTITLES = [
    "Our planet is changing faster than ever.",
    "Yet the communities facing the storm are left blind to what is coming.",
    "We created Huiracocha to change that forever.",
    "We bring the boundless vision of space straight into the hands of those who walk the earth.",
    "Now, any community can see threats rising,",
    "protect their water and land, and act before disaster strikes.",
    "The truth is here.",
    "The power to defend your home is finally yours.",
]
SLIDE_OF_SEGMENT = [1, 2, 3, 4, 5, 6, 7, 7]
SLIDE_TITLES = {
    1: "Huiracocha AI", 2: "The challenge", 3: "The application", 4: "Real NASA data",
    5: "Honest statistics", 6: "RAG + LoRA", 7: "Impact & links",
}
FPS = 30
W, H = 1920, 1080
PRESENTER_W = 608

FRAME = """<!doctype html><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#0e1a1d;font-family:"Segoe UI",system-ui,sans-serif;color:#fff}}
.stage{{position:relative;width:{W}px;height:{H}px;background:radial-gradient(1300px 760px at 76% 18%,#18353b 0%,#0e1a1d 64%)}}
.slot{{position:absolute;left:0;top:0;width:{PW}px;height:{H}px;background:#09130f}}
.edge{{position:absolute;left:{PW}px;top:0;width:3px;height:{H}px;background:linear-gradient(180deg,#3fc2a8,#125e5a)}}
.brand{{position:absolute;left:672px;top:30px;display:flex;align-items:baseline;gap:18px}}
.brand b{{font-size:31px;letter-spacing:-.01em}}
.brand span{{font-size:16px;letter-spacing:.16em;text-transform:uppercase;color:#9fc4bf}}
.window{{position:absolute;left:672px;top:84px;width:1216px;border-radius:14px;overflow:hidden;background:#fff;
 box-shadow:0 26px 70px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.14)}}
.chrome{{height:42px;background:#e7eded;display:flex;align-items:center;padding:0 16px;gap:9px}}
.dot{{width:12px;height:12px;border-radius:50%;background:#c4cfcd}}
.url{{flex:1;margin:0 14px;height:26px;border-radius:13px;background:#fff;display:flex;align-items:center;padding:0 14px;
 font:600 15px "Segoe UI",sans-serif;color:#33484c}}
.live{{display:flex;align-items:center;gap:8px;font:700 13px "Segoe UI",sans-serif;letter-spacing:.12em;color:#125e5a}}
.live i{{width:9px;height:9px;border-radius:50%;background:#1aa37a;box-shadow:0 0 0 4px rgba(26,163,122,.22)}}
.window img{{display:block;width:1216px;height:684px}}
.sub{{position:absolute;left:672px;top:828px;width:1216px;height:128px;display:flex;align-items:center;justify-content:center;
 text-align:center;font-size:40px;line-height:1.22;font-weight:600;text-shadow:0 2px 14px rgba(0,0,0,.65)}}
.foot{{position:absolute;left:672px;bottom:30px;width:1216px;display:flex;justify-content:space-between;align-items:center;
 font-size:17px;color:#9fc4bf}}
.dots{{display:flex;gap:8px;align-items:center;margin-right:16px}}
.dots i{{width:34px;height:6px;border-radius:3px;background:rgba(255,255,255,.2)}}
.dots i.on{{background:#3fc2a8}}
.left{{display:flex;align-items:center}}
.ai{{font-size:15px;letter-spacing:.04em;color:#ecc983;border:1px solid rgba(236,201,131,.5);padding:6px 14px;border-radius:999px;
 background:rgba(236,201,131,.08)}}
</style>
<div class="stage">
 <div class="slot"></div><div class="edge"></div>
 <div class="brand"><b>Huiracocha AI</b><span>EarthTrend Detective · NASA Space Apps 2026</span></div>
 <div class="window">
  <div class="chrome"><i class="dot"></i><i class="dot"></i><i class="dot"></i>
   <div class="url">huiracochaia.soulgeit.com</div><div class="live"><i></i>LIVE</div></div>
  <img src="{slide_uri}" alt="">
 </div>
 <div class="sub">{subtitle}</div>
 <div class="foot">
  <div class="left"><div class="dots">{dots}</div><span>{slide_no}/7 · {slide_title}</span></div>
  <div class="ai">Narration: AI-generated voice (ElevenLabs) · English subtitles</div>
 </div>
</div>"""


def render_slides(tmp: Path) -> dict[int, Path]:
    """Each slide of docs/demo/slides.html as a 1280x720 PNG."""
    out: dict[int, Path] = {}
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:  # bundled Chromium not installed
            browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(SLIDES_HTML.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(1200)
        for number in range(1, 8):
            path = tmp / f"slide_{number}.png"
            page.locator(f"#slide-{number}").screenshot(path=str(path))
            out[number] = path
        browser.close()
    return out


def render_frames(tmp: Path, slides: dict[int, Path]) -> list[Path]:
    frames: list[Path] = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": W, "height": H})
        for i, text in enumerate(SUBTITLES):
            slide = SLIDE_OF_SEGMENT[i]
            dots = "".join(f'<i class="{"on" if n == slide else ""}"></i>' for n in range(1, 8))
            html = FRAME.format(W=W, H=H, PW=PRESENTER_W, slide_uri=slides[slide].as_uri(), subtitle=text,
                                dots=dots, slide_no=slide, slide_title=SLIDE_TITLES[slide])
            html_path = tmp / f"frame_{i}.html"
            html_path.write_text(html, encoding="utf-8")
            page.goto(html_path.as_uri(), wait_until="load")
            page.wait_for_timeout(250)
            png = tmp / f"frame_{i}.png"
            page.screenshot(path=str(png))
            frames.append(png)
        browser.close()
    return frames


def compose(presenter: Path, narration: Path, frames: list[Path], out: Path, tmp: Path) -> None:
    durations = [A[i + 1] - A[i] for i in range(len(SUBTITLES))]
    lines: list[str] = []
    for frame, seconds in zip(frames, durations):
        lines += [f"file '{frame.as_posix()}'", f"duration {seconds:.3f}"]
    lines.append(f"file '{frames[-1].as_posix()}'")
    listing = tmp / "frames.txt"
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")

    parts = []
    for i in range(len(SUBTITLES)):
        factor = (A[i + 1] - A[i]) / (V[i + 1] - V[i])
        parts.append(
            f"[1:v]trim=start={V[i]:.3f}:end={V[i + 1]:.3f},setpts=(PTS-STARTPTS)*{factor:.5f},"
            f"scale={PRESENTER_W}:{H},fps={FPS}[p{i}]"
        )
    concat = "".join(f"[p{i}]" for i in range(len(SUBTITLES)))
    total = A[-1]
    graph = ";".join(parts + [
        f"{concat}concat=n={len(SUBTITLES)}:v=1:a=0[pres]",
        f"[0:v]fps={FPS},format=yuv420p[bg]",
        "[bg][pres]overlay=0:0:shortest=1,format=yuv420p,"
        f"fade=t=in:st=0:d=0.25,fade=t=out:st={total - 0.3:.2f}:d=0.3[v]",
        f"[2:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total - 0.04:.3f}:d=0.04[a]",
    ])
    command = [
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-i", str(presenter), "-i", str(narration), "-filter_complex", graph,
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out),
    ]
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("presenter", type=Path)
    parser.add_argument("narration", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "demo" / "Huiracocha_AI_pitch_30s.mp4")
    args = parser.parse_args()
    for path in (args.presenter, args.narration, SLIDES_HTML):
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pitch_") as raw:
        tmp = Path(raw)
        slides = render_slides(tmp)
        frames = render_frames(tmp, slides)
        compose(args.presenter, args.narration, frames, args.out, tmp)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "default=nw=1",
         str(args.out)], capture_output=True, text=True)
    print(probe.stdout.strip().replace("\n", " | "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
