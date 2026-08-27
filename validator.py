import sqlite3
import requests
from bs4 import BeautifulSoup

ORPHAN_SIGNATURES = {
    "herokuapp.com": ["no such app", "404 not found"],
    "netlify.app": ["not found - request id", "page not found"],
    "vercel.app": ["deploy not found", "404: not_found"],
    "github.io": ["there isn't a github pages site here"],
    "surge.sh": ["no such site"],
}

def validate_orphans():
    conn = sqlite3.connect('harvested.db')
    c = conn.cursor()
    
    # Auto-create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS subdomains (
            subdomain TEXT UNIQUE,
            cname_target TEXT,
            status TEXT,
            date_found TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    c.execute("SELECT subdomain, cname_target FROM subdomains WHERE status = 'cname_found'")
    targets = c.fetchall()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for target in targets:
        subdomain = target[0]
        cname = target[1]
        
        hoster_signature = None
        for host, signatures in ORPHAN_SIGNATURES.items():
            if host in cname:
                hoster_signature = signatures
                break
        
        if not hoster_signature:
            continue

        try:
            response = requests.get(f"http://{subdomain}", headers=headers, timeout=10, allow_redirects=False)
            body_text = response.text.lower()
            
            is_orphaned = False
            for sig in hoster_signature:
                if sig in body_text:
                    is_orphaned = True
                    break
            
            if is_orphaned:
                c.execute("UPDATE subdomains SET status = 'orphaned' WHERE subdomain = ?", (subdomain,))
                print(f"🔥 ORPHAN FOUND: {subdomain} is vulnerable!")
            else:
                c.execute("UPDATE subdomains SET status = 'live' WHERE subdomain = ?", (subdomain,))
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    print("[*] Validation complete.")

if __name__ == "__main__":
    validate_orphans()
