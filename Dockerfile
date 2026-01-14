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

# 1. kijai/ComfyUI-KJNodes (provides ImageScaleToTotalPixels and other image processing nodes)
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git /comfyui/custom_nodes/ComfyUI-KJNodes \
    && cd /comfyui/custom_nodes/ComfyUI-KJNodes && git checkout 4dfb85dcc52e4315c33170d97bb987baa46d128b \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 2. cubiq/ComfyUI_essentials (provides utility nodes)
RUN git clone https://github.com/cubiq/ComfyUI_essentials.git /comfyui/custom_nodes/ComfyUI_essentials \
    && cd /comfyui/custom_nodes/ComfyUI_essentials \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Note: Qwen-specific nodes (TextEncodeQwenImageEditPlus, CFGNorm, ModelSamplingAuraFlow) 
# should be included with the Qwen models or in ComfyUI core.
# If workflow fails with missing nodes, these need to be added from the correct source.

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
