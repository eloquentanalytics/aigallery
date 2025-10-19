import uuid
import os
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
from datetime import datetime
from PIL import Image
import io
import logging
from sqlalchemy.orm import Session

from ..models.database import Render, SessionLocal
from .model_adapters import ModelRegistry

logger = logging.getLogger(__name__)

class RenderService:
    def __init__(self, settings):
        self.settings = settings
        self.model_registry = ModelRegistry(settings)

        # Background thread executor (limit concurrent API calls as per DESIGN.md)
        self.executor = ThreadPoolExecutor(max_workers=2)

    def enqueue_render(self, render_id: str):
        """Enqueue render for background processing"""
        logger.info(f"Enqueueing render {render_id}")
        self.executor.submit(self.process_render, render_id)

    def process_render(self, render_id: str):
        """Process render in background thread"""
        with SessionLocal() as db:
            try:
                render = db.query(Render).filter(Render.id == render_id).first()
                if not render:
                    logger.error(f"Render {render_id} not found")
                    return

                logger.info(f"Processing render {render_id}")

                # Get model adapter
                adapter = self.model_registry.get_adapter(render.model_key)

                # Build effective prompt
                effective_prompt = self.model_registry.build_prompt(
                    render.base_prompt, render.style_phrase
                )

                # Default generation parameters
                params = {
                    "width": 1024,
                    "height": 1024,
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 50
                }

                # Add any custom params from metadata
                if render.render_metadata and "params" in render.render_metadata:
                    params.update(render.render_metadata["params"])

                # Generate image
                if render.input_image_path:
                    # Image-to-image
                    results = asyncio.run(adapter.img2img(
                        render.input_image_path,
                        effective_prompt,
                        strength=0.8,
                        params=params
                    ))
                else:
                    # Text-to-image
                    results = asyncio.run(adapter.text2img(
                        effective_prompt,
                        negative=None,  # TODO: Add negative prompt support
                        params=params
                    ))

                if not results:
                    raise Exception("No images generated")

                # Process the first result
                result = results[0]

                # Download and save image
                image_bytes = self.download_image(result.image_url)
                if not image_bytes:
                    raise Exception("Failed to download generated image")

                # Save files
                self.save_image_files(render, image_bytes, db)

                # Update render status
                render.status = "done"
                render.render_metadata = {
                    **(render.render_metadata or {}),
                    "generation": result.metadata,
                    "effective_prompt": effective_prompt,
                    "completed_at": datetime.utcnow().isoformat()
                }

                db.commit()
                logger.info(f"Completed render {render_id}")

            except Exception as e:
                logger.error(f"Failed to process render {render_id}: {e}")

                # Update render status to failed
                render = db.query(Render).filter(Render.id == render_id).first()
                if render:
                    render.status = "failed"
                    render.render_metadata = {
                        **(render.render_metadata or {}),
                        "error": str(e),
                        "failed_at": datetime.utcnow().isoformat()
                    }
                    db.commit()

                # TODO: Refund credits if this was a paid render

    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None

    def save_image_files(self, render: Render, image_bytes: bytes, db: Session):
        """Save image and thumbnail files"""
        # Create directory structure by date
        now = datetime.utcnow()
        year = now.year
        month = now.month

        image_dir = f"data/images/{year}/{month:02d}"
        os.makedirs(image_dir, exist_ok=True)

        # Generate filenames
        filename = f"{render.id}.webp"
        thumb_filename = f"{render.id}-thumb.webp"

        image_path = f"{image_dir}/{filename}"
        thumb_path = f"{image_dir}/{thumb_filename}"

        # Save full image
        image = Image.open(io.BytesIO(image_bytes))
        image.save(image_path, "WEBP", quality=90)

        # Create and save thumbnail
        thumb_image = image.copy()
        thumb_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
        thumb_image.save(thumb_path, "WEBP", quality=80)

        # Update render paths
        render.image_path = f"images/{year}/{month:02d}/{filename}"
        render.thumb_path = f"images/{year}/{month:02d}/{thumb_filename}"

        logger.info(f"Saved image files for render {render.id}")

    async def create_render(self,
                          db: Session,
                          user_id: Optional[int],
                          style_phrase: str,
                          model_key: str,
                          base_prompt: str,
                          input_image_path: Optional[str] = None,
                          cost_credits: int = 1) -> Render:
        """Create new render record and enqueue for processing"""

        # Validate model exists
        if model_key not in self.model_registry.list_models():
            raise ValueError(f"Model {model_key} not available")

        # Create render record
        render = Render(
            id=str(uuid.uuid4()),
            user_id=user_id,
            style_phrase=style_phrase,
            model_key=model_key,
            base_prompt=base_prompt,
            input_image_path=input_image_path,
            status="pending",
            cost_credits=cost_credits,
            image_path="",  # Will be set when processing completes
            thumb_path="",  # Will be set when processing completes
            render_metadata={
                "created_at": datetime.utcnow().isoformat(),
                "model_available": True
            }
        )

        db.add(render)
        db.commit()
        db.refresh(render)

        # Enqueue for background processing
        self.enqueue_render(render.id)

        return render

    async def get_render_status(self, db: Session, render_id: str) -> Optional[Dict[str, Any]]:
        """Get render status"""
        render = db.query(Render).filter(Render.id == render_id).first()
        if not render:
            return None

        return {
            "id": render.id,
            "status": render.status,
            "style_phrase": render.style_phrase,
            "model_key": render.model_key,
            "base_prompt": render.base_prompt,
            "image_path": render.image_path,
            "thumb_path": render.thumb_path,
            "created_at": render.created_at,
            "metadata": render.render_metadata
        }

    async def create_matrix_renders(self,
                                  db: Session,
                                  base_prompt: str,
                                  style_phrases: list[str],
                                  model_keys: list[str],
                                  user_id: Optional[int] = None) -> list[Render]:
        """Create renders for all combinations of styles and models"""
        renders = []

        for style_phrase in style_phrases:
            for model_key in model_keys:
                render = await self.create_render(
                    db=db,
                    user_id=user_id,
                    style_phrase=style_phrase,
                    model_key=model_key,
                    base_prompt=base_prompt,
                    cost_credits=0  # Free for public gallery generation
                )
                renders.append(render)

        logger.info(f"Created {len(renders)} matrix renders")
        return renders