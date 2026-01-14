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
            if requests.get(url, timeout=5).status_code == 200:
                return True
        except (requests.RequestException, Exception) as e:
            # Log but continue retrying
            if _ == retries - 1:
                print(f"Server check failed after {retries} attempts: {e}")
        time.sleep(delay)
    return False

def fal_image_to_base64(img: Image) -> str:
    pil = img.to_pil()
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def validate_image_url(url: str):
    """Validate image URL to prevent SSRF attacks."""
    from urllib.parse import urlparse
    import ipaddress
    
    parsed = urlparse(url)
    
    # Only allow http/https
    if parsed.scheme not in ['http', 'https']:
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed.")
    
    # Check hostname
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing hostname")
    
    # Prevent localhost/private IP access
    hostname_lower = hostname.lower()
    if hostname_lower in ['localhost', 'localhost.localdomain']:
        raise ValueError("Access to localhost not allowed")
    
    # Check for private IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            raise ValueError(f"Access to private IP addresses not allowed: {hostname}")
    except ValueError:
        # Not an IP address, check for common private patterns
        if any(hostname_lower.startswith(prefix) for prefix in ['192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.']):
            raise ValueError(f"Access to private networks not allowed: {hostname}")

def image_url_to_base64(image_url: str, max_size_mb: int = 50) -> str:
    """Download image from URL and convert to base64 with validation."""
    validate_image_url(image_url)
    
    # Add retry logic for transient failures
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content length before downloading
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size_mb * 1024 * 1024:
                raise ValueError(f"Image too large. Max size: {max_size_mb}MB")
            
            # Download with size limit
            content = BytesIO()
            total_size = 0
            max_bytes = max_size_mb * 1024 * 1024
            
            for chunk in response.iter_content(8192):
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise ValueError(f"Image exceeds {max_size_mb}MB limit")
                content.write(chunk)
            
            content.seek(0)
            
            # Validate it's actually an image and convert to PNG
            try:
                pil = PILImage.open(content)
                # Verify it's a valid image by loading it
                pil.verify()
                # Reopen for actual conversion (verify closes the file)
                content.seek(0)
                pil = PILImage.open(content)
                
                # Convert to RGB if necessary (handles RGBA, L, etc.)
                if pil.mode not in ['RGB', 'L']:
                    if pil.mode == 'RGBA':
                        # Create white background for transparency
                        background = PILImage.new('RGB', pil.size, (255, 255, 255))
                        background.paste(pil, mask=pil.split()[3] if len(pil.split()) == 4 else None)
                        pil = background
                    else:
                        pil = pil.convert('RGB')
                
                buf = BytesIO()
                pil.save(buf, format="PNG")
                return base64.b64encode(buf.getvalue()).decode()
            except Exception as img_err:
                raise ValueError(f"Invalid image format: {str(img_err)}")
            
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            raise ValueError(f"Failed to download image after {max_retries} attempts: {str(e)}")

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
    request_timeout = 300  # 5 minutes max per request
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
    def handler(self, input: LightTransferInput, request=None):
        try:
            # Validate workflow structure
            job = copy.deepcopy(WORKFLOW_JSON)
            if "input" not in job or "workflow" not in job["input"]:
                raise ValueError("Invalid workflow structure")
            
            workflow = job["input"]["workflow"]

            main_img = f"main_{uuid.uuid4().hex}.png"
            ref_img = f"ref_{uuid.uuid4().hex}.png"

            # Download and validate images
            try:
                main_b64 = image_url_to_base64(input.main_image_url)
                ref_b64 = image_url_to_base64(input.reference_image_url)
            except ValueError as img_err:
                return {"error": f"Image validation failed: {str(img_err)}"}
            except Exception as img_err:
                return {"error": f"Failed to download images: {str(img_err)}"}

            upload_images([
                {"name": main_img, "image": main_b64},
                {"name": ref_img, "image": ref_b64}
            ])

            # Validate and update workflow nodes
            if "31" not in workflow or "inputs" not in workflow["31"]:
                raise ValueError("Invalid workflow: missing node 31")
            if "7" not in workflow or "inputs" not in workflow["7"]:
                raise ValueError("Invalid workflow: missing node 7")
            
            workflow["31"]["inputs"]["image"] = main_img
            workflow["7"]["inputs"]["image"] = ref_img

            seed_value = random.randint(0, 2**63 - 1)
            apply_fixed_values(workflow, seed_value)

            # Run ComfyUI
            client_id = str(uuid.uuid4())
            ws = websocket.WebSocket()
            ws.settimeout(240)  # 4 minute websocket timeout
            temp_files = []  # Track temp files for cleanup
            
            try:
                ws.connect(f"ws://{COMFY_HOST}/ws?clientId={client_id}")

                resp = requests.post(
                    f"http://{COMFY_HOST}/prompt",
                    json={"prompt": workflow, "client_id": client_id},
                    timeout=30
                )
                
                # Log detailed error if request fails
                if resp.status_code != 200:
                    error_detail = resp.text
                    print(f"ComfyUI Error Response: {error_detail}")
                    return {"error": f"ComfyUI rejected workflow: {error_detail}"}
                
                prompt_id = resp.json()["prompt_id"]

                # Wait for completion with timeout
                import time
                start_time = time.time()
                while time.time() - start_time < 240:  # 4 minute max
                    msg = json.loads(ws.recv())
                    if msg.get("type") == "executing" and msg["data"]["node"] is None:
                        break
                else:
                    raise TimeoutError("Workflow execution timed out")

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
                        temp_files.append(temp_path)
                        with open(temp_path, "wb") as f:
                            f.write(r.content)
                        try:
                            images.append(Image.from_path(temp_path, request=request))
                        except Exception as upload_err:
                            print(f"Image upload warning: {upload_err}")
                            # Fallback: use CDN repository which doesn't require auth
                            images.append(Image.from_path(temp_path, repository="cdn"))

                return {"status": "success", "images": images}
            finally:
                # Cleanup websocket
                try:
                    ws.close()
                except Exception as ws_err:
                    print(f"Warning: Failed to close websocket: {ws_err}")
                
                # Cleanup temp files
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as file_err:
                        print(f"Warning: Failed to remove temp file {temp_file}: {file_err}")

        except TimeoutError as e:
            return {"error": f"Request timed out: {str(e)}"}
        except ValueError as e:
            # User input validation errors - don't log full traceback
            return {"error": str(e)}
        except Exception as e:
            # Unexpected errors - log full traceback
            traceback.print_exc()
            return {"error": f"Internal server error: {str(e)}"}
