"""
Seed script for loading initial data
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, create_tables
from app.models import Sample, Tasting, Event, SampleStatus
from app.countries import get_country_name

# Sample data
COUNTRIES = ["CO", "PE", "EC", "BO", "ETH", "KE", "HN", "GT"]
ORIGINS = {
    "CO": ["Huila", "Nariño", "Cauca", "Antioquia"],
    "PE": ["Cusco", "Junín", "Ucayali"],
    "EC": ["Manabí", "Esmeraldas", "Pichincha"],
    "BO": ["La Paz", "Cochabamba"],
    "ETH": ["Yirgacheffe", "Sidamo", "Harrar"],
    "KE": ["Mount Kenya", "Kisii", "Nyeri"],
    "HN": ["Copán", "Lempira"],
    "GT": ["Antigua", "Huehuetenango", "San Marcos"],
}
VARIETIES = ["Geisha", "Bourbon", "Typica", "Catuaí", "Mundo Novo", "Pacamara"]
PROCESSORS = ["Washed", "Natural", "Honey", "Anaerobic", "Fermented"]

def seed_database():
    """Seed initial database"""
    
    # Create tables
    create_tables()
    
    # Get session
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Sample).delete()
        db.commit()
        
        print("Creating sample data...")
        
        # Create samples
        samples_created = 0
        for country in COUNTRIES:
            for i, origin in enumerate(ORIGINS.get(country, ["Unknown"])[:2]):
                code = f"{country}-{origin[:3].upper()}-{i+1:03d}"
                
                sample = Sample(
                    code=code,
                    country_code=country,
                    country_name=get_country_name(country),
                    origin=origin,
                    producer=f"Productor {origin} {i+1}",
                    harvest_date=f"202{random.randint(3, 5)}-{random.randint(1, 12):02d}",
                    variety=random.choice(VARIETIES),
                    altitude=random.randint(1200, 2200),
                    processing=random.choice(PROCESSORS),
                    initial_quantity=random.uniform(100, 500),
                    available_quantity=random.uniform(50, 500),
                    status=random.choice(list(SampleStatus)),
                    notes=f"Sample from {origin}"
                )
                
                db.add(sample)
                samples_created += 1
                
                # Flush to get ID
                db.flush()
                
                # Create a tasting for some samples
                if random.random() > 0.3:  # 70% have tastings
                    tasting = Tasting(
                        sample_id=sample.id,
                        evaluator="Juan García",
                        tasting_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                        sieve_18=random.uniform(40, 80),
                        sieve_16=random.uniform(10, 40),
                        sieve_14=random.uniform(5, 20),
                        humidity=random.uniform(10, 13),
                        defects_primary=random.randint(0, 10),
                        defects_secondary=random.randint(0, 5),
                        aroma=random.randint(6, 10),
                        acidity=random.randint(6, 10),
                        body=random.randint(6, 10),
                        flavor=random.randint(6, 10),
                        aftertaste=random.randint(6, 10),
                        cleanliness=random.randint(7, 10),
                        balance=random.randint(6, 10),
                        cup_score=random.uniform(80, 95),
                        indian_score=random.uniform(70, 95),
                        commercial_score=random.uniform(65, 90),
                        tasting_notes="Excellent balance and complexity",
                    )
                    db.add(tasting)
                
                # Create events
                event = Event(
                    sample_id=sample.id,
                    event_type="received",
                    description=f"Sample received from {origin}",
                    event_date=datetime.utcnow() - timedelta(days=random.randint(10, 60))
                )
                db.add(event)
        
        db.commit()
        print(f"✓ Created {samples_created} samples with tastings and events")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully!")
