#!/usr/bin/env python3
"""
Vercel Serverless Entry Point for AI Gallery
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

# Import from the app module
from app.models import create_tables, get_db, User, Render
from app.utils.config import get_settings

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Gallery",
    description="AI image generation gallery with style exploration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on first request
@app.on_event("startup")
async def startup_event():
    """Initialize database for serverless environment"""
    try:
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

settings = get_settings()

@app.get("/api")
@app.get("/api/")
async def root():
    """API root endpoint"""
    return {
        "message": "AI Gallery API",
        "status": "running",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Gallery is running on Vercel"}

@app.get("/api/search")
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
                "image_url": f"/api/images/{r.id}",  # Changed to API endpoint
                "thumb_url": f"/api/images/{r.id}?thumb=true",
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

@app.get("/api/styles")
async def get_styles(db: Session = Depends(get_db)):
    """Get distinct style phrases for search suggestions"""
    try:
        styles = db.query(Render.style_phrase).filter(Render.status == "done").distinct().all()
        return {"styles": [s[0] for s in styles]}
    except Exception as e:
        logger.error(f"Get styles error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get styles")

@app.get("/api/default")
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
                "image_url": f"/api/images/{r.id}",
                "thumb_url": f"/api/images/{r.id}?thumb=true",
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

        return {"results": results}

    except Exception as e:
        logger.error(f"Get default renders error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get default renders")

@app.get("/api/render/{render_id}")
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
            "image_url": f"/api/images/{render.id}",
            "thumb_url": f"/api/images/{render.id}?thumb=true",
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

@app.get("/api/images/{render_id}")
async def serve_image(render_id: str, thumb: bool = Query(False), db: Session = Depends(get_db)):
    """Serve image files - placeholder for external storage integration"""
    try:
        render = db.query(Render).filter(Render.id == render_id).first()
        if not render:
            raise HTTPException(status_code=404, detail="Image not found")

        # In serverless, we'd return a redirect to external storage
        # For now, return placeholder response
        return {
            "message": "Image serving requires external storage integration",
            "render_id": render_id,
            "thumb": thumb,
            "note": "Integrate with Vercel Blob, Cloudinary, or S3 for actual image serving"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Serve image error: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")

@app.get("/api/me")
async def get_current_user():
    """Get current user session info (mock for now)"""
    return {
        "user_id": None,
        "email": None,
        "credits": 0,
        "lifetime_spend": 0,
        "unlocked_status": False
    }

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        headers = request.headers

        # In production, verify the webhook signature here
        logger.info(f"Received Stripe webhook: {len(payload)} bytes")

        return {"received": True}

    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

@app.post("/api/checkout")
async def create_checkout():
    """Create Stripe checkout session (mock implementation)"""
    return {
        "checkout_url": "https://checkout.stripe.com/mock-session-123",
        "session_id": "cs_mock_123",
        "message": "Mock checkout session created"
    }

@app.get("/api/billing-portal")
async def billing_portal():
    """Redirect to Stripe customer portal (mock implementation)"""
    return {
        "portal_url": "https://billing.stripe.com/p/session_mock_456",
        "message": "Mock billing portal session created"
    }

# Handler for Vercel
handler = app