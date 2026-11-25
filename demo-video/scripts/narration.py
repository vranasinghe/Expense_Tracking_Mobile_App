"""Voice-over script for the ExpenseTracker mobile demo.

Run:  python narration.py   -> writes ../build/audio/<scene>.mp3 + durations.json
"""
import asyncio
import json
import pathlib
import re
import subprocess

import edge_tts
import imageio_ffmpeg

VOICE = "en-US-AndrewNeural"
RATE = "+4%"

SCENES = [
    ("intro", "Meet ExpenseTracker: a mobile app, built with React Native and Expo, "
              "that helps you track every dollar, effortlessly."),
    ("onboarding", "A short onboarding introduces the three core ideas. Log expenses in seconds, "
                   "set budgets to stay in control, and see exactly where your money goes. You can skip ahead at any time."),
    ("signup", "Returning users can sign in, and new users create an account with a name, email and password. "
               "Accounts are powered by Firebase Authentication, with Google and Apple sign-in on the same screen."),
    ("balance", "Next, set your starting balance on the built-in keypad, or skip it for now. "
                "This is your baseline. Every expense and every income is tracked from here."),
    ("home", "The home dashboard shows your current balance, how much you've spent this month, "
             "and your income versus expenses at a glance. Below that is a list of your most recent transactions."),
    ("add_expense", "Adding an expense takes just a few taps. Tap the plus button, enter the amount, "
                    "pick a category, and save. Your balance updates instantly."),
    ("add_income", "Income works the same way. Switch to income, enter the amount, "
                   "choose a source such as salary or freelance work, and save it."),
    ("notifications", "The notification center keeps you on track, with budget alerts, weekly summaries and daily reminders. "
                      "Tap one to mark it as read, or clear them all at once."),
    ("analytics", "Tap see all, and Analytics turns your data into insight. Move between months, switch between week, month and year views, "
                  "and explore the daily spending chart, income versus expenses, and a full category breakdown."),
    ("budgets", "Budgets let you set a monthly spending limit for each category. "
                "Progress bars show how much you've used, and any category that goes over its limit is flagged right away."),
    ("new_budget", "Creating a new budget is simple. Pick a category, enter a monthly limit, and it's added to your list."),
    ("delete_budget", "Changed your mind? Press and hold a budget, confirm, and it's removed."),
    ("history", "Your profile brings everything together. Transaction history lets you search every transaction "
                "and filter by expenses or income."),
    ("delete_txn", "Logged something by mistake? Press and hold any transaction to delete it, "
                   "and your totals update straight away."),
    ("balance_update", "You can correct your starting balance at any time, right from your profile."),
    ("settings", "Switch the display currency, and set your preferences: dark mode, daily reminders, "
                 "and a biometric lock for extra security."),
    ("help", "The help center puts support just one tap away."),
    ("logout", "When you're done, log out securely. Signing back in takes just your email and password."),
    ("outro", "ExpenseTracker. Simple, fast, and built to help you take control of your money."),
]

OUT = pathlib.Path(__file__).resolve().parent.parent / "build" / "audio"


def duration(path: pathlib.Path) -> float:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    err = subprocess.run([ff, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    durations = {}
    for key, text in SCENES:
        path = OUT / f"{key}.mp3"
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(path))
        durations[key] = round(duration(path), 3)
        print(f"{key:14s} {durations[key]:6.2f}s")
    (OUT / "durations.json").write_text(json.dumps(durations, indent=2))
    print("total", round(sum(durations.values()), 1), "s")


if __name__ == "__main__":
    asyncio.run(main())
