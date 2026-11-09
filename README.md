# MP3 Converter

Paste a YouTube or Spotify link, press **Convert**, and get an MP3 with the song title, artist and cover art.

Website: https://annazelegend.github.io/mp3-converter/

## Install (macOS)

You need [Homebrew](https://brew.sh). Then paste this into Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/AnnaZelegend/mp3-converter/main/install.sh | bash
```

An **MP3 Converter** app appears on your Desktop. Double-click it and the converter opens in your browser.

## How it works

- **YouTube:** the audio is downloaded with [yt-dlp](https://github.com/yt-dlp/yt-dlp) and converted to MP3 with ffmpeg.
- **Spotify:** Spotify's audio is copy-protected, so [spotDL](https://github.com/spotDL/spotify-downloader) reads the song details from Spotify and downloads the matching song from YouTube Music.

Everything runs on your own computer. Nothing is uploaded anywhere.

There is also a command-line version: `python3 tomp3.py <link> [-o folder] [-q 320]`.

## Updating

Run the install command again. If downloads start failing, run `brew upgrade yt-dlp`.

For personal use only. Downloading may go against YouTube's and Spotify's terms of service.
