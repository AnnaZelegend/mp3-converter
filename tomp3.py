#!/usr/bin/env python3
"""tomp3 - convert YouTube / Spotify links to MP3 files.

YouTube:  downloads the audio with yt-dlp and converts it to MP3 (ffmpeg).
Spotify:  Spotify audio is DRM-protected, so spotdl reads the track/album/
          playlist metadata from Spotify, finds the matching song on YouTube,
          and saves it as an MP3 with the Spotify tags and cover art.

Usage:
  tomp3 <url> [<url> ...] [-o OUTPUT_DIR] [-q BITRATE]
  tomp3                     # interactive: paste links one per line

For personal use with content you have the right to download.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

DEFAULT_OUT = os.path.expanduser("~/Music/tomp3")

YOUTUBE_RE = re.compile(r"(youtube\.com|youtu\.be|music\.youtube\.com)", re.I)
SPOTIFY_RE = re.compile(r"(open\.spotify\.com|spotify:)", re.I)


def need(tool):
    if shutil.which(tool) is None:
        sys.exit(f"error: '{tool}' is not installed. Run:  brew install ffmpeg yt-dlp pipx && pipx install spotdl")


def youtube(url, out, bitrate):
    need("yt-dlp")
    need("ffmpeg")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", f"{bitrate}K",
        "--embed-thumbnail",
        "--embed-metadata",
        "--no-overwrites",
        "-o", os.path.join(out, "%(title)s.%(ext)s"),
        url,
    ]
    return subprocess.call(cmd)


def spotify(url, out, bitrate):
    need("spotdl")
    need("ffmpeg")
    cmd = [
        "spotdl", "download", url,
        "--output", os.path.join(out, "{artists} - {title}.{output-ext}"),
        "--format", "mp3",
        "--bitrate", f"{bitrate}k",
        "--overwrite", "skip",
    ]
    return subprocess.call(cmd)


def convert(url, out, bitrate):
    url = url.strip()
    if not url:
        return 0
    if SPOTIFY_RE.search(url):
        print(f"\n[spotify] {url}")
        return spotify(url, out, bitrate)
    if YOUTUBE_RE.search(url):
        print(f"\n[youtube] {url}")
        return youtube(url, out, bitrate)
    print(f"skipping (not a YouTube or Spotify link): {url}", file=sys.stderr)
    return 1


def main():
    p = argparse.ArgumentParser(description="Convert YouTube / Spotify links to MP3.")
    p.add_argument("urls", nargs="*", help="YouTube or Spotify links (tracks, albums, playlists)")
    p.add_argument("-o", "--output", default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT})")
    p.add_argument("-q", "--quality", default="320", choices=["128", "192", "256", "320"],
                   help="MP3 bitrate in kbps (default: 320)")
    args = p.parse_args()

    urls = args.urls
    if not urls:
        print("Paste YouTube/Spotify links, one per line. Empty line to start:")
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break
            if not line:
                break
            urls.append(line)
    if not urls:
        p.print_help()
        return 1

    out = os.path.expanduser(args.output)
    os.makedirs(out, exist_ok=True)

    failed = [u for u in urls if convert(u, out, args.quality) != 0]
    print(f"\nDone. {len(urls) - len(failed)}/{len(urls)} succeeded. Files are in: {out}")
    for u in failed:
        print(f"  failed: {u}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
