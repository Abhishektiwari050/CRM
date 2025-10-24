# 🚀 Vercel Deployment Quick Start Guide

## What We Fixed

The previous deployment was failing because it tried to mount the entire FastAPI backend (which includes templates, static files, and local file system dependencies) into Vercel's serverless environment. 

We've now created a **serverless-compatible API wrapper** that:
- ✅ Works in Vercel's serverless function environment
- ✅ Properly handles database connections
- ✅ Includes only essential API endpoints
- ✅ Doesn't require local file system access for templates/static files

## 📋 Prerequisites

1. **GitHub Account** (you already have this ✅)
2. **Vercel Account** - Sign up at https://vercel.com
3. **PostgreSQL Database** - Get a free one from:
   - **Neon** (Recommended): https://neon.tech - Free tier, excellent for serverless
   - **Supabase**: https://supabase.com - Free tier with 500MB
   - **Railway**: https://railway.app - Free trial
   - **Vercel Postgres**: https://vercel.com/storage/postgres

## 🗄️ Step 1: Set Up Your Database

### Option A: Neon (Recommended)

1. Go to https://neon.tech and sign up
2. Create a new project
3. Copy your connection string (looks like):
   ```
   postgresql://username:password@ep-cool-name.region.aws.neon.tech/dbname?sslmode=require
   ```

### Option B: Supabase

1. Go to https://supabase.com and create a project
2. Go to Settings → Database
3. Copy the "Connection String" (URI format)
4. Make sure to add `?sslmode=require` at the end

### Step 1.5: Initialize Your Database

On your local machine, run:

```bash
# Set your database URL
export DATABASE_URL="your_postgresql_connection_string_here"

# Run the initialization script
python scripts/init_vercel_db.py

# Or with custom admin credentials
ADMIN_EMAIL="admin@yourcompany.com" ADMIN_PASSWORD="SecurePass123!" python scripts/init_vercel_db.py
```

This will:
- Create all necessary database tables
- Create a default admin user
- Verify the database connection

## 🚀 Step 2: Deploy to Vercel

### Via Vercel Dashboard (Easiest)

1. **Go to Vercel**: https://vercel.com/dashboard
2. **Click "Add New Project"**
3. **Import your GitHub repo**: 
   - Select: `Abhishektiwari050/CRM`
4. **Configure Project**:
   - Framework Preset: **Other**
   - Root Directory: `./` (leave default)
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

5. **Add Environment Variables** (IMPORTANT!):

   Click "Environment Variables" and add:

   | Name | Value |
   |------|-------|
   | `DATABASE_URL` | Your PostgreSQL connection string from Step 1 |
   | `SECRET_KEY` | Generate below ⬇️ |
   | `CORS_ORIGINS` | `*` (for testing) or your frontend URL |
   | `ENVIRONMENT` | `production` |

   **Generate a SECRET_KEY:**
   ```bash
   # On Windows PowerShell:
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
   
   # On Mac/Linux:
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

6. **Click "Deploy"** 🎉

### Via Vercel CLI (Alternative)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to your project
cd "D:\Projects\Competence CRM"

# Login
vercel login

# Deploy
vercel

# Follow prompts and set environment variables when asked
```

## ✅ Step 3: Test Your Deployment

After deployment completes, you'll get a URL like: `https://your-project.vercel.app`

### Test the API:

```bash
# Health check
curl https://your-project.vercel.app/api/health

# Should return:
# {"status":"healthy","service":"Competence CRM API",...}
```

### Test Login:

```bash
curl -X POST https://your-project.vercel.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Should return:
# {"access_token":"eyJ...","token_type":"bearer","user":{...}}
```

### Test with Token:

