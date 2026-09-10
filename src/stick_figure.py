import math

import numpy as np
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1080, 1920
INK = (25, 25, 25)
PAPER = (255, 255, 255)


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
    return "walk"


def _pick_emotion(pillar: str) -> str:
    text = (pillar or "").lower()
    if "growth" in text or "accountability" in text:
        return "determined"
    if "resilien" in text or "struggle" in text or "life" in text:
        return "neutral"
    return "worried"  # male perspective / relationship pillars default to this


def _point(origin, angle, length):
    return (origin[0] + math.sin(angle) * length, origin[1] + math.cos(angle) * length)


def _draw_limb(draw, origin, angle, bend, upper, lower, width):
    joint = _point(origin, angle, upper)
    end = _point(joint, angle + bend, lower)
    draw.line([origin, joint], fill=INK, width=width)
    draw.line([joint, end], fill=INK, width=width)
    return end


def _draw_face(draw, head_c, head_r, emotion):
    eye_dx = head_r * 0.35
    eye_y = head_c[1] - head_r * 0.05
    eye_r = max(2, head_r * 0.07)

    for side in (-1, 1):
        ex = head_c[0] + side * eye_dx
        draw.ellipse([ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r], fill=INK)

        brow_y = eye_y - head_r * 0.32
        if emotion == "worried":
            inner = (ex - side * head_r * 0.18, brow_y - head_r * 0.1)
            outer = (ex + side * head_r * 0.22, brow_y + head_r * 0.12)
        elif emotion == "determined":
            inner = (ex - side * head_r * 0.18, brow_y - head_r * 0.05)
            outer = (ex + side * head_r * 0.22, brow_y + head_r * 0.1)
        else:
            inner = (ex - side * head_r * 0.2, brow_y)
            outer = (ex + side * head_r * 0.2, brow_y)
        draw.line([inner, outer], fill=INK, width=max(2, int(head_r * 0.06)))

    mouth_y = head_c[1] + head_r * 0.42
    mw = head_r * 0.32
    if emotion == "worried":
        pts = [(head_c[0] - mw, mouth_y - head_r * 0.08), (head_c[0], mouth_y + head_r * 0.1), (head_c[0] + mw, mouth_y - head_r * 0.08)]
    elif emotion == "determined":
        pts = [(head_c[0] - mw, mouth_y), (head_c[0] + mw, mouth_y)]
    else:
        pts = [(head_c[0] - mw, mouth_y), (head_c[0], mouth_y + head_r * 0.04), (head_c[0] + mw, mouth_y)]
    draw.line(pts, fill=INK, width=max(2, int(head_r * 0.05)))


def _draw_figure(draw, cx, cy, scale, pose, emotion):
    width = max(5, int(scale * 0.022))
    hip = (cx, cy - scale * 0.45)
    lean_x = math.sin(pose["lean"]) * scale * 0.15
    neck = (hip[0] + lean_x, hip[1] - scale * 0.32)
    head_c = (neck[0] + lean_x * 0.4, neck[1] - scale * 0.13 + pose["head_bob"])
    head_r = scale * 0.09

    draw.line([hip, neck], fill=INK, width=width)

    _draw_limb(draw, neck, pose["arm_l"], pose["arm_l_bend"], scale * 0.19, scale * 0.17, width)
    _draw_limb(draw, neck, pose["arm_r"], pose["arm_r_bend"], scale * 0.19, scale * 0.17, width)
    foot_l = _draw_limb(draw, hip, pose["leg_l"], pose["leg_l_bend"], scale * 0.23, scale * 0.22, width)
    foot_r = _draw_limb(draw, hip, pose["leg_r"], pose["leg_r_bend"], scale * 0.23, scale * 0.22, width)

    draw.ellipse(
        [head_c[0] - head_r, head_c[1] - head_r, head_c[0] + head_r, head_c[1] + head_r],
        outline=INK,
        width=width,
    )
    _draw_face(draw, head_c, head_r, emotion)

    return {"head": head_c, "head_r": head_r, "neck": neck, "hip": hip, "feet": (foot_l, foot_r)}


def _pose_walk(t):
    stride = math.sin(2 * math.pi * t * 1.6)
    return {
        "head_bob": abs(stride) * 4,
        "lean": 0.05,
        "arm_l": -0.5 * stride, "arm_l_bend": 0.3,
        "arm_r": 0.5 * stride, "arm_r_bend": 0.3,
        "leg_l": 0.5 * stride, "leg_l_bend": -0.4 * max(0, -stride),
        "leg_r": -0.5 * stride, "leg_r_bend": -0.4 * max(0, stride),
    }


def _pose_carry(t):
    stride = math.sin(2 * math.pi * t * 1.1)
    return {
        "head_bob": abs(stride) * 3,
        "lean": 0.32,
        "arm_l": 0.55, "arm_l_bend": 0.35,
        "arm_r": -0.2, "arm_r_bend": -0.15,
        "leg_l": 0.3 * stride, "leg_l_bend": -0.3 * max(0, -stride),
        "leg_r": -0.3 * stride, "leg_r_bend": -0.3 * max(0, stride),
    }


