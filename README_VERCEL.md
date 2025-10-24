# Vercel Python API

This directory contains the Vercel Python API configuration for the CRM application.

## Setup

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `vercel --prod`

## Environment Variables

Set these in Vercel dashboard:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (min 32 characters)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `DEBUG`: Set to "false" for production
- `PORT`: Will be set automatically by Vercel

## Important Notes

- The application uses FastAPI with Uvicorn
- Static files are served from the `/static` directory
- Database migrations should be run separately before deployment
- Ensure PostgreSQL is accessible from Vercel's IP ranges