```bash
# Save the token from above login
TOKEN="your_access_token_here"

# Get current user info
curl https://your-project.vercel.app/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# List clients
curl https://your-project.vercel.app/api/clients \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Troubleshooting

### Issue: 500 Internal Server Error

**Solution:**
1. Go to Vercel Dashboard → Your Project
2. Click on the deployment
3. Click "Functions" tab
4. Click `api/index.py` to see logs
5. Look for the error message

**Common causes:**
- ❌ Missing `DATABASE_URL` environment variable
- ❌ Missing `SECRET_KEY` environment variable
- ❌ Database tables not created (run init script)
- ❌ Database connection refused (check connection string)

### Issue: Database connection failed

**Check your connection string format:**

✅ Correct (PostgreSQL):
```
postgresql://user:password@host.region.neon.tech/database?sslmode=require
```

❌ Wrong:
```
postgres://...  # Should be postgresql://
postgresql://... # Missing ?sslmode=require for Neon/Supabase
```

**Test locally first:**
```bash
export DATABASE_URL="your_connection_string"
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print('✅ Connected!' if engine.connect() else '❌ Failed')"
```

### Issue: Import errors in logs

**Solution:**
1. Check that `backend/` folder exists in your repo
2. Verify `.vercelignore` isn't excluding necessary files
3. Make sure all dependencies are in `requirements.txt`

### Issue: Tables don't exist

**Solution:**
Run the initialization script again:
```bash
export DATABASE_URL="your_db_url"
python scripts/init_vercel_db.py
```

## 📊 Available API Endpoints

Your deployed API has these endpoints:

### 🌍 Public Endpoints
- `GET /` - Health check
- `GET /api/health` - Health check (detailed)
- `POST /api/auth/login` - Login and get JWT token

### 🔒 Protected Endpoints (require Bearer token)
- `GET /api/auth/me` - Get current user
- `GET /api/clients` - List all clients (filtered by role)
- `GET /api/clients/{id}` - Get specific client
- `GET /api/activities` - List activity logs
- `GET /api/users` - List users (admin/manager only)

## 🎯 Next Steps

1. **Change Admin Password**: Login and change from default
2. **Configure CORS**: Update `CORS_ORIGINS` to your frontend domain
3. **Set up Custom Domain**: In Vercel project settings
4. **Connect Frontend**: Update frontend API URL to your Vercel URL
5. **Enable Monitoring**: Turn on Vercel Analytics
6. **Set up Backup**: Configure database backups

## 🔐 Security Checklist

Before going live:
- [ ] Change default admin password
- [ ] Set a strong `SECRET_KEY` (not the example one)
- [ ] Update `CORS_ORIGINS` to specific domains (not `*`)
- [ ] Use a strong database password
- [ ] Enable SSL/HTTPS (Vercel does this automatically)
- [ ] Review Vercel security settings
- [ ] Set up rate limiting (optional)
- [ ] Configure token expiration appropriately

## 📝 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | ✅ Yes | - | JWT signing key (32+ chars) |
| `CORS_ORIGINS` | ⚠️ Recommended | `*` | Comma-separated allowed origins |
| `ENVIRONMENT` | No | `production` | Environment name |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token lifetime in minutes |
| `DEBUG` | No | `false` | Debug mode (set to `false` in prod) |

## 💡 Pro Tips

1. **Use Vercel's Environment Variables UI** - Easier than CLI
2. **Test locally first** - Run the init script with your production DB URL
3. **Check logs often** - Vercel Functions tab shows real-time logs
4. **Use Neon's free tier** - Best for serverless, handles connections well
5. **Enable Auto-Deploy** - Vercel deploys automatically on git push
6. **Use Vercel CLI for logs** - `vercel logs your-deployment-url`

## 🆘 Getting Help

**Check logs first:**
```bash
vercel logs --follow
```

**Common log locations:**
- Vercel Dashboard → Project → Deployments → Latest → Functions → `api/index.py`

**Still stuck?**
- Check database connection
- Verify all environment variables are set
- Ensure initialization script ran successfully
- Review error messages in Vercel logs

## 🎉 Success!

Once you see this response from `/api/health`:
```json
{
  "status": "healthy",
  "service": "Competence CRM API",
  "deployment": "vercel",
  "timestamp": "2024-..."
}
```

**Your API is live! 🚀**

Now you can connect your frontend and start using the CRM system!

---

**Deployment URL**: `https://your-project.vercel.app`

Remember to bookmark this URL and update your frontend configuration!