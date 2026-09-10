"""Upload a video to a Facebook Page as a Reel.

Required environment variables (set as GitHub Secrets):
  FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN
    -> from a Meta app with the pages_manage_posts / publish_video permissions,
       generated for the target Page via the Graph API Explorer or a server-side OAuth flow.
"""
import argparse
import os
import sys

import requests

REQUIRED_ENV = ["FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"]
GRAPH_VERSION = "v19.0"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--description", default="")
    args = parser.parse_args()

    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"Skipping Facebook upload, missing secrets: {', '.join(missing)}")
        sys.exit(0)

    page_id = os.environ["FACEBOOK_PAGE_ID"]
    token = os.environ["FACEBOOK_PAGE_ACCESS_TOKEN"]

    url = f"https://graph-video.facebook.com/{GRAPH_VERSION}/{page_id}/videos"
    with open(args.file, "rb") as f:
        response = requests.post(
            url,
            data={"access_token": token, "description": args.description},
            files={"source": f},
            timeout=600,
        )

    response.raise_for_status()
    data = response.json()
    print(f"Uploaded: https://facebook.com/{data.get('id')}")


if __name__ == "__main__":
    main()
