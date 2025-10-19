from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import replicate
import openai
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)

@dataclass
class ImageResult:
    """Result from image generation"""
    image_url: str
    image_bytes: Optional[bytes] = None
    metadata: Dict[str, Any] = None

class ImageModelAdapter(ABC):
    """Abstract base class for image model adapters"""

    @abstractmethod
    async def text2img(self, prompt: str, negative: Optional[str], params: Dict[str, Any]) -> List[ImageResult]:
        """Generate images from text prompt"""
        pass

    @abstractmethod
    async def img2img(self, image_path: str, prompt: str, strength: float, params: Dict[str, Any]) -> List[ImageResult]:
        """Generate images from image + text prompt"""
        pass

class ReplicateAdapter(ImageModelAdapter):
    """Adapter for Replicate models"""

    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)

    async def text2img(self, prompt: str, negative: Optional[str], params: Dict[str, Any]) -> List[ImageResult]:
        """Generate images using Replicate SDXL"""
        try:
            model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

            input_params = {
                "prompt": prompt,
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
                "num_outputs": params.get("num_outputs", 1),
                "scheduler": params.get("scheduler", "K_EULER"),
                "num_inference_steps": params.get("num_inference_steps", 50),
                "guidance_scale": params.get("guidance_scale", 7.5),
                "seed": params.get("seed"),
            }

            if negative:
                input_params["negative_prompt"] = negative

            # Run the model
            output = self.client.run(model, input=input_params)

            # Convert output to ImageResult objects
            results = []
            for url in output:
                results.append(ImageResult(
                    image_url=url,
                    metadata={
                        "model": model,
                        "input_params": input_params,
                        "provider": "replicate"
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"Replicate text2img error: {e}")
            raise

    async def img2img(self, image_path: str, prompt: str, strength: float, params: Dict[str, Any]) -> List[ImageResult]:
        """Generate images using Replicate SDXL img2img"""
        try:
            model = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

            # Read and encode the input image
            with open(image_path, "rb") as f:
                image_data = f.read()

            input_params = {
                "prompt": prompt,
                "image": image_data,
                "strength": strength,
                "width": params.get("width", 1024),
                "height": params.get("height", 1024),
                "num_outputs": params.get("num_outputs", 1),
                "scheduler": params.get("scheduler", "K_EULER"),
                "num_inference_steps": params.get("num_inference_steps", 50),
                "guidance_scale": params.get("guidance_scale", 7.5),
                "seed": params.get("seed"),
            }

            # Run the model
            output = self.client.run(model, input=input_params)

            # Convert output to ImageResult objects
            results = []
            for url in output:
                results.append(ImageResult(
                    image_url=url,
                    metadata={
                        "model": model,
                        "input_params": input_params,
                        "provider": "replicate",
                        "input_image": image_path
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"Replicate img2img error: {e}")
            raise

class OpenAIAdapter(ImageModelAdapter):
    """Adapter for OpenAI DALL-E models"""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    async def text2img(self, prompt: str, negative: Optional[str], params: Dict[str, Any]) -> List[ImageResult]:
        """Generate images using DALL-E 3"""
        try:
            # DALL-E 3 doesn't support negative prompts, so we'll incorporate them into the main prompt
            if negative:
                prompt = f"{prompt}. Avoid: {negative}"

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=params.get("size", "1024x1024"),
                quality=params.get("quality", "standard"),
                n=1,  # DALL-E 3 only supports n=1
                style=params.get("style", "vivid")
            )

            results = []
            for image in response.data:
                results.append(ImageResult(
                    image_url=image.url,
                    metadata={
                        "model": "dall-e-3",
                        "input_params": {
                            "prompt": prompt,
                            "size": params.get("size", "1024x1024"),
                            "quality": params.get("quality", "standard"),
                            "style": params.get("style", "vivid")
                        },
                        "provider": "openai",
                        "revised_prompt": image.revised_prompt
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"OpenAI text2img error: {e}")
            raise

    async def img2img(self, image_path: str, prompt: str, strength: float, params: Dict[str, Any]) -> List[ImageResult]:
        """OpenAI doesn't have direct img2img, use image editing instead"""
        try:
            # For now, we'll use DALL-E 2's edit endpoint as a workaround
            # This requires an alpha mask, so we'll create a simple one

            # Read the input image
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Create a simple mask (for demonstration - in production you'd want better masking)
            image = Image.open(io.BytesIO(image_data))
            mask = Image.new("RGBA", image.size, (0, 0, 0, 128))  # Semi-transparent mask
            mask_bytes = io.BytesIO()
            mask.save(mask_bytes, format="PNG")
            mask_bytes.seek(0)

            response = self.client.images.edit(
                model="dall-e-2",  # Only DALL-E 2 supports editing
                image=image_data,
                mask=mask_bytes.getvalue(),
                prompt=prompt,
                n=1,
                size=params.get("size", "1024x1024")
            )

            results = []
            for image in response.data:
                results.append(ImageResult(
                    image_url=image.url,
                    metadata={
                        "model": "dall-e-2",
                        "input_params": {
                            "prompt": prompt,
                            "size": params.get("size", "1024x1024"),
                            "strength": strength
                        },
                        "provider": "openai",
                        "input_image": image_path
                    }
                ))

            return results

        except Exception as e:
            logger.error(f"OpenAI img2img error: {e}")
            raise

class ModelRegistry:
    """Registry for available image models"""

    def __init__(self, settings):
        self.settings = settings
        self.adapters = {}

        # Initialize adapters based on available API keys
        if settings.replicate_api_token:
            self.adapters["replicate:sdxl"] = ReplicateAdapter(settings.replicate_api_token)

        if settings.openai_api_key:
            self.adapters["openai:dalle3"] = OpenAIAdapter(settings.openai_api_key)
            self.adapters["openai:dalle2"] = OpenAIAdapter(settings.openai_api_key)

    def get_adapter(self, model_key: str) -> ImageModelAdapter:
        """Get adapter for model key"""
        if model_key not in self.adapters:
            raise ValueError(f"Model {model_key} not available")
        return self.adapters[model_key]

    def list_models(self) -> List[str]:
        """List available models"""
        return list(self.adapters.keys())

    def build_prompt(self, base_prompt: str, style_phrase: str) -> str:
        """Build effective prompt from base + style"""
        return f"{base_prompt} {style_phrase}"