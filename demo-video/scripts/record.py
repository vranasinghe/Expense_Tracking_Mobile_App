"""Records a phone-viewport walkthrough of the Expo web build, timed to the voice-over.

Needs the dev server on http://localhost:8081 (npx expo start --web) and build/audio from narration.py.
Run:  python record.py  -> build/raw.mp4 + build/timeline.json (build/shots/FAIL_*.png if a step breaks)
"""
import base64
import json
import pathlib
import shutil
import subprocess
import time

import imageio_ffmpeg

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DUR = json.loads((BUILD / "audio" / "durations.json").read_text())
URL = "http://localhost:8081"
W, H, DPR = 390, 844, 2
GAP = 0.7  # breathing room after each narration line

# Shows a soft circle where the "finger" taps, so viewers can follow the interaction.
TOUCH_JS = """
(() => {
  const add = () => {
    if (document.getElementById('__tap')) return;
    const d = document.createElement('div');
    d.id = '__tap';
    d.style.cssText = 'position:fixed;left:0;top:0;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;' +
      'background:rgba(255,255,255,.28);border:2px solid rgba(255,255,255,.75);pointer-events:none;z-index:2147483647;' +
      'opacity:0;transition:opacity .25s, transform .18s;transform:scale(.6)';
    document.body.appendChild(d);
    addEventListener('mousemove', e => { d.style.left = e.clientX + 'px'; d.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { d.style.opacity = 1; d.style.transform = 'scale(1)'; }, true);
    addEventListener('mouseup', () => { setTimeout(() => { d.style.opacity = 0; d.style.transform = 'scale(.6)'; }, 220); }, true);
  };
  if (document.body) add(); else addEventListener('DOMContentLoaded', add);
})();
"""


