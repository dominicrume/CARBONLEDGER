#!/usr/bin/env bash
# Builds the short: frames (render.mjs) + each voice line placed at its scene's speaking time + a soft room tone.
# Usage: ./build.sh            (re-renders frames)   SKIP_FRAMES=1 ./build.sh   (re-mix audio only)
set -euo pipefail
cd "$(dirname "$0")"
FRAMES="${FRAMES:-${TMPDIR:-/tmp}/cl-short-01-frames}"
OUT="${OUT:-out}"; mkdir -p "$OUT" "$FRAMES"
PORT=8811; (curl -s -o /dev/null "http://127.0.0.1:$PORT/index.html") || { python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & sleep 1; }
if [ "${SKIP_FRAMES:-}" != "1" ]; then rm -f "$FRAMES"/f*.jpg; node render.mjs frames "$FRAMES" 30; fi
# voice timeline: the same arithmetic as index.html (LEAD, HOLD, CLOSE_HOLD)
python3 - "$OUT" <<'PY'
import json, subprocess, sys
S = json.load(open("script.json")); LEAD, HOLD, CLOSE = 0.45, 1.6, 3.4
t, inputs, filt = 0.0, [], []
for i, sc in enumerate(S["scenes"]):
    start = t + LEAD
    inputs += ["-i", sc.get("audio", f"audio/{sc['id']}.aiff")]
    filt.append(f"[{i}:a]aresample=48000,adelay={int(start*1000)}|{int(start*1000)}[a{i}]")
    t += LEAD + sc["voice_s"] + (CLOSE if i == len(S["scenes"]) - 1 else HOLD)
n = len(S["scenes"])
mix = "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,volume=1.6,apad,atrim=0:{t:.3f}[v]"
tone = f"anoisesrc=d={t:.3f}:c=brown:a=0.012,lowpass=f=400,aresample=48000[n]"
cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={t:.3f}",
       "-filter_complex", ";".join(filt) + ";" + mix + f";{tone};[v][n]amix=inputs=2:normalize=0[out]", "-map", "[out]", "-ac", "2", "-ar", "48000", f"{sys.argv[1]}/voice.wav"]
subprocess.run(cmd, check=True); print(f"voice track {t:.2f}s")
PY
ffmpeg -y -loglevel error -framerate 30 -i "$FRAMES/f%05d.jpg" -i "$OUT/voice.wav" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/carbonledger-short-01.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT/carbonledger-short-01.mp4"
