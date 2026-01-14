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

# 1. obisin/ComfyUI-FSampler
RUN git clone https://github.com/obisin/ComfyUI-FSampler.git /comfyui/custom_nodes/ComfyUI-FSampler \
    && cd /comfyui/custom_nodes/ComfyUI-FSampler && git checkout 032a40ffbf1f93a67c1d6b9fa550979ce33c8ffd \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 2. M1kep/ComfyLiterals
RUN git clone https://github.com/M1kep/ComfyLiterals.git /comfyui/custom_nodes/ComfyLiterals \
    && cd /comfyui/custom_nodes/ComfyLiterals && git checkout bdddb08ca82d90d75d97b1d437a652e0284a32ac \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 3. JPS-GER/ComfyUI_JPS-Nodes
RUN git clone https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git /comfyui/custom_nodes/ComfyUI_JPS-Nodes \
    && cd /comfyui/custom_nodes/ComfyUI_JPS-Nodes && git checkout 0e2a9aca02b17dde91577bfe4b65861df622dcaf \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 4. ClownsharkBatwing/RES4LYF
RUN git clone https://github.com/ClownsharkBatwing/RES4LYF.git /comfyui/custom_nodes/RES4LYF \
    && cd /comfyui/custom_nodes/RES4LYF && git checkout 46de917234f9fef3f2ab411c41e07aa3c633f4f7 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 5. MadiatorLabs/ComfyUI-RunpodDirect
RUN git clone https://github.com/MadiatorLabs/ComfyUI-RunpodDirect.git /comfyui/custom_nodes/ComfyUI-RunpodDirect \
    && cd /comfyui/custom_nodes/ComfyUI-RunpodDirect && git checkout f7cc02cccb499e0170d8040d1788bf44598e2709 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 6. MoonGoblinDev/Civicomfy
RUN git clone https://github.com/MoonGoblinDev/Civicomfy.git /comfyui/custom_nodes/Civicomfy \
    && cd /comfyui/custom_nodes/Civicomfy && git checkout 1fcd88d571a871cb29f15fa5b67bbf014339b1a6 \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 7. kijai/ComfyUI-KJNodes
RUN git clone https://github.com/kijai/ComfyUI-KJNodes.git /comfyui/custom_nodes/ComfyUI-KJNodes \
    && cd /comfyui/custom_nodes/ComfyUI-KJNodes && git checkout 4dfb85dcc52e4315c33170d97bb987baa46d128b \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# 8. cubiq/ComfyUI_essentials (provides: GetImageSize+)
RUN git clone https://github.com/cubiq/ComfyUI_essentials.git /comfyui/custom_nodes/ComfyUI_essentials \
    && cd /comfyui/custom_nodes/ComfyUI_essentials \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

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
