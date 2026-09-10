import argparse
import os
import sys
import tempfile

from moviepy import AudioFileClip, ImageSequenceClip

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import captions
import database
import stick_figure
import tts

FPS = 30


def generate_one(row: dict, out_dir: str, voice: str) -> str:
    video_id = row["id"]
    print(f"[{video_id}] synthesizing narration...")

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = os.path.join(tmp, f"{video_id}.mp3")
        word_timings = tts.synthesize(row["full_text"], audio_path, voice=voice)

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        print(f"[{video_id}] rendering {duration:.1f}s of stick-figure animation...")
        frames = stick_figure.render_frames(
            duration_sec=duration,
            fps=FPS,
            pillar=row["pillar"],
            character_visual=row["character_visual"],
            animation_cue=row["animation_cue"],
        )

        print(f"[{video_id}] burning captions...")
        frames = captions.burn_captions(frames, word_timings, FPS)

        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{video_id}.mp4")

        video_clip = ImageSequenceClip(frames, fps=FPS).with_audio(audio_clip)
        video_clip.write_videofile(out_path, codec="libx264", audio_codec="aac", fps=FPS, logger=None)

        audio_clip.close()
        video_clip.close()

    print(f"[{video_id}] done -> {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate stick-figure narration videos from the script database.")
    parser.add_argument("--db", required=True, help="Path to the .xlsx script database.")
    parser.add_argument("--id", help="Single Video ID to generate (e.g. VID-00001).")
    parser.add_argument("--start-id", help="First Video ID to generate when batching.")
    parser.add_argument("--count", type=int, default=1, help="How many rows to generate when batching.")
    parser.add_argument("--out-dir", default="output", help="Directory to write .mp4 files to.")
    parser.add_argument("--voice", default=tts.DEFAULT_VOICE, help="edge-tts voice name.")
    args = parser.parse_args()

    if args.id:
        row = database.load_row(args.db, args.id)
        generate_one(row, args.out_dir, args.voice)
    else:
        rows = list(database.iter_rows(args.db, start_id=args.start_id, count=args.count))
        if not rows:
            print("No rows found for the given range.", file=sys.stderr)
            sys.exit(1)
        for row in rows:
            generate_one(row, args.out_dir, args.voice)


if __name__ == "__main__":
    main()
