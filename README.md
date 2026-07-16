# Toth — Voice Assistant on Pi Zero 2W

A full AI voice assistant running on a Raspberry Pi Zero 2W (415MB RAM) with Hermes AI, Telegram bot integration, Bluetooth ring control, and text-to-speech book reader.

## What it does

- **Voice interaction** — speak to Toth, it responds via TTS (edge-tts)
- **Telegram bot** — full chat interface with media controls
- **JX-05 ring control** — Bluetooth smart ring for navigation (swipe, tap, double-tap)
- **Book reader** — PDF to JSON to TTS with chapter navigation via ring
- **Bluetooth audio** — connects to Bluetooth speakers/headphones
- **Music player** — YouTube audio extraction, local playback
- **Smart home** — Tuya/eWeLink device control via voice
- **Screen display** — Whisplay HAT ST7789 240x280 with screensaver

## Hardware

- Raspberry Pi Zero 2W (415MB RAM, 1GHz)
- WM8960 audio HAT (microphone + speaker)
- Whisplay HAT ST7789 240x280 display
- JX-05 Bluetooth smart ring
- USB Bluetooth dongle (for A2DP speakers)

## Key challenges solved

- Running AI assistant on 415MB RAM (Piper TTS, edge-tts, lightweight stack)
- Bluetooth ring integration via evdev (/dev/input/eventX)
- Audio routing with PulseAudio on Pi Zero (no pkill, use fuser -k)
- Reverse SSH tunnel for remote access (watchdog cron)
- Bluetooth MAC spoofing for multiple devices
- Book reader with real PDF chapter extraction (PyMuPDF TOC)

## Architecture

```
User voice -> WM8960 mic -> Whisper (VPS) -> Hermes AI -> edge-tts -> speaker
                                                       |
                                               Telegram bot <-> user

JX-05 ring -> evdev -> swipe/tap events -> media control
```

## Author

Remy Paul — [GitHub](https://github.com/remypaul78-cell)

## License

MIT