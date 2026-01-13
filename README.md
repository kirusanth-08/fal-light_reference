# Light Reference Deployment

A Docker-based deployment for Qwen Image Edit light reference/migration model using ComfyUI, optimized for fal.

## Overview

This repository contains a complete deployment setup for the Qwen Image Edit light reference model, which applies lighting and color tone from a reference image to a main image.

### Required Inputs

**Both inputs are mandatory:**
- **Main Image**: The image you want to relight/recolor
- **Reference Image**: The image whose lighting and color tone will be applied to the main image

### Example Use Cases

**Example 1: Indoor Lighting Transfer**
- Main Image: Portrait with neutral lighting
- Reference Image: Scene with warm golden hour lighting
- Result: Portrait with warm golden hour lighting applied

**Example 2: Color Tone Migration**
- Main Image: Product photo with cool white lighting
- Reference Image: Scene with warm sunset tones
- Result: Product photo with warm sunset color tones

## Quick Start


### Local Deployment

1. **Clone the repository or navigate to your workspace directory**


### Model Download
All the models downloaded must be stored in a persistent volume which in fal's case is /data
So the setup function in the handler.py takes in a MODEL_LIST and checks if it already exists in the data directory. If it does then its alright. It proceeds to symlink the models directory of the container's comfyui with the /data/models
If it does not exist in the data then it downloads the model and stores it in the data/models directory. 
To add models you need to edit the comfy_models.py file and update the list there.
It contains:
 - url: url which the code will use to download the model
 - path: the persistent volume path where the model will be downloaded
 - target: the container comfyui target where the model should be present so that comfyui can access it



## Configuration



### Workflow Configuration

The `workflow.py` contains a complete ComfyUI workflow with the format that is acceptable by the api
## Custom Nodes

The deployment includes the following custom ComfyUI node:

- **ComfyUI-KJNodes**: Provides ImageScaleToTotalPixels node for image scaling

Custom nodes are added using the Dockerfile. You can see the custom nodes section in the Dockerfile on how to add nodes. Some custom nodes don't have a requirements file so you need to skip the requirements installation part for them.

## Usage

1. **Setup**: Change the model paths and urls and the custom nodes according to your workflow
2. **Python Version**: The python version in the dockerfile should match the local computer. Python 3.12 is used in this deployment.
3. **Testing**: Add the fal api key in your env and select the appropriate team. Then use the command ```fal run handler.py::LightTransfer``` to run the container. It will give you 3 links. Use the playground link to test your workflow.

   **In the playground, you'll see two required fields:**
   - Main Image URL: The image you want to relight/recolor
   - Reference Image URL: The image whose lighting will be applied
   
   Both fields are mandatory. The playground will show example URLs by default.

4. **Deploy**: Use ```fal deploy handler.py::LightTransfer``` to deploy the serverless endpoint completely.

5. **Querying Using Endpoint**: We will mostly be using the asynchronous endpoint. Once you have that endpoint you need to send request to it in this format
```POST https://queue.fal.run/VISIONREIMAGINE/d11f80a6-1d26-452b-bdf2-14eacd823871/```
Inside the headers you need to add the following 
```"Content-Type: application/json"``` 
```"Authorization: Key $FAL_API_KEY"```

In body you need to pass the required image URLs:

**Required Request Body:**
```json
{
  "main_image_url": "https://example.com/your-main-image.jpg",
  "reference_image_url": "https://example.com/your-reference-image.jpg"
}
```

**Sample Request with Example Images:**
```json
{
  "main_image_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800",
  "reference_image_url": "https://images.unsplash.com/photo-1495954484750-af469f2f9be5?w=800"
}
```

Note: Both `main_image_url` and `reference_image_url` are mandatory fields.

Now you will get the response in this format
```json
{
    "status": "IN_QUEUE",
    "request_id": "af0b0652-d0ae-4eed-867f-167f9d970db0",
    "response_url": "https://queue.fal.run/VISIONREIMAGINE/d11f80a6-1d26-452b-bdf2-14eacd823871/requests/af0b0652-d0ae-4eed-867f-167f9d970db0",
    "status_url": "https://queue.fal.run/VISIONREIMAGINE/d11f80a6-1d26-452b-bdf2-14eacd823871/requests/af0b0652-d0ae-4eed-867f-167f9d970db0/status",
    "cancel_url": "https://queue.fal.run/VISIONREIMAGINE/d11f80a6-1d26-452b-bdf2-14eacd823871/requests/af0b0652-d0ae-4eed-867f-167f9d970db0/cancel",
    "logs": null,
    "metrics": {},
    "queue_position": 0
}```
You can use the status_url with the same headers to check the status and then once you get the completed status you can use the response_url to see your response. You should get the response in this format
```json
{
    "status": "success",
    "images": [
        {
            "filename": "ComfyUI_00002_.png",
            "image": {
                "url": "https://fal.media/files/koala/FepkJXVcW306v7fF5alrA_6750ac9ada0e4b4a9a87b01536e594cc.png",
                "content_type": "image/png",
                "file_name": "6750ac9ada0e4b4a9a87b01536e594cc.png",
                "file_size": 2185448,
                "width": null,
                "height": null
            }
        }
    ]
}

```

