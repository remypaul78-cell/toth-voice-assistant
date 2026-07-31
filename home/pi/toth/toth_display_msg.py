#!/usr/bin/env python3
"""Affiche un message sur l'écran LCD de Toth (240x280, fond violet, texte jaune).
Usage: python3 toth_display_msg.py "Mon message ici" [taille_police]
"""
import sys, os
sys.path.insert(0, "/home/pi/whisplay/runtime")
from PIL import Image, ImageDraw, ImageFont
from whisplay import WhisplayBoard

FONT_PATH = "/usr/share/fonts/truetype/montserrat/Montserrat-Black.ttf"
BG = "#2D004B"   # violet sombre
FG = "#FFFF00"   # jaune vif

def pil_to_rgb565(img):
    px = img.load()
    buf = bytearray()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            val = (((r >> 3) & 0x1F) << 11) | (((g >> 2) & 0x3F) << 5) | ((b >> 3) & 0x1F)
            buf.append((val >> 8) & 0xFF)
            buf.append(val & 0xFF)
    return bytes(buf)

def display_message(text, font_size=22):
    img = Image.new("RGB", (240, 280), BG)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Word wrap
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        t = (cur + " " + w).strip() if cur else w
        b = draw.textbbox((0, 0), t, font=font)
        if (b[2] - b[0]) > 224:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)

    # Center vertically
    line_h = font_size + 4
    total_h = len(lines) * line_h
    y_start = max(8, (280 - total_h) // 2)

    y = y_start
    for line in lines[:12]:
        draw.text((8, y), line, font=font, fill=FG)
        y += line_h

    data = pil_to_rgb565(img)

    # Init board and draw
    board = WhisplayBoard()
    board.draw_image(0, 0, 240, 280, data)
    board.cleanup()
    print(f"[OK] Affiché: {text[:60]}")

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Toth prêt."
    fs = int(sys.argv[2]) if len(sys.argv) > 2 else 22
    display_message(text, fs)
