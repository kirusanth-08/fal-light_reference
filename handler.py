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
# PRESETS = {
#     "imperfect_skin": {"cfg": 0.1, "denoise": 0.34, "resolution": 2048},
#     "high_end_skin": {"cfg": 1.1, "denoise": 0.30, "resolution": 3072},
#     "smooth_skin": {
#         "cfg": 1.1,
#         "denoise": 0.30,
#         "resolution": 2048,
#         "prompt_override": True,
#         "positive_prompt": (
#             "ultra realistic portrait of [subject], flawless clear face, "
#             "smooth radiant skin texture, fine pores, balanced complexion, "
#             "healthy glow, cinematic lighting"
#         ),
#         "negative_prompt": (
#             "freckles, spots, blemishes, acne, pigmentation, redness, "
#             "rough skin, waxy skin, plastic texture, airbrushed"
#         )
#     },
#     "portrait": {"cfg": 0.5, "denoise": 0.35, "resolution": 2048},
#     "mid_range": {"cfg": 1.4, "denoise": 0.40, "resolution": 2048},
#     "full_body": {"cfg": 1.5, "denoise": 0.30, "resolution": 2048},
# }

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
class LightMigrationInput(BaseModel):
    image1: Image = Field(description="Input Main Image")
    image2: Image = Field(description="Input Reference Image")


# -------------------------------------------------
# App
# -------------------------------------------------
class LightMigration(fal.App):
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
    def handler(self, request: dict) -> dict:
        try:
            print("=" * 80)
            print("HANDLER STARTED")
            print("=" * 80)
            
            # Debug: Print request info
            print(f"1. Request type: {type(request)}")
            print(f"2. Request keys: {list(request.keys())}")
            print(f"3. Full request (first 500 chars): {str(request)[:500]}")
            
            # Get the workflow from the request
            workflow_input = request.get("input", {})
            print(f"4. workflow_input keys: {list(workflow_input.keys()) if workflow_input else 'None'}")
            
            workflow = workflow_input.get("workflow", {})
            print(f"5. workflow found: {bool(workflow)}")
            
            if not workflow:
                print(f"ERROR: No workflow found!")
                raise ValueError(f"No workflow found in request. Keys: {list(request.keys())}, input: {workflow_input}")
            
            print(f"6. Workflow has {len(workflow)} nodes")
            print(f"7. First 10 workflow nodes: {list(workflow.keys())[:10]}")
            
            job = copy.deepcopy(request)
            
            print("8. Creating ComfyUI client")
            # Run ComfyUI
            client_id = str(uuid.uuid4())
            print(f"9. Client ID: {client_id}")
            
            ws = websocket.WebSocket()
            print(f"10. Connecting to websocket: ws://{COMFY_HOST}/ws?clientId={client_id}")
            ws.connect(f"ws://{COMFY_HOST}/ws?clientId={client_id}")
            print("11. Websocket connected")

            print("12. Sending prompt to ComfyUI")
            resp = requests.post(
                f"http://{COMFY_HOST}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=30
            )
            print(f"13. Response status: {resp.status_code}")
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]
            print(f"14. Prompt ID: {prompt_id}")

            print("15. Waiting for execution to complete")
            while True:
                msg = json.loads(ws.recv())
                if msg.get("type") == "executing" and msg["data"]["node"] is None:
                    print("16. Execution completed")
                    break

            print("17. Fetching history")
            history = requests.get(
                f"http://{COMFY_HOST}/history/{prompt_id}"
            ).json()
            print(f"18. History keys: {list(history.keys())}")

            print("19. Processing output images")
            images = []
            for node_id, node in history[prompt_id]["outputs"].items():
                print(f"20. Processing node {node_id}")
                for img in node.get("images", []):
                    print(f"21. Found image: {img['filename']}")
                    params = (
                        f"filename={img['filename']}"
                        f"&subfolder={img.get('subfolder','')}"
                        f"&type={img['type']}"
                    )
                    print(f"22. Fetching image with params: {params}")
                    r = requests.get(f"http://{COMFY_HOST}/view?{params}")
                    print(f"23. Image fetch status: {r.status_code}, size: {len(r.content)} bytes")
                    images.append(Image.from_bytes(r.content, format="png"))

            ws.close()
            print(f"24. Returning {len(images)} images")
            print("=" * 80)
            print("HANDLER COMPLETED SUCCESSFULLY")
            print("=" * 80)
            return {"status": "success", "images": images}

        except Exception as e:
            print("=" * 80)
            print(f"ERROR: {type(e).__name__}: {str(e)}")
            print("=" * 80)
            traceback.print_exc()
            return {"error": str(e)}
