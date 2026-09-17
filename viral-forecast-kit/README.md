# Viral forecast kit

Two questions, kept apart on purpose:

1. **Can I recognise growth early?** — a frozen forecast, scored against a plain
   velocity baseline, including the misses.
2. **Can I produce something people watch or pay for?** — a separate test, on my
   own distribution.

This folder is the starter kit for both: a forecast journal that refuses to
overwrite a saved prediction, the prompt library from the three finished
recreations, and six role briefs for running it as a production line.

**Status: the forward test has not been run.** The prompts and the workflow are
real. Predictive accuracy is an open question. Nothing here has been validated as
a way to pick hits.

## What this does not include

No feed collector, scheduler, budget enforcement service or publisher is
installed or implied. Those integrations have to be connected to the accounts you
intend to use. A generation CLI supplies images and videos; it does not supply a
trend feed, your account, or your files.

---

## 1. Forecast journal

```
forecast_journal.py init     --cohort C1 --niche surreal-reveal --candidates candidates.csv
forecast_journal.py observe  --cohort C1 --observations observations-t0.csv
forecast_journal.py metrics  --cohort C1 --cutoff 2026-09-14T15:00:00Z
forecast_journal.py freeze   --cohort C1 --cutoff 2026-09-14T15:00:00Z \
                             --picks v03,v19,v10 --reasons reasons.json
forecast_journal.py outcome  --cohort C1 --observations observations-t48.csv
forecast_journal.py score    --cohort C1
forecast_journal.py verify   --cohort C1
```

Stdlib only, Python 3.11+. Journals are JSON, one file per cohort, under `journal/`.

### CSV formats

```
candidates.csv    video_id,url,creator,published_at[,source_evidence,notes]
observations.csv  video_id,observed_at,views[,likes,comments,shares,source_evidence]
```

ISO-8601 timestamps; a trailing `Z` is treated as UTC. Missing fields stay
missing — nothing is inferred or back-filled.

### What it enforces

| Guard | Behaviour |
| --- | --- |
| Frozen forecast | `freeze` refuses to overwrite one. Start a new cohort instead. |
| Data discipline | `freeze` rejects a cutoff that any observation postdates. |
| Cohort integrity | duplicate `video_id`, unknown pick, or stray `reasons.json` key is an error. |
| Honest intervals | velocity uses real elapsed time, so a late collection is fine if stamped honestly. |
| Comparison method | the recent-velocity top three are recorded automatically at freeze. |
| Missing outcomes | excluded from scoring and reported — never counted as misses. |
| Ties | a tie at the quartile boundary includes every tied candidate and is printed. |
| Tamper check | `verify` recomputes the frozen block's SHA-256. |

The checksum detects a **changed record**. It is not proof of when the decision
was made. For a public test, put the frozen block in an externally timestamped
record before the observation window opens.

### Measurement

```
velocity        = (later views − earlier views) / elapsed hours
velocity change = second interval velocity − first interval velocity
```

A clip going 12,000 → 21,000 → 39,000 at three-hour intervals grows first at
3,000 views/hour, then 6,000 — its recent rate doubled. A clip going
100,000 → 103,000 → 106,000 has more total views at a steady 1,000 views/hour.
The first is worth investigating; that is not a guarantee about its next interval.

Compare an upload to that creator's earlier uploads **only where real historical
snapshots at a similar age exist**. Lifetime totals cannot reconstruct how an old
clip performed in its first hours. Mark the baseline unavailable otherwise.

### Success rule

A selected video is a hit if its absolute view gain over the 48-hour window lands
in the top quarter of its cohort (`ceil(n/4)` slots). Defined before outcomes are
collected, stored inside the frozen block.

Never output an invented probability. "87% chance of going viral" from an
uncalibrated model is a fabricated number.

### Worked example

`examples/` holds a 20-candidate synthetic cohort — three pre-cutoff observation
passes, one post-window pass, one candidate that disappears before the window
closes, and a `reasons.json`. `journal/EXAMPLE.json` is the resulting record.