class Demo:
    def __init__(self, page, t0):
        self.page, self.t0 = page, t0
        self.timeline, self.mouse = [], (W / 2, H * 0.6)
        self.shots = BUILD / "shots"

    def now(self):
        return time.time() - self.t0

    def scene(self, key, actions):
        start = self.now()
        self.timeline.append({"key": key, "start": round(start, 3), "dur": DUR[key]})
        print(f"[{start:7.2f}] {key}")
        actions()
        end = start + DUR[key] + GAP
        remaining = end - self.now()
        if remaining > 0:
            self.page.wait_for_timeout(remaining * 1000)
        else:
            print(f"   ! actions ran {-remaining:.1f}s past the narration")

    def wait(self, s):
        self.page.wait_for_timeout(s * 1000)

    def vis(self, text, exact=True):
        return self.page.get_by_text(text, exact=exact).locator("visible=true").last

    def move_to(self, x, y, steps=18):
        self.page.mouse.move(x, y, steps=steps)
        self.mouse = (x, y)

    def _ready(self, target):
        loc = self.vis(target) if isinstance(target, str) else target
        loc.wait_for(state="visible", timeout=15000)
        box = loc.bounding_box()
        if box["y"] < 0 or box["y"] + box["height"] > H:
            loc.scroll_into_view_if_needed()
            self.wait(0.5)
            box = loc.bounding_box()
        return box

    def long_press(self, target, hold=0.9):
        box = self._ready(target)
        self.move_to(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.wait(0.15)
        self.page.mouse.down()
        self.wait(hold)
        self.page.mouse.up()

    def tap(self, target, pause=0.35):
        box = self._ready(target)
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        self.move_to(x, y)
        self.wait(0.12)
        self.page.mouse.down()
        self.wait(0.08)
        self.page.mouse.up()
        self.wait(pause)

    def type_into(self, placeholder, text):
        field = self.page.get_by_placeholder(placeholder).locator("visible=true").last
        self.tap(field, pause=0.2)
        field.press_sequentially(text, delay=70)
        self.wait(0.25)

    def keypad(self, digits, gap=0.18):
        for d in digits:
            self.tap(self.vis(d), pause=gap)

    def scroll(self, dy, x=None, y=None, steps=14, dx=0):
        x = x if x is not None else W / 2
        y = y if y is not None else H * 0.55
        self.move_to(x, y, steps=8)
        for _ in range(steps):
            self.page.mouse.wheel(dx / steps, dy / steps)
            self.wait(0.035)
        self.wait(0.4)


def run():
    for p in ("shots", "frames"):
        shutil.rmtree(BUILD / p, ignore_errors=True)
        (BUILD / p).mkdir(parents=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True, args=[f"--force-device-scale-factor={DPR}"])
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=DPR,
            is_mobile=True,
            has_touch=True,
            color_scheme="dark",
            locale="en-US",
        )
        ctx.add_init_script(TOUCH_JS)
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle", timeout=180000)
        page.get_by_text("Track Every Dollar", exact=False).first.wait_for(timeout=120000)
        page.wait_for_timeout(1500)  # fonts + entrance animation

        # DevTools screencast gives full device-pixel frames (Playwright's recorder captures CSS pixels only).
        frames = []
        cdp = ctx.new_cdp_session(page)

        def on_frame(ev):
            name = f"{len(frames):05d}.jpg"
            (BUILD / "frames" / name).write_bytes(base64.b64decode(ev["data"]))
            frames.append((name, ev["metadata"]["timestamp"]))
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                          "maxWidth": W * DPR, "maxHeight": H * DPR, "everyNthFrame": 1})
        page.wait_for_timeout(600)
        t0 = time.time()
        d = Demo(page, t0)
        d.move_to(W / 2, H * 0.62, steps=1)

        def intro():
            d.wait(4.0)
            d.move_to(W / 2, 760)

        def onboarding():
            d.tap("Next")
            d.wait(3.4)
            d.tap("Next")
            d.wait(3.0)
            d.tap("Skip", pause=0.3)

        def signup():
            d.wait(0.5)
            d.tap("Sign In", pause=1.4)
            d.tap("Sign Up", pause=0.6)
            d.type_into("Alex Morgan", "Alex Morgan")
            d.type_into("you@example.com", "alex@example.com")
            d.type_into("••••••••", "demo1234")
            d.wait(0.4)
            d.tap("Create Account")

        def balance():
            d.vis("Set Your Starting Balance").wait_for(timeout=15000)
            d.wait(1.2)
            d.move_to(*_center(d.vis("Skip")))
            d.wait(0.8)
            d.keypad("5000", gap=0.3)
            d.wait(0.8)
            d.tap("Continue")

        def home():
            d.vis("Recent Transactions").wait_for(timeout=15000)
            d.wait(3.8)
            d.scroll(420)
            d.wait(1.6)
            d.scroll(-420)

        def add_expense():
            d.tap(_fab(page), pause=0.8)
            d.keypad("45", gap=0.3)
            d.wait(0.4)
            d.tap("Food", pause=0.6)
            d.tap("Save Expense", pause=1.0)

        def add_income():
            d.tap(_fab(page), pause=0.8)
            d.tap(_toggle(page, "Income"), pause=0.6)
            d.keypad("250", gap=0.3)
            d.tap("Freelance", pause=0.6)
            d.tap("Save Income", pause=1.0)

        def notifications():
            d.tap(_bell(page), pause=0.5)
            d.wait(3.2)
            d.tap(d.vis("Food Budget Alert", exact=False), pause=1.6)
            d.tap("Mark all read", pause=1.0)
            d.tap(_close(page), pause=0.3)

        def analytics():
            d.tap("See all", pause=1.2)
            d.tap(_icon_button(page, "chevron-back"), pause=1.0)
            d.tap(_icon_button(page, "chevron-forward"), pause=0.8)
            for p in ("Week", "Year", "Month"):
                d.tap(p, pause=0.7)
            d.scroll(380)
            d.wait(1.0)
            d.scroll(450)
            d.wait(1.0)
            d.scroll(-830)

        def budgets():
            d.tap("Budgets", pause=1.5)
            d.wait(1.6)
            d.scroll(380)
            d.wait(1.4)
            d.scroll(-380)

        def new_budget():
            d.tap("New Budget", pause=0.8)
            food = d.vis("Food").bounding_box()
            d.scroll(0, x=W * 0.6, y=food["y"] + food["height"] / 2, steps=12, dx=260)
            d.tap("Bills", pause=0.4)
            d.type_into("500", "1500")
            d.tap(page.get_by_text("Create Budget", exact=True).locator("visible=true").last, pause=1.0)
            d.scroll(700)

        def delete_budget():
            d.wait(0.6)
            d.long_press(d.vis("Bills"))
            d.wait(1.2)
            d.tap("Delete", pause=1.0)

        def history():
            d.tap("Profile", pause=1.2)
            d.tap("Transaction History", pause=1.0)
            d.type_into("Search transactions...", "rent")
            d.wait(0.8)
            page.get_by_placeholder("Search transactions...").fill("")
            d.tap("Expense", pause=0.8)
            d.tap("Income", pause=0.8)
            d.tap("All", pause=0.4)

        def delete_txn():
            d.long_press(d.vis("Starbucks Coffee"))
            d.wait(1.4)
            d.tap("Delete", pause=1.2)
            d.tap(_close(page), pause=0.3)

        def balance_update():
            d.tap("Starting Balance", pause=0.6)
            d.type_into("5000", "6000")
            d.tap("Update", pause=0.6)

        def settings():
            d.tap("€", pause=0.9)
            d.tap("$", pause=0.6)
            d.scroll(300)
            switches = page.get_by_role("switch")
            d.tap(switches.nth(0), pause=0.8)   # dark mode
            d.move_to(*_center(switches.nth(1)))  # daily reminder (already on)
            d.wait(0.8)
            d.tap(switches.nth(2), pause=0.6)   # biometric lock

        def help_center():
            d.tap("Contact Support", pause=1.6)
            d.tap("OK", pause=0.2)

        def logout():
            d.tap("Log Out", pause=1.0)
            d.tap(d.vis("Log Out"), pause=0.8)
            d.vis("Create Account").wait_for(timeout=15000)
            d.tap("Sign In", pause=0.4)
            d.type_into("you@example.com", "alex@example.com")
            d.type_into("••••••••", "demo1234")

        def outro():
            d.move_to(W / 2, H * 0.45)

        for key, fn in [("intro", intro), ("onboarding", onboarding), ("signup", signup), ("balance", balance),
                        ("home", home), ("add_expense", add_expense), ("add_income", add_income),
                        ("notifications", notifications), ("analytics", analytics), ("budgets", budgets),
                        ("new_budget", new_budget), ("delete_budget", delete_budget), ("history", history),
                        ("delete_txn", delete_txn), ("balance_update", balance_update), ("settings", settings),
                        ("help", help_center), ("logout", logout), ("outro", outro)]:
            try:
                d.scene(key, fn)
            except Exception:
                page.screenshot(path=str(BUILD / "shots" / f"FAIL_{key}.png"))
                raise
        page.wait_for_timeout(800)

        cdp.send("Page.stopScreencast")
        end_ts = time.time()
        ctx.close()
        browser.close()

    # Variable-rate frames -> constant 30 fps video. Timeline is re-based on the first frame.
    base = frames[0][1]
    lines = []
    for (name, ts), nxt in zip(frames, [f[1] for f in frames[1:]] + [end_ts]):
        lines += [f"file 'frames/{name}'", f"duration {max(nxt - ts, 0.001):.4f}"]
    lines.append(f"file 'frames/{frames[-1][0]}'")
    (BUILD / "frames.txt").write_text("\n".join(lines) + "\n")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(BUILD / "frames.txt"), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264",
                    "-crf", "14", "-preset", "fast", str(BUILD / "raw.mp4")], check=True, cwd=BUILD)
    for s in d.timeline:
        s["start"] = round(s["start"] + t0 - base, 3)
    (BUILD / "timeline.json").write_text(json.dumps(d.timeline, indent=2))
    print(f"done -> {BUILD / 'raw.mp4'} ({len(frames)} frames)")


GLYPHS = json.loads((ROOT.parent / "mobile" / "node_modules" / "@expo" / "vector-icons" / "build" / "vendor"
                     / "react-native-vector-icons" / "glyphmaps" / "Ionicons.json").read_text())


def _icon_button(page, icon_name):
    return page.get_by_text(chr(GLYPHS[icon_name]), exact=True).locator("visible=true").last


def _toggle(page, text):
    """The Expense/Income switch in the add sheet: the match on the same row as the "Expense" toggle."""
    ref = page.get_by_text("Expense", exact=True).locator("visible=true").last.bounding_box()
    for loc in page.get_by_text(text, exact=True).locator("visible=true").all():
        b = loc.bounding_box()
        if b and abs(b["y"] - ref["y"]) < 8:
            return loc
    raise RuntimeError(f"toggle {text!r} not found")


def _center(loc):
    b = loc.bounding_box()
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


def _fab(page):
    return _icon_button(page, "add")


def _bell(page):
    return _icon_button(page, "notifications-outline")


def _close(page):
    return _icon_button(page, "close")


if __name__ == "__main__":
    run()
