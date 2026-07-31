#!/usr/bin/env python3
"""Generate battery icon PIL Image — Android-style top-right indicator."""
from PIL import Image, ImageDraw, ImageFont
import os

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def battery_icon(width=240, height=280, percentage=None):
    """Return raw RGB565 bytes for LCD with battery icon overlaid top-right.
    If percentage is None, reads from PiSugar via I2C."""
    import sys
    sys.path.insert(0, "/home/pi/toth")
    from battery import read_battery
    
    if percentage is None:
        percentage = read_battery()
        if percentage < 0:
            percentage = 0
    
    # Create base black canvas
    img = Image.new("RGB", (width, height), "#000000")
    draw = ImageDraw.Draw(img)
    
    # Battery icon dimensions
    icon_w, icon_h = 48, 22
    margin_right, margin_top = 8, 6
    x = width - margin_right - icon_w
    y = margin_top
    
    # Color based on level
    if percentage > 60:
        fill_color = "#4CAF50"   # green
    elif percentage > 20:
        fill_color = "#FFC107"   # yellow/amber
    else:
        fill_color = "#F44336"   # red
    
    # Battery body (rounded rect)
    body_w = icon_w - 6  # leave room for tip
    draw.rounded_rectangle([x, y, x + body_w, y + icon_h], radius=4, outline="#888888", width=2)
    
    # Battery tip (small rectangle on right)
    tip_x = x + body_w
    tip_w = 4
    tip_h = icon_h // 2
    draw.rectangle([tip_x, y + tip_h//2, tip_x + tip_w, y + tip_h//2 + tip_h], fill="#888888")
    
    # Fill level
    fill_margin = 3
    fill_w = int((body_w - 2 * fill_margin) * percentage / 100)
    if fill_w > 0:
        fill_x1 = x + fill_margin
        fill_y1 = y + fill_margin
        fill_x2 = x + fill_margin + fill_w
        fill_y2 = y + icon_h - fill_margin
        draw.rounded_rectangle([fill_x1, fill_y1, fill_x2, fill_y2], radius=2, fill=fill_color)
    
    # Percentage text
    try:
        font = ImageFont.truetype(FONT_PATH, 10)
    except Exception:
        font = ImageFont.load_default()
    
    pct_text = f"{percentage}%"
    bbox = draw.textbbox((0, 0), pct_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Place text centered in the remaining space (left of battery icon)
    text_x = x - text_w - 6
    text_y = y + (icon_h - text_h) // 2
    draw.text((text_x, text_y), pct_text, font=font, fill="#FFFFFF")
    
    # Convert to RGB565 for LCD
    px = img.load()
    buf = bytearray()
    for py in range(height):
        for px_x in range(width):
            r, g, b = px[px_x, py]
            val = (((r >> 3) & 0x1F) << 11) | (((g >> 2) & 0x3F) << 5) | ((b >> 3) & 0x1F)
            buf.append((val >> 8) & 0xFF)
            buf.append(val & 0xFF)
    return bytes(buf)

if __name__ == "__main__":
    pct = None
    import sys
    if len(sys.argv) > 1:
        pct = int(sys.argv[1])
    raw = battery_icon(percentage=pct)
    sys.stdout.buffer.write(raw)
