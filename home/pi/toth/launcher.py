#!/usr/bin/env python3
"""Toth Launcher — auto-restart on crash, GPIO cleanup, RAM monitoring."""
import subprocess, time, os, sys

TOTH_SCRIPT = "/home/pi/toth/toth_chatbot.py"
LOG_FILE = "/tmp/toth_launcher.log"
MAX_RAM_MB = 380  # Si RAM dispo < 50 Mo, on attend avant de relancer

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def free_ram_mb():
    """Get available RAM in MB."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) // 1024
    except:
        pass
    return 0

def kill_stale_locks():
    """Kill any process holding /dev/gpiochip0."""
    try:
        result = subprocess.run(["fuser", "/dev/gpiochip0"],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split()
            my_pid = str(os.getpid())
            pids = [p for p in pids if p != my_pid]
            if pids:
                log(f"Killing stale GPIO locks: {pids}")
                subprocess.run(["sudo", "kill", "-9"] + pids,
                              capture_output=True, timeout=3)
                time.sleep(2)
    except Exception as e:
        log(f"GPIO cleanup error: {e}")

def wait_for_ram():
    """Wait until at least 60 MB free RAM."""
    for _ in range(30):
        available = free_ram_mb()
        if available > 60:
            return True
        log(f"RAM low ({available} MB) — waiting...")
        time.sleep(3)
    return False

def main():
    log("=== Toth Launcher started ===")
    restart_count = 0

    while True:
        kill_stale_locks()

        if not wait_for_ram():
            log("RAM critically low for 90s — rebooting system...")
            os.system("sudo shutdown -r now")
            time.sleep(30)

        restart_count += 1
        log(f"Starting Toth (attempt #{restart_count})...")

        try:
            proc = subprocess.Popen(
                [sys.executable, TOTH_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Log Toth output
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    log(f"[TOTH] {line}")

            proc.wait()
            exit_code = proc.returncode

            if exit_code == 0:
                log("Toth exited normally")
            elif exit_code == 137:
                log(f"Toth OOM-killed (signal 9) — will restart after RAM frees")
            elif exit_code < 0:
                log(f"Toth killed by signal {-exit_code} — will restart")
            else:
                log(f"Toth exited with code {exit_code} — will restart")

        except Exception as e:
            log(f"Launcher error: {e}")

        # Cooldown before restart
        time.sleep(3)

if __name__ == "__main__":
    main()
