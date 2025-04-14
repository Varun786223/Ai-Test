import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from memory import MemoryManager
from utils import process_image, save_3d_model
import os
from dotenv import load_dotenv
import base64
from PIL import Image
import io
from datetime import datetime
import aiohttp
import json
from openfabric import Stub, Remote, AppModel, InputClass, OutputClass, ConfigClass, schema, manifest

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize memory manager
memory_manager = MemoryManager()

# Initialize local LLM (using DeepSeek as specified in readme)
try:
    model_name = "deepseek-ai/deepseek-coder-6.7b-base"  # Using DeepSeek as specified
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    logger.info("Successfully loaded DeepSeek model")
except Exception as e:
    logger.error(f"Failed to load language model: {str(e)}")
    raise

# Define schemas for the apps
text_to_image_schema = schema.Schema(
    input=schema.Input(
        prompt=schema.String(description="Text prompt for image generation")
    ),
    output=schema.Output(
        image=schema.String(description="Base64 encoded generated image")
    )
)

image_to_3d_schema = schema.Schema(
    input=schema.Input(
        image=schema.String(description="Base64 encoded input image")
    ),
    output=schema.Output(
        model=schema.String(description="Base64 encoded 3D model")
    )
)

# Create manifests for the apps
text_to_image_manifest = manifest.Manifest(
    id=os.getenv("TEXT_TO_IMAGE_APP_ID"),
    name="Text to Image Generator",
    description="Generates images from text prompts",
    schema=text_to_image_schema
)

image_to_3d_manifest = manifest.Manifest(
    id=os.getenv("IMAGE_TO_3D_APP_ID"),
    name="Image to 3D Converter",
    description="Converts images to 3D models",
    schema=image_to_3d_schema
)

class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

def execute(model: AppModel) -> None:
    """
    Main execution entry point for handling a model pass.

    Args:
        model (AppModel): The model object containing request and response structures.
    """
    try:
        # Retrieve input
        request: InputClass = model.request
        prompt = request.prompt

        # Retrieve user config
        user_config: ConfigClass = configurations.get('super-user', None)
        logging.info(f"{configurations}")

        # Initialize the Stub and Remote with app IDs and manifests
        app_ids = user_config.app_ids if user_config else [
            os.getenv("TEXT_TO_IMAGE_APP_ID"),
            os.getenv("IMAGE_TO_3D_APP_ID")
        ]
        stub = Stub(app_ids)
        remote = Remote(app_ids)

        # Register manifests
        remote.register_manifest(text_to_image_manifest)
        remote.register_manifest(image_to_3d_manifest)

        # Expand prompt using local LLM
        expanded_prompt = expand_prompt(prompt)
        logger.info(f"Expanded prompt: {expanded_prompt}")

        # Generate image using Text-to-Image app
        image_response = stub.execute(
            os.getenv("TEXT_TO_IMAGE_APP_ID"),
            {"prompt": expanded_prompt}
        )
        
        if not image_response.success:
            raise Exception("Image generation failed")

        # Process the generated image
        image_path = process_image(image_response.data)

        # Convert to 3D using Image-to-3D app
        model_3d_response = stub.execute(
            os.getenv("IMAGE_TO_3D_APP_ID"),
            {"image": image_path}
        )

        if not model_3d_response.success:
            raise Exception("3D model generation failed")

        # Save the 3D model
        model_path = save_3d_model(model_3d_response.data)

        # Store in memory
        if request.session_id:
            memory_manager.store(
                session_id=request.session_id,
                prompt=prompt,
                expanded_prompt=expanded_prompt,
                image_path=image_path,
                model_path=model_path
            )

        # Prepare response
        response: OutputClass = model.response
        response.message = "Generation successful"
        response.data = {
            "image_path": image_path,
            "model_path": model_path,
            "expanded_prompt": expanded_prompt
        }

    except Exception as e:
        logger.error(f"Error in execute: {str(e)}")
        response: OutputClass = model.response
        response.message = f"Error: {str(e)}"
        response.success = False

def expand_prompt(prompt: str) -> str:
    """Use local LLM to expand and enhance the user's prompt."""
    try:
        inputs = tokenizer(prompt, return_tensors="pt", max_length=100, truncation=True)
        outputs = model.generate(
            **inputs,
            max_length=200,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        expanded_prompt = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return expanded_prompt
    except Exception as e:
        logger.error(f"Error in expand_prompt: {str(e)}")
        return prompt  # Return original prompt if expansion fails

if __name__ == "__main__":
    import uvicorn
    app = FastAPI()
    uvicorn.run(app, host="0.0.0.0", port=8888) 