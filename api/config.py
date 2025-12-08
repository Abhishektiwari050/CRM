"""
Configuration management for the CRM API
"""
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Application Configuration
# ============================================================================

class Settings:
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Competence CRM")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Demo mode
    USE_DEMO: bool = os.getenv("USE_DEMO", "0") == "1"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # Rate limiting
    LOGIN_RATE_WINDOW: int = int(os.getenv("LOGIN_RATE_WINDOW", "60"))
    LOGIN_RATE_MAX: int = int(os.getenv("LOGIN_RATE_MAX", "10"))
    
    # Cache
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "0"))
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"
    
    def validate(self) -> None:
        """Validate critical configuration"""
        if not self.JWT_SECRET:
            raise ValueError("JWT_SECRET must be set")
        
        if not self.USE_DEMO:
            if not self.SUPABASE_URL or not self.SUPABASE_KEY:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set when USE_DEMO=0"
                )

# Global settings instance
settings = Settings()
