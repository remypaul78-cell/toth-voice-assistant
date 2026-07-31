#!/usr/bin/env python3
import serial, datetime, os, sys, time
LOG = "/home/pi/toth/toth_satellite_serial.log"
PID = "/tmp/log_satellite.pid"
with open(PID, "w") as f:
    f.write(str(os.getpid()))
try:
    with serial.Serial("/dev/ttyACM0", 115200, timeout=2) as s, open(LOG, "a") as f:
        s.reset_input_buffer()
        while True:
            try:
                line = s.readline().decode(errors="ignore").rstrip()
                if line:
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    msg = f"[{ts}] {line}"
                    f.write(msg + "\n")
                    f.flush()
            except Exception as e:
                time.sleep(1)
finally:
    try: os.remove(PID)
    except: pass
