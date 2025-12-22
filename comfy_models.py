MODEL_LIST = [

    # =======================================================
    # 1. MAIN SKIN CHECKPOINT (CUSTOM)
    # =======================================================
    {
        "url": "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors",
        "path": "/data/models/diffusion_models/Qwen-Image-Edit-2509_fp8_e4m3fn.safetensors",
        "target": "/comfyui/models/diffusion_models/Qwen-Image-Edit-2509_fp8_e4m3fn.safetensors"
    },

    # =======================================================
    # 2. SEEDVR2 UPSCALER ✅ FINAL FIXED LOCATION
    # =======================================================
    {
        "url": "https://huggingface.co/numz/SeedVR2_comfyUI/resolve/main/seedvr2_ema_7b_fp16.safetensors",
        "path": "/data/models/SEEDVR2/seedvr2_ema_7b_fp16.safetensors",
        "target": "/comfyui/models/SEEDVR2/seedvr2_ema_7b_fp16.safetensors"
    },
    {
        "url": "https://huggingface.co/numz/SeedVR2_comfyUI/resolve/main/ema_vae_fp16.safetensors",
        "path": "/data/models/SEEDVR2/ema_vae_fp16.safetensors",
        "target": "/comfyui/models/SEEDVR2/ema_vae_fp16.safetensors"
    },

    # =======================================================
    # 3. VAE FOR QWEN-IMAGE MODEL
    # =======================================================
    {
        "url": "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors",
        "path": "/data/models/vae/qwen_image_vae.safetensors",
        "target": "/comfyui/models/vae/qwen_image_vae.safetensors"
    },

    # =======================================================
    # 4. CLIP MODELS FOR QWEN-IMAGE MODEL
    # =======================================================
    {
        "url": "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b.safetensors",
        "path": "/data/models/text_encoders/qwen_2.5_vl_7b.safetensors",
        "target": "/comfyui/models/text_encoders/qwen_2.5_vl_7b.safetensors"
    },

    # =======================================================
    # 5. LORA MODELS FOR QWEN-IMAGE-EDIT MODEL
    # =======================================================

    {
        "url": "https://huggingface.co/dx8152/Qwen-Edit-2509-Light-Migration/resolve/main/%E5%8F%82%E8%80%83%E8%89%B2%E8%B0%83.safetensors",
        "path": "/data/models/loras/light_migrate.safetensors",
        "target": "/comfyui/models/loras/light_migrate.safetensors"
    },
    {
        "url": "https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors",
        "path": "/data/models/loras/Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors",
        "target": "/comfyui/models/loras/Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors"
    }
]
