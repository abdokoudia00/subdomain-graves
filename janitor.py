import sqlite3
import os
import requests

NETLIFY_TOKENS = os.environ.get('NETLIFY_TOKEN', '').split(',')
VERCEL_TOKENS = os.environ.get('VERCEL_TOKEN', '').split(',')

def cleanup_netlify(site_id):
    token = NETLIFY_TOKENS[0] if NETLIFY_TOKENS and NETLIFY_TOKENS[0] else None
    if not token: return
    headers = {'Authorization': f'Bearer {token}'}
    requests.delete(f"https://api.netlify.com/api/v1/sites/{site_id}", headers=headers)

def cleanup_vercel(project_id):
    token = VERCEL_TOKENS[0] if VERCEL_TOKENS and VERCEL_TOKENS[0] else None
    if not token: return
    headers = {'Authorization': f'Bearer {token}'}
    requests.delete(f"https://api.vercel.com/v9/projects/{project_id}", headers=headers)

def main():
    conn = sqlite3.connect('harvested.db')
    c = conn.cursor()
    
    # Find all domains deployed more than 30 days ago
    c.execute("SELECT subdomain, cname_target FROM subdomains WHERE status='deployed' AND date_found < datetime('now', '-30 days')")
    old_sites = c.fetchall()
    
    if not old_sites:
        print("[*] Janitor: No old sites to clean.")
        return

    for site in old_sites:
        subdomain = site[0]
        cname = site[1]
        
        # Delete from hoster (basic implementation, doesn't need site ID since we can look it up, 
        # but for simplicity we just mark it expired in our DB. Real deletion can be manual if needed).
        
        # To avoid hitting API limits, we just mark as expired in DB for now. 
        # The free tier limits refresh dynamically if you delete from the dashboard.
        c.execute("UPDATE subdomains SET status='expired' WHERE subdomain=?", (subdomain,))
        print(f"[-] Janitor: Expired {subdomain}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
