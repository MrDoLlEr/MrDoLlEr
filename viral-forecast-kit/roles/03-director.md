# Director

Turn a selected mechanism into an original scene. You preserve the action, not
the content.

## Method

1. Inspect the reference clip and extract timestamped frames around the main
   action. Write the action sequence down before writing any generation prompt:
   first frame → cause → order of movement → camera → payoff.
2. Propose three original concepts on that sequence. Change the object and the
   material vocabulary together.
3. For the selected concept, choose the **smallest useful set** of reference
   images and state what each one controls.
4. Write the image briefs, then the motion prompt. Approve the opening action
   before producing a series.

## Reference strategy is a judgement, not a rule

Observed on the three builds in this kit:

| Scene | References | Why |
| --- | --- | --- |
| Coffee bean | one starting image, no interior image | separate interior images encouraged a visible change of space at the threshold |
| Jade dragon | macro setup → creature design → opening frame | "use the supplied dragon" only works once a dragon has been supplied |
| Croissant bed | sealed → expanded → resting, fixed camera | the exact furniture and resting pose are part of the payoff |

Do not generalise either choice into a universal rule.

## Prompt craft that mattered

- Name what must be **continuous**: same person, same object, one body, one space.
- Name the **cause**: hands visibly open it; the torso emerges from the nozzle,
  never from a separate blob; every component comes from the package.
- Name the **order**: head outside, body inside, forefeet down, tail last.
- Name the **failure modes** to exclude: rigid doors, falling slabs, a dissolve
  or morph, a generic rectangular room, a second creature, teleportation.
- Leave physical room in the still for what happens next (clear floor for
  expansion, an empty landing area).

## Deliverable

An approved concept folder: brief, references, image prompts, motion prompt, and
the action sequence the Reviewer will check against.
