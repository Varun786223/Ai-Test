import os
import base64
from typing import Union
import numpy as np
from PIL import Image
import io
from datetime import datetime

def ensure_output_dirs():
    """Ensure output directories exist."""
    os.makedirs("output/images", exist_ok=True)
    os.makedirs("output/models", exist_ok=True)

def process_image(image_data: Union[str, bytes]) -> str:
    """
    Process the generated image and save it to disk.
    
    Args:
        image_data: Base64 encoded image data or bytes
        
    Returns:
        str: Path to the saved image
    """
    ensure_output_dirs()
    
    # Convert base64 to image if necessary
    if isinstance(image_data, str):
        image_data = base64.b64decode(image_data)
    
    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(image_data))
    
    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    filename = f"output/images/generation_{timestamp}.png"
    
    # Save image
    image.save(filename)
    
    return filename

def save_3d_model(model_data: Union[str, bytes]) -> str:
    """
    Save the generated 3D model to disk.
    
    Args:
        model_data: Base64 encoded model data or bytes
        
    Returns:
        str: Path to the saved 3D model
    """
    ensure_output_dirs()
    
    # Convert base64 to bytes if necessary
    if isinstance(model_data, str):
        model_data = base64.b64decode(model_data)
    
    # Generate unique filename
    timestamp = int(datetime.now().timestamp())
    filename = f"output/models/model_{timestamp}.glb"
    
    # Save model
    with open(filename, "wb") as f:
        f.write(model_data)
    
    return filename

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Decode a base64 string to PIL Image.
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        Image.Image: PIL Image object
    """
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data)) 