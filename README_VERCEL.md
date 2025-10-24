# Deploying Competence CRM to Vercel

This guide will walk you through deploying the CRM API to Vercel's serverless platform.

## Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. [Vercel CLI](https://vercel.com/cli) installed (optional, but recommended)
3. A PostgreSQL database (we recommend [Neon](https://neon.tech), [Supabase](https://supabase.com), or [Railway](https://railway.app))

## Quick Start

### 1. Prepare Your Database

You'll need a PostgreSQL database. Here are some free options:

- **Neon** (Recommended): https://neon.tech
- **Supabase**: https://supabase.com
- **Railway**: https://railway.app
- **Vercel Postgres**: https://vercel.com/storage/postgres

Get your database connection string (it should look like):
```
postgresql://username:password@host:5432/database
```

### 2. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard (Easiest)

1. Push your code to GitHub (already done!)
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "Add New Project"
4. Import your GitHub repository: `https://github.com/Abhishektiwari050/CRM`
5. Configure your project:
   - **Framework Preset**: Other
   - **Root Directory**: Leave as `./`
6. Add Environment Variables (click "Environment Variables"):
   ```
   DATABASE_URL=your_postgresql_connection_string
   SECRET_KEY=your_super_secret_key_here_change_this
   CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
   ENVIRONMENT=production
   ```
7. Click "Deploy"

#### Option B: Deploy via CLI

```bash
# Install Vercel CLI if you haven't
npm install -g vercel

# Navigate to project directory
cd "D:\Projects\Competence CRM"

# Login to Vercel
vercel login

# Deploy
vercel

# Follow the prompts and add environment variables when asked
```

### 3. Configure Environment Variables

In your Vercel project settings, add these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Secret key for JWT tokens (generate a random string) | `your-super-secret-key-minimum-32-chars` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `https://yourapp.com,http://localhost:3000` |
| `ENVIRONMENT` | Deployment environment | `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration (optional) | `1440` (24 hours) |

#### Generate a Secret Key

You can generate a secure secret key using Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or online at: https://generate-secret.vercel.app/32

### 4. Initialize Your Database

After deployment, you need to initialize your database with tables and a default admin user.

#### Option 1: Run Locally Then Deploy

```bash
# Set your database URL locally
export DATABASE_URL="your_postgresql_connection_string"

# Navigate to backend
cd backend

# Run initialization script
python -c "from app.database.connection import init_db; init_db()"

# Create admin user
python -c "
from app.database.connection import get_db, SessionLocal
from app.models.models import User, UserRole
from app.middleware.auth import AuthService

db = SessionLocal()
auth = AuthService()

admin = User(
    email='admin@example.com',
    full_name='Admin User',
    hashed_password=auth.hash_password('admin123'),
    role=UserRole.ADMIN,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
"
```

#### Option 2: Create Database Tables Manually

Connect to your PostgreSQL database and run the SQL schema from `backend/app/database/schema.sql` (if available), or let SQLAlchemy create tables on first run.

### 5. Test Your Deployment

Once deployed, test your API:

```bash
# Health check
curl https://your-app.vercel.app/api/health

# Login (update with your admin credentials)
curl -X POST https://your-app.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

## API Endpoints

Your deployed API will have the following endpoints:

### Public Endpoints
- `GET /` - Health check
- `GET /api/health` - Health check
- `POST /api/auth/login` - User login

### Protected Endpoints (require Bearer token)
- `GET /api/auth/me` - Get current user info
- `GET /api/clients` - List clients
- `GET /api/clients/{id}` - Get client details
- `GET /api/activities` - List activity logs
- `GET /api/users` - List users (admin/manager only)

## Troubleshooting

### 500 Internal Server Error

**Check Vercel Logs:**
1. Go to your Vercel project dashboard
2. Click on your deployment
3. Click "Functions" tab
4. Click on `api/index.py` to see logs

**Common Issues:**
- Missing environment variables (DATABASE_URL, SECRET_KEY)
- Database connection issues
- Database tables not created

### Database Connection Issues

**PostgreSQL Connection String Format:**
```
postgresql://username:password@host:5432/database?sslmode=require
```

**For Neon/Supabase:** Make sure to add `?sslmode=require` at the end

**Test your connection locally first:**
```bash
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DATABASE_URL'); print('Connected!' if engine.connect() else 'Failed')"
```

### Import Errors

If you see import errors in logs, make sure:
1. All dependencies are in `requirements.txt`
2. The `backend` folder is included in deployment
3. Check `.vercelignore` isn't excluding necessary files

### Database Tables Not Found

Run the database initialization script locally (see step 4 above) or create an admin endpoint to initialize tables.

## Performance Optimization

### Cold Starts
Serverless functions may have cold starts. To minimize:
- Keep dependencies minimal
- Use connection pooling for database
- Consider using Vercel's Edge Functions for critical paths

### Database Connection Pooling
The app is configured with connection pooling. Adjust in environment variables:
```
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
```

## Monitoring

### Vercel Analytics
Enable Vercel Analytics in your project settings for:
- Request metrics
- Error tracking
- Performance monitoring

### Logs
View real-time logs:
```bash
vercel logs your-deployment-url
```

## Updating Your Deployment

### Automatic Deployments
By default, Vercel automatically deploys when you push to your GitHub repository:

```bash
git add .
git commit -m "Update API"
git push origin main
```

### Manual Deployment
```bash
vercel --prod
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set strong database password
- [ ] Configure CORS_ORIGINS properly (don't use `*` in production)
- [ ] Use HTTPS only
- [ ] Enable rate limiting in production
- [ ] Review and set appropriate token expiration times
- [ ] Regularly update dependencies
- [ ] Enable Vercel's security features (DDoS protection, etc.)

## Support

For issues specific to this CRM:
- Check Vercel function logs
- Review environment variables
- Test database connection
- Verify all tables are created

For Vercel-specific issues:
- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Support](https://vercel.com/support)

## Next Steps

1. Connect your frontend to the deployed API
2. Set up monitoring and alerts
3. Configure custom domain
4. Enable Vercel Analytics
5. Set up CI/CD pipeline
6. Configure backup strategy for your database

---

**Deployment URL:** Your app will be available at `https://your-project-name.vercel.app`

Remember to update your frontend configuration to point to this URL!