def _pose_climb(t):
    stride = math.sin(2 * math.pi * t * 2.2)
    return {
        "head_bob": 0,
        "lean": 0.15,
        "arm_l": -0.8 - 0.3 * stride, "arm_l_bend": 0.5,
        "arm_r": 0.8 + 0.3 * stride, "arm_r_bend": -0.5,
        "leg_l": 0.7 * stride, "leg_l_bend": -0.6,
        "leg_r": -0.7 * stride, "leg_r_bend": -0.6,
    }


def _pose_shield(t):
    sway = math.sin(2 * math.pi * t * 1.0)
    return {
        "head_bob": sway * 3,
        "lean": 0.02 * sway,
        "arm_l": -2.3, "arm_l_bend": 0.6,
        "arm_r": 2.3, "arm_r_bend": -0.6,
        "leg_l": -0.08, "leg_l_bend": 0,
        "leg_r": 0.08, "leg_r_bend": 0,
    }


def _pose_idle(t):
    sway = math.sin(2 * math.pi * t * 1.3)
    return {
        "head_bob": sway * 3,
        "lean": 0.03 * sway,
        "arm_l": -0.2, "arm_l_bend": 0.15,
        "arm_r": 0.2, "arm_r_bend": -0.15,
        "leg_l": -0.06, "leg_l_bend": 0,
        "leg_r": 0.06, "leg_r_bend": 0,
    }


_POSE_FUNCS = {"walk": _pose_walk, "carry": _pose_carry, "climb": _pose_climb, "shield": _pose_shield}


def _draw_road(draw, base_y):
    points = []
    for x in range(-50, WIDTH + 60, 20):
        y = base_y + math.sin(x / WIDTH * 3.4 + 0.6) * HEIGHT * 0.05
        points.append((x, y))
    draw.line(points, fill=INK, width=6, joint="curve")


def _draw_steps(draw):
    for i in range(6):
        y = HEIGHT * (0.95 - i * 0.09)
        x0 = WIDTH * (0.15 + i * 0.06)
        draw.line([(x0, y), (x0 + WIDTH * 0.5, y)], fill=INK, width=6)


def _draw_heart(draw, center, size):
    x, y = center
    r = size * 0.55
    draw.ellipse([x - r * 1.5, y - r, x - r * 0.1, y + r * 0.7], outline=INK, width=4)
    draw.ellipse([x + r * 0.1, y - r, x + r * 1.5, y + r * 0.7], outline=INK, width=4)
    draw.polygon([(x - r * 1.5, y + r * 0.25), (x + r * 1.5, y + r * 0.25), (x, y + r * 1.9)], outline=INK, width=4)


def _draw_burden(draw, parts, scale):
    neck = parts["neck"]
    r = scale * 0.13
    boulder_c = (neck[0] + scale * 0.34, neck[1] - scale * 0.02)
    draw.ellipse([boulder_c[0] - r, boulder_c[1] - r, boulder_c[0] + r, boulder_c[1] + r], outline=INK, width=5)
    draw.line([neck, (boulder_c[0] - r * 0.6, boulder_c[1] + r * 0.6)], fill=INK, width=4)


def render_frames(duration_sec: float, fps: int, pillar: str, character_visual: str, animation_cue: str) -> list:
    style = _pick_style(animation_cue, character_visual)
    emotion = _pick_emotion(pillar)
    has_heart = "heart" in f"{character_visual} {animation_cue}".lower()

    total_frames = max(1, int(round(duration_sec * fps)))
    cx, cy = WIDTH / 2, HEIGHT * 0.62
    scale = HEIGHT * 0.32

    base = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    base_draw = ImageDraw.Draw(base)
    if style == "climb":
        _draw_steps(base_draw)
    elif style == "couch":
        base_draw.line([(WIDTH * 0.1, HEIGHT * 0.68), (WIDTH * 0.9, HEIGHT * 0.68)], fill=INK, width=8)
    else:
        _draw_road(base_draw, cy + scale * 0.42)

    frames = []
    for i in range(total_frames):
        t = i / total_frames
        frame = base.copy()
        draw = ImageDraw.Draw(frame)

        if style == "couch":
            gap = 0.05 * math.sin(2 * math.pi * t * 0.8)
            for fx in (WIDTH * (0.28 - gap), WIDTH * (0.72 + gap)):
                _draw_figure(draw, fx, HEIGHT * 0.68, HEIGHT * 0.22, _pose_idle(t), emotion)
        else:
            fx, fy = cx, cy
            if style == "climb":
                fx = WIDTH * (0.3 + 0.4 * t)
                fy = HEIGHT * (0.72 - 0.28 * t)

            if style == "shield":
                arc_box = [fx - scale * 0.55, fy - scale * 1.15, fx + scale * 0.55, fy - scale * 0.55]
                draw.arc(arc_box, start=200, end=340, fill=INK, width=6)

            pose = _POSE_FUNCS[style](t)
            parts = _draw_figure(draw, fx, fy, scale, pose, emotion)

            if style == "carry":
                _draw_burden(draw, parts, scale)
            if has_heart:
                pulse = scale * 0.09 + math.sin(2 * math.pi * t * 2) * scale * 0.01
                _draw_heart(draw, (parts["neck"][0], parts["neck"][1] + scale * 0.1), pulse)

        frames.append(np.array(frame))

    return frames
