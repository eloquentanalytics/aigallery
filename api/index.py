#!/usr/bin/env python3
"""
Vercel Serverless Entry Point for AI Gallery - Simplified Version
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Configure logging for Vercel
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

@app.get("/api")
@app.get("/api/")
async def root():
    """API root endpoint"""
    return {
        "message": "AI Gallery API",
        "status": "running",
        "version": "1.0.0",
        "environment": "vercel",
        "docs": "Visit /api/docs for API documentation"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Gallery is running on Vercel",
        "environment": os.environ.get("VERCEL_ENV", "unknown"),
        "region": os.environ.get("VERCEL_REGION", "unknown")
    }

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "test": "success",
        "message": "API is working correctly",
        "timestamp": "2025-10-19"
    }

@app.get("/api/search")
async def search_renders():
    """Search renders - simplified for testing"""
    return {
        "results": [
            {
                "id": "test-1",
                "style_phrase": "oil painting",
                "model_key": "test:model",
                "base_prompt": "A beautiful landscape",
                "image_url": "/api/images/test-1",
                "created_at": "2025-10-19T00:00:00"
            }
        ],
        "total": 1,
        "status": "mock_data"
    }

@app.get("/api/styles")
async def get_styles():
    """Get available styles - simplified"""
    return {
        "styles": ["oil painting", "watercolor", "pixel art", "digital art"],
        "status": "mock_data"
    }

@app.get("/api/default")
async def get_default_renders():
    """Get default renders - simplified"""
    return {
        "results": [
            {
                "id": "default-1",
                "style_phrase": "digital art",
                "model_key": "test:model",
                "base_prompt": "Abstract digital artwork",
                "image_url": "/api/images/default-1",
                "created_at": "2025-10-19T00:00:00"
            }
        ],
        "status": "mock_data"
    }

@app.get("/api/images/{render_id}")
async def serve_image(render_id: str):
    """Serve image placeholder"""
    return {
        "message": "Image placeholder",
        "render_id": render_id,
        "note": "Images will be served from external storage in production"
    }

@app.get("/api/me")
async def get_current_user():
    """Get current user session info"""
    return {
        "user_id": None,
        "email": None,
        "credits": 0,
        "status": "mock_user"
    }

# Handler for Vercel - this is required
handler = app