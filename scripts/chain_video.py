#!/usr/bin/env python3
"""Make a longer video by chaining short Wan 2.2 5B clips in ComfyUI.

Each clip starts from the last frame of the clip before it, and the clips are
joined into one video. Give one prompt per clip to change what happens as it
goes; if there are fewer prompts than clips, the last prompt is reused.

Outside the Phase 1 plan; added at Rob's request. Needs ComfyUI running
(scripts/start_comfyui.sh) and the three Wan 2.2 5B model files.

Example (four clips of about 2 seconds, roughly 70 minutes on the M1 Pro):

    python3 scripts/chain_video.py --image wan-test-start.png --clips 4 \
        --prompt "She strums the guitar, the campfire flickers." \
        --prompt "She looks up at the stars."

--image is a file name in ComfyUI's input folder (~/ComfyUI-data/input).
The videos are saved in ~/ComfyUI-data/output/video/.
"""
import argparse
import json
import time
import urllib.error
import urllib.request

NEGATIVE = ("overexposed, static, blurry details, subtitles, worst quality, low quality, "
            "deformed, extra limbs, still image")


def build_workflow(args):
    """One ComfyUI job holding every clip, so the last frame passes from clip to clip inside it."""
    wf = {
        "model": {"class_type": "UNETLoader",
                  "inputs": {"unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
        "shift": {"class_type": "ModelSamplingSD3", "inputs": {"shift": 8, "model": ["model", 0]}},
        "negative": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["clip", 0]}},
        "load": {"class_type": "LoadImage", "inputs": {"image": args.image}},
        "start0": {"class_type": "ImageScale",
                   "inputs": {"image": ["load", 0], "upscale_method": "lanczos",
                              "width": args.width, "height": args.height, "crop": "center"}},
    }
    joined = None
    for i in range(args.clips):
        prompt = args.prompt[min(i, len(args.prompt) - 1)]
        wf[f"prompt{i}"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["clip", 0]}}
        wf[f"latent{i}"] = {"class_type": "Wan22ImageToVideoLatent",
                            "inputs": {"width": args.width, "height": args.height, "length": args.frames,
                                       "batch_size": 1, "vae": ["vae", 0], "start_image": [f"start{i}", 0]}}
        wf[f"sample{i}"] = {"class_type": "KSampler",
                            "inputs": {"seed": args.seed + i, "steps": args.steps, "cfg": 5,
                                       "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1,
                                       "model": ["shift", 0], "positive": [f"prompt{i}", 0],
                                       "negative": ["negative", 0], "latent_image": [f"latent{i}", 0]}}
        wf[f"frames{i}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"sample{i}", 0], "vae": ["vae", 0]}}
        # Save each clip separately too, so a long run that fails part-way still leaves something.
        wf[f"clipvideo{i}"] = {"class_type": "CreateVideo", "inputs": {"fps": args.fps, "images": [f"frames{i}", 0]}}
        wf[f"clipsave{i}"] = {"class_type": "SaveVideo",
                              "inputs": {"filename_prefix": f"video/{args.name}-clip{i + 1}", "format": "auto",
                                         "codec": "auto", "video": [f"clipvideo{i}", 0]}}
        # The last frame of this clip is the starting picture of the next.
        wf[f"start{i + 1}"] = {"class_type": "ImageFromBatch",
                               "inputs": {"image": [f"frames{i}", 0], "batch_index": args.frames - 1, "length": 1}}
        if joined is None:
            joined = [f"frames{i}", 0]
        else:
            # Later clips repeat that frame as their first, so drop it before joining.
            wf[f"rest{i}"] = {"class_type": "ImageFromBatch",
                              "inputs": {"image": [f"frames{i}", 0], "batch_index": 1, "length": args.frames - 1}}
            wf[f"join{i}"] = {"class_type": "ImageBatch", "inputs": {"image1": joined, "image2": [f"rest{i}", 0]}}
            joined = [f"join{i}", 0]
    del wf[f"start{args.clips}"]  # nothing follows the final clip
    wf["fullvideo"] = {"class_type": "CreateVideo", "inputs": {"fps": args.fps, "images": joined}}
    wf["fullsave"] = {"class_type": "SaveVideo",
                      "inputs": {"filename_prefix": f"video/{args.name}-full", "format": "auto",
                                 "codec": "auto", "video": ["fullvideo", 0]}}
    return wf


def call(url, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url + path, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as reply:
            return json.loads(reply.read() or b"{}")
    except urllib.error.HTTPError as err:
        raise SystemExit(f"ComfyUI refused the job (HTTP {err.code}): {err.read().decode()[:2000]}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", required=True, help="starting picture: a file name in ComfyUI's input folder")
    p.add_argument("--prompt", action="append", required=True, help="what happens; repeat for one prompt per clip")
    p.add_argument("--clips", type=int, default=4, help="how many clips to chain (default 4)")
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=640)
    p.add_argument("--frames", type=int, default=49, help="frames per clip; 49 is about 2 seconds (default 49)")
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--name", default="chain", help="start of the saved file names (default chain)")
    p.add_argument("--url", default="http://127.0.0.1:8188", help="where ComfyUI is running")
    args = p.parse_args()

    start = time.time()
    job = call(args.url, "/prompt", {"prompt": build_workflow(args)})["prompt_id"]
    total = args.frames + (args.clips - 1) * (args.frames - 1)
    print(f"Sent to ComfyUI: {args.clips} clips, {total} frames, about {total / args.fps:.1f} seconds of video.", flush=True)
    while True:
        time.sleep(15)
        history = call(args.url, "/history/" + job)
        if job in history:
            break
    minutes = (time.time() - start) / 60
    status = history[job]["status"]
    print(f"Finished: {status.get('status_str')} after {minutes:.1f} minutes.")
    for kind, detail in status.get("messages", []):
        if kind == "execution_error":
            print(f"Error in {detail.get('node_type')}: {detail.get('exception_message')}")
    for output in history[job].get("outputs", {}).values():
        for item in output.get("images", []):
            print(f"  saved {item.get('subfolder')}/{item.get('filename')}")
    if status.get("status_str") != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
