import sqlite3

# The TLDs that SEO agencies pay a premium for
PREMIUM_TLDS = ['.io', '.ai', '.co', '.app', '.dev', '.tech', '.net']

def find_flippable_domains():
    conn = sqlite3.connect('harvested.db')
    c = conn.cursor()
    
    # Get all domains we have successfully deployed
    c.execute("SELECT subdomain FROM subdomains WHERE status='deployed'")
    deployed_domains = c.fetchall()
    
    flippable = []
    
    for row in deployed_domains:
        domain = row[0]
        # Check if the domain ends with a premium TLD
        if any(domain.endswith(tld) or tld + '.' in domain for tld in PREMIUM_TLDS):
            flippable.append(domain)
            
    conn.close()
    
    if flippable:
        print("[🔥] FLIPPABLE PREMIUM DOMAINS FOUND:")
        for d in flippable:
            print(f"  -> {d}")
    else:
        print("[*] No premium flippable domains deployed yet.")

if __name__ == "__main__":
    find_flippable_domains()
