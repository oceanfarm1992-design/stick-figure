import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_SIZE = 58


def _load_font():
    for path in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, _FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default(size=_FONT_SIZE)


def _group_words(word_timings, max_words=4, max_gap=0.6):
    groups, current = [], []
    for w in word_timings:
        if not w.get("text", "").strip():
            continue
        if current and (
            len(current) >= max_words
            or w["start"] - (current[-1]["start"] + current[-1]["duration"]) > max_gap
        ):
            groups.append(current)
            current = []
        current.append(w)
    if current:
        groups.append(current)
    return groups


def burn_captions(frames: list, word_timings: list, fps: int) -> list:
    if not word_timings:
        return frames

    groups = _group_words(word_timings)
    spans = [
        {
            "text": " ".join(w["text"] for w in g).strip(),
            "start": g[0]["start"],
            "end": g[-1]["start"] + g[-1]["duration"] + 0.15,
        }
        for g in groups
    ]

    font = _load_font()
    height, width = frames[0].shape[0], frames[0].shape[1]
    span_idx = 0
    out = []

    for i, frame in enumerate(frames):
        t = i / fps
        while span_idx < len(spans) - 1 and t > spans[span_idx]["end"]:
            span_idx += 1

        span = spans[span_idx]
        img = Image.fromarray(frame)
        if span["start"] <= t <= span["end"]:
            _draw_caption(img, span["text"], font, width, height)
        out.append(np.array(img))

    return out


def _draw_caption(img: Image.Image, text: str, font, width, height):
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    cx, cy = width / 2, height * 0.78
    pad_x, pad_y = 28, 18
    box = [cx - text_w / 2 - pad_x, cy - text_h / 2 - pad_y, cx + text_w / 2 + pad_x, cy + text_h / 2 + pad_y]
    draw.rounded_rectangle(box, radius=14, fill=(255, 214, 0))
    draw.text((cx - text_w / 2, cy - text_h / 2 - bbox[1]), text, font=font, fill=(20, 20, 20))
