from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging
from contextlib import asynccontextmanager

from .models import create_tables, get_db, User, Render
from .services import AuthService, StripeService, RenderService
from .utils.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Gallery application...")
    create_tables()
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    yield
    # Shutdown
    logger.info("Shutting down AI Gallery application...")

app = FastAPI(
    title="AI Gallery",
    description="AI image generation gallery with style exploration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
settings = get_settings()
auth_service = AuthService(settings)
stripe_service = StripeService(settings)
render_service = RenderService(settings)

# Static files - serve frontend
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Gallery is running"}

@app.get("/")
async def root():
    """Serve the frontend app"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "AI Gallery API", "docs": "/docs"}

# Auth endpoints
@app.post("/auth/google")
async def google_auth(
    request: Request,
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticate with Google ID token"""
    try:
        user_info = await auth_service.verify_google_token(token)
        user = auth_service.get_or_create_user(db, user_info)

        # Set session cookie
        response = {"user_id": user.id, "email": user.email}
        # TODO: Set HttpOnly cookie
        return response
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/me")
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user session info"""
    # TODO: Extract user from session cookie
    # For now, return mock data
    return {
        "user_id": None,
        "email": None,
        "credits": 0,
        "lifetime_spend": 0,
        "unlocked_status": False
    }

# Search and discovery endpoints
@app.get("/search")
async def search_renders(
    q: Optional[str] = None,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search renders by style phrase"""
    query = db.query(Render).filter(Render.status == "done")

    if q:
        query = query.filter(Render.style_phrase.contains(q))

    renders = query.offset(offset).limit(limit).all()

    return {
        "results": [
            {
                "id": r.id,
                "style_phrase": r.style_phrase,
                "model_key": r.model_key,
                "image_path": r.image_path,
                "thumb_path": r.thumb_path,
                "created_at": r.created_at
            }
            for r in renders
        ],
        "total": query.count(),
        "offset": offset,
        "limit": limit
    }

@app.get("/styles")
async def get_styles(db: Session = Depends(get_db)):
    """Get distinct style phrases for search suggestions"""
    styles = db.query(Render.style_phrase).filter(Render.status == "done").distinct().all()
    return {"styles": [s[0] for s in styles]}

@app.get("/default")
async def get_default_renders(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get curated default render set"""
    renders = db.query(Render).filter(Render.status == "done").limit(limit).all()

    return {
        "results": [
            {
                "id": r.id,
                "style_phrase": r.style_phrase,
                "model_key": r.model_key,
                "image_path": r.image_path,
                "thumb_path": r.thumb_path,
                "created_at": r.created_at
            }
            for r in renders
        ]
    }

@app.get("/render/{render_id}")
async def get_render(render_id: str, db: Session = Depends(get_db)):
    """Get single render detail"""
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
        "created_at": render.created_at
    }

# Pro features
@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    request: Request = None
):
    """Upload image for style application"""
    # TODO: Authenticate user
    # TODO: Save uploaded file
    # TODO: Return upload_id
    return {"upload_id": "mock-upload-id", "message": "Upload not yet implemented"}

@app.post("/apply-style")
async def apply_style(
    upload_id: str = Form(...),
    style_phrase: str = Form(...),
    model_key: str = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Apply style to uploaded image"""
    # TODO: Authenticate user
    # TODO: Check credits
    # TODO: Enqueue render job
    return {"message": "Style application not yet implemented"}

# File serving
@app.get("/images/{year}/{month}/{filename}")
async def serve_image(year: int, month: int, filename: str):
    """Serve image files"""
    file_path = f"data/images/{year}/{month}/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Image not found")

# Stripe endpoints
@app.post("/checkout")
async def create_checkout(
    product_type: str = Form(...),  # "credits", "pro", "library"
    request: Request = None
):
    """Create Stripe checkout session"""
    # TODO: Implement Stripe checkout
    return {"checkout_url": "https://checkout.stripe.com/mock", "message": "Checkout not yet implemented"}

@app.get("/billing-portal")
async def billing_portal(request: Request = None):
    """Redirect to Stripe customer portal"""
    # TODO: Implement billing portal
    return {"portal_url": "https://billing.stripe.com/mock", "message": "Billing portal not yet implemented"}

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    # TODO: Implement webhook processing
    return {"message": "Webhook processing not yet implemented"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)