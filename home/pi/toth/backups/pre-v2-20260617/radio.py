#!/usr/bin/env python3
"""Radio player for Toth — streams web radios with mpv (lightweight, CPU-efficient)."""
import sys, os, subprocess, signal, time

RADIOS = {
    "fip":       ("FIP",          "http://icecast.radiofrance.fr/fip-hifi.aac"),
    "nova":      ("Radio Nova",   "https://novazz.ice.infomaniak.ch/novazz-128.mp3"),
    "nrj":       ("NRJ",          "http://cdn.nrjaudio.fm/adwz1/fr/30001/mp3_128.mp3"),
    "skyrock":   ("Skyrock",      "http://icecast.skyrock.net/s/natio_mp3_128k"),
    "fun":       ("Fun Radio",    "http://streaming.radio.funradio.fr/fun-1-44-128"),
    "reggae":    ("1.FM Reggae",  "http://strm112.1.fm/reggae_mobile_mp3"),
    "dub":       ("Roots Dub",    "http://tropicalisima.stream:8000/zona-dub"),
    "ragga":     ("Ragga Radio",  "http://jazzpro.radio2b.net:8000/ragga"),
}

AUDIO_DEV = "hw:0,0"
AIRPODS_SINK = "bluez_output.E4_90_FD_E3_4A_D3.1"
PID_FILE = "/tmp/toth_radio.pid"
STATE_FILE = "/tmp/toth_radio_state"

def list_radios():
    print("Radios disponibles :")
    for key, (name, url) in RADIOS.items():
        print(f"  {key:12} → {name}")

def stop_radio():
    """Kill mpv process and clean up PID file."""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            print(f"Radio arrêtée (PID {pid})")
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    else:
        # Fallback: kill any lingering mpv radio process
        try:
            subprocess.run(["pkill", "-f", "mpv.*icecast"], timeout=3, capture_output=True)
        except Exception:
            pass

def play_radio(key):
    """Stream radio with mpv — much lighter on CPU than ffmpeg pipe."""
    if key not in RADIOS:
        print(f"Radio inconnue: {key}")
        print("Utilise: python3 radio.py list")
        return False

    stop_radio()

    name, url = RADIOS[key]
    print(f"▶ Lancement de {name}...")
    print(f"   URL: {url}")

    # Save state for resume after TTS
    with open(STATE_FILE, "w") as f:
        f.write(key)

    # Try PulseAudio (AirPods) first, then WM8960, then ALSA default
    audio_devices = [
        ("pulse", "PulseAudio"),
        ("alsa/hw:0,0", "WM8960 speaker"),
        ("alsa/default", "ALSA default"),
    ]

    for dev, label in audio_devices:
        try:
            cmd = [
                "mpv",
                "--no-config",
                "--no-video",
                "--no-terminal",
                f"--audio-device={dev}",
                "--audio-buffer=0.5",      # Small buffer for live radio responsiveness
                "--cache=yes",
                "--cache-secs=3",           # 3 seconds cache to handle network jitter
                "--demuxer-max-bytes=2M",   # Limit demuxer memory on Pi Zero
                "--demuxer-max-back-bytes=1M",
                "--msg-level=all=no",       # Silence all mpv output
                url,
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )

            # Wait briefly to see if it starts without error
            time.sleep(2)
            poll = proc.poll()
            if poll is None:
                # Still running — success!
                print(f"   ▶ Audio sur: {label}")
                with open(PID_FILE, "w") as f:
                    f.write(str(proc.pid))
                proc.wait()
                # Clean up PID file when mpv exits naturally
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                return True
            else:
                # Exited with error — try next device
                print(f"   ✗ {label} failed (exit {poll})")
                try:
                    proc.kill()
                except Exception:
                    pass
        except Exception as e:
            print(f"   ✗ {label} exception: {e}")
            continue

    print("   ❌ Aucun périphérique audio disponible")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 radio.py <nom_radio|stop|list>")
        print("Exemples:")
        print("  python3 radio.py fip      # Lance FIP")
        print("  python3 radio.py nrj      # Lance NRJ")
        print("  python3 radio.py stop     # Arrête la radio")
        print("  python3 radio.py list     # Liste les radios")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_radios()
    elif cmd == "stop":
        stop_radio()
    else:
        play_radio(cmd)
