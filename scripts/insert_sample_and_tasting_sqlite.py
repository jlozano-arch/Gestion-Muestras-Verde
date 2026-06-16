import sqlite3
from datetime import datetime

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
db_path = ROOT / 'data' / 'muestras.db'
conn = sqlite3.connect(str(db_path))
c = conn.cursor()

# Insert sample
code = 'AUTO_TEST_1'
try:
    c.execute("INSERT INTO samples (code, country_code, country_name, origin, producer, initial_quantity, available_quantity, status) VALUES (?,?,?,?,?,?,?,?)",
              (code, 'COL', 'Colombia', 'Huila', 'Finca Auto', 3.0, 3.0, 'received'))
    conn.commit()
    sample_id = c.lastrowid
    print('CREATED_SAMPLE_ID', sample_id)
except Exception as e:
    print('ERROR_CREATING_SAMPLE', e)
    conn.rollback()
    # Try to find existing sample by code
    res = c.execute("SELECT id FROM samples WHERE code=?", (code,)).fetchone()
    sample_id = res[0] if res else None
    print('FOUND_SAMPLE_ID', sample_id)

# Insert tasting
if sample_id:
    try:
        tasting_vals = (
            sample_id,
            'Tester SQLite',
            datetime.utcnow().isoformat(),
            60.0, # sieve_18
            20.0, # sieve_16
            10.0, # sieve_14
            11.0, # humidity
            1,    # defects_primary
            0,    # defects_secondary
            8,8,7,8,7,8,7, # aroma, acidity, body, flavor, aftertaste, cleanliness, balance
            7.6, # cup_score
            82.0, # indian_score
            80.0, # commercial_score
            'Notas test sqlite',
            'Recom test',
        )
        # Build insert with many columns explicitly since table may have extras
        c.execute('''INSERT INTO tastings (
            sample_id, evaluator, tasting_date, sieve_18, sieve_16, sieve_14, humidity,
            defects_primary, defects_secondary, aroma, acidity, body, flavor, aftertaste,
            cleanliness, balance, cup_score, indian_score, commercial_score, tasting_notes, recommendations
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', tasting_vals)
        conn.commit()
        tasting_id = c.lastrowid
        print('CREATED_TASTING_ID', tasting_id)
    except Exception as e:
        print('ERROR_CREATING_TASTING', e)
        conn.rollback()
else:
    print('NO_SAMPLE_AVAILABLE, SKIPPING_TASTING')

# Verify
print('\nLATEST SAMPLE ROW:')
print(c.execute('SELECT * FROM samples WHERE id=?', (sample_id,)).fetchone())
print('\nLATEST TASTING ROW:')
print(c.execute('SELECT * FROM tastings WHERE sample_id=? ORDER BY id DESC LIMIT 1', (sample_id,)).fetchone())

conn.close()
