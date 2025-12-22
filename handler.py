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
    
    # Track recent requests to detect duplicates
    _recent_requests = {}

    def setup(self):
        print("[SETUP] Starting setup")
        print("="*80)

        # Check persistent storage
        print(f"[STORAGE] FAL_PERSISTENT_DIR: {FAL_PERSISTENT_DIR}")
        if os.path.exists(FAL_PERSISTENT_DIR):
            print(f"[STORAGE] ✓ Persistent directory exists")
            data_models_dir = os.path.join(FAL_PERSISTENT_DIR, "models")
            if os.path.exists(data_models_dir):
                print(f"[STORAGE] ✓ Models directory exists: {data_models_dir}")
                # List subdirectories
                for subdir in os.listdir(data_models_dir):
                    subdir_path = os.path.join(data_models_dir, subdir)
                    if os.path.isdir(subdir_path):
                        files = os.listdir(subdir_path)
                        print(f"[STORAGE]   - {subdir}/: {len(files)} file(s)")
                        for f in files[:3]:  # Show first 3 files
                            print(f"[STORAGE]     • {f}")
            else:
                print(f"[STORAGE] ✗ Models directory does not exist yet")
        else:
            print(f"[STORAGE] ✗ Persistent directory does not exist")

        print("="*80)
        print("[MODELS] Starting model download and setup")

        # Download models
        for idx, model in enumerate(MODEL_LIST, 1):
            print(f"[MODEL {idx}/{len(MODEL_LIST)}] Checking: {os.path.basename(model['path'])}")
            if os.path.exists(model["path"]):
                file_size = os.path.getsize(model["path"]) / (1024**3)  # GB
                print(f"[MODEL {idx}/{len(MODEL_LIST)}] ✓ Already exists ({file_size:.2f} GB)")
            else:
                print(f"[MODEL {idx}/{len(MODEL_LIST)}] ✗ Not found, downloading from {model['url'][:80]}...")
            download_if_missing(model["url"], model["path"])

        print("="*80)
        print("[SYMLINK] Creating symlinks to ComfyUI models directory")

        # Symlink models
        for idx, model in enumerate(MODEL_LIST, 1):
            ensure_dir(model["target"])
            if not os.path.exists(model["target"]):
                os.symlink(model["path"], model["target"])
                print(f"[SYMLINK {idx}/{len(MODEL_LIST)}] ✓ Linked {os.path.basename(model['target'])}")
            else:
                print(f"[SYMLINK {idx}/{len(MODEL_LIST)}] ✓ Already linked: {os.path.basename(model['target'])}")

        print("="*80)
        print("[COMFY] Starting ComfyUI server")

        print("="*80)
        print("[COMFY] Starting ComfyUI server")
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

        print("[COMFY] Waiting for ComfyUI to be ready...")
        if not check_server(f"http://{COMFY_HOST}/system_stats"):
            raise RuntimeError("ComfyUI failed to start")

        print("[COMFY] ✓ ComfyUI is ready and responding")
        print("="*80)
        print("[SETUP] ✓ Setup completed successfully")
        print("="*80)

    @fal.endpoint("/")
    def handler(self, input: LightMigrationInput):
        from fastapi import Request
        
        # Get the request context for authentication
        try:
            from starlette.requests import Request as StarletteRequest
            request_context = None  # Will be injected by fal
        except:
            request_context = None
            
        try:
            print("="*80)
            print("[REQUEST] New request received")
            print(f"[INPUT] Main image URL: {input.main_image_url[:100]}...")
            print(f"[INPUT] Reference image URL: {input.reference_image_url[:100]}...")
            print("="*80)

            print("[WORKFLOW] Copying workflow template")
            job = copy.deepcopy(WORKFLOW_JSON)
            workflow = job["input"]["workflow"]
            print(f"[WORKFLOW] Template has {len(workflow)} nodes")

            seed_value = random.randint(0, 2**63 - 1)
            print(f"[SEED] Using seed {seed_value}")

            main_img = f"main_{uuid.uuid4().hex}.png"
            ref_img = f"ref_{uuid.uuid4().hex}.png"
            print(f"[IMAGE] Main image filename: {main_img}")
            print(f"[IMAGE] Reference image filename: {ref_img}")

            print(f"[DOWNLOAD] Downloading main image from URL...")
            upload_image_url(input.main_image_url, main_img)
            print("[UPLOAD] ✓ Main image uploaded to ComfyUI")
            
            print(f"[DOWNLOAD] Downloading reference image from URL...")
            upload_image_url(input.reference_image_url, ref_img)
            print("[UPLOAD] ✓ Reference image uploaded to ComfyUI")

            # Inject images into workflow (KEEP YOUR NODE IDs)
            print(f"[WORKFLOW] Injecting images into workflow nodes")
            workflow["31"]["inputs"]["image"] = main_img
            workflow["7"]["inputs"]["image"] = ref_img
            print(f"[WORKFLOW] ✓ Node 31 image: {workflow['31']['inputs']['image']}")
            print(f"[WORKFLOW] ✓ Node 7 image: {workflow['7']['inputs']['image']}")

            print(f"[WORKFLOW] Applying fixed values (cfg={FIXED_CFG}, denoise={FIXED_DENOISE}, resolution={FIXED_RESOLUTION})")
            apply_fixed_values(workflow, seed_value)
            print(f"[WORKFLOW] ✓ Fixed values applied")

            # Run ComfyUI
            print("[COMFY] Initializing ComfyUI execution")
            client_id = str(uuid.uuid4())
            print(f"[COMFY] Client ID: {client_id}")
            
            print(f"[WEBSOCKET] Connecting to ws://{COMFY_HOST}/ws?clientId={client_id}")
            ws = websocket.WebSocket()
            ws.connect(f"ws://{COMFY_HOST}/ws?clientId={client_id}")
            print(f"[WEBSOCKET] ✓ Connected")

            print(f"[COMFY] Submitting workflow to ComfyUI...")
            resp = requests.post(
                f"http://{COMFY_HOST}/prompt",
                json={"prompt": workflow, "client_id": client_id},
                timeout=30
            )
            print(f"[COMFY] Response status: {resp.status_code}")

            if resp.status_code != 200:
                print("[ERROR] ComfyUI rejected workflow")
                print(resp.text)
                return {"error": resp.text}

            prompt_id = resp.json()["prompt_id"]
            print(f"[COMFY] ✓ Prompt queued with ID: {prompt_id}")

            print(f"[EXECUTION] Waiting for workflow to complete...")
            message_count = 0
            while True:
                msg = json.loads(ws.recv())
                message_count += 1
                
                # Log progress messages
                if msg.get("type") == "executing":
                    node = msg["data"].get("node")
                    if node is None:
                        print(f"[EXECUTION] ✓ Workflow completed (received {message_count} messages)")
                        break
                    else:
                        print(f"[EXECUTION] Processing node: {node}")
                elif msg.get("type") == "progress":
                    value = msg["data"].get("value", 0)
                    max_val = msg["data"].get("max", 100)
                    print(f"[PROGRESS] {value}/{max_val}")

            print(f"[HISTORY] Fetching execution history...")
            history = requests.get(
                f"http://{COMFY_HOST}/history/{prompt_id}"
            ).json()
            print(f"[HISTORY] ✓ History retrieved")

            print(f"[OUTPUT] Processing output images...")
            outputs = []
            node_count = 0
            for node_id, node in history[prompt_id]["outputs"].items():
                node_count += 1
                images_in_node = node.get("images", [])
                print(f"[OUTPUT] Node {node_id}: {len(images_in_node)} image(s)")
                
                for idx, img in enumerate(images_in_node):
                    filename = img['filename']
                    print(f"[OUTPUT] Fetching image {idx+1}: {filename}")
                    params = (
                        f"filename={filename}"
                        f"&subfolder={img.get('subfolder','')}"
                        f"&type={img['type']}"
                    )
                    r = requests.get(f"http://{COMFY_HOST}/view?{params}")
                    print(f"[OUTPUT] Image size: {len(r.content)} bytes")
                    
                    print(f"[OUTPUT] Converting to fal Image object...")
                    try:
                        fal_image = Image.from_bytes(
                            r.content, 
                            format="png",
                            repository="cdn"
                        )
                        print(f"[OUTPUT] ✓ Image converted successfully")
                        print(f"[OUTPUT] ✓ Image URL: {fal_image.url[:80]}...")
                        outputs.append(fal_image)
                    except Exception as img_error:
                        print(f"[ERROR] Failed to convert image: {type(img_error).__name__}: {str(img_error)}")
                        traceback.print_exc()
                        raise

            ws.close()
            print(f"[WEBSOCKET] ✓ Closed")
            print("="*80)
            print(f"[SUCCESS] ✓ Workflow completed successfully! Generated {len(outputs)} image(s)")
            print("="*80)

            return {"status": "success", "images": outputs}

        except Exception as e:
            print("="*80)
            print(f"[ERROR] ✗ Exception occurred: {type(e).__name__}")
            print(f"[ERROR] Message: {str(e)}")
            print("[ERROR] Full traceback:")
            traceback.print_exc()
            print("="*80)
            return {"error": str(e)}
