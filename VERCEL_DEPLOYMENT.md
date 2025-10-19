# Vercel Deployment Guide

Deploy the AI Gallery to Vercel's serverless platform with zero configuration.

## 🚀 Quick Deployment

### Prerequisites

1. **GitHub Repository**
   - Push your code to GitHub
   - Ensure all changes are committed

2. **Vercel Account**
   - Sign up at: https://vercel.com
   - Connect your GitHub account

3. **Environment Variables**
   - Prepare your API keys and secrets

### Step 1: Deploy to Vercel

#### Option A: Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from project directory
vercel

# Follow prompts:
# - Link to existing project? N
# - Project name: ai-gallery
# - Deploy? Y
```

#### Option B: Vercel Dashboard
1. Go to: https://vercel.com/new
2. Import your GitHub repository
3. Configure project settings
4. Deploy

### Step 2: Setup Database

#### Option A: Vercel Postgres (Recommended)
```bash
# Add Vercel Postgres to your project
vercel postgres create

# This will automatically set DATABASE_URL in your environment
```

#### Option B: External Database (Neon, PlanetScale, etc.)
```bash
# Set DATABASE_URL environment variable
vercel env add DATABASE_URL

# Enter your database URL:
# postgresql://user:password@host:port/database
```

### Step 3: Configure Environment Variables

```bash
# Add all required environment variables
vercel env add GOOGLE_CLIENT_ID
vercel env add STRIPE_SECRET_KEY
vercel env add STRIPE_WEBHOOK_SECRET
vercel env add REPLICATE_API_TOKEN
vercel env add OPENAI_API_KEY
vercel env add SECRET_KEY

# Deploy with new environment variables
vercel --prod
```

## 📊 Architecture Changes for Vercel

### 🎨 Full-Stack Deployment

**Complete Application:**
- ✅ **Next.js Frontend** - Modern gallery interface with auto-scroll, search, and responsive design
- ✅ **FastAPI Backend** - Serverless API for all data operations
- ✅ **Dual build system** - Both frontend and backend deploy automatically

### 🔄 Serverless Adaptations Made

1. **Frontend Structure**
   - Next.js app in `/frontend/` directory
   - Tailwind CSS for styling
   - API calls adapted for Vercel routes
   - Auto-scroll gallery with keyboard shortcuts

2. **API Structure**
   - Moved FastAPI app to `/api/index.py`
   - Added `/api/` prefix to all endpoints
   - Configured routes in `vercel.json`

3. **Database Support**
   - Added PostgreSQL support for production
   - Kept SQLite for local development
   - Auto-detects database type from URL

4. **File Storage**
   - Removed local file serving (serverless incompatible)
   - Image endpoints return placeholders
   - Ready for external storage integration

5. **Configuration**
   - Added Vercel environment detection
   - Optimized for serverless cold starts
   - Dual build configuration for frontend + backend

### 🗂️ File Structure

```
ai-gallery/
├── api/
│   └── index.py          # Serverless FastAPI entry point
├── app/                  # Application code (unchanged)
├── static/               # Static files (served by Vercel)
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies (+ psycopg2)
└── .env.example          # Environment template
```

## 🔧 Environment Variables

### Required Variables
```env
# Database (auto-set if using Vercel Postgres)
DATABASE_URL=postgresql://...

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id

# Stripe Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# AI Services
REPLICATE_API_TOKEN=r8_...
OPENAI_API_KEY=sk-...

# Security
SECRET_KEY=your-random-secret-key
```

### Vercel Auto-Set Variables
```env
VERCEL=1                  # Auto-set by Vercel
VERCEL_ENV=production     # development, preview, production
VERCEL_URL=your-app.vercel.app
```

## 🏗️ Database Setup

### Initialize Database Tables

After deployment, initialize your database:

```bash
# Using Vercel CLI
vercel env ls  # Check DATABASE_URL is set

