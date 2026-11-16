#!/usr/bin/env python3
"""Point Open WebUI's image generation and image editing at ComfyUI.

Not part of the Phase 1 plan; added at Rob's request. The same thing can be done by hand in
Admin Panel > Settings > Images: choose ComfyUI, paste the workflow file and map the nodes.

ComfyUI must be running first:  scripts/start_comfyui.sh

Usage:  python3 scripts/setup_images.py            FLUX.2 klein for making and editing images
        python3 scripts/setup_images.py z-image    Z-Image Turbo for making images (it cannot edit, so editing stays on FLUX.2 klein)
"""
import json
import pathlib
import sys
import urllib.request

BASE = "http://localhost:3000"
COMFYUI = "http://host.docker.internal:8188"  # Open WebUI runs in Docker; this address reaches ComfyUI on the Mac itself.
ROOT = pathlib.Path(__file__).resolve().parent.parent

# For each model: the workflow file, the model file, the number of steps, and which part of the
# workflow each Open WebUI setting goes into: (setting, field name, node numbers).
GENERATE = {
    "klein": (
        "flux2-klein-api.json",
        "flux-2-klein-4b-fp8.safetensors",
        4,
        [("model", "unet_name", ["1"]), ("prompt", "text", ["4"]), ("width", "width", ["6", "7"]), ("height", "height", ["6", "7"]),
         ("n", "batch_size", ["6"]), ("steps", "steps", ["7"]), ("seed", "noise_seed", ["9"])],
    ),
    "z-image": (
        "z-image-turbo-api.json",
        "z_image_turbo_bf16.safetensors",
        8,
        [("model", "unet_name", ["1"]), ("prompt", "text", ["4"]), ("width", "width", ["6"]), ("height", "height", ["6"]),
         ("n", "batch_size", ["6"]), ("steps", "steps", ["8"]), ("seed", "seed", ["8"])],
    ),
}
# Editing: the picture keeps its own shape, so no width or height is passed in.
EDIT = (
    "flux2-klein-edit-api.json",
    "flux-2-klein-4b-fp8.safetensors",
    [("model", "unet_name", ["1"]), ("prompt", "text", ["4"]), ("image", "image", ["20"]), ("seed", "noise_seed", ["9"])],
)


def call(path, token=None, body=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    return json.load(urllib.request.urlopen(urllib.request.Request(BASE + path, data=data, headers=headers), timeout=60))


def nodes(mapping):
    return [{"type": t, "key": k, "node_ids": ids} for t, k, ids in mapping]


def main():
    choice = sys.argv[1] if len(sys.argv) > 1 else "klein"
    if choice not in GENERATE:
        sys.exit("Choose one of: " + ", ".join(GENERATE))
    workflow, model, steps, mapping = GENERATE[choice]
    edit_workflow, edit_model, edit_mapping = EDIT

    token = call("/api/v1/auths/signin", body={"email": "", "password": ""})["token"]
    config = call("/api/v1/images/config", token=token)  # keep every other setting as it is
    config.update(
        ENABLE_IMAGE_GENERATION=True,
        IMAGE_GENERATION_ENGINE="comfyui",
        IMAGE_GENERATION_MODEL=model,
        IMAGE_SIZE="1024x1024",
        IMAGE_STEPS=steps,
        COMFYUI_BASE_URL=COMFYUI,
        COMFYUI_WORKFLOW=(ROOT / "comfyui" / workflow).read_text(),
        COMFYUI_WORKFLOW_NODES=nodes(mapping),
        ENABLE_IMAGE_EDIT=True,
        IMAGE_EDIT_ENGINE="comfyui",
        IMAGE_EDIT_MODEL=edit_model,
        IMAGE_EDIT_SIZE="",
        IMAGES_EDIT_COMFYUI_BASE_URL=COMFYUI,
        IMAGES_EDIT_COMFYUI_WORKFLOW=(ROOT / "comfyui" / edit_workflow).read_text(),
        IMAGES_EDIT_COMFYUI_WORKFLOW_NODES=nodes(edit_mapping),
    )
    saved = call("/api/v1/images/config/update", token=token, body=config)
    for key in ("ENABLE_IMAGE_GENERATION", "IMAGE_GENERATION_MODEL", "IMAGE_STEPS", "ENABLE_IMAGE_EDIT", "IMAGE_EDIT_ENGINE", "IMAGE_EDIT_MODEL"):
        print(key, "=", saved[key])


if __name__ == "__main__":
    main()
