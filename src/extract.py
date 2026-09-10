import cv2
import numpy as np

def extract_frames_and_motion(video_path: str):
    cap = cv2.VideoCapture(video_path)
    frames, centers = [], []
    backSub = cv2.createBackgroundSubtractorMOG2()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        fg_mask = backSub.apply(frame)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest)
            cx = int(M["m10"]/M["m00"]) if M["m00"] != 0 else frame.shape[1] // 2
            cy = int(M["m01"]/M["m00"]) if M["m00"] != 0 else frame.shape[0] // 2
            centers.append((cx, cy))
        else:
            centers.append((frame.shape[1] // 2, frame.shape[0] // 2))
        frames.append(frame)
    cap.release()
    return frames, centers
