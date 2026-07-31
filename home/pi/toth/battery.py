#!/usr/bin/env python3
"""Read PiSugar battery level via I2C."""
import smbus2
import sys

PI_SUGAR_ADDR = 0x57
SOC_REG = 0x04  # State of Charge (2 bytes)

def read_battery():
    """Return battery percentage (0-100) or -1 on error."""
    try:
        bus = smbus2.SMBus(1)
        # Read SOC register (2 bytes, big-endian)
        data = bus.read_i2c_block_data(PI_SUGAR_ADDR, SOC_REG, 2)
        bus.close()
        # Combine two bytes (big-endian)
        soc = (data[0] << 8) | data[1]
        # MAX17048: SOC is in 1/256%, so divide by 256
        # But PiSugar often reports directly as percentage
        # If value > 100, it's in 1/256% format
        if soc > 10000:
            soc = soc // 256
        # Clamp to 0-100
        return max(0, min(100, soc))
    except Exception as e:
        print(f"Battery read error: {e}", file=sys.stderr)
        return -1

if __name__ == "__main__":
    pct = read_battery()
    print(pct)
