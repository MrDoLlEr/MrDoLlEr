#!/usr/bin/env bash
# Scene 2 — jade dragon extrusion. Four steps, strictly in order.
#
# Requires the Picsart gen-ai CLI on PATH and an authenticated account:
#   npx skills add PicsArt/gen-ai-skills
#
# Steps 2 and 3 each depend on the approved output of the step before, so they
# cannot run in parallel. Every `generate` spends credits; set the ceiling on
# the account, not in the prompt. Record the job handle at submission.

set -euo pipefail
cd "$(dirname "$0")"

STEP="${1:-}"

case "$STEP" in
setup)
  # 1. The macro setup: hand, tube, nozzle, tile, light. No creature yet.
  gen-ai generate -m gpt-image-2 \
    --prompt-file prompts/image-1-macro-setup.txt \
    --aspect-ratio 9:16 --quality high \
    --download images --no-input
  echo "Approve, then copy to images/macro-setup.png"
  ;;

design)
  # 2. The finished creature, generated FROM the approved setup so the hand,
  #    tube, camera and light carry over unchanged.
  : "${SETUP:=images/macro-setup.png}"
  test -f "$SETUP" || { echo "missing approved setup still: $SETUP" >&2; exit 1; }
  gen-ai generate -m gpt-image-2 \
    --prompt-file prompts/image-2-creature-design.txt \
    --image "$SETUP" \
    --aspect-ratio 9:16 --quality high \
    --download images --no-input
  echo "Approve, then copy to images/dragon-design.png"
  echo "Expect a residual gel bead at the nozzle tip — that is intended here,"
  echo "and the motion prompt tells the video model to ignore it."
  ;;

start)
  # 3. The video's first frame: head already out, body still inside the tube.
  : "${DESIGN:=images/dragon-design.png}"
  test -f "$DESIGN" || { echo "missing approved design still: $DESIGN" >&2; exit 1; }
  gen-ai generate -m gpt-image-2 \
    --prompt-file prompts/image-3-opening-frame.txt \
    --image "$DESIGN" \
    --aspect-ratio 9:16 --quality high \
    --download images --no-input
  echo "Approve, then copy to images/dragon-start.png"
  echo "Reject it if: no head at the nozzle, a bead instead of a head, paste on"
  echo "the table, or a whole dragon already outside."
  ;;

video)
  # 4. One generation, 7 seconds, fixed camera. Start frame = still 3,
  #    design reference = still 2.
  : "${START:=images/dragon-start.png}"
  : "${DESIGN:=images/dragon-design.png}"
  for f in "$START" "$DESIGN"; do
    test -f "$f" || { echo "missing approved still: $f" >&2; exit 1; }
  done
  gen-ai generate -m seedance-2.5 \
    --prompt-file prompts/video.txt \
    --start-frame "$START" \
    --reference-image "$DESIGN" \
    --aspect-ratio 9:16 --duration 7 --resolution 1080p \
    --generate-audio --download . --no-input
  echo "Review the MIDDLE frames against brief/action-sequence.md before accepting."
  ;;

*)
  cat <<'USAGE'
usage: ./run.sh <step>          # in this order, approving each output first

  setup     macro setup still (hand, tube, nozzle, tile, no creature)
  design    creature design, from the approved setup
  start     opening frame (head out, body in), from the approved design
  video     7s clip: start frame = opening frame, reference = design

Flags checked against Picsart CLI 2.75.0. Confirm the video model accepts a
start frame AND a separate reference image before running the last step —
support differs per model, and a different provider will not reproduce the
same pixels.
USAGE
  exit 1
  ;;
esac
