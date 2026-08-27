import sqlite3
import os
import requests
import zipfile
import io

NETLIFY_TOKEN = os.environ.get('NETLIFY_TOKEN')
DB_NAME = 'harvested.db'

def deploy_to_netlify(subdomain, cname_target):
    # Netlify replaces dots with dashes in their generated subdomains.
    # If DNS points to "app.startup.io.netlify.app", Netlify site name is "app-startup-io"
    # We extract the subdomain part before ".netlify.app"
    if '.netlify.app' not in cname_target:
        return False
        
    # Extract the part before .netlify.app
    base_name = cname_target.split('.netlify.app')[0]
    # Netlify site names can't have dots, must use dashes
    site_name = base_name.replace('.', '-')
    
    headers = {
        'Authorization': f'Bearer {NETLIFY_TOKEN}'
    }

    # 1. Create the site on Netlify
    print(f"[*] Creating Netlify site: {site_name}")
    site_url = "https://api.netlify.com/api/v1/sites"
    site_payload = {'name': site_name}
    
    try:
        res = requests.post(site_url, headers=headers, json=site_payload)
        if res.status_code != 200 and res.status_code != 201:
            print(f"[-] Failed to create site {site_name}: {res.text}")
            return False
            
        site_data = res.json()
        site_id = site_data['id']
        print(f"[+] Site created. ID: {site_id}")

        # 2. Create a ZIP file in memory containing our template.html
        print("[*] Building deployment payload...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            with open('template.html', 'r', encoding='utf-8') as f:
                file_content = f.read()
            zip_file.writestr('index.html', file_content)
        
        zip_buffer.seek(0)

        # 3. Deploy the ZIP file to the new site
        print("[*] Deploying payload...")
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
        deploy_headers = {
            'Authorization': f'Bearer {NETLIFY_TOKEN}',
            'Content-Type': 'application/zip'
        }
        
        deploy_res = requests.post(deploy_url, headers=deploy_headers, data=zip_buffer.read())
        
        if deploy_res.status_code == 200 or deploy_res.status_code == 201:
            print(f"🔥 DEPLOY SUCCESS: {subdomain}")
            return True
        else:
            print(f"[-] Deploy failed: {deploy_res.text}")
            return False

    except Exception as e:
        print(f"[-] Error deploying {subdomain}: {e}")
        return False

def main():
    if not NETLIFY_TOKEN:
        print("[-] NETLIFY_TOKEN environment variable not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT subdomain, cname_target FROM subdomains WHERE status='orphaned'")
    targets = c.fetchall()
    
    if not targets:
        print("[*] No orphaned domains to deploy yet.")
        return

    for target in targets:
        subdomain = target[0]
        cname_target = target[1]
        
        success = deploy_to_netlify(subdomain, cname_target)
        
        if success:
            c.execute("UPDATE subdomains SET status='deployed' WHERE subdomain=?", (subdomain,))
        else:
            c.execute("UPDATE subdomains SET status='deploy_failed' WHERE subdomain=?", (subdomain,))
            
        conn.commit()

    conn.close()
    print("[*] Deployment run complete.")

if __name__ == "__main__":
    main()
