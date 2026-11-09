#!/usr/bin/env python3
"""MP3 Converter - a simple local web app around tomp3.py.

Run it (or double-click "MP3 Converter" on the Desktop) and a page opens in
your browser: paste YouTube / Spotify links, press Convert.
"""
import html
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8765
URL = f"http://127.0.0.1:{PORT}"
CONFIG = os.path.expanduser("~/.tomp3.json")


def load_out():
    try:
        with open(CONFIG) as f:
            return json.load(f)["out"]
    except Exception:
        return os.path.expanduser("~/Music/tomp3")


def save_out(path):
    try:
        with open(CONFIG, "w") as f:
            json.dump({"out": path}, f)
    except OSError:
        pass


def choose_folder(current):
    """Show the macOS folder picker. Returns the chosen path, or None if cancelled."""
    start = current if os.path.isdir(current) else os.path.expanduser("~")
    script = [
        "-e", "activate",
        "-e", f'POSIX path of (choose folder with prompt "Save MP3s to:" '
              f'default location (POSIX file "{start.replace(chr(34), "")}"))',
    ]
    r = subprocess.run(["osascript", *script], capture_output=True, text=True)
    path = r.stdout.strip()
    if r.returncode != 0 or not path:
        return None  # cancelled
    return path.rstrip("/") or "/"


DEFAULT_OUT = load_out()

# Apps launched from Finder don't get the Terminal PATH, so add the tool folders.
os.environ["PATH"] = ":".join([
    "/opt/homebrew/bin", "/usr/local/bin", os.path.expanduser("~/.local/bin"),
    os.environ.get("PATH", ""),
])

state = {"running": False, "log": "", "done": False, "ok": None}
lock = threading.Lock()


def run_job(urls, quality, out):
    cmd = [sys.executable, os.path.join(HERE, "tomp3.py"), *urls, "-q", quality, "-o", out]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env={**os.environ, "TERM": "dumb"})
    for line in proc.stdout:
        with lock:
            state["log"] += line
    proc.wait()
    with lock:
        state.update(running=False, done=True, ok=(proc.returncode == 0))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MP3 Converter</title>
