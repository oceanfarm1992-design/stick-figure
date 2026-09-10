import cv2

def build_video_container(frames: list, output_path: str, fps: int = 30):
    if not frames: raise ValueError("No frames provided.")
    h, w, _ = frames[0].shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    for frame in frames: out.write(frame)
    out.release()
    print(f"Video created: {output_path}")
