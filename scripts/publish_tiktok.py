"""Upload a video to TikTok via the Content Posting API (direct post).

Required environment variables (set as GitHub Secrets):
  TIKTOK_ACCESS_TOKEN
    -> from a TikTok for Developers app with the video.publish scope,
       approved for the Content Posting API and authorized for your account.
       (TikTok requires app review before direct posting works outside audit mode.)
"""
import argparse
import os
import sys

import requests

REQUIRED_ENV = ["TIKTOK_ACCESS_TOKEN"]
API_BASE = "https://open.tiktokapis.com/v2"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--title", default="")
    args = parser.parse_args()

    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"Skipping TikTok upload, missing secrets: {', '.join(missing)}")
        sys.exit(0)

    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    file_size = os.path.getsize(args.file)
    init_body = {
        "post_info": {"title": args.title[:150], "privacy_level": "SELF_ONLY"},
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }
    init_resp = requests.post(
        f"{API_BASE}/post/publish/video/init/", headers=headers, json=init_body, timeout=60
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()["data"]

    with open(args.file, "rb") as f:
        upload_resp = requests.put(
            init_data["upload_url"],
            headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"},
            data=f,
            timeout=600,
        )
    upload_resp.raise_for_status()

    print(f"Uploaded, publish_id: {init_data['publish_id']} (review it under TikTok Studio > Drafts)")


if __name__ == "__main__":
    main()
