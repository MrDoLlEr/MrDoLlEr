#!/usr/bin/env bash
# Scene 1 — giant coffee bean. Three steps, stop and look after each one.
#
# Requires the Picsart gen-ai CLI on PATH and an authenticated account:
#   npx skills add PicsArt/gen-ai-skills
#
# Nothing here is idempotent: every run of a `generate` step spends credits.
# Set a spending ceiling on the account, not in the prompt.

set -euo pipefail
cd "$(dirname "$0")"

STEP="${1:-}"

case "$STEP" in
still)
  # 1. The starting photograph. Expect a chimney/window to appear — that is the
  #    known defect this scene corrects in step 2.
  gen-ai generate -m gpt-image-2 \
    --prompt-file prompts/image.txt \
    --aspect-ratio 9:16 --quality high \
    --download images --no-input
  echo "Now LOOK at images/. Record the job handle in jobs/ before continuing."
  ;;

correct)
  # 2. Remove the chimney, window, lantern, hardware and ivy. Pass the still
  #    from step 1 as the image to edit.
  : "${SRC:?set SRC=images/<file from step 1>.png}"
  gen-ai generate -m gpt-image-2 \
    --prompt-file prompts/image-correction.txt \
    --image "$SRC" \
    --aspect-ratio 9:16 --quality high \
    --download images --no-input
  echo "Approve the corrected still, then copy it to images/coffee-start.png."
  ;;

video)
  # 3. One generation, 9 seconds, from the approved still. No interior image.
  : "${START:=images/coffee-start.png}"
  test -f "$START" || { echo "missing approved still: $START" >&2; exit 1; }
  gen-ai generate -m seedance-2.5 \
    --prompt-file prompts/video.txt \
    --start-frame "$START" \
    --aspect-ratio 9:16 --duration 9 --resolution 1080p \
    --generate-audio --download . --no-input
  echo "Review the MIDDLE frames against brief/action-sequence.md before accepting."
  ;;

*)
  cat <<'USAGE'
usage: ./run.sh <step>

  still     generate the starting photograph
  correct   SRC=images/<file> ./run.sh correct   — remove the chimney and window
  video     START=images/coffee-start.png ./run.sh video

Flags checked against Picsart CLI 2.75.0. Recheck a model's supported inputs
before changing providers; different models will not reproduce the same pixels.
USAGE
  exit 1
  ;;
esac
