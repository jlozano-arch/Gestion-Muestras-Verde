from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


class SampleStatus(str, enum.Enum):
    """Sample status enumeration"""
    RECEIVED = "received"
    ANALYZING = "analyzing"
    EVALUATED = "evaluated"
    AVAILABLE = "available"
    PARTIALLY_SHIPPED = "partially_shipped"
    SHIPPED = "shipped"
    ARCHIVED = "archived"


class Sample(Base):
    """Coffee sample model"""
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    country_code = Column(String(5))
    country_name = Column(String(100))
    origin = Column(String(200))
    producer = Column(String(200))
    supplier_reference = Column(String(200))
    provider_sample_number = Column(String(200))
    purchase_contract_cvc = Column(String(100))
    sales_contract_cvv = Column(String(100))
    quality = Column(String(100))
    warehouse = Column(String(200))
    sample_type = Column(String(100))
    category = Column(String(100))
    commercial_result = Column(String(100))
    harvest_date = Column(String(50))
    variety = Column(String(200))
    altitude = Column(Integer)
    processing = Column(String(100))
    physical_location = Column(String(500))
    initial_quantity = Column(Float)  # kg (deprecated, for backward compatibility)
    available_quantity = Column(Float)  # kg
    # New gram-based fields
    received_quantity_g = Column(Integer, default=0)
    available_quantity_g = Column(Integer, default=0)
    status = Column(Enum(SampleStatus), default=SampleStatus.RECEIVED)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tastings = relationship("Tasting", back_populates="sample", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="sample", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="sample", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="sample", cascade="all, delete-orphan")


class Tasting(Base):
    """Tasting/cupping evaluation"""
    __tablename__ = "tastings"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), index=True)
    evaluator = Column(String(200))
    tasting_date = Column(DateTime, default=datetime.utcnow)
    roast_date = Column(DateTime, nullable=True)
    
    # Sieve analysis
    sieve_18 = Column(Float)  # %
    sieve_17 = Column(Float)
    sieve_16 = Column(Float)  # %
    sieve_15 = Column(Float)
    sieve_14 = Column(Float)  # %
    sieve_13 = Column(Float)
    sieve_12 = Column(Float)
    sieve_plato = Column(Float)
    
    # Humidity
    humidity = Column(Float)  # %
    
    # Defects
    defects_primary = Column(Integer)  # count
    defects_secondary = Column(Integer)  # count
    
    # Tasting notes
    aroma = Column(Integer)  # 0-10
    acidity = Column(Integer)  # 0-10
    body = Column(Integer)  # 0-10
    flavor = Column(Integer)  # 0-10
    aftertaste = Column(Integer)  # 0-10
    cleanliness = Column(Integer)  # 0-10
    balance = Column(Integer)  # 0-10
    
    # Overall scores
    cup_score = Column(Float)  # 0-100
    indian_score = Column(Float)  # 0-100 proprietary
    commercial_score = Column(Float)  # 0-100 commercial viability
    valuation = Column(Float, nullable=True)

    class TastingResult(str, enum.Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    result = Column(Enum(TastingResult), default=TastingResult.PENDING)
    
    # Notes
    tasting_notes = Column(Text)
    recommendations = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    sample = relationship("Sample", back_populates="tastings")
    documents = relationship("Document", back_populates="tasting", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="tasting", cascade="all, delete-orphan")


class Shipment(Base):
    """Shipment record"""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), index=True)
    quantity = Column(Float)  # kg
    quantity_g = Column(Integer)
    shipment_date = Column(DateTime, default=datetime.utcnow)
    destination = Column(String(200))
    reference = Column(String(100), unique=True)
    status = Column(String(50), default="pending")
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    sample = relationship("Sample", back_populates="shipments")


class Event(Base):
    """Event timeline"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), index=True)
    event_type = Column(String(50))  # received, tasted, shipped, archived, etc.
    tasting_id = Column(Integer, ForeignKey("tastings.id"), index=True, nullable=True)
    description = Column(String(500))
    event_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    sample = relationship("Sample", back_populates="events")
    tasting = relationship("Tasting", back_populates="events")


class Document(Base):
    """Document/photo storage"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.id"), index=True)
    tasting_id = Column(Integer, ForeignKey("tastings.id"), index=True, nullable=True)
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(String(50))  # photo, certificate, analysis, etc.
    upload_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    sample = relationship("Sample", back_populates="documents")
    tasting = relationship("Tasting", back_populates="documents")
