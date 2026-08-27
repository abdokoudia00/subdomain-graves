import sqlite3

conn = sqlite3.connect('harvested.db')
c = conn.cursor()

# Create table for scanned domains
c.execute('''
    CREATE TABLE IF NOT EXISTS subdomains (
        subdomain TEXT UNIQUE,
        cname_target TEXT,
        status TEXT, -- "scanned", "orphaned", "deployed", "dead"
        date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("Database initialized.")
