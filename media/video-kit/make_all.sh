#!/usr/bin/env bash
# One command from script to mp4 in a cloned voice: takes (resumable), check, finish, word timings, bed, frames, mp4.
# Runs detached-safe:  nohup ./make_all.sh > make_all.log 2>&1 &
# F5_PY: python of the venv with f5-tts-mlx.  WHISPER_PY: python of the venv with faster-whisper and soundfile.
set -uo pipefail
cd "$(dirname "$0")"
F5_PY="${F5_PY:-voice/f5env/bin/python}"; WHISPER_PY="${WHISPER_PY:-.venv/bin/python}"
n_beats=$(python3 -c "import json; print(len(json.load(open('film.json'))['beats']))")
for round in 1 2 3 4; do
  "$F5_PY" voice/clone_tts.py film.json 2>&1 | grep -E "^b|Error" | tr '\n' ' '; echo
  "$WHISPER_PY" voice/qc.py film.json 2>&1 | grep -E "REDO|rejected|Error"
  n=$(ls audio/*.raw.wav 2>/dev/null | wc -l | tr -d ' '); echo "round $round: $n/$n_beats beats complete"
  [ "$n" = "$n_beats" ] && break
done
[ "$(ls audio/*.raw.wav 2>/dev/null | wc -l | tr -d ' ')" = "$n_beats" ] || { echo "STOP: not all beats passed"; exit 1; }
python3 voice_finish.py
"$WHISPER_PY" words.py 2>&1 | grep -v Warn | tail -1
"$WHISPER_PY" bed.py
./build.sh
echo DONE
