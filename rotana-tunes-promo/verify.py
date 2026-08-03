"""Check the finished mix still reads.

Transcribes `build/mix.wav` with Whisper and diffs it against the script. A
clean run means the bed is sitting under the voice rather than on top of it;
if words start dropping, lower the music or deepen the duck in `mix.py`.
"""

from __future__ import annotations

import difflib
import json
import re
import sys

from config import BUILD

STRIP = re.compile(r"[\u064B-\u0652\u0670،.؟!,]")


def normalise(text: str) -> list[str]:
    text = STRIP.sub("", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    text = text.replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    return [w for w in text.split() if w]


def main() -> int:
    from faster_whisper import WhisperModel

    timing = json.loads((BUILD / "vo_timing.json").read_text(encoding="utf-8"))
    script = []
    for line in timing["lines"]:
        script += normalise(line["text"])

    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(BUILD / "mix.wav"), language="ar", vad_filter=False)
    heard = []
    for s in segments:
        print(f"[{s.start:6.2f} -> {s.end:6.2f}] {s.text.strip()}")
        heard += normalise(s.text)

    ratio = difflib.SequenceMatcher(None, script, heard).ratio()
    matched = sum(b.size for b in difflib.SequenceMatcher(None, script, heard).get_matching_blocks())
    print(f"\nscript words : {len(script)}")
    print(f"heard words  : {len(heard)}")
    print(f"exact matches: {matched}")
    print(f"similarity   : {ratio:.3f}")

    if ratio < 0.70:
        print("\nFAIL: the voice is getting buried. Lower the bed in mix.build_mix.")
        return 1
    print("\nOK: the voice-over survives the mix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
