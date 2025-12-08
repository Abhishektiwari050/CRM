"""
Database connection and utilities
"""
import os
import logging
from supabase import create_client, Client
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Supabase Client
# ============================================================================

_supabase_client: Optional[Client] = None

def get_supabase() -> Optional[Client]:
    """Get Supabase client instance (singleton)"""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    if settings.USE_DEMO:
        logger.info("Demo mode active - Supabase disabled")
        return None
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase credentials not configured")
        return None
    
    try:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase connected successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return None

# Initialize on import
supabase = get_supabase()

# ============================================================================
# PostgreSQL Direct Connection (if needed)
# ============================================================================

def get_pg_connection():
    """Get direct PostgreSQL connection for complex queries"""
    import psycopg2
    
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)
    
    # Fallback to individual parameters
    return psycopg2.connect(
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
        port=os.getenv("port", "5432"),
        dbname=os.getenv("dbname")
    )