# The tables will be created automatically on first API call
# Or run manually in Vercel dashboard's Functions tab
```

### Seed Data (Optional)

Since the seed script uses local files, you'll need to adapt it:

```python
# Create a /api/admin/seed.py endpoint
# Or manually insert data via your database console
```

## 🖼️ Image Storage Integration

The current deployment needs external storage for images. Options:

### Option A: Vercel Blob Storage
```bash
# Add Vercel Blob storage
vercel blob create

# Update image endpoints to use Vercel Blob
```

### Option B: Cloudinary (Recommended)
```bash
# Add Cloudinary environment variables
vercel env add CLOUDINARY_CLOUD_NAME
vercel env add CLOUDINARY_API_KEY
vercel env add CLOUDINARY_API_SECRET

# Images will be stored and served via Cloudinary CDN
```

### Option C: AWS S3
```bash
# Add AWS credentials
vercel env add AWS_ACCESS_KEY_ID
vercel env add AWS_SECRET_ACCESS_KEY
vercel env add AWS_S3_BUCKET
```

## 📈 API Endpoints

All endpoints are prefixed with `/api/`:

- `GET /api/` - API info
- `GET /api/health` - Health check
- `GET /api/search` - Search gallery
- `GET /api/styles` - Get available styles
- `GET /api/default` - Get default renders
- `GET /api/render/{id}` - Get render details
- `GET /api/images/{id}` - Serve images (needs external storage)
- `POST /api/checkout` - Stripe checkout
- `POST /api/webhook/stripe` - Stripe webhooks

## 🔍 Monitoring

### View Logs
```bash
# View function logs
vercel logs

# View specific deployment logs
vercel logs [deployment-url]
```

### Analytics
- Visit: https://vercel.com/dashboard
- Select your project
- View Analytics tab for performance metrics

## 💰 Cost Estimation

### Vercel Pricing (2024)

**Hobby Plan (Free)**
- 100GB bandwidth/month
- 100GB-hours serverless function execution
- Includes 1 Vercel Postgres database

**Pro Plan ($20/month)**
- 1TB bandwidth/month
- 1000GB-hours function execution
- Unlimited Vercel Postgres databases

### External Services
- **Vercel Postgres**: Free on Hobby, $0.24/GB/month storage
- **Cloudinary**: 25 credits/month free, $0.017/1000 transformations
- **API Costs**: Replicate + OpenAI based on usage

## 🆘 Troubleshooting

### Common Issues

#### 1. Cold Start Timeouts
```bash
# Increase function timeout in vercel.json
{
  "functions": {
    "api/index.py": {
      "maxDuration": 30
    }
  }
}
```

#### 2. Database Connection Errors
```bash
# Check DATABASE_URL is set
vercel env ls

# Ensure database accepts connections from Vercel IPs
# Most managed databases allow this by default
```

#### 3. Import Errors
```bash
# Check Python path in vercel.json
{
  "env": {
    "PYTHONPATH": "."
  }
}
```

#### 4. Package Size Too Large
```bash
# Optimize requirements.txt (remove unused packages)
# Use excludeFiles in vercel.json to reduce bundle size
```

### Debug Commands
```bash
# Local serverless testing
vercel dev

# Check deployment status
vercel ls

# View project info
vercel project ls
```

## 🔄 CI/CD Pipeline

### Automatic Deployments

Vercel automatically deploys:
- **Production**: Pushes to `main` branch
- **Preview**: Pull requests and feature branches

### Custom Deployment

```bash
# Deploy specific branch
vercel --prod

# Deploy with specific alias
vercel --alias my-custom-domain.com
```

## 🌐 Custom Domain

```bash
# Add custom domain
vercel domains add yourdomain.com

# SSL certificates are automatically managed
```

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Vercel project created and connected
- [ ] Database configured (Vercel Postgres or external)
- [ ] Environment variables set
- [ ] API endpoints tested
- [ ] Image storage integrated (Cloudinary/S3/Blob)
- [ ] Stripe webhook URL updated
- [ ] Custom domain configured (optional)
- [ ] Monitoring and alerts setup

## 🤝 Support

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Community**: https://github.com/vercel/vercel/discussions
- **Status Page**: https://vercel-status.com/

Your app will be available at: `https://your-project.vercel.app`