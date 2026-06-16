import sqlite3
from pathlib import Path

db_path = Path('data') / 'muestras.db'
print('DB path:', db_path)
if not db_path.exists():
    print('ERROR: DB file not found')
    raise SystemExit(1)

conn = sqlite3.connect(str(db_path))
c = conn.cursor()

def ensure_columns(table, extras):
    cur = c.execute(f"PRAGMA table_info('{table}')")
    existing = {row[1] for row in cur.fetchall()}
    print(f"Table {table}, existing columns: {existing}")
    for col, coltype in extras.items():
        if col not in existing:
            try:
                print(f"Adding column {col} {coltype} to {table}")
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
                conn.commit()
            except Exception as e:
                print('ERROR adding', col, e)
        else:
            print(f"Column {col} already present in {table}")

sample_extras = {
    'supplier_reference': 'TEXT',
    'provider_sample_number': 'TEXT',
    'purchase_contract_cvc': 'TEXT',
    'sales_contract_cvv': 'TEXT',
    'quality': 'TEXT',
    'warehouse': 'TEXT',
    'sample_type': 'TEXT',
    'category': 'TEXT',
    'commercial_result': 'TEXT'
}

doc_extras = {
    'tasting_id': 'INTEGER'
}

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

ensure_columns('samples', sample_extras)
ensure_columns('documents', doc_extras)
ensure_columns('tastings', tasting_extras)

print('Migration script finished')
conn.close()
