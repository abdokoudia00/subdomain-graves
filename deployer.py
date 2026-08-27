import sqlite3
import os
import requests
import zipfile
import io

NETLIFY_TOKEN = os.environ.get('NETLIFY_TOKEN')
VERCEL_TOKEN = os.environ.get('VERCEL_TOKEN')
DB_NAME = 'harvested.db'

# --- NETLIFY DEPLOYMENT ---
def deploy_to_netlify(subdomain, cname_target):
    if '.netlify.app' not in cname_target:
        return False
        
    base_name = cname_target.split('.netlify.app')[0]
    site_name = base_name.replace('.', '-')
    
    headers = {
        'Authorization': f'Bearer {NETLIFY_TOKEN}'
    }

    print(f"[*] Creating Netlify site: {site_name}")
    site_url = "https://api.netlify.com/api/v1/sites"
    site_payload = {'name': site_name}
    
    try:
        res = requests.post(site_url, headers=headers, json=site_payload)
        if res.status_code != 200 and res.status_code != 201:
            return False
            
        site_data = res.json()
        site_id = site_data['id']
        print(f"[+] Site created. ID: {site_id}")

        print("[*] Building deployment payload...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            with open('template.html', 'r', encoding='utf-8') as f:
                file_content = f.read()
            zip_file.writestr('index.html', file_content)
        
        zip_buffer.seek(0)

        print("[*] Deploying payload...")
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
        deploy_headers = {
            'Authorization': f'Bearer {NETLIFY_TOKEN}',
            'Content-Type': 'application/zip'
        }
        
        deploy_res = requests.post(deploy_url, headers=deploy_headers, data=zip_buffer.read())
        
        if deploy_res.status_code == 200 or deploy_res.status_code == 201:
            print(f"🔥 DEPLOY SUCCESS (Netlify): {subdomain}")
            return True
        else:
            print(f"[-] Deploy failed: {deploy_res.text}")
            return False

    except Exception as e:
        print(f"[-] Error deploying {subdomain}: {e}")
        return False

# --- VERCEL DEPLOYMENT ---
def deploy_to_vercel(subdomain, cname_target):
    if '.vercel.app' not in cname_target:
        return False

    # Vercel project names cannot contain dots. e.g., app.startup.vercel.app -> app-startup
    base_name = cname_target.split('.vercel.app')[0]
    project_name = base_name.replace('.', '-')

    headers = {
        'Authorization': f'Bearer {VERCEL_TOKEN}',
        'Content-Type': 'application/json'
    }

    print(f"[*] Creating Vercel project: {project_name}")
    project_url = "https://api.vercel.com/v10/projects"
    project_payload = {'name': project_name}
    
    try:
        res = requests.post(project_url, headers=headers, json=project_payload)
        if res.status_code != 200 and res.status_code != 201:
            print(f"[-] Failed to create Vercel project {project_name}: {res.text}")
            return False
            
        project_data = res.json()
        project_id = project_data['id']
        print(f"[+] Project created. ID: {project_id}")

        # Build ZIP in memory
        print("[*] Building deployment payload...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            with open('template.html', 'r', encoding='utf-8') as f:
                file_content = f.read()
            zip_file.writestr('index.html', file_content)
        
        zip_buffer.seek(0)

        # Deploy via Vercel API using ZIP
        print("[*] Deploying payload to Vercel...")
        deploy_url = "https://api.vercel.com/v13/deployments"
        deploy_headers = {
            'Authorization': f'Bearer {VERCEL_TOKEN}',
            'Content-Type': 'application/zip'
        }
        params = {
            'name': project_name,
            'target': 'production'
        }
        
        deploy_res = requests.post(deploy_url, headers=deploy_headers, params=params, data=zip_buffer.read())
        
        if deploy_res.status_code == 200 or deploy_res.status_code == 201:
            print(f"🔥 DEPLOY SUCCESS (Vercel): {subdomain}")
            return True
        else:
            print(f"[-] Vercel Deploy failed: {deploy_res.text}")
            return False

    except Exception as e:
        print(f"[-] Vercel Error deploying {subdomain}: {e}")
        return False

# --- MAIN ROUTER ---
def main():
    if not NETLIFY_TOKEN and not VERCEL_TOKEN:
        print("[-] No API tokens found.")
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
        
        # Route to the correct hoster
        if '.netlify.app' in cname_target and NETLIFY_TOKEN:
            success = deploy_to_netlify(subdomain, cname_target)
        elif '.vercel.app' in cname_target and VERCEL_TOKEN:
            success = deploy_to_vercel(subdomain, cname_target)
        else:
            # Unsupported hoster (github.io, surge.sh, etc.) - skip for now
            c.execute("UPDATE subdomains SET status='deploy_skipped' WHERE subdomain=?", (subdomain,))
            conn.commit()
            continue
        
        if success:
            c.execute("UPDATE subdomains SET status='deployed' WHERE subdomain=?", (subdomain,))
        else:
            c.execute("UPDATE subdomains SET status='deploy_failed' WHERE subdomain=?", (subdomain,))
            
        conn.commit()

    conn.close()
    print("[*] Deployment run complete.")

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
