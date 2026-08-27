import sqlite3
import dns.resolver

TARGET_HOSTERS = [
    "netlify.app", "vercel.app", "github.io", "herokuapp.com", "surge.sh", "bitbucket.io"
]

def resolve_cnames():
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
    
    c.execute("SELECT subdomain FROM subdomains WHERE status = 'scanned' AND cname_target IS NULL")
    domains_to_resolve = c.fetchall()
    
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5

    for domain_tuple in domains_to_resolve:
        domain = domain_tuple[0]
        try:
            answer = resolver.resolve(domain, 'CNAME')
            cname_target = str(answer[0].target).rstrip('.').lower()
            
            if any(host in cname_target for host in TARGET_HOSTERS):
                c.execute("UPDATE subdomains SET cname_target = ?, status = 'cname_found' WHERE subdomain = ?", (cname_target, domain))
                print(f"[+] MATCH: {domain} -> {cname_target}")
            else:
                c.execute("UPDATE subdomains SET cname_target = ?, status = 'unmatched' WHERE subdomain = ?", (cname_target, domain))
        except dns.resolver.NXDOMAIN:
            c.execute("UPDATE subdomains SET status = 'dead_dns' WHERE subdomain = ?", (domain,))
        except dns.resolver.NoAnswer:
            c.execute("UPDATE subdomains SET status = 'no_cname' WHERE subdomain = ?", (domain,))
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    print("[*] DNS Resolution complete for this batch.")

if __name__ == "__main__":
    resolve_cnames()
