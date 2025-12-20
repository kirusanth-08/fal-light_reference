FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04 AS base

ARG COMFYUI_VERSION=latest
ARG ENABLE_PYTORCH_UPGRADE=false
ARG PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu128

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_PREFER_BINARY=1 \
    CMAKE_BUILD_PARALLEL_LEVEL=8

# ---------------------------------------------------------
# System & Python Setup
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common git git-lfs wget curl ffmpeg libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 ca-certificates \
    && git lfs install \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-dev python3.12-venv python3-pip python3-distutils build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python

RUN python3.12 -m ensurepip --upgrade && \
    python3.12 -m pip install --upgrade pip setuptools wheel

# ---------------------------------------------------------
# PyTorch (CUDA 12.8)
# ---------------------------------------------------------
RUN pip install torch==2.7.0 -f https://download.pytorch.org/whl/cu128/torch_stable.html

# ---------------------------------------------------------
# ComfyUI Setup
# ---------------------------------------------------------
WORKDIR /opt
RUN pip install comfy-cli
RUN yes | comfy --workspace /comfyui install --version "${COMFYUI_VERSION}" --nvidia

WORKDIR /comfyui

# ---------------------------------------------------------
# Extra dependencies
# ---------------------------------------------------------
RUN pip install requests websocket-client sageattention \
    accelerate transformers opencv-python insightface onnxruntime-gpu==1.18.0

# FIX: Add missing websocket packages for fal run
RUN pip install websocket-client websockets

# ---------------------------------------------------------
# ComfyUI Custom Nodes - Put custom nodes here
# ---------------------------------------------------------

# 1. ComfyRoll Custom Nodes (NO requirements.txt)
RUN git clone https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes.git /comfyui/custom_nodes/ComfyUI_Comfyroll_CustomNodes \
    && true

# 2. ComfyUI Essentials (HAS requirements)
RUN git clone https://github.com/cubiq/ComfyUI_essentials.git /comfyui/custom_nodes/ComfyUI_essentials \
    && pip install -r /comfyui/custom_nodes/ComfyUI_essentials/requirements.txt

# 3. comfyui_face_parsing (HAS requirements)
RUN git clone https://github.com/Ryuukeisyou/comfyui_face_parsing.git /comfyui/custom_nodes/comfyui_face_parsing \
    && pip install -r /comfyui/custom_nodes/comfyui_face_parsing/requirements.txt

# 4. ComfyUI LayerStyle Advance (HAS requirements)
RUN git clone https://github.com/chflame163/ComfyUI_LayerStyle_Advance.git /comfyui/custom_nodes/ComfyUI_LayerStyle_Advance \
    && pip install -r /comfyui/custom_nodes/ComfyUI_LayerStyle_Advance/requirements.txt

# 5. comfyui-custom-scripts (NO requirements)
RUN git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git /comfyui/custom_nodes/ComfyUI-Custom-Scripts \
    && true

# 6. ComfyUI Florence2 (HAS requirements)
RUN git clone https://github.com/kijai/ComfyUI-Florence2.git /comfyui/custom_nodes/ComfyUI-Florence2 \
    && pip install -r /comfyui/custom_nodes/ComfyUI-Florence2/requirements.txt

# 7. ComfyUI KJNodes (HAS requirements)
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git /comfyui/custom_nodes/ComfyUI-KJNodes \
    && pip install -r /comfyui/custom_nodes/ComfyUI-KJNodes/requirements.txt

# 8. ComfyUI Post-Processing Nodes (NO requirements)
RUN git clone https://github.com/EllangoK/ComfyUI-post-processing-nodes.git /comfyui/custom_nodes/ComfyUI-post-processing-nodes \
    && true

# 9. Masquerade Nodes (NO requirements)
RUN git clone https://github.com/BadCafeCode/masquerade-nodes-comfyui.git /comfyui/custom_nodes/masquerade-nodes-comfyui \
    && true

# 10. rgthree – Power Lora Loader (HAS requirements)
RUN git clone https://github.com/rgthree/rgthree-comfy.git /comfyui/custom_nodes/rgthree-comfy \
    && pip install -r /comfyui/custom_nodes/rgthree-comfy/requirements.txt

# 11. SeedVR2 Upscaler – alex-node-final (HAS requirements)
RUN git clone https://github.com/shangeethAlex/alex-node-final.git /comfyui/custom_nodes/ComfyUI-SeedVR2 \
    && pip install -r /comfyui/custom_nodes/ComfyUI-SeedVR2/requirements.txt

# ---------------------------------------------------------
# fal Runtime Requirements
# ---------------------------------------------------------
RUN pip install --no-cache-dir \
    boto3==1.35.74 \
    protobuf==4.25.1 \
    pydantic==2.10.6

ENV HF_HOME=/fal-volume/models/huggingface

WORKDIR /comfyui
EXPOSE 8188
