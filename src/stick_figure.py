import math

import numpy as np
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1080, 1920

_THEMES = {
    "male": {"top": (18, 20, 28), "bottom": (40, 28, 20), "accent": (255, 196, 120), "figure": (225, 225, 230)},
    "relationship": {"top": (30, 15, 25), "bottom": (58, 22, 36), "accent": (255, 170, 190), "figure": (230, 210, 220)},
    "growth": {"top": (15, 22, 25), "bottom": (42, 34, 14), "accent": (255, 210, 90), "figure": (235, 225, 200)},
    "resilience": {"top": (18, 24, 32), "bottom": (30, 42, 56), "accent": (255, 225, 140), "figure": (220, 225, 230)},
}

_COLOR_KEYWORDS = [
    ("gold", (222, 180, 80)),
    ("amber", (222, 180, 80)),
    ("blonde", (230, 210, 140)),
    ("dark grey", (90, 90, 100)),
    ("dark gray", (90, 90, 100)),
    ("charcoal", (80, 80, 88)),
    ("blue", (110, 150, 210)),
    ("red", (200, 90, 90)),
    ("white", (235, 235, 235)),
    ("black", (45, 45, 50)),
]


def _pick_theme(pillar: str) -> dict:
    text = (pillar or "").lower()
    if "male" in text:
        return _THEMES["male"]
    if "relationship" in text:
        return _THEMES["relationship"]
    if "growth" in text or "accountability" in text:
        return _THEMES["growth"]
    if "resilien" in text or "struggle" in text or "life" in text:
        return _THEMES["resilience"]
    return _THEMES["male"]


def _pick_color(character_visual: str, fallback: tuple) -> tuple:
    text = (character_visual or "").lower()
    for keyword, rgb in _COLOR_KEYWORDS:
        if keyword in text:
            return rgb
    return fallback


def _pick_style(animation_cue: str, character_visual: str) -> str:
    text = f"{animation_cue or ''} {character_visual or ''}".lower()
    if any(k in text for k in ("boulder", "weight", "backpack", "burden", "carry", "carrying")):
        return "carry"
    if any(k in text for k in ("couch", "split screen", "gap", "rift", "apart")):
        return "couch"
    if any(k in text for k in ("step", "climb", "stairs", "stone block", "uphill")):
        return "climb"
    if any(k in text for k in ("rain", "umbrella", "shield", "mirror")):
        return "shield"
    return "idle"


def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _background(theme: dict) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    top, bottom = theme["top"], theme["bottom"]
    for y in range(HEIGHT):
        color = _lerp_color(top, bottom, y / HEIGHT)
        for x in range(0, WIDTH, 4):  # coarse fill, upscaled below, keeps render fast
            px[x, y] = color
    return img.resize((WIDTH, HEIGHT), Image.NEAREST)


