WORKFLOW_JSON={
  "input": {
    "uid": "testUid",
    "customNodes": [],
    "customModels": [],
    "images": [],
    "workflow": { 
      "1": {
        "inputs": {
          "strength": 1,
          "model": [
            "2",
            0
          ]
        },
        "class_type": "CFGNorm",
        "_meta": {
          "title": "CFGNorm"
        }
      },
      "2": {
        "inputs": {
          "shift": 3,
          "model": [
            "20",
            0
          ]
        },
        "class_type": "ModelSamplingAuraFlow",
        "_meta": {
          "title": "ModelSamplingAuraFlow"
        }
      },
      "3": {
        "inputs": {
          "prompt": "",
          "clip": [
            "76",
            0
          ],
          "vae": [
            "22",
            0
          ],
          "image1": [
            "39",
            0
          ],
          "image2": [
            "40",
            0
          ]
        },
        "class_type": "TextEncodeQwenImageEditPlus",
        "_meta": {
          "title": "TextEncodeQwenImageEditPlus"
        }
      },
      "7": {
        "inputs": {
          "image": "Photos-During-Golden-Hour-009.jpg"
        },
        "class_type": "LoadImage",
        "_meta": {
          "title": "Load Image"
        }
      },
      "10": {
        "inputs": {
          "pixels": [
            "39",
            0
          ],
          "vae": [
            "22",
            0
          ]
        },
        "class_type": "VAEEncode",
        "_meta": {
          "title": "VAE Encode"
        }
      },
      "11": {
        "inputs": {
          "prompt": "参考色调，移除图1原有的光照并参考图2的光照和色调对图1重新照明",
          "clip": [
            "76",
            0
          ],
          "vae": [
            "22",
            0
          ],
          "image1": [
            "39",
            0
          ],
          "image2": [
            "40",
            0
          ]
        },
        "class_type": "TextEncodeQwenImageEditPlus",
        "_meta": {
          "title": "TextEncodeQwenImageEditPlus"
        }
      },
      "12": {
        "inputs": {
          "samples": [
            "14",
            0
          ],
          "vae": [
            "22",
            0
          ]
        },
        "class_type": "VAEDecode",
        "_meta": {
          "title": "VAE Decode"
        }
      },
      "14": {
        "inputs": {
          "seed": 1053423613535130,
          "steps": 8,
          "cfg": 1,
          "sampler_name": "euler",
          "scheduler": "simple",
          "denoise": 1,
          "model": [
            "1",
            0
          ],
          "positive": [
            "11",
            0
          ],
          "negative": [
            "3",
            0
          ],
          "latent_image": [
            "10",
            0
          ]
        },
        "class_type": "KSampler",
        "_meta": {
          "title": "KSampler"
        }
      },
      "20": {
        "inputs": {
          "lora_name": "Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors",
          "strength_model": 1,
          "model": [
            "81",
            0
          ]
        },
        "class_type": "LoraLoaderModelOnly",
        "_meta": {
          "title": "LoraLoaderModelOnly"
        }
      },
      "22": {
        "inputs": {
          "vae_name": "qwen_image_vae.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
          "title": "Load VAE"
        }
      },
      "31": {
        "inputs": {
          "image": "istockphoto-1077242420-612x612.jpg"
        },
        "class_type": "LoadImage",
        "_meta": {
          "title": "Load Image"
        }
      },
      "39": {
        "inputs": {
          "upscale_method": "lanczos",
          "megapixels": 1,
          "image": [
            "31",
            0
          ]
        },
        "class_type": "ImageScaleToTotalPixels",
        "_meta": {
          "title": "ImageScaleToTotalPixels"
        }
      },
      "40": {
        "inputs": {
          "upscale_method": "lanczos",
          "megapixels": 1,
          "image": [
            "7",
            0
          ]
        },
        "class_type": "ImageScaleToTotalPixels",
        "_meta": {
          "title": "ImageScaleToTotalPixels"
        }
      },
      "60": {
        "inputs": {
          "image": [
            "39",
            0
          ]
        },
        "class_type": "easy imageSize",
        "_meta": {
          "title": "ImageSize"
        }
      },
      "61": {
        "inputs": {
          "image": [
            "40",
            0
          ]
        },
        "class_type": "easy imageSize",
        "_meta": {
          "title": "ImageSize"
        }
      },
      "76": {
        "inputs": {
          "clip_name": "qwen_2.5_vl_7b.safetensors",
          "type": "stable_diffusion",
          "device": "default"
        },
        "class_type": "CLIPLoader",
        "_meta": {
          "title": "Load CLIP"
        }
      },
      "77": {
        "inputs": {
          "unet_name": "Qwen-Image-Edit-2509_fp8_e4m3fn.safetensors",
          "weight_dtype": "default"
        },
        "class_type": "UNETLoader",
        "_meta": {
          "title": "Load Diffusion Model"
        }
      },
      "81": {
        "inputs": {
          "lora_name": "light_migrate.safetensors",
          "strength_model": 1,
          "model": [
            "77",
            0
          ]
        },
        "class_type": "LoraLoaderModelOnly",
        "_meta": {
          "title": "LoraLoaderModelOnly"
        }
      },
      "82": {
        "inputs": {
          "model": "seedvr2_ema_7b_fp16.safetensors",
          "device": "cuda:0",
          "blocks_to_swap": 32,
          "swap_io_components": True,
          "offload_device": "cpu",
          "cache_model": "sdpa",
          "attention_mode": "sdpa"
        },
        "class_type": "SeedVR2LoadDiTModel",
        "_meta": {
          "title": "SeedVR2 (Down)Load DiT Model"
        }
      },
      "83": {
        "inputs": {
          "model": "ema_vae_fp16.safetensors",
          "device": "cuda:0",
          "encode_tiled": True,
          "encode_tile_size": 1024,
          "encode_tile_overlap": 128,
          "decode_tiled": True,
          "decode_tile_size": 1024,
          "decode_tile_overlap": 128,
          "tile_debug": "False",
          "offload_device": "cpu",
          "cache_model": False
        },
        "class_type": "SeedVR2LoadVAEModel",
        "_meta": {
          "title": "SeedVR2 (Down)Load VAE Model"
        }
      },
      "84": {
        "inputs": {
          "upscale_method": "lanczos",
          "scale_by": 0.5000000000000001,
          "image": [
            "12",
            0
          ]
        },
        "class_type": "ImageScaleBy",
        "_meta": {
          "title": "Upscale Image By"
        }
      },
      "85": {
        "inputs": {
          "seed": 1419136762,
          "resolution": [
            "96",
            0
          ],
          "max_resolution": 4096,
          "batch_size": 5,
          "uniform_batch_size": False,
          "color_correction": "lab",
          "temporal_overlap": 0,
          "prepend_frames": 0,
          "input_noise_scale": 0,
          "latent_noise_scale": 0,
          "offload_device": "cpu",
          "enable_debug": False,
          "image": [
            "84",
            0
          ],
          "dit": [
            "82",
            0
          ],
          "vae": [
            "83",
            0
          ]
        },
        "class_type": "SeedVR2VideoUpscaler",
        "_meta": {
          "title": "SeedVR2 Video Upscaler (v2.5.14)"
        }
      },
      "87": {
        "inputs": {
          "filename_prefix": "ComfyUI",
          "images": [
            "85",
            0
          ]
        },
        "class_type": "SaveImage",
        "_meta": {
          "title": "Save Image"
        }
      },
      "96": {
        "inputs": {
          "int_a": [
            "97",
            0
          ],
          "float_b": 2
        },
        "class_type": "Multiply Int Float (JPS)",
        "_meta": {
          "title": "Multiply Int Float (JPS)"
        }
      },
      "97": {
        "inputs": {
          "image": [
            "31",
            0
          ]
        },
        "class_type": "GetImageSize+",
        "_meta": {
          "title": "🔧 Get Image Size"
        }
      }
    }
  }
}