WORKFLOW_JSON={
  "input": {
    "uid": "testUid",
    "customNodes": [],
    "customModels": [],
    "images": [
      {
        "name": "01.jpg",
        "image": "base64.."
      }
    ],
    "workflow": {
      "1": {
        "inputs": {
          "samples": [
            "10",
            0
          ],
          "mask": [
            "28",
            1
          ]
        },
        "class_type": "SetLatentNoiseMask",
        "_meta": {
          "title": "Set Latent Noise Mask"
        }
      },
      "2": {
        "inputs": {
          "mask": [
            "13",
            0
          ]
        },
        "class_type": "MaskToImage",
        "_meta": {
          "title": "Convert Mask to Image"
        }
      },
      "3": {
        "inputs": {
          "samples": [
            "29",
            0
          ],
          "vae": [
            "24",
            2
          ]
        },
        "class_type": "VAEDecode",
        "_meta": {
          "title": "VAE Decode"
        }
      },
      "5": {
        "inputs": {
          "text1": "BEFORE",
          "text2": "AFTER",
          "footer_height": 100,
          "font_name": "impact.ttf",
          "font_size": 50,
          "mode": "dark",
          "border_thickness": 20,
          "image1": [
            "30",
            0
          ],
          "image2": [
            "23",
            0
          ]
        },
        "class_type": "CR Simple Image Compare",
        "_meta": {
          "title": "📱 CR Simple Image Compare"
        }
      },
      "6": {
        "inputs": {
          "device": "cuda"
        },
        "class_type": "FaceParsingModelLoader(FaceParsing)",
        "_meta": {
          "title": "FaceParsingModelLoader(FaceParsing)"
        }
      },
      "7": {
        "inputs": {},
        "class_type": "FaceParsingProcessorLoader(FaceParsing)",
        "_meta": {
          "title": "FaceParsingProcessorLoader(FaceParsing)"
        }
      },
      "9": {
        "inputs": {
          "text": [
            "26",
            0
          ]
        },
        "class_type": "ShowText|pysssss",
        "_meta": {
          "title": "Show Text 🐍"
        }
      },
      "10": {
        "inputs": {
          "pixels": [
            "30",
            0
          ],
          "vae": [
            "24",
            2
          ]
        },
        "class_type": "VAEEncode",
        "_meta": {
          "title": "VAE Encode"
        }
      },
      "13": {
        "inputs": {
          "expand": -5,
          "incremental_expandrate": 0,
          "tapered_corners": True,
          "flip_input": False,
          "blur_radius": 4,
          "lerp_alpha": 1,
          "decay_factor": 1,
          "fill_holes": False,
          "mask": [
            "14",
            0
          ]
        },
        "class_type": "GrowMaskWithBlur",
        "_meta": {
          "title": "Grow Mask With Blur"
        }
      },
      "14": {
        "inputs": {
          "background": False,
          "skin": False,
          "nose": False,
          "eye_g": False,
          "r_eye": True,
          "l_eye": True,
          "r_brow": True,
          "l_brow": True,
          "r_ear": False,
          "l_ear": False,
          "mouth": True,
          "u_lip": True,
          "l_lip": True,
          "hair": False,
          "hat": False,
          "ear_r": False,
          "neck_l": False,
          "neck": False,
          "cloth": False,
          "result": [
            "15",
            1
          ]
        },
        "class_type": "FaceParsingResultsParser(FaceParsing)",
        "_meta": {
          "title": "EXCLUSION"
        }
      },
      "15": {
        "inputs": {
          "model": [
            "6",
            0
          ],
          "processor": [
            "7",
            0
          ],
          "image": [
            "3",
            0
          ]
        },
        "class_type": "FaceParse(FaceParsing)",
        "_meta": {
          "title": "FaceParse(FaceParsing)"
        }
      },
      "16": {
        "inputs": {
          "force_resize_width": 0,
          "force_resize_height": 0,
          "image": [
            "3",
            0
          ],
          "mask": [
            "2",
            0
          ]
        },
        "class_type": "Cut By Mask",
        "_meta": {
          "title": "Cut By Mask"
        }
      },
      "17": {
        "inputs": {
          "text_input": "",
          "task": "region_caption",
          "fill_mask": True,
          "keep_model_loaded": False,
          "max_new_tokens": 1024,
          "num_beams": 3,
          "do_sample": True,
          "output_mask_select": "",
          "seed": 767440173469992,
          "image": [
            "30",
            0
          ],
          "florence2_model": [
            "22",
            0
          ]
        },
        "class_type": "Florence2Run",
        "_meta": {
          "title": "Florence2Run"
        }
      },
      "18": {
        "inputs": {
          "amount": 0.4,
          "image": [
            "19",
            0
          ]
        },
        "class_type": "ImageCASharpening+",
        "_meta": {
          "title": "🔧 Image Contrast Adaptive Sharpening"
        }
      },
      "19": {
        "inputs": {
          "intensity": 0.03,
          "scale": 10,
          "temperature": 0,
          "vignette": 0,
          "image": [
            "23",
            0
          ]
        },
        "class_type": "FilmGrain",
        "_meta": {
          "title": "Film Grain Effect"
        }
      },
      "20": {
        "inputs": {
          "text": [
            "26",
            0
          ],
          "clip": [
            "27",
            1
          ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
          "title": "CLIP Text Encode (Prompt)"
        }
      },
      "21": {
        "inputs": {
          "filename_prefix": "body1_",
          "images": [
            "18",
            0
          ]
        },
        "class_type": "SaveImage",
        "_meta": {
          "title": "Save Image"
        }
      },
      "22": {
        "inputs": {
          "model": "microsoft/Florence-2-base",
          "precision": "fp16",
          "attention": "sdpa",
          "convert_to_safetensors": False
        },
        "class_type": "DownloadAndLoadFlorence2Model",
        "_meta": {
          "title": "DownloadAndLoadFlorence2Model"
        }
      },
      "23": {
        "inputs": {
          "x": 0,
          "y": 0,
          "resize_source": False,
          "destination": [
            "3",
            0
          ],
          "source": [
            "30",
            0
          ],
          "mask": [
            "13",
            0
          ]
        },
        "class_type": "ImageCompositeMasked",
        "_meta": {
          "title": "ImageCompositeMasked"
        }
      },
      "24": {
        "inputs": {
          "ckpt_name": "VXVI_LastFame_DMD2.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
          "title": "Load Checkpoint"
        }
      },
      "25": {
        "inputs": {
          "text": "redness, rash, wrinkles, oily skin, pores enlarged, rough texture, plastic skin, waxy skin, airbrushed, fake textures, lowres, blurry, deformed face, face morph, cartoon, cgi, 3d render, doll-like, blur",
          "clip": [
            "27",
            1
          ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
          "title": "NEGATIVE"
        }
      },
      "26": {
        "inputs": {
          "part1": "",
          "part2": [
            "17",
            2
          ],
          "part3": " beautiful face, flawless smooth skin, clean natural skin texture, fine pores, subtle tone variation, soft complexion, radiant healthy skin, high detail skin texture, natural glow, photorealistic, masterpiece",
          "part4": "",
          "separator": " "
        },
        "class_type": "CR Combine Prompt",
        "_meta": {
          "title": "⚙️ CR Combine Prompt"
        }
      },
      "27": {
        "inputs": {
          "PowerLoraLoaderHeaderWidget": {
            "type": "PowerLoraLoaderHeaderWidget"
          },
          "lora_1": {
            "on": False,
            "lora": "epiCRealness.safetensors",
            "strength": 1.04
          },
          "lora_2": {
            "on": False,
            "lora": "epiCRealismXL_KiSS_Enhancer.safetensors",
            "strength": 0.82
          },
          "lora_3": {
            "on": False,
            "lora": "epiCPhotoXL.safetensors",
            "strength": 1.5
          },
          "lora_4": {
            "on": False,
            "lora": "real_humans.safetensors",
            "strength": 1.7
          },
          "➕ Add Lora": "",
          "model": [
            "24",
            0
          ],
          "clip": [
            "24",
            1
          ]
        },
        "class_type": "Power Lora Loader (rgthree)",
        "_meta": {
          "title": "Power Lora Loader (rgthree)"
        }
      },
      "28": {
        "inputs": {
          "face": True,
          "hair": False,
          "body": True,
          "clothes": False,
          "accessories": False,
          "background": True,
          "confidence": 0.4,
          "detail_method": "VITMatte",
          "detail_erode": 6,
          "detail_dilate": 6,
          "black_point": 0.01,
          "white_point": 0.99,
          "process_detail": True,
          "device": "cuda",
          "max_megapixels": 2,
          "images": [
            "30",
            0
          ]
        },
        "class_type": "LayerMask: PersonMaskUltra V2",
        "_meta": {
          "title": "LayerMask: PersonMaskUltra V2(Advance)"
        }
      },
      "29": {
        "inputs": {
          "seed": 179859358044891,
          "steps": 30,
          "cfg": 2,
          "sampler_name": "dpmpp_2m",
          "scheduler": "karras",
          "denoise": 0.3,
          "model": [
            "27",
            0
          ],
          "positive": [
            "20",
            0
          ],
          "negative": [
            "25",
            0
          ],
          "latent_image": [
            "1",
            0
          ]
        },
        "class_type": "KSampler",
        "_meta": {
          "title": "KSampler"
        }
      },
      "30": {
        "inputs": {
          "model": "seedvr2_ema_7b_fp16.safetensors",
          "seed": 3524851102,
          "new_resolution": 2048,
          "batch_size": 5,
          "color_correction": "none",
          "input_noise_scale": 0,
          "latent_noise_scale": 0.03,
          "images": [
            "32",
            0
          ],
          "block_swap_config": [
            "33",
            0
          ],
          "extra_args": [
            "31",
            0
          ]
        },
        "class_type": "SeedVR2",
        "_meta": {
          "title": "SeedVR2 Video Upscaler"
        }
      },
      "31": {
        "inputs": {
          "tiled_vae": True,
          "vae_tile_size": 1024,
          "vae_tile_overlap": 128,
          "preserve_vram": True,
          "cache_model": True,
          "enable_debug": False,
          "device": "cuda:0"
        },
        "class_type": "SeedVR2ExtraArgs",
        "_meta": {
          "title": "SeedVR2 Extra Args"
        }
      },
      "32": {
        "inputs": {
          "image": "01.jpg"
        },
        "class_type": "LoadImage",
        "_meta": {
          "title": "Load Image"
        }
      },
      "33": {
        "inputs": {
          "blocks_to_swap": 15,
          "offload_io_components": True
        },
        "class_type": "SeedVR2BlockSwap",
        "_meta": {
          "title": "SeedVR2 BlockSwap Config"
        }
      }
    }
  }
}