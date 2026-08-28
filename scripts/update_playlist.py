import json
import os
import re
import requests
import uuid
import time

COMMON_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MEDIAHUBMX_CLIENT_VERSION = "3.1.4"

# GitHub'da güncel tutmak istediğin Vavoo kanal listesi
CHANNELS = [
    {"name": "Kanal D", "url": "https://vavoo.to/live2/index.m3u8?id=kanald"},
    {"name": "Star TV", "url": "https://vavoo.to/live2/index.m3u8?id=startv"},
    {"name": "ATV", "url": "https://vavoo.to/live2/index.m3u8?id=atv"},
]

def get_addon_signature():
    """Lokke API'den 24 saat geçerli addonSig imzasını alır."""
    url = "https://www.lokke.app/api/app/ping"
    now_ms = int(time.time() * 1000)
    
    payload = {
        "token": "ldCvE092e7gER0rVIajfsXIvRhwlrAzP6_1oEJ4q6HH89QHt24v6NNL_jQJO219hiLOXF2hqEfsUuEWitEIGN4EaHHEHb7Cd7gojc5SQYRFzU3XWo_kMeryAUbcwWnQrnf0-",
        "reason": "player.enter",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {"type": "Handset", "brand": "google", "model": "Nexus", "name": "21081111RG", "uniqueId": str(uuid.uuid4()).replace("-", "")[:16]},
            "os": {"name": "android", "version": "7.1.2", "abis": ["arm64-v8a"], "host": "android"},
            "app": {"platform": "android", "version": "1.1.0", "buildId": "97215000", "engine": "hbc85", "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"], "installer": "com.android.vending"},
            "version": {"package": "app.lokke.main", "binary": "1.1.0", "js": "1.1.0"},
            "platform": {"isAndroid": True, "isIOS": False, "isTV": False, "isWeb": False, "isMobile": True, "isWebTV": False, "isElectron": False}
        },
        "appFocusTime": 0,
        "playerActive": False,
        "playDuration": 0,
        "devMode": True,
        "hasAddon": True,
        "castConnected": False,
        "package": "app.lokke.main",
        "version": "1.1.0",
        "process": "app",
        "firstAppStart": now_ms - 86400000,
        "lastAppStart": now_ms,
        "adblockEnabled": False,
        "iap": {"supported": True}
    }
    
    headers = {"User-Agent": "okhttp/4.11.0", "Accept": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            sig = res.json().get("addonSig")
            if sig:
                print(f"[+] Imza alindi: {sig[:15]}...")
                return sig
    except Exception as e:
        print(f"[-] Imza alma hatasi: {e}")
    return None

def resolve_vavoo_url(source_url, signature):
    """Vavoo meidaurl-resolve API'sini kullanarak stream URL'sini çözer."""
    api_url = "https://vavoo.to/mediahubmx-resolve.json"
    payload = {
        "language": "de",
        "region": "AT",
        "url": source_url,
        "clientVersion": MEDIAHUBMX_CLIENT_VERSION
    }
    headers = {
        "User-Agent": COMMON_UA,
        "Accept": "*/*",
        "Accept-Language": "de",
        "Connection": "close"
    }
    if signature:
        headers["mediahubmx-signature"] = signature

    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            resolved_url = None
            if isinstance(data, list) and len(data) > 0:
                resolved_url = data[0].get("url")
            elif isinstance(data, dict):
                resolved_url = data.get("url") or data.get("data", {}).get("url")
            
            if resolved_url and not ("vypn.net" in resolved_url or "weiterschauen" in resolved_url):
                return resolved_url
    except Exception as e:
        print(f"[-] Cozme hatasi ({source_url}): {e}")
    return None

def generate_m3u():
    signature = get_addon_signature()
    m3u_content = "#EXTM3U\n"
    
    for ch in CHANNELS:
        print(f"[*] Cozuluyor: {ch['name']}")
        stream_url = resolve_vavoo_url(ch["url"], signature)
        
        if stream_url:
            m3u_content += f"#EXTINF:-1 tvg-name=\"{ch['name']}\",{ch['name']}\n"
            # ExoPlayer / OkHttp için gerekli User-Agent header parametresini ekliyoruz
            m3u_content += f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n"
            m3u_content += f"{stream_url}\n"
            print(f"[+] Basarili: {ch['name']}")
        else:
            print(f"[-] Basarisiz: {ch['name']}")
            
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print("[+] playlist.m3u olusturuldu.")

if __name__ == "__main__":
    generate_m3u()
