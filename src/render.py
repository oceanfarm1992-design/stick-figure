import cv2
import numpy as np
from PIL import Image, ImageDraw

def render_graphics_overlay(frame: np.ndarray, text: str, progress: float) -> np.ndarray:
    h, w, _ = frame.shape
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    panel_y = int(h * 0.82)
    draw.rectangle([(20, panel_y), (w - 20, panel_y + 60)], fill=(0, 0, 0, 180))
    draw.text((35, panel_y + 20), text, fill=(255, 255, 255))
    bar_w = int((w - 40) * progress)
    draw.rectangle([(20, h - 15), (20 + bar_w, h - 5)], fill=(0, 255, 180))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def process_graphics_stage(frames: list, caption: str) -> list:
    return [render_graphics_overlay(f, caption, (i + 1) / len(frames)) for i, f in enumerate(frames)]
