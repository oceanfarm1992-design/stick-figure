import asyncio

import edge_tts

DEFAULT_VOICE = "en-US-GuyNeural"  # deep male narrator, matches the content pillars' voice direction


async def _synthesize_async(text: str, out_path: str, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    word_timings = []

    with open(out_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append(
                    {
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,  # 100-ns units -> seconds
                        "duration": chunk["duration"] / 10_000_000,
                    }
                )

    return word_timings


def synthesize(text: str, out_path: str, voice: str = DEFAULT_VOICE) -> list:
    """Generate narration audio for `text`, saved to `out_path` (mp3).

    Returns a list of {text, start, duration} word timings in seconds,
    used to sync burned-in captions to the voiceover.
    """
    return asyncio.run(_synthesize_async(text, out_path, voice))
