import os
import requests
import json
import cloudscraper

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'desktop': False
    }
)

# İzlemek istediğiniz kanalların adlarını ve ID'lerini buraya ekleyin
CHANNELS = [
    {"name": "Kanal D", "id": "3828793616b62b9cc5834c"},
    # Örnek ilave kanal:
    # {"name": "Star TV", "id": "DIĞER_KANAL_ID"},
]

def get_vavoo_auth_token():
    """Vavoo sunucusundan oturum imzası (auth token) alır."""
    auth_url = "https://www.lokke.app/api/app/ping"
    payload = {
        "token": "ldCvE092e7gER0rVIajfsXIvRhwlrAzP6_1oEJ4q6HH89QHt24v6NNL_jQJO219hiLOXF2hqEfsUuEWitEIGN4EaHHEHb7Cd7gojc5SQYRFzU3XWo_kMeryAUbcwWnQrnf0-",
        "reason": "player.enter",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {"type": "Handset", "brand": "google", "model": "Nexus", "name": "21081111RG", "uniqueId": "8b5a7c3d9e0f1a2b"},
            "os": {"name": "android", "version": "12", "abis": ["arm64-v8a"], "host": "android"},
            "app": {"platform": "android", "version": "1.1.0", "buildId": "97215000", "engine": "hbc85", "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"], "installer": "com.android.vending"},
            "version": {"package": "app.lokke.main", "binary": "1.1.0", "js": "1.1.0"},
            "platform": {"isAndroid": True, "isIOS": False, "isTV": False, "isWeb": False, "isMobile": True, "isWebTV": False, "isElectron": False}
        },
        "appFocusTime": 0, "playerActive": False, "playDuration": 0, "devMode": True, "hasAddon": True,
        "castConnected": False, "package": "app.lokke.main", "version": "1.1.0", "process": "app",
        "firstAppStart": 1700000000000, "lastAppStart": 1700000000000, "adblockEnabled": False, "iap": {"supported": True}
    }
    
    headers = {
        "User-Agent": "okhttp/4.11.0",
        "Content-Type": "application/json"
    }
    
    try:
        res = scraper.post(auth_url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("addonSig")
    except Exception as e:
        print(f"[-] Imza alma hatasi: {e}")
    return None

def get_stream_url(live_id, signature):
    """Token ile canlı stream linkini çözer."""
    headers = {
        "User-Agent": "VAVOO/2.6",
        "Accept": "*/*"
    }
    
    if signature:
        headers["mediahubmx-signature"] = signature

    urls_to_try = [
        f"https://vavoo.to/live2/index.m3u8?id={live_id}",
        f"https://vavoo.to/live/index.m3u8?id={live_id}"
    ]
    if signature:
        urls_to_try.insert(0, f"https://vavoo.to/live2/index.m3u8?id={live_id}&token={signature}")

    for url in urls_to_try:
        try:
            res = scraper.get(url, headers=headers, allow_redirects=True, timeout=10)
            print(f"[*] Deneniyor: Status {res.status_code}")
            
            if res.status_code == 200 and "Not found" not in res.text:
                return res.url
        except Exception as e:
            print(f"[-] Istek hatasi: {e}")
            
    return None

def generate_m3u():
    print("[*] Vavoo oturum imzasi aliniyor...")
    signature = get_vavoo_auth_token()
    print(f"[*] Imza: {'Alindi' if signature else 'Alinamadi'}")

    m3u_lines = ["#EXTM3U"]
    success_count = 0

    for ch in CHANNELS:
        print(f"\n[*] Cozuluyor: {ch['name']} ({ch['id']})")
        stream_url = get_stream_url(ch["id"], signature)
        
        if stream_url:
            m3u_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}",{ch["name"]}')
            m3u_lines.append("#EXTVLCOPT:http-user-agent=VAVOO/2.6")
            m3u_lines.append(stream_url)
            success_count += 1
            print(f"[+] Basarili: {ch['name']} -> {stream_url}")
        else:
            print(f"[-] Basarisiz: {ch['name']}")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")
        print(f"\n[+] {success_count} kanal ile playlist.m3u güncellendi.")
    else:
        print("\n[!] Hicbir kanal cozulemedigi icin playlist.m3u degistirilmedi.")

if __name__ == "__main__":
    generate_m3u()
