# -*- coding: utf-8 -*-
import sys
from faster_whisper import WhisperModel

files = [
    (r"D:\xwechat_files\wxid_rj63lwxc0bek22_1040\msg\file\2026-06\录音\2026年06月17日 13点58分.m4a",
     r"C:\Users\18273\Desktop\ai\_transcript_3.txt"),
    (r"D:\xwechat_files\wxid_rj63lwxc0bek22_1040\msg\file\2026-06\录音\2026年06月17日 15点03分.m4a",
     r"C:\Users\18273\Desktop\ai\_transcript_4.txt"),
]

print("loading model...", flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
print("model loaded", flush=True)

for src, dst in files:
    print(f"transcribing {src}", flush=True)
    segments, info = model.transcribe(
        src, language="zh", vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )
    with open(dst, "w", encoding="utf-8") as f:
        for seg in segments:
            line = f"[{seg.start:7.1f}s] {seg.text.strip()}"
            f.write(line + "\n")
            print(line, flush=True)
    print(f"DONE -> {dst}", flush=True)

print("ALL DONE", flush=True)
