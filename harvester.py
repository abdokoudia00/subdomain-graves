import requests
import sqlite3
import time
import requests.exceptions

def fetch_crt_sh_logs():
        # Rotate TLDs to avoid timeout and catch different startups every run
    import random
    tlds = ['%.io', '%.ai', '%.co', '%.app', '%.dev', '%.net']
    chosen_tld = random.choice(tlds)
    url = f"https://crt.sh/?q={chosen_tld}&output=json"
    print(f"[*] Scanning TLD: {chosen_tld}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    max_retries = 5
    data = None

    for attempt in range(max_retries):
        try:
            print(f"[*] Fetching CT logs (Attempt {attempt + 1}/{max_retries})...")
            response = requests.get(url, headers=headers, timeout=90)
            
            if response.status_code == 200:
                # Check if response is actually JSON before parsing
                if 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    break
                else:
                    print("[-] crt.sh returned HTML instead of JSON. Retrying in 10s...")
                    time.sleep(10)
            else:
                print(f"[-] crt.sh returned Status Code: {response.status_code}. Retrying in 10s...")
                time.sleep(10)
        except Exception as e:
            print(f"[-] Network Error: {e}. Retrying in 10s...")
            time.sleep(10)

    if not data:
        print("[-] Failed to fetch data from crt.sh. The server might be completely down. Try again later.")
        return

    try:
        conn = sqlite3.connect('harvested.db')
        c = conn.cursor()
        
        count = 0
        for item in data:
            domain_names = item.get('name_value', '').split('\n')
            
            for domain in domain_names:
                domain = domain.strip().lower()
                if '*' not in domain and domain.count('.') >= 2:
                    try:
                        c.execute("INSERT INTO subdomains (subdomain, status) VALUES (?, 'scanned')", (domain,))
                        count += 1
                    except sqlite3.IntegrityError:
                        pass
        
        conn.commit()
        conn.close()
        print(f"[+] Harvested {count} new subdomains from CT logs.")
    except Exception as e:
        print(f"[-] Database Error: {e}")

if __name__ == "__main__":
    fetch_crt_sh_logs()

