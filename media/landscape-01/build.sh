#!/usr/bin/env bash
# Builds the film: frames (render.mjs) + each voice line at its scene's speaking time + a soft music bed + a whoosh on each cut.
# Usage: ./build.sh            (re-renders frames)   SKIP_FRAMES=1 ./build.sh   (re-mix audio only)
set -euo pipefail
cd "$(dirname "$0")"
FRAMES="${FRAMES:-${TMPDIR:-/tmp}/cl-landscape-01-frames}"
OUT="${OUT:-out}"; mkdir -p "$OUT" "$FRAMES"
PORT=8812; (curl -s -o /dev/null "http://127.0.0.1:$PORT/index.html") || { python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & sleep 1; }
if [ "${SKIP_FRAMES:-}" != "1" ]; then rm -f "$FRAMES"/f*.jpg; node render.mjs frames "$FRAMES" 30; fi
# audio: the same timeline arithmetic as index.html (LEAD, HOLD, CLOSE_HOLD)
python3 - "$OUT" <<'PY'
import json, subprocess, sys
S = json.load(open("script.json")); LEAD, HOLD, CLOSE = 0.45, 1.2, 3.6
t, inputs, filt, cuts = 0.0, [], [], []
for i, sc in enumerate(S["scenes"]):
    if i: cuts.append(t)
    start = t + LEAD
    inputs += ["-i", sc["audio"]]
    filt.append(f"[{i}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,adelay={int(start*1000)}|{int(start*1000)}[a{i}]")
    t += LEAD + sc["voice_s"] + (CLOSE if i == len(S["scenes"]) - 1 else HOLD)
n = len(S["scenes"])
voice = "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,volume=1.5,apad,atrim=0:{t:.3f}[v]"
# music bed: a slow A minor 9 pad (A2 E3 G3 B3 C4) with gentle movement, ducked under the voice
notes = [110.0, 164.81, 196.0, 246.94, 261.63]
pad = "+".join(f"{0.05 if k < 2 else 0.03}*sin(2*PI*{f}*t)*(0.75+0.25*sin(2*PI*{0.07 + k*0.03:.2f}*t))" for k, f in enumerate(notes))
bed = f"aevalsrc='{pad}':s=48000:d={t:.3f},lowpass=f=1800,afade=t=in:d=2,afade=t=out:st={t-3:.3f}:d=3,pan=stereo|c0=c0|c1=c0,volume=0.55[m]"
# whooshes: filtered noise swells centred on each cut
wh = [f"anoisesrc=d=0.6:c=pink:a=0.5,bandpass=f=1200:w=1600,afade=t=in:d=0.3,afade=t=out:st=0.3:d=0.3,volume=0.22,pan=stereo|c0=c0|c1=c0,adelay={int((c-0.3)*1000)}|{int((c-0.3)*1000)}[w{j}]" for j, c in enumerate(cuts)]
whmix = "".join(f"[w{j}]" for j in range(len(cuts))) + f"amix=inputs={len(cuts)}:normalize=0,apad,atrim=0:{t:.3f}[wh]"
duck = "[v]asplit=2[vk][vs];[m][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md]"
graph = ";".join(filt + [voice, bed, *wh, whmix, duck, "[vs][md][wh]amix=inputs=3:normalize=0,alimiter=limit=0.95[out]"])
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]", "-ac", "2", "-ar", "48000", f"{sys.argv[1]}/voice.wav"], check=True)
print(f"audio track {t:.2f}s, {len(cuts)} cuts")
PY
ffmpeg -y -loglevel error -framerate 30 -i "$FRAMES/f%05d.jpg" -i "$OUT/voice.wav" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/carbonledger-landscape-01.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT/carbonledger-landscape-01.mp4"
