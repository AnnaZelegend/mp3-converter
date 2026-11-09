#!/bin/bash
# MP3 Converter installer for macOS.
# Usage:  curl -fsSL https://raw.githubusercontent.com/AnnaZelegend/mp3-converter/main/install.sh | bash
set -e

REPO="https://github.com/AnnaZelegend/mp3-converter.git"
DIR="$HOME/mp3-converter"
APP="$HOME/Desktop/MP3 Converter.app"

if [ "$(uname)" != "Darwin" ]; then
  echo "This installer is for macOS only." >&2; exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is needed first. Install it from https://brew.sh, then run this again." >&2; exit 1
fi

echo "==> Installing ffmpeg, yt-dlp and pipx (this can take a few minutes)..."
brew install ffmpeg yt-dlp pipx git

echo "==> Installing spotdl..."
pipx install spotdl || pipx upgrade spotdl
pipx ensurepath >/dev/null

echo "==> Downloading MP3 Converter to $DIR..."
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only
else
  git clone "$REPO" "$DIR"
fi

echo "==> Creating the app on your Desktop..."
rm -rf "$APP"
osacompile -o "$APP" -e "do shell script \"nohup /usr/bin/python3 '$DIR/app.py' > /tmp/mp3-converter.log 2>&1 &\""

echo
echo "Done! Double-click \"MP3 Converter\" on your Desktop to start."
