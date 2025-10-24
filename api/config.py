"""
Vercel-specific configuration for FastAPI deployment
Handles environment variables and deployment-specific settings
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class VercelConfig:
    """Configuration class optimized for Vercel deployment"""
    
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "CRM System")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database settings - prioritize DATABASE_URL for Vercel
    DATABASE_URL: str = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./crm.db"))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS settings - Vercel-friendly defaults
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "https://*,http://localhost:3000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        origins = []
        for origin in self.CORS_ORIGINS.split(","):
            origin = origin.strip()
            if origin:
                origins.append(origin)
        return origins if origins else ["*"]
    
    # Rate limiting
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Database pool settings (PostgreSQL only)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/crm.log")
    
    # Business logic settings
    REMINDER_CHECK_INTERVAL: int = int(os.getenv("REMINDER_CHECK_INTERVAL", "60"))
    ACTIVITY_RETENTION_DAYS: int = int(os.getenv("ACTIVITY_RETENTION_DAYS", "90"))
    
    # Notification services
    ENABLE_EMAIL_NOTIFICATIONS: bool = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    
    # Scheduler settings
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    
    # File upload settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # Export settings
    EXPORT_DIR: str = os.getenv("EXPORT_DIR", "exports")
    
    def validate_settings(self):
        """Validate critical settings for production deployment"""
        if self.DEBUG:
            logger.warning("Running in DEBUG mode - not recommended for production")
        
        if self.SECRET_KEY == "your-secret-key-change-in-production":
            logger.warning("Using default SECRET_KEY - change this in production")
        
        if not self.DATABASE_URL:
            logger.error("DATABASE_URL is not set")
            return False
        
        logger.info("Configuration validation completed")
        return True

# Create singleton instance
settings = VercelConfig()

# Validate on import
try:
    settings.validate_settings()
except Exception as e:
    logger.error(f"Configuration validation failed: {e}")