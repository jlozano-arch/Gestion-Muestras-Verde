from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/muestras.db")

# Create engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    # Ensure new columns exist for Sample (simple automatic migration for SQLite)
    try:
        with engine.connect() as conn:
            res = conn.execute("PRAGMA table_info('samples')")
            existing = {row[1] for row in res.fetchall()}

            # desired columns and their SQLite types
            extras = {
                'supplier_reference': 'TEXT',
                'provider_sample_number': 'TEXT',
                'purchase_contract_cvc': 'TEXT',
                'sales_contract_cvv': 'TEXT',
                'quality': 'TEXT',
                'warehouse': 'TEXT',
                'sample_type': 'TEXT',
                'category': 'TEXT',
                'commercial_result': 'TEXT',
            }

            for col, coltype in extras.items():
                if col not in existing:
                    try:
                        conn.execute(f"ALTER TABLE samples ADD COLUMN {col} {coltype}")
                    except Exception:
                        pass
            # Ensure documents table has tasting_id column for tasting-specific docs
            try:
                res2 = conn.execute("PRAGMA table_info('documents')")
                existing_docs = {row[1] for row in res2.fetchall()}
                if 'tasting_id' not in existing_docs:
                    try:
                        conn.execute("ALTER TABLE documents ADD COLUMN tasting_id INTEGER")
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass
