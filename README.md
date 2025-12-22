# Kora WAN 2.2 Deployment

A Docker-based deployment for the WAN 2.2 text-to-video model using ComfyUI, optimized for fal and featuring advanced upscaling capabilities.

## Overview

This repository contains a complete deployment setup for the WAN 2.2 model, which is a powerful text-to-image generation system. The deployment includes:



## Quick Start


### Local Deployment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/noobprograms/kora-wan-t2i.git
   cd kora-wan-t2i
   ```


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

The deployment includes several custom ComfyUI nodes:

- **comfyui-kjnodes**: Advanced node collection
- **comfyui_controlnet_aux**: ControlNet auxiliary models
- **cg-use-everywhere**: Global node utilities
- **comfyui-easy-use**: Simplified workflow nodes
- **RES4LYF**: Custom upscaling and enhancement nodes

All these custom nodes are added using the docker file. You can see the 46-52 lines in the Dockerfile on how to add custom nodes. Some custom nodes don't have a requirements file so you need to skip the requirements installation part for them

## Usage

1. **Setup**: Change the model paths and urls and the custom nodes according to your workflow
2. **Python Version**: The python version in teh dockerfile should match the local computer. My PC uses python 3.12. So the dockerfile was modified to use python 3.12
3. **Testing**: Add the fal api key in your env and select the appropriate team. Then use the command ```fal run handler.py::KoraProApp``` to run the container. It will give you 3 links. Use the playground link to test your workflow.py there.
4. **Deploy**: Use ```fal deploy handler.py::KoraProApp``` to deploy the serverless endpoint completely.

5. **Querying Using Endpoint**: We will mostly be using the asynchronous endpoint. Once you have that endpoint you need to send request to it in this format
```POST https://queue.fal.run/VISIONREIMAGINE/d11f80a6-1d26-452b-bdf2-14eacd823871/```
Inside the headers you need to add the following 
```"Content-Type: application/json"``` 
```"Authorization: Key $FAL_API_KEY"```

In body you just need to pass in the workflow.py

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

