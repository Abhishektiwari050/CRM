"""
Database Initialization Script for Vercel Deployment
This script initializes the database with tables and creates a default admin user.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base, init_db
from app.models.models import User, UserRole
from app.middleware.auth import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database(database_url: str):
    """Initialize database with tables"""
    try:
        logger.info("Connecting to database...")
        engine = create_engine(database_url)

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful!")

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")

        return engine
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def create_admin_user(engine, email: str, password: str, full_name: str = "Admin User"):
    """Create default admin user"""
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == email).first()
        if existing_admin:
            logger.warning(f"Admin user with email {email} already exists!")
            db.close()
            return existing_admin

        # Create admin user
        auth_service = AuthService()
        admin = User(
            email=email,
            full_name=full_name,
            hashed_password=auth_service.hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        logger.info(f"Admin user created successfully!")
        logger.info(f"Email: {email}")
        logger.info(f"Password: {password}")
        logger.info("⚠️  Please change the password after first login!")

        db.close()
        return admin

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        raise


def main():
    """Main initialization function"""
    # Get database URL from environment or argument
    database_url = os.getenv("DATABASE_URL")

    if len(sys.argv) > 1:
        database_url = sys.argv[1]

    if not database_url:
        logger.error("DATABASE_URL not provided!")
        logger.info("Usage: python init_vercel_db.py [DATABASE_URL]")
        logger.info("Or set DATABASE_URL environment variable")
        sys.exit(1)

    # Get admin credentials
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("ADMIN_NAME", "Admin User")

    try:
        logger.info("=" * 50)
        logger.info("CRM Database Initialization for Vercel")
        logger.info("=" * 50)

        # Initialize database
        engine = initialize_database(database_url)

        # Create admin user
        create_admin_user(engine, admin_email, admin_password, admin_name)

        logger.info("=" * 50)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 50)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Deploy your application to Vercel")
        logger.info("2. Set environment variables in Vercel dashboard")
        logger.info("3. Test the API endpoints")
        logger.info("4. Change admin password after first login")
        logger.info("")

    except Exception as e:
        logger.error("=" * 50)
        logger.error("❌ Database initialization failed!")
        logger.error("=" * 50)
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