<style>
  :root { --bg:#f6f5f2; --card:#fff; --ink:#1d1d1f; --muted:#6e6e73; --line:#dedcd6;
          --accent:#1f7a4d; --accent-ink:#fff; --err:#b3261e; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#161616; --card:#212121; --ink:#f2f2f2; --muted:#a0a0a0; --line:#353535;
            --accent:#3fae74; --accent-ink:#0d1f15; --err:#ff8a80; }
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.5 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }
  main { max-width:640px; margin:48px auto; padding:0 16px; }
  h1 { font-size:28px; margin:0 0 4px; letter-spacing:-0.02em; }
  p.sub { color:var(--muted); margin:0 0 24px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px; }
  label { font-weight:600; font-size:14px; display:block; margin-bottom:6px; }
  textarea, input, select { width:100%; font:inherit; color:inherit; background:var(--bg);
         border:1px solid var(--line); border-radius:10px; padding:10px 12px; }
  textarea { min-height:120px; resize:vertical; }
  .row { display:flex; gap:12px; margin-top:16px; }
  .row > div { flex:1; }
  .row > div.q { flex:0 0 130px; }
  button { font:inherit; font-weight:600; border:0; border-radius:10px; padding:12px 18px; cursor:pointer; }
  #go { width:100%; margin-top:20px; background:var(--accent); color:var(--accent-ink); font-size:17px; }
  #go:disabled { opacity:.55; cursor:default; }
  .secondary { background:transparent; color:var(--ink); border:1px solid var(--line); }
  #status { margin:20px 0 8px; font-weight:600; min-height:1.5em; }
  #status.err { color:var(--err); }
  pre { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px;
        font:12px/1.45 ui-monospace, Menlo, monospace; color:var(--muted);
        max-height:260px; overflow:auto; white-space:pre-wrap; word-break:break-all; margin:0; }
  .actions { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
  .hint { color:var(--muted); font-size:13px; margin-top:6px; }
  .folder { display:flex; gap:8px; align-items:center; }
  .folder span { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
         direction:rtl; text-align:left; background:var(--bg); border:1px solid var(--line);
         border-radius:10px; padding:10px 12px; }
  .folder button { padding:10px 14px; white-space:nowrap; }
</style></head>
<body><main>
  <h1>MP3 Converter</h1>
  <p class="sub">Paste YouTube or Spotify links (songs, albums or playlists), then press Convert.</p>
  <div class="card">
    <label for="urls">Links</label>
    <textarea id="urls" placeholder="https://www.youtube.com/watch?v=...&#10;https://open.spotify.com/track/..."></textarea>
    <div class="hint">One link per line. You can paste several at once.</div>
    <div class="row">
      <div><label>Save to folder</label>
        <div class="folder"><span id="out" title="__OUT__">__OUT__</span>
        <button class="secondary" id="pick" type="button">Choose…</button></div></div>
      <div class="q"><label for="q">Quality</label>
        <select id="q"><option value="320">320 kbps</option><option value="256">256 kbps</option>
        <option value="192">192 kbps</option><option value="128">128 kbps</option></select></div>
    </div>
    <button id="go">Convert</button>
  </div>
  <div id="status"></div>
  <pre id="log" hidden></pre>
  <div class="actions">
    <button class="secondary" id="open">Open folder</button>
    <button class="secondary" id="quit">Quit app</button>
  </div>
<script>
const $ = id => document.getElementById(id);
let timer = null;
async function poll() {
  const s = await (await fetch('/status')).json();
  $('log').hidden = !s.log; $('log').textContent = s.log; $('log').scrollTop = 1e9;
  if (s.running) { $('status').className=''; $('status').textContent = 'Converting… this can take a minute per song.'; return; }
  clearInterval(timer); timer = null; $('go').disabled = false;
  if (s.done) {
    $('status').className = s.ok ? '' : 'err';
    $('status').textContent = s.ok ? 'Done! Your MP3s are in the folder.' : 'Some links failed — see the details below.';
  }
}
$('go').onclick = async () => {
  const urls = $('urls').value.split(/\\s+/).filter(Boolean);
  if (!urls.length) { $('status').className='err'; $('status').textContent='Paste at least one link first.'; return; }
  $('go').disabled = true;
  const r = await fetch('/convert', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({urls, quality:$('q').value, out:$('out').title})});
  if (!r.ok) { $('status').className='err'; $('status').textContent = await r.text(); $('go').disabled=false; return; }
  timer = setInterval(poll, 800); poll();
};
$('open').onclick = () => fetch('/open', {method:'POST', body: $('out').title});
$('pick').onclick = async () => {
  $('pick').disabled = true;
  const r = await fetch('/choose', {method:'POST', body: $('out').title});
  $('pick').disabled = false;
  if (r.status === 200) { const p = await r.text(); $('out').textContent = p; $('out').title = p; }
};
$('quit').onclick = async () => { await fetch('/quit', {method:'POST'}); document.body.innerHTML =
  '<main><h1>MP3 Converter closed</h1><p class="sub">You can close this tab.</p></main>'; };
poll();
</script>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n).decode() if n else ""

    def do_GET(self):
        if self.path == "/":
            self.send(200, PAGE.replace("__OUT__", html.escape(DEFAULT_OUT)), "text/html; charset=utf-8")
        elif self.path == "/status":
            with lock:
                self.send(200, json.dumps(state), "application/json")
        else:
            self.send(404, "not found")

    def do_POST(self):
        # Only accept requests from this app's own page.
        origin = self.headers.get("Origin")
        if origin and origin != URL:
            return self.send(403, "forbidden")
        if self.path == "/convert":
            req = json.loads(self.body() or "{}")
            urls = [u for u in req.get("urls", []) if u.startswith(("http", "spotify:"))]
            if not urls:
                return self.send(400, "Those don't look like links.")
            quality = req.get("quality") if req.get("quality") in ("128", "192", "256", "320") else "320"
            out = os.path.expanduser(req.get("out") or DEFAULT_OUT)
            with lock:
                if state["running"]:
                    return self.send(409, "Already converting — wait for it to finish.")
                state.update(running=True, done=False, ok=None, log="")
            threading.Thread(target=run_job, args=(urls, quality, out), daemon=True).start()
            self.send(200, "started")
        elif self.path == "/open":
            out = os.path.expanduser(self.body() or DEFAULT_OUT)
            os.makedirs(out, exist_ok=True)
            subprocess.Popen(["open", out])
            self.send(200, "ok")
        elif self.path == "/choose":
            path = choose_folder(self.body() or DEFAULT_OUT)
            if path:
                save_out(path)
                self.send(200, path)
            else:
                self.send(204, "")
        elif self.path == "/quit":
            self.send(200, "bye")
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send(404, "not found")


def main():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        webbrowser.open(URL)  # already running: just show it
        return
    threading.Timer(0.5, lambda: webbrowser.open(URL)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
