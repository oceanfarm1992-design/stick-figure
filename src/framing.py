import cv2

def calculate_crop_box(center: tuple, orig_dim: tuple, target_aspect: float = 9/16):
    orig_w, orig_h = orig_dim
    cx, cy = center
    target_h = orig_h
    target_w = int(target_h * target_aspect)
    if target_w > orig_w:
        target_w = orig_w
        target_h = int(target_w / target_aspect)
    x1 = max(0, min(cx - target_w // 2, orig_w - target_w))
    y1 = max(0, min(cy - target_h // 2, orig_h - target_h))
    return int(x1), int(y1), int(target_w), int(target_h)

def apply_dynamic_framing(frames: list, centers: list, target_aspect: float = 9/16):
    framed_frames = []
    for frame, center in zip(frames, centers):
        h, w, _ = frame.shape
        x, y, crop_w, crop_h = calculate_crop_box(center, (w, h), target_aspect)
        framed_frames.append(frame[y:y+crop_h, x:x+crop_w])
    return framed_frames
