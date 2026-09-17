# Role briefs

Six jobs, executed **sequentially by one agent** for the first batches. Split them
into separate workers only when a real queue makes that useful.

| # | Role | Owns | Hands off |
| --- | --- | --- | --- |
| 1 | [Scout](01-scout.md) | candidate collection, source evidence | source observations |
| 2 | [Forecaster](02-forecaster.md) | the frozen forecast | frozen forecast |
| 3 | [Director](03-director.md) | original concept, image briefs, motion prompts | approved concept |
| 4 | [Producer](04-producer.md) | job submission, handles, downloads, settings | checked images → rendered video |
| 5 | [Reviewer](05-reviewer.md) | action, continuity, scale, anatomy, export | reviewed export |
| 6 | [Analyst](06-analyst.md) | forecast scoring, our own performance and cost | measured outcome |

Handoff chain:

```
source observations → frozen forecast → approved concept
→ checked images → rendered video → reviewed export
→ authorized publication → measured outcome
```

Two rules hold across every role:

- A job handle means the request exists. It does not mean a finished video exists.
  A successful render does not mean the scene passed review.
- Nothing here installs a feed collector, scheduler, budget enforcement service
  or publisher. Those integrations must be connected to the accounts you intend
  to use.
