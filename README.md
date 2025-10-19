# AI Gallery

A minimal image generation gallery with style matrix exploration. Python-only, single container, filesystem storage.

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone <repository-url>
cd ai-gallery

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Build and run
docker-compose up --build

# Seed the database
docker-compose exec ai-gallery python seed_data.py
```

### Option 2: Local Development

```bash
# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run database setup and seeding
python -c "from app.models import create_tables; create_tables()"
python seed_data.py

# Start the application
python app_simple.py
```

The application will be available at: http://localhost:8000

## 🚀 Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/eloquentanalytics/aigallery)

1. Click the deploy button above
2. Connect your GitHub account
3. Deploy instantly!

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed setup instructions.

## 📁 Project Structure

```
ai-gallery/
├── app/                    # Main application code
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   └── utils/             # Utilities and configuration
├── data/                  # Persistent data (SQLite + images)
├── frontend/              # Next.js frontend (optional)
├── tests/                 # Test suite
├── app_simple.py          # Main FastAPI application
├── seed_data.py           # Database seeding script
├── Dockerfile             # Container definition
└── docker-compose.yml     # Container orchestration
```

## 🎯 Core Features

### Public Gallery
- Browse AI-generated images across multiple styles and models
- Search by style phrase (e.g., "oil painting", "pixel art")
- Fixed result sets for predictable, atomic browsing experiences

### Pro Features (Credits Required)
- Upload images and apply discovered styles via image-to-image
- Request new style matrix runs across models

### Payment System
- Stripe integration for credit packs and library access
- Lifetime spend threshold unlocks full access
- One-time ZIP library purchase with permissive licensing

## 🔧 Configuration

Required environment variables:

- `GOOGLE_CLIENT_ID` - For user authentication
- `STRIPE_SECRET_KEY` - For payment processing
- `STRIPE_WEBHOOK_SECRET` - For webhook verification
- `REPLICATE_API_TOKEN` - For Replicate AI models
- `OPENAI_API_KEY` - For OpenAI DALL-E models
- `SECRET_KEY` - For session security

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_api.py -v
python -m pytest tests/test_database.py -v

# Test basic functionality
python test_basic.py
```

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `GET /search` - Search renders by style phrase
- `GET /styles` - Get available style phrases
- `GET /default` - Get curated default renders
- `GET /render/{id}` - Get single render details

### User & Auth
- `GET /me` - Current user session info
- `POST /auth/google` - Google OAuth authentication

### Payment & Billing
- `POST /checkout` - Create Stripe checkout session
- `GET /billing-portal` - Access Stripe customer portal
- `POST /webhook/stripe` - Stripe webhook handler

### File Serving
- `GET /images/{year}/{month}/{filename}` - Serve image files

## 🐳 Deployment

### Single Container Deployment

```bash
# Build the container
docker build -t ai-gallery .

# Run with mounted volume
docker run -v $(pwd)/data:/app/data -p 8000:8000 ai-gallery

# Or use docker-compose
docker-compose up --build
```

### Production Deployment

1. **Deploy to any container platform** (Fly.io, Railway, Render, etc.)
2. **Set environment variables** in your deployment platform
3. **Configure Stripe webhook** endpoint to `yoursite.com/webhook/stripe`
4. **Mount persistent volume** for `/app/data`

## 🎨 Architecture

### Single-Container Design
- **FastAPI** serves both API and static files
- **SQLite** database (single file)
- **Filesystem** image storage
- **In-memory** credit caching with Stripe as source of truth
- **Background threads** for image generation processing

### Data Model
```sql
-- Users: minimal local data, Stripe is source of truth
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    google_sub TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    stripe_customer_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Renders: flat denormalized table
CREATE TABLE renders (
    id TEXT PRIMARY KEY,  -- uuid
    user_id INTEGER REFERENCES users(id),
    style_phrase TEXT NOT NULL,
    model_key TEXT NOT NULL,  -- "replicate:sdxl", "openai:dalle3"
    base_prompt TEXT NOT NULL,
    image_path TEXT NOT NULL,
    thumb_path TEXT NOT NULL,
    input_image_path TEXT,  -- for img2img
    status TEXT CHECK(status IN ('pending','done','failed')),
    cost_credits INTEGER DEFAULT 1,
    render_metadata JSON,  -- generation params, provider response
    stripe_event_id TEXT,  -- for idempotency
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Background Processing

Simple background processing using Python ThreadPoolExecutor:

- **Max 2 concurrent API calls** to external providers
- **Automatic retry logic** for failed generations
- **File handling** with WebP compression and thumbnail generation
- **Database updates** with generation metadata

## 💳 Stripe Integration

- **Credits** stored in Stripe customer metadata
- **Webhooks** handle payment completions
- **Customer Portal** for subscription management
- **Library licensing** via one-time payments

## 📈 Scaling Considerations

This single-container architecture is designed for:
- **~10k+ images** (SQLite performance)
- **External API rate limits** (not your compute)
- **Simple deployment** (one container, one volume)

When you need more:
- Refactor to separate worker processes
- Move to PostgreSQL
- Add Redis for job queuing
- Implement horizontal scaling

## 🔒 Security

- **Google OIDC** for authentication
- **HttpOnly cookies** for sessions
- **Stripe webhooks** for payment verification
- **API rate limiting** via simple in-memory counters
- **NSFW filtering** via provider safety flags

## 📝 License

This implementation is designed for the AI Gallery concept outlined in the technical design documents. Adapt as needed for your specific use case.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `python -m pytest tests/ -v`
4. Submit a pull request

For questions or issues, please refer to the technical design documents in `/DEV/`.