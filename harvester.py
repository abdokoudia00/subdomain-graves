import requests
import sqlite3
import time

def fetch_crt_sh_logs():
    # Query crt.sh for all .com domains. %.com means wildcard.
    # You can change this to %.io or %.ai for startup-heavy domains.
    url = "https://crt.sh/?q=%.io&output=json"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        conn = sqlite3.connect('harvested.db')
        c = conn.cursor()
        
        count = 0
        for item in data:
            # crt.sh often returns comma-separated SANs (Subject Alternative Names)
            domain_names = item.get('name_value', '').split('\n')
            
            for domain in domain_names:
                domain = domain.strip().lower()
                # Filter out wildcard domains (*.) and root domains
                if '*' not in domain and domain.count('.') >= 2:
                    try:
                        c.execute("INSERT INTO subdomains (subdomain, status) VALUES (?, 'scanned')", (domain,))
                        count += 1
                    except sqlite3.IntegrityError:
                        # Domain already exists in DB, skip
                        pass
        
        conn.commit()
        conn.close()
        print(f"[+] Harvested {count} new subdomains from CT logs.")
    except Exception as e:
        print(f"[-] Error fetching CT logs: {e}")

if __name__ == "__main__":
    fetch_crt_sh_logs()
