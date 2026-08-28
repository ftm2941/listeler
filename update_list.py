import re
import urllib.request

# Güncel Taraftarium Adresi
TARGET_URL = "https://taraftarium24.ch"
OUTPUT_FILE = "kanallar.m3u8"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'Referer': f'{TARGET_URL}/'
}

# Sadece BeIN Sports kanallarına eklenecek logo
BEIN_LOGO = "https://resmim.net/cdn/2026/07/22/ETtrXH.png"

# Taraftarium Orijinal Kanal Yapısı
CHANNELS = [
    # BeinSports
    {"name": "BeIN Sports 1", "logo": BEIN_LOGO, "group": "BeinSports", "path": "patron/mono.m3u8"},
    {"name": "BeIN Sports 2", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b2/mono.m3u8"},
    {"name": "BeIN Sports 3", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b3/mono.m3u8"},
    {"name": "BeIN Sports 4", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b4/mono.m3u8"},
    {"name": "BeIN Sports 5", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b5/mono.m3u8"},
    {"name": "BeIN Sports 1 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "bm1/mono.m3u8"},
    {"name": "BeIN Sports 2 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "bm2/mono.m3u8"},
    
    # S Sports
    {"name": "S Sports 1", "logo": "", "group": "S Sports", "path": "ss/mono.m3u8"},
    {"name": "S Sports 2", "logo": "", "group": "S Sports", "path": "ss2/mono.m3u8"},
    
    # Tivibu
    {"name": "Tivibu Sports", "logo": "", "group": "Tivibu", "path": "t1/mono.m3u8"},
    {"name": "Tivibu Sports 2", "logo": "", "group": "Tivibu", "path": "t2/mono.m3u8"},
    {"name": "Tivibu Sports 3", "logo": "", "group": "Tivibu", "path": "t3/mono.m3u8"},
    {"name": "Tivibu Sports 4", "logo": "", "group": "Tivibu", "path": "t4/mono.m3u8"},
    
    # Spor
    {"name": "Smart Spor", "logo": "", "group": "Smart Sports", "path": "smarts/mono.m3u8"},
    {"name": "Smart Spor 2", "logo": "", "group": "Smart Sports", "path": "sms2/mono.m3u8"},
    {"name": "TRT Spor", "logo": "", "group": "TRT", "path": "trtspor/mono.m3u8"},
    {"name": "TRT Spor 2", "logo": "", "group": "TRT", "path": "trtspor2/mono.m3u8"},
    {"name": "NBA TV", "logo": "", "group": "NBA", "path": "nbatv/mono.m3u8"},
    {"name": "Eurosport 1", "logo": "", "group": "Eurosport", "path": "eu1/mono.m3u8"},
    
    # Ulusal
    {"name": "A Spor", "logo": "", "group": "Ulusal", "path": "as/mono.m3u8"},
    {"name": "ATV", "logo": "", "group": "Ulusal", "path": "atv/mono.m3u8"},
    {"name": "TV8", "logo": "", "group": "Ulusal", "path": "tv8/mono.m3u8"},
    {"name": "TV8.5", "logo": "", "group": "Ulusal", "path": "tv85/mono.m3u8"},
]

def fetch_stream_base():
    try:
        req = urllib.request.Request(TARGET_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # Taraftarium ana sayfasından .cfd veya .xyz uzantılı yayın sunucusunu yakalama
        match = re.search(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online|me|top)', html)
        if match:
            return match.group(0)
            
        return "https://2i4.d72577a9dd0ec71.cfd" # Eşleşmezse varsayılan eski adres
    except Exception as e:
        print(f"Domain çekme hatası: {e}")
        return "https://2i4.d72577a9dd0ec71.cfd"

def build_m3u():
    base_url = fetch_stream_base()
    
    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={TARGET_URL}",
        "#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXT-X-REFERER:{TARGET_URL}",
        f"#EXT-X-ORIGIN:{TARGET_URL}",
        ""
    ]

    for ch in CHANNELS:
        logo_str = f' tvg-logo="{ch["logo"]}"' if ch["logo"] else ' tvg-logo=""'
        extinf = f'#EXTINF:-1 tvg-name="{ch["name"]}"{logo_str} group-title="{ch["group"]}",{ch["name"]}'
        stream_link = f"{base_url}/{ch['path']}"
        
        m3u_lines.append(extinf)
        m3u_lines.append(stream_link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
        
    print(f"{OUTPUT_FILE} başarıyla oluşturuldu ve {base_url} üzerinden güncellendi.")

if __name__ == "__main__":
    build_m3u()