In that example the frozen picks score 2/3 and the plain velocity baseline scores
3/3. That is the point of keeping the baseline: the extra analysis has to beat it,
across fresh cohorts, before it has earned anything.

### The first test, small enough to lose

1. Collect 20 eligible candidates and keep the complete cohort.
2. Pick three using only information available at the cutoff. Save the reasoning,
   the missing data, and an alternative explanation per pick.
3. Freeze. The baseline picks are recorded for you.
4. Wait out the 48-hour window.
5. Collect outcomes for all 20.
6. `score`, then repeat on fresh cohorts before claiming an advantage.

---

## 2. Prompt library

`prompts/` holds the exact prompts behind the three finished recreations, plus
the two agent briefs.

| Path | What it is |
| --- | --- |
| `01-forecast-analysis.txt` | cohort analysis + frozen selection |
| `02-director-brief.txt` | inspect reference → concepts → stills → animate |
| `coffee-bean/` | impact → crack → hands open it → camera enters (9s, one generation from one still) |
| `jade-dragon/` | recognisable creature emerging continuously, head first (7s, 3 stills) |
| `croissant-bed/` | compact package → expansion → someone uses the result (16s, 3 stills, fixed camera) |

The three references are **retrospective**. They were used to test production, not
predicted in advance.

### Reference strategy is a judgement

The coffee scene was more coherent from **one** starting image: separate interior
images encouraged a visible change of space at the threshold. The fixed-camera
bed scene needed three states, because the exact furniture and the resting pose
are the payoff. Neither is a universal rule.

### Production order

```
still(s) → inspect → correct the still → animate → inspect the middle frames → export
```

Correct the still before animating. The first coffee-bean image had a window and
a chimney, which revealed the surprise too early; `image-correction.txt` removes
them. A beautiful first and last frame can hide a completely wrong transition, so
step through the middle.

### Running it with the Picsart CLI

```
npx skills add PicsArt/gen-ai-skills

gen-ai models info gpt-image-2
gen-ai models info seedance-2.5

gen-ai generate -m gpt-image-2 \
  --prompt-file prompts/coffee-bean/image.txt \
  --aspect-ratio 9:16 --quality high \
  --download output --no-input

gen-ai generate -m seedance-2.5 \
  --prompt-file prompts/coffee-bean/video.txt \
  --start-frame assets/coffee-start.png \
  --aspect-ratio 9:16 --duration 9 --resolution 1080p \
  --generate-audio --download output --no-input
```

Flags and model schemas checked against Picsart CLI 2.75.0. Changing providers or
image models will not reproduce identical pixels; recheck a model's supported
inputs before transferring the multi-reference scenes.

---

## 3. Roles and folders

`roles/` has the six briefs: Scout, Forecaster, Director, Producer, Reviewer,
Analyst. Run them sequentially as one agent first; split into workers only when a
real queue makes that useful.

```
source observations → frozen forecast → approved concept
→ checked images → rendered video → reviewed export
→ authorized publication → measured outcome
```

Copy `concepts/_template/` per concept. Keep the brief, source references,
character image, prompts, job records, accepted assets, **rejected attempts** and
review notes together — if a render fails, that folder tells the next run where to
resume.

Two truths worth repeating: a job handle means the request exists, not that a
finished video exists. A successful render does not mean the scene passed review.

Review notes must name a change someone can make:

> The shell falls away instead of being pulled open.
> The dragon forms from a pile after extrusion.
> The exterior and interior behave like different spaces.

"Make it more viral" tells the Producer nothing to fix.

---

## Tests

```
python3 viral-forecast-kit/tests/test_forecast_journal.py     # stdlib runner
python3 -m pytest viral-forecast-kit/tests -q                 # if pytest is available
```

17 tests cover interval maths, the freeze refusals, quartile scoring, boundary
ties, missing outcomes, and tamper detection.
