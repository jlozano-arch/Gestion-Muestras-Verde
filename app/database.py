from sqlalchemy import create_engine, text
import logging
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
    logger = logging.getLogger("app.database")
    logger.setLevel(logging.DEBUG)
    try:
        with engine.connect() as conn:
            res = conn.exec_driver_sql("PRAGMA table_info('samples')")
            existing = {row[1] for row in res.fetchall()}

            # desired columns and their SQLite types
            extras = {
                'supplier_reference': 'TEXT',
                'provider_sample_number': 'TEXT',
                'container_number': 'TEXT',
                'purchase_contract_cvc': 'TEXT',
                'sales_contract_cvv': 'TEXT',
                'quality': 'TEXT',
                'warehouse': 'TEXT',
                'sample_type': 'TEXT',
                'category': 'TEXT',
                'commercial_result': 'TEXT',
                'physical_location': 'TEXT',
            }

            for col, coltype in extras.items():
                if col not in existing:
                    try:
                        conn.exec_driver_sql(f"ALTER TABLE samples ADD COLUMN {col} {coltype}")
                        logger.info(f"Added column {col} to samples")
                    except Exception:
                        logger.exception(f"Failed to add column {col} to samples")

            # Ensure documents table has tasting_id column for tasting-specific docs
            try:
                res2 = conn.exec_driver_sql("PRAGMA table_info('events')")
                existing_events = {row[1] for row in res2.fetchall()}
                if 'tasting_id' not in existing_events:
                    try:
                        conn.exec_driver_sql("ALTER TABLE events ADD COLUMN tasting_id INTEGER")
                        logger.info("Added column tasting_id to events")
                    except Exception:
                        logger.exception("Failed to add tasting_id to events")
            except Exception:
                logger.exception("Failed to inspect/modify events table")

            # Ensure documents table has tasting_id column too (documents separate table)
            try:
                res_docs = conn.exec_driver_sql("PRAGMA table_info('documents')")
                existing_docs = {row[1] for row in res_docs.fetchall()}
                if 'tasting_id' not in existing_docs:
                    try:
                        conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN tasting_id INTEGER")
                        logger.info("Added column tasting_id to documents")
                    except Exception:
                        logger.exception("Failed to add tasting_id to documents")
            except Exception:
                logger.exception("Failed to inspect/modify documents table")

            # Ensure tastings table has new sieve/roast/valuation/result columns
            try:
                res3 = conn.exec_driver_sql("PRAGMA table_info('tastings')")
                existing_t = {row[1] for row in res3.fetchall()}
                tasting_extras = {
                    'roast_date': 'DATETIME',
                    'sieve_17': 'REAL',
                    'sieve_15': 'REAL',
                    'sieve_13': 'REAL',
                    'sieve_12': 'REAL',
                    'sieve_plato': 'REAL',
                    'valuation': 'REAL',
                    'result': 'TEXT'
                }
                for col, coltype in tasting_extras.items():
                    if col not in existing_t:
                        try:
                            conn.exec_driver_sql(f"ALTER TABLE tastings ADD COLUMN {col} {coltype}")
                            logger.info(f"Added column {col} to tastings")
                        except Exception:
                            logger.exception(f"Failed to add column {col} to tastings")
            except Exception:
                logger.exception("Failed to inspect/modify tastings table")

            # Ensure samples table has gram-based quantity columns
            try:
                res4 = conn.exec_driver_sql("PRAGMA table_info('samples')")
                existing_s = {row[1] for row in res4.fetchall()}
                sample_extras = {
                    'received_quantity_g': 'INTEGER',
                    'available_quantity_g': 'INTEGER'
                }
                for col, coltype in sample_extras.items():
                    if col not in existing_s:
                        try:
                            conn.exec_driver_sql(f"ALTER TABLE samples ADD COLUMN {col} {coltype}")
                            logger.info(f"Added column {col} to samples")
                        except Exception:
                            logger.exception(f"Failed to add column {col} to samples")

                try:
                    conn.exec_driver_sql("""
                        UPDATE samples
                        SET status = CASE
                            WHEN lower(status) IN ('received', 'recibida', 'pending', 'pendiente') THEN 'received'
                            WHEN lower(status) IN ('available', 'disponible') THEN 'available'
                            WHEN lower(status) IN ('approved', 'aprobada', 'evaluated', 'evaluada', 'purchased') THEN 'approved'
                            WHEN lower(status) IN ('rejected', 'rechazada') THEN 'rejected'
                            WHEN lower(status) IN ('shipped', 'enviada', 'exhausted', 'agotada') THEN 'shipped'
                            WHEN lower(status) IN ('archived', 'archivada') THEN 'archived'
                            WHEN lower(status) = 'partially_shipped' AND COALESCE(available_quantity_g, 0) > 0 THEN 'available'
                            WHEN lower(status) = 'partially_shipped' THEN 'shipped'
                            WHEN lower(status) = 'analyzing' THEN 'received'
                            ELSE 'received'
                        END
                        WHERE status IS NOT NULL
                    """)
                    conn.commit()
                except Exception:
                    logger.exception("Failed to normalize sample statuses")
            except Exception:
                logger.exception("Failed to inspect/modify samples table")

            # Ensure shipments table has quantity_g column
            try:
                res5 = conn.exec_driver_sql("PRAGMA table_info('shipments')")
                existing_shipments = {row[1] for row in res5.fetchall()}
                if 'quantity_g' not in existing_shipments:
                    try:
                        conn.exec_driver_sql("ALTER TABLE shipments ADD COLUMN quantity_g INTEGER")
                        logger.info("Added column quantity_g to shipments")
                    except Exception:
                        logger.exception("Failed to add quantity_g to shipments")
            except Exception:
                logger.exception("Failed to inspect/modify shipments table")

            # Ensure import staging rows have decision/apply metadata
            try:
                res_import_rows = conn.exec_driver_sql("PRAGMA table_info('import_rows')")
                existing_import_rows = {row[1] for row in res_import_rows.fetchall()}
                import_row_extras = {
                    'source_sheet': 'TEXT',
                    'source_sheet_key': 'TEXT',
                    'final_action': 'TEXT',
                    'status': 'TEXT',
                    'sample_id': 'INTEGER',
                    'before_snapshot_json': 'TEXT',
                    'after_snapshot_json': 'TEXT',
                }
                if existing_import_rows:
                    for col, coltype in import_row_extras.items():
                        if col not in existing_import_rows:
                            try:
                                conn.exec_driver_sql(f"ALTER TABLE import_rows ADD COLUMN {col} {coltype}")
                                logger.info(f"Added column {col} to import_rows")
                            except Exception:
                                logger.exception(f"Failed to add {col} to import_rows")
            except Exception:
                logger.exception("Failed to inspect/modify import_rows table")
    except Exception:
        logging.exception("Unexpected error running migrations in create_tables")
