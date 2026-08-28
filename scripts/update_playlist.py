import json
import requests
import uuid
import time

COMMON_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
MEDIAHUBMX_CLIENT_VERSION = "3.1.4"

# Kanallarınızı tarayıcıda gördüğünüz bu "watch?live=..." linkleri ile tanımlayın
CHANNELS = [
    {"name": "Kanal 1", "url": "https://vavoo.to/watch?live=3828793616b62b9cc5834c"},
    # Diğer kanalların watch?live=... adreslerini buraya ekleyebilirsiniz:
    # {"name": "Kanal 2", "url": "https://vavoo.to/watch?live=BURAYA_ID_GELECEK"},
]

def get_addon_signature():
    """Lokke / Vavoo imzasını alır."""
    url = "https://www.lokke.app/api/app/ping"
    now_ms = int(time.time() * 1000)
    
    payload = {
        "token": "ldCvE092e7gER0rVIajfsXIvRhwlrAzP6_1oEJ4q6HH89QHt24v6NNL_jQJO219hiLOXF2hqEfsUuEWitEIGN4EaHHEHb7Cd7gojc5SQYRFzU3XWo_kMeryAUbcwWnQrnf0-",
        "reason": "player.enter",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {"type": "Handset", "brand": "google", "model": "Nexus", "name": "21081111RG", "uniqueId": str(uuid.uuid4()).replace("-", "")[:16]},
            "os": {"name": "android", "version": "12", "abis": ["arm64-v8a"], "host": "android"},
            "app": {"platform": "android", "version": "1.1.0", "buildId": "97215000", "engine": "hbc85", "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"], "installer": "com.android.vending"},
            "version": {"package": "app.lokke.main", "binary": "1.1.0", "js": "1.1.0"},
            "platform": {"isAndroid": True, "isIOS": False, "isTV": False, "isWeb": False, "isMobile": True, "isWebTV": False, "isElectron": False}
        },
        "appFocusTime": 0, "playerActive": False, "playDuration": 0, "devMode": True, "hasAddon": True,
        "castConnected": False, "package": "app.lokke.main", "version": "1.1.0", "process": "app",
        "firstAppStart": now_ms - 86400000, "lastAppStart": now_ms, "adblockEnabled": False, "iap": {"supported": True}
    }
    
    headers = {"User-Agent": "okhttp/4.11.0", "Accept": "application/json", "Content-Type": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=12)
        if res.status_code == 200:
            return res.json().get("addonSig")
    except Exception as e:
        print(f"[-] Imza hatasi: {e}")
    return None

def resolve_vavoo_url(source_url, signature):
    """vavoo.to/watch?live=... adresini .m3u8 akışına dönüştürür."""
    api_url = "https://vavoo.to/mediahubmx-resolve.json"
    
    # Eğer watch?live= adresi geldiyse resolver'ın kabul ettiği medya formatına çeviriyoruz
    target_url = source_url
    if "watch?live=" in source_url:
        live_id = source_url.split("watch?live=")[-1]
        target_url = f"https://vavoo.to/live/index.m3u8?id={live_id}"

    payload = {
        "language": "de",
        "region": "AT",
        "url": target_url,
        "clientVersion": MEDIAHUBMX_CLIENT_VERSION
    }
    headers = {
        "User-Agent": COMMON_UA,
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://vavoo.to",
        "Referer": "https://vavoo.to/"
    }
    if signature:
        headers["mediahubmx-signature"] = signature

    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=15)
        print(f"[*] Resolve status ({live_id if 'watch?live=' in source_url else source_url}): {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            resolved_url = None
            if isinstance(data, list) and len(data) > 0:
                resolved_url = data[0].get("url")
            elif isinstance(data, dict):
                resolved_url = data.get("url") or data.get("data", {}).get("url")
            
            if resolved_url and not any(bad in resolved_url for bad in ["vypn.net", "weiterschauen", "error"]):
                return resolved_url
            else:
                print(f"[-] Engelli veya gecersiz URL dondu: {resolved_url}")
    except Exception as e:
        print(f"[-] Cozme hatasi: {e}")
    return None

def generate_m3u():
    signature = get_addon_signature()
    print(f"[*] Imza durumu: {'Basarili' if signature else 'Basarisiz'}")

    m3u_lines = ["#EXTM3U"]
    success_count = 0

    for ch in CHANNELS:
        print(f"\n[*] Cozuluyor: {ch['name']}")
        stream_url = resolve_vavoo_url(ch["url"], signature)
        if stream_url:
            m3u_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}",{ch["name"]}')
            m3u_lines.append("#EXTVLCOPT:http-user-agent=VAVOO/2.6")
            m3u_lines.append(stream_url)
            success_count += 1
            print(f"[+] Basarili: {ch['name']} -> {stream_url[:50]}...")
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
