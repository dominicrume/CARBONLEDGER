#!/usr/bin/env bash
# Frames in 8 parallel parts, then the mix: finished voice at each beat's speaking time, the bed ducked under it,
# loudness to -14 LUFS like the VOREM references, captions as .srt, the mp4.  SKIP_FRAMES=1 ./build.sh re-mixes only.
set -euo pipefail
cd "$(dirname "$0")"
FRAMES="${FRAMES:-${TMPDIR:-/tmp}/video-kit-frames}"; FPS=30; mkdir -p "$FRAMES" out
(curl -s -o /dev/null http://127.0.0.1:8822/stage.html) || { (python3 -m http.server 8822 --bind 127.0.0.1 >/dev/null 2>&1 &); sleep 1; }
if [ "${SKIP_FRAMES:-}" != "1" ]; then
  rm -f "$FRAMES"/f*.jpg
  for p in 0 1 2 3 4 5 6 7; do node render.mjs frames "$FRAMES" $FPS $p 8 & done; wait
fi
python3 - <<'PY'
import json, subprocess
F = json.load(open("film.json")); ins, filt, srt = [], [], []
fmt = lambda s: f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(round(s%1*1000)):03d}"
for i, b in enumerate(F["beats"]):
    ins += ["-i", b["audio"]]; ms = int(b["speak"] * 1000)
    filt.append(f"[{i}:a]aresample=48000,adelay={ms}[v{i}]")
    ws, cur = b["words"], []
    for j, w in enumerate(ws):                                    # .srt in readable lines of up to 8 words
        cur.append(w)
        if len(cur) >= 8 or w[2][-1] in ".?!:" or j == len(ws) - 1:
            srt.append(f"{len(srt)+1}\n{fmt(b['speak'] + cur[0][0])} --> {fmt(b['speak'] + cur[-1][1] + .25)}\n{' '.join(x[2] for x in cur)}\n"); cur = []
n = len(F["beats"]); T = F["total"]
g = ";".join(filt) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad,atrim=0:{T:.3f},asplit=2[voice][key];"
g += f"[{n}:a]volume=0.55[bed];[bed][key]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=600[duck];"
g += "[voice]pan=stereo|c0=c0|c1=c0[vs];[vs][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1:LRA=6[out]"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", "audio/bed.wav", "-filter_complex", g, "-map", "[out]", "-ar", "48000", "-ac", "2", "out/mix.wav"], check=True)
open("out/film.srt", "w").write("\n".join(srt))
print(f"audio {T:.1f}s, {len(srt)} caption lines")
PY
ffmpeg -y -loglevel error -framerate $FPS -i "$FRAMES/f%06d.jpg" -i out/mix.wav -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -shortest -movflags +faststart "out/film.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "out/film.mp4"
