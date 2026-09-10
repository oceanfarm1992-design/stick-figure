import numpy as np
from PIL import Image


def apply_climax_zoom(frames: list, max_zoom: float = 0.08) -> list:
    """Slow zoom-in across the clip (Ken Burns style) so intensity builds
    toward the end, per the 'camera dynamics' direction for emotional climaxes.
    """
    n = len(frames)
    if n <= 1:
        return frames

    h, w = frames[0].shape[:2]
    out = []
    for i, frame in enumerate(frames):
        t = i / (n - 1)
        zoom = 1 + max_zoom * t
        crop_w, crop_h = w / zoom, h / zoom
        x0, y0 = (w - crop_w) / 2, (h - crop_h) / 2
        img = Image.fromarray(frame).crop((x0, y0, x0 + crop_w, y0 + crop_h)).resize((w, h), Image.BILINEAR)
        out.append(np.array(img))

    return out
