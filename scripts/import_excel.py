"""
Import script for loading samples from Excel files
"""
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, create_tables
from app.models import Sample
from app.countries import get_country_name

def import_from_excel(file_path):
    """Import samples from Excel file"""
    
    # Create tables if they don't exist
    create_tables()
    
    # Read Excel file
    df = pd.read_excel(file_path)
    
    # Get database session
    db = SessionLocal()
    
    imported = 0
    errors = []
    
    try:
        for idx, row in df.iterrows():
            try:
                # Extract data
                code = str(row.get('Código', f'SAMPLE-{idx}')).strip()
                country_code = str(row.get('País', 'CO')).strip()[:5]
                origin = str(row.get('Origen', '')).strip()
                producer = str(row.get('Productor', '')).strip()
                harvest_date = str(row.get('Cosecha', '')).strip()
                variety = str(row.get('Variedad', '')).strip()
                altitude = int(row.get('Altitud', 0)) if pd.notna(row.get('Altitud')) else 0
                processing = str(row.get('Procesamiento', '')).strip()
                quantity = float(row.get('Cantidad', 0)) if pd.notna(row.get('Cantidad')) else 0
                
                # Check if exists
                existing = db.query(Sample).filter(Sample.code == code).first()
                if existing:
                    errors.append(f"Row {idx + 2}: Código duplicado '{code}'")
                    continue
                
                # Create sample
                sample = Sample(
                    code=code,
                    country_code=country_code,
                    country_name=get_country_name(country_code),
                    origin=origin,
                    producer=producer,
                    harvest_date=harvest_date,
                    variety=variety,
                    altitude=altitude,
                    processing=processing,
                    initial_quantity=quantity,
                    available_quantity=quantity,
                )
                
                db.add(sample)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        # Commit all changes
        db.commit()
        
        print(f"✓ Importadas {imported} muestras")
        
        if errors:
            print(f"\n⚠ Errores encontrados:")
            for error in errors:
                print(f"  - {error}")
    
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python import_excel.py <archivo.xlsx>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: Archivo no encontrado: {file_path}")
        sys.exit(1)
    
    import_from_excel(file_path)
