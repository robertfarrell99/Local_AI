#!/bin/sh
# Start ComfyUI (image generation) on this Mac only, at http://localhost:8188.
# Images, uploads and previews go in ~/ComfyUI-data, which docker-compose.yml shares with
# Open WebUI so that the "Delete images" buttons can empty it.
# Not part of the Phase 1 plan; added at Rob's request.
DATA="$HOME/ComfyUI-data"
mkdir -p "$DATA/output" "$DATA/input"
cd "$HOME/ComfyUI" && exec .venv/bin/python main.py \
  --output-directory "$DATA/output" --input-directory "$DATA/input" --temp-directory "$DATA"
