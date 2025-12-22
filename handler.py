import fal
from fal.container import ContainerImage
from pathlib import Path
import json
import uuid
import requests
import websocket
import traceback
import os
import copy
import random
from io import BytesIO

from pydantic import BaseModel, Field
from fal.toolkit import download_file, FAL_PERSISTENT_DIR
from fal.toolkit.image import Image

from comfy_models import MODEL_LIST
from workflow import WORKFLOW_JSON

# -------------------------------------------------
# Container setup
# -------------------------------------------------
PWD = Path(__file__).resolve().parent
dockerfile_path = f"{PWD}/Dockerfile"
custom_image = ContainerImage.from_dockerfile(dockerfile_path)

COMFY_HOST = "127.0.0.1:8188"

# -------------------------------------------------
# Fixed INTERNAL parameters (NOT exposed in UI)
# -------------------------------------------------
FIXED_CFG = 1.1
FIXED_DENOISE = 0.30
FIXED_RESOLUTION = 2048

# -------------------------------------------------
# Utilities
# -------------------------------------------------
def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def download_if_missing(url, path):
    if os.path.exists(path):
        return
    ensure_dir(path)
    print(f"[MODEL] Downloading {url}")
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
        except Exception:
            pass
        time.sleep(delay)
    return False

def upload_image_bytes(filename: str, blob: bytes):
    files = {"image": (filename, BytesIO(blob), "image/png")}
    r = requests.post(f"http://{COMFY_HOST}/upload/image", files=files)
    r.raise_for_status()
    print(f"[UPLOAD] Uploaded {filename}")

def download_input_file(url: str) -> str:
    target_dir = Path(FAL_PERSISTENT_DIR) / "inputs"
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        return download_file(url)
    except TypeError:
        return download_file(url, target_dir)

def upload_image_url(image_url: str, filename: str):
    local_path = download_input_file(image_url)
    with open(local_path, "rb") as f:
        upload_image_bytes(filename, f.read())

def apply_fixed_values(workflow: dict, seed_value: int):
    for node in workflow.values():
        inputs = node.get("inputs", {})

        if node.get("class_type") == "KSampler":
            inputs["cfg"] = FIXED_CFG
            inputs["denoise"] = FIXED_DENOISE
            inputs["seed"] = seed_value

        if "new_resolution" in inputs:
            inputs["new_resolution"] = FIXED_RESOLUTION

# -------------------------------------------------
# Input Model (ONLY image inputs in UI)
# -------------------------------------------------
class LightMigrationInput(BaseModel):
    main_image_url: str = Field(
        title="Main Image",
        ui={"field": "image"},
    )
    reference_image_url: str = Field(
        title="Reference Image",
        ui={"field": "image"},
    )

# -------------------------------------------------
# App
# -------------------------------------------------
class LightMigration(fal.App):
    image = custom_image
    machine_type = "GPU-H100"
    max_concurrency = 5
    requirements = ["websockets", "websocket-client"]

    # 🔓 LOGS ENABLED
    private_logs = False

    def setup(self):
        print("[SETUP] Starting setup")

        # Download models
        for model in MODEL_LIST:
            download_if_missing(model["url"], model["path"])

        # Symlink models
        for model in MODEL_LIST:
            ensure_dir(model["target"])
            if not os.path.exists(model["target"]):
                os.symlink(model["path"], model["target"])
                print(f"[MODEL] Linked {model['target']}")

        # Start ComfyUI (LOGS VISIBLE)
        import subprocess
        subprocess.Popen(
            [
                "python", "-u", "/comfyui/main.py",
                "--disable-auto-launch",
                "--disable-metadata",
                "--listen", "--port", "8188"
            ]
        )

        if not check_server(f"http://{COMFY_HOST}/system_stats"):
            raise RuntimeError("ComfyUI failed to start")

        print("[SETUP] ComfyUI is ready")

    @fal.endpoint("/")
    def handler(self, input: LightMigrationInput):
        try:
            print("[REQUEST] New request received")

            job = copy.deepcopy(WORKFLOW_JSON)
            workflow = job["input"]["workflow"]

            seed_value = random.randint(0, 2**63 - 1)
            print(f"[SEED] Using seed {seed_value}")

            main_img = f"main_{uuid.uuid4().hex}.png"
            ref_img = f"ref_{uuid.uuid4().hex}.png"

            upload_image_url(input.main_image_url, main_img)
            upload_image_url(input.reference_image_url, ref_img)

            # Inject images into workflow (KEEP YOUR NODE IDs)
            workflow["31"]["inputs"]["image"] = main_img
            workflow["7"]["inputs"]["image"] = ref_img

            apply_fixed_values(workflow, seed_value)

            # Run ComfyUI
            client_id = str(uuid.uuid4())
            ws = websocket.WebSocket()
            ws.connect(f"ws://{COMFY_HOST}/ws?clientId={client_id}")

            resp = requests.post(
                f"http://{COMFY_HOST}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=30
            )

            if resp.status_code != 200:
                print("[ERROR] ComfyUI rejected workflow")
                print(resp.text)
                return {"error": resp.text}

            prompt_id = resp.json()["prompt_id"]
            print(f"[COMFY] Prompt queued: {prompt_id}")

            while True:
                msg = json.loads(ws.recv())
                if msg.get("type") == "executing" and msg["data"]["node"] is None:
                    break

            history = requests.get(
                f"http://{COMFY_HOST}/history/{prompt_id}"
            ).json()

            outputs = []
            for node in history[prompt_id]["outputs"].values():
                for img in node.get("images", []):
                    params = (
                        f"filename={img['filename']}"
                        f"&subfolder={img.get('subfolder','')}"
                        f"&type={img['type']}"
                    )
                    r = requests.get(f"http://{COMFY_HOST}/view?{params}")
                    outputs.append(Image.from_bytes(r.content, format="png"))

            ws.close()
            print("[SUCCESS] Workflow completed")

            return {"status": "success", "images": outputs}

        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}
