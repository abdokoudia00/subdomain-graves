import sqlite3
import os
import requests
import zipfile
import io
import base64
import time

NETLIFY_TOKEN = os.environ.get('NETLIFY_TOKEN')
VERCEL_TOKEN = os.environ.get('VERCEL_TOKEN')
GH_TOKEN = os.environ.get('GH_ORG_TOKEN')
DB_NAME = 'harvested.db'

# --- NETLIFY DEPLOYMENT ---
def deploy_to_netlify(subdomain, cname_target):
    if '.netlify.app' not in cname_target:
        return False
        
    base_name = cname_target.split('.netlify.app')[0]
    site_name = base_name.replace('.', '-')
    
    headers = {'Authorization': f'Bearer {NETLIFY_TOKEN}'}

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
        
        if deploy_res.status_code in [200, 201]:
            print(f"🔥 DEPLOY SUCCESS (Netlify): {subdomain}")
            return True
        return False

    except Exception as e:
        print(f"[-] Error deploying {subdomain}: {e}")
        return False

# --- VERCEL DEPLOYMENT ---
def deploy_to_vercel(subdomain, cname_target):
    if '.vercel.app' not in cname_target:
        return False

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
        if res.status_code not in [200, 201]:
            return False
            
        project_data = res.json()
        project_id = project_data['id']

        print("[*] Building deployment payload...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            with open('template.html', 'r', encoding='utf-8') as f:
                file_content = f.read()
            zip_file.writestr('index.html', file_content)
        zip_buffer.seek(0)

        print("[*] Deploying payload to Vercel...")
        deploy_url = "https://api.vercel.com/v13/deployments"
        deploy_headers = {
            'Authorization': f'Bearer {VERCEL_TOKEN}',
            'Content-Type': 'application/zip'
        }
        params = {'name': project_name, 'target': 'production'}
        
        deploy_res = requests.post(deploy_url, headers=deploy_headers, params=params, data=zip_buffer.read())
        
        if deploy_res.status_code in [200, 201]:
            print(f"🔥 DEPLOY SUCCESS (Vercel): {subdomain}")
            return True
        return False

    except Exception as e:
        print(f"[-] Vercel Error deploying {subdomain}: {e}")
        return False

# --- GITHUB PAGES DEPLOYMENT ---
def deploy_to_github(subdomain, cname_target):
    if '.github.io' not in cname_target:
        return False
        
    # e.g., app.startup.github.io -> target user/org is "app-startup" wait no.
    # DNS for github pages usually points directly to: username.github.io
    target_org = cname_target.split('.github.io')[0]
    repo_name = f"{target_org}.github.io"
    
    headers = {
        'Authorization': f'token {GH_TOKEN}',
        'Accept': 'application/vnd.github+json'
    }

    print(f"[*] Creating GitHub Org: {target_org}")
    org_url = "https://api.github.com/orgs"
    org_payload = {'login': target_org}
    
    try:
        org_res = requests.post(org_url, headers=headers, json=org_payload)
        # 201 = Created, 422 = Already exists
        if org_res.status_code not in [201, 422]:
            print(f"[-] Failed to create Org {target_org}: {org_res.text}")
            return False

        print(f"[+] Org ready: {target_org}")
        
        print(f"[*] Creating GitHub Repo: {repo_name} under {target_org}")
        repo_url = f"https://api.github.com/orgs/{target_org}/repos"
        repo_payload = {'name': repo_name, 'visibility': 'public'}
        
        repo_res = requests.post(repo_url, headers=headers, json=repo_payload)
        if repo_res.status_code not in [201, 422]:
            print(f"[-] Failed to create Repo: {repo_res.text}")
            return False

        print("[*] Uploading index.html via Contents API...")
        with open('template.html', 'r', encoding='utf-8') as f:
            content_base64 = base64.b64encode(f.read().encode('utf-8')).decode('utf-8')
            
        file_url = f"https://api.github.com/repos/{target_org}/{repo_name}/contents/index.html"
        file_payload = {
            'message': 'Initial deploy',
            'content': content_base64
        }
        
        file_res = requests.put(file_url, headers=headers, json=file_payload)
        if file_res.status_code not in [200, 201]:
            print(f"[-] Failed to upload HTML: {file_res.text}")
            return False

        print("[*] Uploading CNAME file...")
        cname_content = base64.b64encode(subdomain.encode('utf-8')).decode('utf-8')
        cname_url = f"https://api.github.com/repos/{target_org}/{repo_name}/contents/CNAME"
        cname_payload = {
            'message': 'Add CNAME',
            'content': cname_content
        }
        
        cname_res = requests.put(cname_url, headers=headers, json=cname_payload)
        if cname_res.status_code not in [200, 201]:
            print(f"[-] Failed to upload CNAME: {cname_res.text}")
            return False

        print(f"🔥 DEPLOY SUCCESS (GitHub Pages): {subdomain}")
        return True

    except Exception as e:
        print(f"[-] GitHub Error deploying {subdomain}: {e}")
        return False

# --- MAIN ROUTER ---
def main():
    if not NETLIFY_TOKEN and not VERCEL_TOKEN and not GH_TOKEN:
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
        
        if '.netlify.app' in cname_target and NETLIFY_TOKEN:
            success = deploy_to_netlify(subdomain, cname_target)
        elif '.vercel.app' in cname_target and VERCEL_TOKEN:
            success = deploy_to_vercel(subdomain, cname_target)
        elif '.github.io' in cname_target and GH_TOKEN:
            success = deploy_to_github(subdomain, cname_target)
        else:
            c.execute("UPDATE subdomains SET status='deploy_skipped' WHERE subdomain=?", (subdomain,))
            conn.commit()
            continue
        
        if success:
            c.execute("UPDATE subdomains SET status='deployed' WHERE subdomain=?", (subdomain,))
        else:
            c.execute("UPDATE subdomains SET status='deploy_failed' WHERE subdomain=?", (subdomain,))
            
        conn.commit()
        time.sleep(2) # Rate limiting safety

    conn.close()
    print("[*] Deployment run complete.")

if __name__ == "__main__":
    main()

