from app.database import SessionLocal
from app.models import Sample

db = SessionLocal()
try:
    s = Sample(
        code='TEST-0001',
        country_code='COL',
        country_name='Colombia',
        origin='Huila',
        producer='Finca Prueba',
        initial_quantity=5.0,
        available_quantity=5.0
    )
    db.add(s)
    db.commit()
    print('CREATED_SAMPLE_ID:', s.id)
except Exception as e:
    print('ERROR_CREATING_SAMPLE:', e)
finally:
    db.close()
