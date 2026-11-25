# Demo video tooling

Scripts that record a narrated, phone-sized walkthrough of the app's web build. Generated audio, frames and videos are git-ignored; only the scripts are tracked.

## Requirements

- Python 3.11+ with `pip install playwright edge-tts imageio-ffmpeg pillow`
- Microsoft Edge (used through Playwright's `msedge` channel)
- The Expo web dev server running on `http://localhost:8081` (`cd mobile && npx expo start --web`)
- A fresh app state (the recorder starts from the onboarding slides)

## Usage

Run from `demo-video/scripts/`, in order:

| Step | Command | Output |
| --- | --- | --- |
| 1. Voice-over | `python narration.py` | `build/audio/*.mp3` and scene durations |
| 2. Recording | `python record.py` | `build/raw.mp4` (390×844 viewport at 2×) and `build/timeline.json` |
| 3. Final video | `python compose.py` | `expense-tracker-demo.mp4` (1080×1920) and `chapters.txt` |

Edit the narration in `narration.py` (`SCENES`) and the matching on-screen actions in `record.py`. Each scene is held for the length of its narration line.

> The voice-over uses Microsoft Edge's online text-to-speech service, so the narration text is sent to Microsoft. Fonts in `compose.py` point to Windows system fonts.
