#!/usr/bin/env bash
# Idempotent multimedia / design toolchain for Cursor Cloud agents.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  imagemagick \
  sox \
  libsox-fmt-all \
  gifsicle \
  optipng \
  pngquant \
  potrace \
  librsvg2-bin \
  mediainfo \
  fonts-hosny-amiri \
  fonts-sil-scheherazade \
  fonts-ibm-plex \
  libraqm0 \
  libcairo2

python3 -m pip install --user -r "$ROOT/requirements-creative.txt"
fc-cache -f >/dev/null 2>&1 || true
