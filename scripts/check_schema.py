import sqlite3

db_path = 'data/muestras.db'
conn = sqlite3.connect(db_path)
for tbl in ('tastings','documents'):
    cur = conn.execute(f"PRAGMA table_info('{tbl}')")
    rows = cur.fetchall()
    print(f"TABLE {tbl} columns:")
    for r in rows:
        print(r)
    print('---')
conn.close()
