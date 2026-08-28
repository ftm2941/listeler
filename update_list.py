import re
import urllib.request

# Güncel Taraftarium Adresi
TARGET_URL = "https://taraftarium1081.xyz"
OUTPUT_FILE = "kanallar.m3u8"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'Referer': f'{TARGET_URL}/'
}

# BeIN Sports logosu
BEIN_LOGO = "https://resmim.net/cdn/2026/07/22/ETtrXH.png"

# Taraftarium Kanal Yolları (Path)
CHANNELS = [
    # BeinSports
    {"name": "BeIN Sports 1", "logo": BEIN_LOGO, "group": "BeinSports", "path": "patron/mono.m3u8"},
    {"name": "BeIN Sports 2", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b2/mono.m3u8"},
    {"name": "BeIN Sports 3", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b3/mono.m3u8"},
    {"name": "BeIN Sports 4", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b4/mono.m3u8"},
    {"name": "BeIN Sports 5", "logo": BEIN_LOGO, "group": "BeinSports", "path": "b5/mono.m3u8"},
    {"name": "BeIN Sports 1 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "bm1/mono.m3u8"},
    {"name": "BeIN Sports 2 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "bm2/mono.m3u8"},
    
    # Exxen
    {"name": "Exxen Sports 1", "logo": "", "group": "Exxen", "path": "exn1/mono.m3u8"},
    {"name": "Exxen Sports 2", "logo": "", "group": "Exxen", "path": "exn2/mono.m3u8"},
    {"name": "Exxen Sports 3", "logo": "", "group": "Exxen", "path": "exn3/mono.m3u8"},
    {"name": "Exxen Sports 4", "logo": "", "group": "Exxen", "path": "exn4/mono.m3u8"},
    
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
    {"name": "TRT Spor Yıldız", "logo": "", "group": "TRT", "path": "trtspor2/mono.m3u8"},
    {"name": "NBA TV", "logo": "", "group": "NBA", "path": "nbatv/mono.m3u8"},
    {"name": "Eurosport 1", "logo": "", "group": "Eurosport", "path": "eu1/mono.m3u8"},
    {"name": "Eurosport 2", "logo": "", "group": "Eurosport", "path": "eu2/mono.m3u8"},
    
    # Ulusal / Diğer
    {"name": "A Spor", "logo": "", "group": "Ulusal", "path": "as/mono.m3u8"},
    {"name": "ATV", "logo": "", "group": "Ulusal", "path": "atv/mono.m3u8"},
    {"name": "TV8", "logo": "", "group": "Ulusal", "path": "tv8/mono.m3u8"},
    {"name": "TV8.5", "logo": "", "group": "Ulusal", "path": "tv85/mono.m3u8"},
    {"name": "FB TV", "logo": "", "group": "Diğer", "path": "fbtv/mono.m3u8"},
    {"name": "GS TV", "logo": "", "group": "Diğer", "path": "gstv/mono.m3u8"},
    {"name": "TJK TV", "logo": "", "group": "Yarış", "path": "tjktv/mono.m3u8"},
]

def fetch_stream_base():
    """Site kaynak kodundan yayın CDN domainini otomatik tespit eder."""
    try:
        req = urllib.request.Request(TARGET_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # 1. Sitedeki aktif yayın sunucusunu (cfd/xyz/site vb.) bul
        matches = re.findall(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online|me|top|link)', html)
        for m in matches:
            if TARGET_URL not in m and "google" not in m and "yandex" not in m:
                return m.rstrip('/')
        
        # 2. Player iframe kaynaklarında ara
        iframes = re.findall(r'src=["\'](https?://[^"\']+)["\']', html)
        for iframe_url in iframes:
            try:
                iframe_req = urllib.request.Request(iframe_url, headers=HEADERS)
                with urllib.request.urlopen(iframe_req, timeout=8) as iframe_res:
                    iframe_html = iframe_res.read().decode('utf-8', errors='ignore')
                    stream_match = re.search(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online)', iframe_html)
                    if stream_match:
                        return stream_match.group(0).rstrip('/')
            except Exception:
                continue

        return TARGET_URL
    except Exception as e:
        print(f"Stream adresi çekilirken hata oluştu: {e}")
        return TARGET_URL

def build_m3u():
    base_url = fetch_stream_base()
    print(f"Tespit edilen Canlı Yayın CDN Adresi: {base_url}")
    
    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={TARGET_URL}/",
        "#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXT-X-REFERER:{TARGET_URL}/",
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
        
    print(f"{OUTPUT_FILE} başarıyla güncellendi.")

if __name__ == "__main__":
    build_m3u()
