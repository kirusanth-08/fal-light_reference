import fal
from fal.container import ContainerImage
from fal.toolkit.image import Image
from pathlib import Path
import json
import uuid
import base64
import requests
import websocket
import traceback
import os
import copy
import random
from io import BytesIO
from typing import Literal
from comfy_models import MODEL_LIST
from workflow import WORKFLOW_JSON
from pydantic import BaseModel, Field

# -------------------------------------------------
# Container setup
# -------------------------------------------------
PWD = Path(__file__).resolve().parent
dockerfile_path = f"{PWD}/Dockerfile"
custom_image = ContainerImage.from_dockerfile(dockerfile_path)

COMFY_HOST = "127.0.0.1:8188"

# -------------------------------------------------
# Presets
# -------------------------------------------------
PRESETS = {
    "imperfect_skin": {"cfg": 0.1, "denoise": 0.34, "resolution": 2048},
    "high_end_skin": {"cfg": 1.1, "denoise": 0.30, "resolution": 3072},
    "smooth_skin": {
        "cfg": 1.1,
        "denoise": 0.30,
        "resolution": 2048,
        "prompt_override": True,
        "positive_prompt": (
            "ultra realistic portrait of [subject], flawless clear face, "
            "smooth radiant skin texture, fine pores, balanced complexion, "
            "healthy glow, cinematic lighting"
        ),
        "negative_prompt": (
            "freckles, spots, blemishes, acne, pigmentation, redness, "
            "rough skin, waxy skin, plastic texture, airbrushed"
        )
    },
    "portrait": {"cfg": 0.5, "denoise": 0.35, "resolution": 2048},
    "mid_range": {"cfg": 1.4, "denoise": 0.40, "resolution": 2048},
    "full_body": {"cfg": 1.5, "denoise": 0.30, "resolution": 2048},
}

# -------------------------------------------------
# Utilities
# -------------------------------------------------
def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def download_if_missing(url, path):
    if os.path.exists(path):
        return
    ensure_dir(path)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

def check_server(url, retries=500, delay=0.1):
    import time
    for _ in range(retries):
        try:
            if requests.get(url).status_code == 200:
                return True
        except:
            pass
        time.sleep(delay)
    return False

def fal_image_to_base64(img: Image) -> str:
    pil = img.to_pil()
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def upload_images(images):
    for img in images:
        blob = base64.b64decode(img["image"])
        files = {"image": (img["name"], BytesIO(blob), "image/png")}
        r = requests.post(f"http://{COMFY_HOST}/upload/image", files=files)
        r.raise_for_status()

# -------------------------------------------------
# Input Model (UI)
# -------------------------------------------------
class SkinFixInput(BaseModel):
    skin_preset: Literal[
        "none",
        "imperfect_skin",
        "high_end_skin",
        "smooth_skin",
        "portrait",
        "mid_range",
        "full_body"
    ] = Field(title="Skin Preset")

    image: Image = Field(title="Input Image")

    cfg: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        title="Skin Realism",
        description="Ignored when preset selected"
    )

    # INTEGER SLIDER → mapped internally to 0.30–0.40
    skin_refinement: int = Field(
        default=0,
        ge=0,
        le=100,
        title="Skin Refinement",
        description="Ignored when preset selected"
    )

    seed: int = Field(
        default=123456789,
        title="Random Seed"
    )

    upscale_resolution: Literal[
        1024, 1280, 1536, 1792,
        2048, 2304, 2560, 2816, 3072
    ] = Field(
        default=2048,
        title="Upscaler Resolution"
    )

# -------------------------------------------------
# App
# -------------------------------------------------
class SkinFixApp(fal.App):
    image = custom_image
    machine_type = "GPU-H100"
    max_concurrency = 5
    requirements = ["websockets", "websocket-client"]

    # 🔒 CRITICAL
    private_logs = True

    def setup(self):
        # Download models
        for model in MODEL_LIST:
            download_if_missing(model["url"], model["path"])

        # Symlink models
        for model in MODEL_LIST:
            ensure_dir(model["target"])
            if not os.path.exists(model["target"]):
                os.symlink(model["path"], model["target"])

        # Start ComfyUI (NO --log-stdout)
        import subprocess
        self.comfy = subprocess.Popen(
            [
                "python", "-u", "/comfyui/main.py",
                "--disable-auto-launch",
                "--disable-metadata",
                "--listen", "--port", "8188"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if not check_server(f"http://{COMFY_HOST}/system_stats"):
            raise RuntimeError("ComfyUI failed to start")

    @fal.endpoint("/")
    def handler(self, input: SkinFixInput):
        try:
            job = copy.deepcopy(WORKFLOW_JSON)
            workflow = job["input"]["workflow"]

            # Upload image
            image_name = f"input_{uuid.uuid4().hex}.png"
            upload_images([{
                "name": image_name,
                "image": fal_image_to_base64(input.image)
            }])
            workflow["32"]["inputs"]["image"] = image_name

            sampler = workflow["29"]["inputs"]

            # Preset logic
            if input.skin_preset != "none":
                p = PRESETS[input.skin_preset]
                sampler["cfg"] = p["cfg"]
                sampler["denoise"] = p["denoise"]
                workflow["30"]["inputs"]["new_resolution"] = p["resolution"]

                if p.get("prompt_override"):
                    workflow["26"]["inputs"]["part1"] = p["positive_prompt"]
                    workflow["25"]["inputs"]["text"] = p["negative_prompt"]
            else:
                sampler["cfg"] = input.cfg
                sampler["denoise"] = 0.30 + (input.skin_refinement / 100.0) * 0.10

            sampler["seed"] = input.seed

            # Auto-random SeedVR2 seed
            workflow["30"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

            # Upscaler resolution
            workflow["31"]["inputs"]["vae_tile_size"] = input.upscale_resolution

            # Run ComfyUI
            client_id = str(uuid.uuid4())
            ws = websocket.WebSocket()
            ws.connect(f"ws://{COMFY_HOST}/ws?clientId={client_id}")

            resp = requests.post(
                f"http://{COMFY_HOST}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=30
            )
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]

            while True:
                msg = json.loads(ws.recv())
                if msg.get("type") == "executing" and msg["data"]["node"] is None:
                    break

            history = requests.get(
                f"http://{COMFY_HOST}/history/{prompt_id}"
            ).json()

            images = []
            for node in history[prompt_id]["outputs"].values():
                for img in node.get("images", []):
                    params = (
                        f"filename={img['filename']}"
                        f"&subfolder={img.get('subfolder','')}"
                        f"&type={img['type']}"
                    )
                    r = requests.get(f"http://{COMFY_HOST}/view?{params}")
                    images.append(Image.from_bytes(r.content, format="png"))

            ws.close()
            return {"status": "success", "images": images}

        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}
