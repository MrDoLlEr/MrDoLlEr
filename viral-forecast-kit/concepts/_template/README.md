# Concept folder

Copy this folder per concept: `concepts/2026-09-coffee-bean/`.

| Path | Holds |
| --- | --- |
| `brief/` | the concept, the recorded action sequence, deliverable spec (size, duration, language, channel) |
| `references/` | source clip, extracted timestamped frames, character reference |
| `prompts/` | the exact image and video prompts used, one file each |
| `images/` | generated stills, including the pre-correction version |
| `jobs/` | one record per submission: model, prompt file, settings, job handle, output path |
| `accepted/` | assets that passed review |
| `rejected/` | attempts that failed, kept with the reason |
| `review/` | defect lists with frame or timecode |

A failed render should leave enough here for the next run to resume without
re-deriving anything.
