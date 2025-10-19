#!/usr/bin/env python3
"""
Simplified AI Gallery FastAPI Application for Testing
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models import create_tables, get_db, User, Render
from app.utils.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Gallery",
    description="AI image generation gallery with style exploration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
create_tables()
os.makedirs("data/images", exist_ok=True)
os.makedirs("data/uploads", exist_ok=True)

# Serve static files if they exist
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

settings = get_settings()

@app.get("/")
async def root():
    """Serve the frontend app or API info"""
    if os.path.exists("static/index.html"):
        with open("static/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)

    return {
        "message": "AI Gallery API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Gallery is running"}

@app.get("/search")
async def search_renders(
    q: Optional[str] = Query(None, description="Search query for style phrases"),
    offset: int = Query(0, description="Result offset"),
    limit: int = Query(10, description="Result limit"),
    db: Session = Depends(get_db)
):
    """Search renders by style phrase"""
    try:
        query = db.query(Render).filter(Render.status == "done")

        if q:
            query = query.filter(Render.style_phrase.contains(q))

        total = query.count()
        renders = query.offset(offset).limit(limit).all()

        results = []
        for r in renders:
            results.append({
                "id": r.id,
                "style_phrase": r.style_phrase,
                "model_key": r.model_key,
                "base_prompt": r.base_prompt,
                "image_path": r.image_path,
                "thumb_path": r.thumb_path,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

        return {
            "results": results,
            "total": total,
            "offset": offset,
            "limit": limit,
            "query": q
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/styles")
async def get_styles(db: Session = Depends(get_db)):
    """Get distinct style phrases for search suggestions"""
    try:
        styles = db.query(Render.style_phrase).filter(Render.status == "done").distinct().all()
        return {"styles": [s[0] for s in styles]}
    except Exception as e:
        logger.error(f"Get styles error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get styles")

@app.get("/default")
async def get_default_renders(
    limit: int = Query(10, description="Number of default renders to return"),
    db: Session = Depends(get_db)
):
    """Get curated default render set"""
    try:
        renders = (
            db.query(Render)
            .filter(Render.status == "done")
            .order_by(Render.created_at.desc())
            .limit(limit)
            .all()
        )

        results = []
        for r in renders:
            results.append({
                "id": r.id,
                "style_phrase": r.style_phrase,
                "model_key": r.model_key,
                "base_prompt": r.base_prompt,
                "image_path": r.image_path,
                "thumb_path": r.thumb_path,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

        return {"results": results}

    except Exception as e:
        logger.error(f"Get default renders error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get default renders")

@app.get("/render/{render_id}")
async def get_render(render_id: str, db: Session = Depends(get_db)):
    """Get single render detail"""
    try:
        render = db.query(Render).filter(Render.id == render_id).first()
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")

        return {
            "id": render.id,
            "style_phrase": render.style_phrase,
            "model_key": render.model_key,
            "base_prompt": render.base_prompt,
            "image_path": render.image_path,
            "thumb_path": render.thumb_path,
            "input_image_path": render.input_image_path,
            "status": render.status,
            "metadata": render.render_metadata,
            "created_at": render.created_at.isoformat() if render.created_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get render error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get render")

@app.get("/images/{year}/{month}/{filename}")
async def serve_image(year: int, month: int, filename: str):
    """Serve image files"""
    file_path = f"data/images/{year}/{month}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/me")
async def get_current_user():
    """Get current user session info (mock for now)"""
    return {
        "user_id": None,
        "email": None,
        "credits": 0,
        "lifetime_spend": 0,
        "unlocked_status": False
    }

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks (mock implementation)"""
    try:
        payload = await request.body()
        headers = request.headers

        # In production, you would verify the webhook signature here
        # For testing, we'll just log and return success

        logger.info(f"Received Stripe webhook: {len(payload)} bytes")

        return {"received": True}

    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@app.post("/checkout")
async def create_checkout():
    """Create Stripe checkout session (mock implementation)"""
    return {
        "checkout_url": "https://checkout.stripe.com/mock-session-123",
        "session_id": "cs_mock_123",
        "message": "Mock checkout session created"
    }

@app.get("/billing-portal")
async def billing_portal():
    """Redirect to Stripe customer portal (mock implementation)"""
    return {
        "portal_url": "https://billing.stripe.com/p/session_mock_456",
        "message": "Mock billing portal session created"
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    # Use PORT from environment for Heroku, or argument, or default to 8000
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    uvicorn.run("app_simple:app", host="0.0.0.0", port=port, reload=False)