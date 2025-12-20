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
# ComfyUI Custom Nodes
# ---------------------------------------------------------

# 1. JPS-GER/ComfyUI_JPS-Nodes
RUN git clone https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git /comfyui/custom_nodes/ComfyUI_JPS-Nodes \
    && cd /comfyui/custom_nodes/ComfyUI_JPS-Nodes && git checkout 0e2a9aca02b17dde91577bfe4b65861df622dcaf \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 2. numz/ComfyUI-SeedVR2_VideoUpscaler
RUN git clone https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler.git /comfyui/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler \
    && cd /comfyui/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler && git checkout 58bc9e8bc946499352e0cb3a9fe0d0a61fd86791 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 3. MadiatorLabs/ComfyUI-RunpodDirect
RUN git clone https://github.com/MadiatorLabs/ComfyUI-RunpodDirect.git /comfyui/custom_nodes/ComfyUI-RunpodDirect \
    && cd /comfyui/custom_nodes/ComfyUI-RunpodDirect && git checkout f7cc02cccb499e0170d8040d1788bf44598e2709 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 4. MoonGoblinDev/Civicomfy
RUN git clone https://github.com/MoonGoblinDev/Civicomfy.git /comfyui/custom_nodes/Civicomfy \
    && cd /comfyui/custom_nodes/Civicomfy && git checkout 1fcd88d571a871cb29f15fa5b67bbf014339b1a6 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 5. kijai/ComfyUI-KJNodes
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git /comfyui/custom_nodes/ComfyUI-KJNodes \
    && cd /comfyui/custom_nodes/ComfyUI-KJNodes && git checkout 62a862db37d77a9a2e7611f638f9ff151a24fdec \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 6. ltdrdata/ComfyUI-Manager
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /comfyui/custom_nodes/ComfyUI-Manager \
    && cd /comfyui/custom_nodes/ComfyUI-Manager && git checkout de64af4a6873547668187f0e98433a8030880940 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 7. comfyui_essentials (via pip)
RUN pip install comfyui-essentials==1.1.0

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
