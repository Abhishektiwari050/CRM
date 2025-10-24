"""
Vercel Entry Point for FastAPI Application
Compatible with Vercel Serverless Functions
"""

import sys
import os
import logging

# Configure logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Add the parent directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    # Set working directory to backend for proper static file serving
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
    os.chdir(backend_dir)
    logger.info(f"Changed working directory to: {os.getcwd()}")
    
    # Override config with Vercel-specific settings
    sys.modules['app.core.config'] = __import__('api.config', fromlist=['settings'])
    
    # Import the FastAPI app
    from backend.app.core.app import app as fastapi_app
    
    # Vercel requires the app to be named 'app'
    app = fastapi_app
    logger.info("FastAPI app imported successfully")
    
    # Add Vercel-specific health check endpoint
    @app.get("/api/health")
    def health_check():
        return {
            "status": "healthy",
            "deployment": "vercel",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    
except Exception as e:
    logger.error(f"Failed to initialize FastAPI app: {e}")
    # Create a minimal fallback app for Vercel
    from fastapi import FastAPI
    app = FastAPI(title="CRM Fallback", version="1.0.0")
    
    @app.get("/")
    def fallback():
        return {"error": "Application initialization failed", "details": str(e)}