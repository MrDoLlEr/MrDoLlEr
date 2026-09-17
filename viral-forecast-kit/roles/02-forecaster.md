# Forecaster

Freeze a selection that can lose. Your output is worthless if it can be edited
after the outcome is known.

## Inputs

The cohort, its observations, timestamped frames or clips, and creator baselines
**where real historical snapshots exist**. Current lifetime totals cannot
reconstruct how an older clip performed in its first hours — mark the baseline
unavailable rather than approximating it.

## Procedure

1. Run `forecast_journal.py metrics --cohort <id> --cutoff <ts>` and read the
   velocity and change-in-velocity columns.
2. Run the analysis prompt (`prompts/01-forecast-analysis.txt`) over the clips
   and the numbers. Require it to separate observed facts from hypotheses.
3. Choose three candidates for absolute view gain over the next 48 hours.
4. Write `reasons.json`: for each pick, the numerical evidence, the visual
   evidence, what is missing, and a plausible reason the forecast fails.
5. Freeze:

```
forecast_journal.py freeze --cohort <id> --cutoff <ts> \
  --picks a,b,c --reasons reasons.json
```

The journal refuses to overwrite a frozen forecast, rejects observations that
postdate the cutoff, and records the plain recent-velocity top three as the
comparison method.

## Hard limits

- No invented probabilities. "87% chance of going viral" from an uncalibrated
  model is a fabricated number.
- Define success before checking results. The default rule is stored in the
  frozen block.
- The checksum detects a changed record. It is not proof of when you decided.
  For a public test, place the frozen block in an externally timestamped record
  before the window opens.
- A strong forecast concerns the *source* videos. It says nothing about whether
  our remake will perform.
