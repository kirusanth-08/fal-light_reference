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
import tempfile
from io import BytesIO
from PIL import Image as PILImage
from pydantic import BaseModel, Field
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
FIXED_CFG = 1.0
FIXED_DENOISE = 1.0

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

def image_url_to_base64(image_url: str) -> str:
    """Download image from URL and convert to base64."""
    response = requests.get(image_url)
    response.raise_for_status()
    pil = PILImage.open(BytesIO(response.content))
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def upload_images(images):
    for img in images:
        blob = base64.b64decode(img["image"])
        files = {"image": (img["name"], BytesIO(blob), "image/png")}
        r = requests.post(f"http://{COMFY_HOST}/upload/image", files=files)
        r.raise_for_status()

def apply_fixed_values(workflow: dict, seed_value: int):
    for node in workflow.values():
        inputs = node.get("inputs", {})

        if node.get("class_type") == "KSampler":
            inputs["cfg"] = FIXED_CFG
            inputs["denoise"] = FIXED_DENOISE
            inputs["seed"] = seed_value

# -------------------------------------------------
# Input Model (ONLY image inputs in UI)
# -------------------------------------------------
class LightTransferInput(BaseModel):
    main_image_url: str = Field(
        ...,
        title="Main Image URL",
        description="URL of the main image to relight/recolor. This is the image that will be modified. (REQUIRED)",
        examples=["https://img.freepik.com/free-photo/young-woman-new-york-city-daytime_23-2149488480.jpg?semt=ais_hybrid&w=740&q=80"]
    )
    reference_image_url: str = Field(
        ...,
        title="Reference Image URL",
        description="URL of the reference image whose lighting and color tone will be applied to the main image. (REQUIRED)",
        examples=["https://images.pexels.com/photos/29422068/pexels-photo-29422068.jpeg?cs=srgb&dl=pexels-omergulen-29422068.jpg&fm=jpg"]
    )

# -------------------------------------------------
# App
# -------------------------------------------------
class LightTransfer(fal.App):
    image = custom_image
    machine_type = "GPU-H100"
    max_concurrency = 5
    requirements = ["websockets", "websocket-client"]

    # 🔒 CRITICAL
    private_logs = False

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
    def handler(self, input: LightTransferInput):
        try:
            job = copy.deepcopy(WORKFLOW_JSON)
            workflow = job["input"]["workflow"]

            main_img = f"main_{uuid.uuid4().hex}.png"
            ref_img = f"ref_{uuid.uuid4().hex}.png"

            upload_images([
                {"name": main_img, "image": image_url_to_base64(input.main_image_url)},
                {"name": ref_img, "image": image_url_to_base64(input.reference_image_url)}
            ])

            workflow["31"]["inputs"]["image"] = main_img
            workflow["7"]["inputs"]["image"] = ref_img

            seed_value = random.randint(0, 2**63 - 1)
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
                    # Save to temp file and use Image.from_path for better compatibility
                    temp_path = f"/tmp/output_{uuid.uuid4().hex}.png"
                    with open(temp_path, "wb") as f:
                        f.write(r.content)
                    images.append(Image.from_path(temp_path))

            ws.close()
            return {"status": "success", "images": images}

        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}