def _draw_glow(base: Image.Image, center, radius, color):
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i, r in enumerate(range(radius, 0, -max(1, radius // 6))):
        alpha = int(70 * (1 - i / 6))
        draw.ellipse(
            [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
            fill=(color[0], color[1], color[2], max(alpha, 0)),
        )
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _draw_figure(draw: ImageDraw.ImageDraw, cx, cy, scale, color, pose):
    width = max(4, int(scale * 0.035))
    hip = (cx, cy - scale * 0.45)
    lean_x = math.sin(pose["lean"]) * scale * 0.18
    neck = (hip[0] + lean_x, hip[1] - scale * 0.32)
    head_c = (neck[0] + lean_x * 0.4, neck[1] - scale * 0.12 + pose["head_bob"])
    head_r = scale * 0.09

    draw.line([hip, neck], fill=color, width=width)

    shoulder = neck
    for side, angle in (("l", pose["arm_l"]), ("r", pose["arm_r"])):
        ex = shoulder[0] + math.sin(angle) * scale * 0.32
        ey = shoulder[1] + math.cos(angle) * scale * 0.32
        draw.line([shoulder, (ex, ey)], fill=color, width=width)

    for side, angle in (("l", pose["leg_l"]), ("r", pose["leg_r"])):
        fx = hip[0] + math.sin(angle) * scale * 0.42
        fy = hip[1] + math.cos(angle) * scale * 0.42
        draw.line([hip, (fx, fy)], fill=color, width=width)

    draw.ellipse(
        [head_c[0] - head_r, head_c[1] - head_r, head_c[0] + head_r, head_c[1] + head_r],
        outline=color,
        width=width,
    )
    return head_c, neck


def _pose_idle(t):
    bob = math.sin(2 * math.pi * t * 3) * 6
    lean = math.sin(2 * math.pi * t * 1.5) * 0.06
    sway = math.sin(2 * math.pi * t * 1.5)
    return {
        "head_bob": bob,
        "lean": lean,
        "arm_l": -0.35 + 0.1 * sway,
        "arm_r": 0.35 - 0.1 * sway,
        "leg_l": -0.12,
        "leg_r": 0.12,
    }


def _pose_carry(t):
    step = math.sin(2 * math.pi * t * 2)
    return {
        "head_bob": abs(math.sin(2 * math.pi * t * 2)) * 5,
        "lean": 0.28,
        "arm_l": 1.1 + 0.15 * step,
        "arm_r": -1.1 - 0.15 * step,
        "leg_l": 0.3 * step,
        "leg_r": -0.3 * step,
    }


def _pose_climb(t):
    step = math.sin(2 * math.pi * t * 3)
    return {
        "head_bob": 0,
        "lean": 0.12,
        "arm_l": -0.6 - 0.3 * step,
        "arm_r": 0.6 + 0.3 * step,
        "leg_l": 0.5 * step,
        "leg_r": -0.5 * step,
    }


def _pose_shield(t):
    sway = math.sin(2 * math.pi * t * 1.2)
    return {
        "head_bob": sway * 4,
        "lean": 0.02 * sway,
        "arm_l": -2.2,
        "arm_r": 2.2,
        "leg_l": -0.1,
        "leg_r": 0.1,
    }


_POSE_FUNCS = {"idle": _pose_idle, "carry": _pose_carry, "climb": _pose_climb, "shield": _pose_shield}


def render_frames(duration_sec: float, fps: int, pillar: str, character_visual: str, animation_cue: str) -> list:
    theme = _pick_theme(pillar)
    color = _pick_color(character_visual, theme["figure"])
    style = _pick_style(animation_cue, character_visual)

    total_frames = max(1, int(round(duration_sec * fps)))
    frames = []
    has_heart = "heart" in f"{character_visual} {animation_cue}".lower()

    bg = _background(theme)

    for i in range(total_frames):
        t = i / total_frames
        frame = bg.copy()

        if style == "couch":
            frame = _render_couch_scene(frame, theme, color, t)
        else:
            cx, cy = WIDTH / 2, HEIGHT * 0.62
            scale = HEIGHT * 0.32

            if style == "climb":
                cx = WIDTH * (0.3 + 0.4 * t)
                cy = HEIGHT * (0.72 - 0.28 * t)
                _draw_steps(frame, theme["accent"])

            pose = _POSE_FUNCS[style](t)
            draw = ImageDraw.Draw(frame)

            if style == "shield":
                arc_box = [cx - scale * 0.55, cy - scale * 1.15, cx + scale * 0.55, cy - scale * 0.55]
                draw.arc(arc_box, start=200, end=340, fill=theme["accent"], width=max(4, int(scale * 0.03)))

            head_c, neck = _draw_figure(draw, cx, cy, scale, color, pose)

            if has_heart:
                heart_center = (neck[0], neck[1] + scale * 0.08)
                glow_r = int(scale * 0.09 + math.sin(2 * math.pi * t * 2) * scale * 0.015)
                frame = _draw_glow(frame, heart_center, glow_r, theme["accent"])

            if style == "carry":
                _draw_burden(frame, cx, cy, scale)

        frames.append(np.array(frame))

    return frames


def _draw_steps(frame: Image.Image, color):
    draw = ImageDraw.Draw(frame)
    for i in range(6):
        y = HEIGHT * (0.95 - i * 0.09)
        x0 = WIDTH * (0.15 + i * 0.06)
        draw.line([(x0, y), (x0 + WIDTH * 0.5, y)], fill=color, width=6)


def _draw_burden(frame: Image.Image, cx, cy, scale):
    draw = ImageDraw.Draw(frame)
    top = cy - scale * 0.95
    box = [cx - scale * 0.22, top - scale * 0.16, cx + scale * 0.22, top + scale * 0.1]
    draw.rounded_rectangle(box, radius=int(scale * 0.05), outline=(140, 140, 150), width=6)


def _render_couch_scene(frame: Image.Image, theme, color, t):
    draw = ImageDraw.Draw(frame)
    couch_y = HEIGHT * 0.68
    draw.line([(WIDTH * 0.1, couch_y), (WIDTH * 0.9, couch_y)], fill=(90, 70, 60), width=14)

    gap = 0.05 * math.sin(2 * math.pi * t * 0.8)
    left_x = WIDTH * (0.28 - gap)
    right_x = WIDTH * (0.72 + gap)
    scale = HEIGHT * 0.22

    for cx in (left_x, right_x):
        pose = _pose_idle(t)
        pose["leg_l"] = -0.05
        pose["leg_r"] = 0.05
        _draw_figure(draw, cx, couch_y, scale, color, pose)

    return frame
