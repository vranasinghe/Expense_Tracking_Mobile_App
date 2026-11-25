"""Builds the final vertical demo video: phone-framed recording + chapter captions + voice-over.

Run after narration.py and record.py:  python compose.py  -> ../expense-tracker-demo.mp4
"""
import json
import pathlib
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
ASSETS = BUILD / "compose"
OUT = ROOT / "expense-tracker-demo.mp4"
FF = imageio_ffmpeg.get_ffmpeg_exe()

CW, CH = 1080, 1920               # output canvas
SH = 1560                         # phone screen height on canvas
SW = round(SH * 390 / 844)        # keeps the 390x844 viewport ratio -> 721
BEZEL = 16
SX, SY = (CW - SW) // 2, 190      # screen position
RADIUS = 58
LEAD = 0.8                        # seconds of video kept before the first line

TITLES = {
    "intro": "Meet ExpenseTracker",
    "onboarding": "Onboarding",
    "signup": "Create an account",
    "balance": "Set a starting balance",
    "home": "Home dashboard",
    "add_expense": "Add an expense",
    "add_income": "Add income",
    "notifications": "Notifications",
    "analytics": "Analytics",
    "budgets": "Budgets",
    "new_budget": "Create a budget",
    "delete_budget": "Delete a budget",
    "history": "Transaction history",
    "delete_txn": "Delete a transaction",
    "balance_update": "Update starting balance",
    "settings": "Currency & preferences",
    "help": "Help center",
    "logout": "Log out & sign in",
    "outro": "Take control of your money",
}

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"


def background():
    img = Image.new("RGB", (CW, CH), "#0E1116")
    glow = Image.new("RGB", (CW, CH), "#0E1116")
    g = ImageDraw.Draw(glow)
    g.ellipse((-300, 1050, 900, 2250), fill="#0F5E4B")
    g.ellipse((500, -350, 1500, 650), fill="#1B2B4A")
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(220)), 0.85)
    d = ImageDraw.Draw(img)
    # phone body + soft shadow
    shadow = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(shadow).rounded_rectangle(
        (SX - BEZEL, SY - BEZEL + 24, SX + SW + BEZEL, SY + SH + BEZEL + 24), RADIUS + BEZEL, fill=170)
    img.paste((0, 0, 0), (0, 0), shadow.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((SX - BEZEL, SY - BEZEL, SX + SW + BEZEL, SY + SH + BEZEL), RADIUS + BEZEL,
                        fill="#05070A", outline="#2A313B", width=3)
    # footer brand
    f = ImageFont.truetype(FONT_BOLD, 34)
    fs = ImageFont.truetype(FONT_REG, 26)
    bx = CW // 2
    d.rounded_rectangle((bx - 205, 1808, bx - 165, 1848), 11, fill="#2ED9A0")
    d.text((bx - 185, 1828), "$", font=ImageFont.truetype(FONT_BOLD, 28), fill="#0E1116", anchor="mm")
    d.text((bx - 150, 1828), "ExpenseTracker", font=f, fill="#FFFFFF", anchor="lm")
    d.text((bx + 112, 1830), "· mobile demo", font=fs, fill="#8A94A3", anchor="lm")
    img.save(ASSETS / "bg.png")


def mask():
    m = Image.new("L", (SW, SH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, SW - 1, SH - 1), RADIUS, fill=255)
    m.save(ASSETS / "mask.png")


def caption(i, key):
    img = Image.new("RGBA", (CW, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    num = ImageFont.truetype(FONT_BOLD, 26)
    big = ImageFont.truetype(FONT_BOLD, 50)
    d.text((CW // 2, 38), f"{i:02d} / {len(TITLES):02d}", font=num, fill="#2ED9A0", anchor="mm")
    d.text((CW // 2, 96), TITLES[key], font=big, fill="#FFFFFF", anchor="mm")
    path = ASSETS / f"cap_{i:02d}.png"
    img.save(path)
    return path


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    timeline = json.loads((BUILD / "timeline.json").read_text())
    background()
    mask()

    t0 = timeline[0]["start"] - LEAD
    end = timeline[-1]["start"] + timeline[-1]["dur"] + 1.6
    total = end - t0

    inputs = ["-loop", "1", "-i", str(ASSETS / "bg.png"),
              "-ss", f"{t0:.3f}", "-t", f"{total:.3f}", "-i", str(BUILD / "raw.mp4"),
              "-loop", "1", "-i", str(ASSETS / "mask.png")]
    n = 3
    caps, auds = [], []
    for i, s in enumerate(timeline, 1):
        inputs += ["-loop", "1", "-i", str(caption(i, s["key"]))]
        caps.append((n, s, i))
        n += 1
    for s in timeline:
        inputs += ["-i", str(BUILD / "audio" / f"{s['key']}.mp3")]
        auds.append((n, s))
        n += 1

    fc = [
        f"[1:v]scale={SW}:{SH}:flags=lanczos:in_range=pc:out_range=tv,format=rgba[scr]",
        "[2:v]format=gray[m]",
        "[scr][m]alphamerge[phone]",
        f"[0:v][phone]overlay={SX}:{SY}:shortest=1[v0]",
    ]
    last = "v0"
    for k, (idx, s, i) in enumerate(caps):
        a = s["start"] - t0
        b = (caps[k + 1][1]["start"] - t0) if k + 1 < len(caps) else total
        fade = f"[{idx}:v]format=rgba,fade=t=in:st={max(a, 0):.2f}:d=0.35:alpha=1[c{i}]"
        fc.append(fade)
        fc.append(f"[{last}][c{i}]overlay=0:22:enable='between(t,{a:.2f},{b:.2f})'[v{i}]")
        last = f"v{i}"
    fc.append(f"[{last}]fade=t=in:st=0:d=0.6,fade=t=out:st={total - 0.8:.2f}:d=0.8,scale=out_range=tv,format=yuv420p[vout]")

    for idx, s in auds:
        ms = int(round((s["start"] - t0) * 1000))
        fc.append(f"[{idx}:a]aresample=48000,adelay={ms}|{ms}[a{idx}]")
    fc.append("".join(f"[a{idx}]" for idx, _ in auds)
              + f"amix=inputs={len(auds)}:normalize=0,apad,atrim=0:{total:.3f},"
              f"loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

    cmd = [FF, "-y", "-loglevel", "error", "-stats", *inputs,
           "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
           "-t", f"{total:.3f}", "-r", "30",
           "-color_range", "tv", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(OUT)]
    subprocess.run(cmd, check=True)

    chapters = [f"{int((s['start'] - t0) // 60)}:{int((s['start'] - t0) % 60):02d}  {TITLES[s['key']]}"
                for s in timeline]
    (ROOT / "chapters.txt").write_text("\n".join(chapters) + "\n", encoding="utf-8")
    print("wrote", OUT, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
