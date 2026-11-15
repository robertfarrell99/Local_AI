#!/usr/bin/env python3
"""Point Open WebUI's image generation at ComfyUI with the Z-Image Turbo workflow.

Not part of the Phase 1 plan; added at Rob's request. The same thing can be done by hand in
Admin Panel > Settings > Images: choose ComfyUI, paste comfyui/z-image-turbo-api.json and map the nodes.

ComfyUI must be running first:  cd ~/ComfyUI && .venv/bin/python main.py

Usage:  python3 scripts/setup_images.py
"""
import json
import pathlib
import urllib.request

BASE = "http://localhost:3000"
ROOT = pathlib.Path(__file__).resolve().parent.parent

# Which part of the workflow each Open WebUI setting goes into: (setting, field name, node number).
NODES = [
    ("model", "unet_name", "1"),
    ("prompt", "text", "4"),
    ("width", "width", "6"),
    ("height", "height", "6"),
    ("n", "batch_size", "6"),
    ("steps", "steps", "8"),
    ("seed", "seed", "8"),
]


def call(path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    return json.load(urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers), timeout=60))


def main():
    token = call("/api/v1/auths/signin", body={"email": "", "password": ""})["token"]
    config = call("/api/v1/images/config", token=token)  # keep every other setting as it is
    config.update(
        ENABLE_IMAGE_GENERATION=True,
        IMAGE_GENERATION_ENGINE="comfyui",
        IMAGE_GENERATION_MODEL="z_image_turbo_bf16.safetensors",
        IMAGE_SIZE="1024x1024",
        IMAGE_STEPS=8,
        # Open WebUI runs in Docker; this address reaches ComfyUI on the Mac itself.
        COMFYUI_BASE_URL="http://host.docker.internal:8188",
        COMFYUI_WORKFLOW=(ROOT / "comfyui" / "z-image-turbo-api.json").read_text(),
        COMFYUI_WORKFLOW_NODES=[{"type": t, "key": k, "node_ids": [n]} for t, k, n in NODES],
    )
    saved = call("/api/v1/images/config/update", token=token, body=config)
    for key in ("ENABLE_IMAGE_GENERATION", "IMAGE_GENERATION_ENGINE", "IMAGE_GENERATION_MODEL", "IMAGE_SIZE", "IMAGE_STEPS", "COMFYUI_BASE_URL"):
        print(key, "=", saved[key])


if __name__ == "__main__":
    main()
