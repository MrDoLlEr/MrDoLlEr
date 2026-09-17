# Analyst

Two separate questions. Do not let one answer stand in for the other.

## 1. Was the forecast any good?

After the window closes, collect outcomes for **all** candidates, including the
ones nobody picked:

```
forecast_journal.py outcome --cohort <id> --observations obs-t48.csv
forecast_journal.py score   --cohort <id>
forecast_journal.py verify  --cohort <id>
```

A selected video is a hit when its absolute view gain over the window lands in
the top quarter of the cohort. Report:

- hits and **misses** for the frozen picks
- hits and misses for the recent-velocity baseline
- ties at the quartile boundary, explicitly
- candidates with missing outcomes, excluded rather than counted as misses

One cohort is one data point. Repeat across fresh cohorts before claiming the
extra analysis beats plain velocity.

## 2. Did our own work perform, and did it pay?

A separate test on our own distribution.

```
contribution per order = collected revenue
  − all generation costs, including rejected attempts
  − editing and review labor
  − allocated software and delivery costs
```

Also track: time to approval, fraction of outputs requiring a remake, and
whether the client orders again. Those numbers say whether more volume helps or
simply multiplies rework.

## Claims you may not make

- That a source video's success predicts our remake's reach.
- That the method is validated because a pick did well.
- Any probability the journal did not measure.
