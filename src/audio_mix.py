import glob
import os

from moviepy import AudioFileClip, CompositeAudioClip
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, AudioLoop, MultiplyVolume

MUSIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
MUSIC_VOLUME_DB = -20  # narration stays at 0 dB; background music sits well under it

_PILLAR_KEYWORDS = {
    "male": ("male",),
    "relationship": ("relationship",),
    "growth": ("growth", "accountability"),
    "resilience": ("resilien", "struggle", "life"),
}


def _find_track(pillar: str):
    if not os.path.isdir(MUSIC_DIR):
        return None

    text = (pillar or "").lower()
    keywords = next((kws for kws in _PILLAR_KEYWORDS.values() if any(k in text for k in kws)), ())

    candidates = glob.glob(os.path.join(MUSIC_DIR, "*"))
    for keyword in keywords:
        for path in candidates:
            if keyword in os.path.basename(path).lower():
                return path
    return None


def mix_with_narration(narration: AudioFileClip, pillar: str):
    """Layer pillar-matched background music under the narration, if a track is present
    in assets/audio/ (filenames should contain a pillar keyword, e.g. "male_ambient.mp3").
    Returns `narration` unchanged if no matching track is found.
    """
    track_path = _find_track(pillar)
    if not track_path:
        return narration

    duration = narration.duration
    music = AudioFileClip(track_path)

    if music.duration < duration:
        music = music.with_effects([AudioLoop(duration=duration)])
    else:
        music = music.subclipped(0, duration)

    volume_factor = 10 ** (MUSIC_VOLUME_DB / 20)
    music = music.with_effects(
        [MultiplyVolume(volume_factor), AudioFadeIn(1.0), AudioFadeOut(1.0)]
    )

    return CompositeAudioClip([music, narration])
