import re
import urllib.request

TARGET_URL = "https://taraftarium1081.xyz"
OUTPUT_FILE = "kanallar.m3u8"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Referer': 'https://taraftarium1081.xyz/'
}

# Şablon yapınız (Kanal isimleri, logoları ve path eşleşmeleri)
CHANNELS = [
    {"name": "BeIN Sports 1", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "patron/mono.m3u8"},
    {"name": "BeIN Sports 2", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "b2/mono.m3u8"},
    {"name": "BeIN Sports 3", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "b3/mono.m3u8"},
    {"name": "BeIN Sports 4", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "b4/mono.m3u8"},
    {"name": "BeIN Sports 5", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "b5/mono.m3u8"},
    {"name": "BeIN Sports 1 Max", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "bm1/mono.m3u8"},
    {"name": "BeIN Sports 2 Max", "logo": "https://resmim.net/cdn/2026/07/22/ETtrXH.png", "group": "BeinSports", "path": "bm2/mono.m3u8"},
    {"name": "S Sports 1", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBw0m1bb64ZQWBrW0CbsQWljjZn_xMyadd6GAtTT57LA&s=10", "group": "S Sports", "path": "ss/mono.m3u8"},
    {"name": "S Sports 2", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRBw0m1bb64ZQWBrW0CbsQWljjZn_xMyadd6GAtTT57LA&s=10", "group": "S Sports", "path": "ss2/mono.m3u8"},
    {"name": "Tivibu Sports", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWV9Dcu2_mquwvTERgrq-ikcVSPlE4vxIqGajCldYSmA&s=10", "group": "Tivibu", "path": "t1/mono.m3u8"},
    {"name": "Tivibu Sports 2", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWV9Dcu2_mquwvTERgrq-ikcVSPlE4vxIqGajCldYSmA&s=10", "group": "Tivibu", "path": "t2/mono.m3u8"},
    {"name": "Tivibu Sports 3", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWV9Dcu2_mquwvTERgrq-ikcVSPlE4vxIqGajCldYSmA&s=10", "group": "Tivibu", "path": "t3/mono.m3u8"},
    {"name": "Tivibu Sports 4", "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWV9Dcu2_mquwvTERgrq-ikcVSPlE4vxIqGajCldYSmA&s=10", "group": "Tivibu", "path": "t4/mono.m3u8"},
    {"name": "Smart Spor", "logo": "", "group": "Smart Sports", "path": "smarts/mono.m3u8"},
    {"name": "Smart Spor 2", "logo": "", "group": "Smart Sports", "path": "sms2/mono.m3u8"},
    {"name": "TRT Spor", "logo": "", "group": "TRT", "path": "trtspor/mono.m3u8"},
    {"name": "TRT Spor 2", "logo": "", "group": "TRT", "path": "trtspor2/mono.m3u8"},
    {"name": "A Spor", "logo": "", "group": "Ulusal", "path": "as/mono.m3u8"},
    {"name": "ATV", "logo": "", "group": "Ulusal", "path": "atv/mono.m3u8"},
    {"name": "TV8", "logo": "", "group": "Ulusal", "path": "tv8/mono.m3u8"},
    {"name": "TV8.5", "logo": "", "group": "Ulusal", "path": "tv85/mono.m3u8"},
    {"name": "NBA TV", "logo": "", "group": "NBA", "path": "nbatv/mono.m3u8"},
    {"name": "Eurosport 1", "logo": "", "group": "Eurosport", "path": "eu1/mono.m3u8"},
]

def fetch_stream_base():
    try:
        req = urllib.request.Request(TARGET_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # Siteden dinamik yayın domainini bulma (ör: https://2i4.d72577a9dd0ec71.cfd)
        match = re.search(r'https?://[a-zA-Z0-9\.\-]+\.cfd', html)
        if match:
            return match.group(0)
        
        # Eşleşme bulunamazsa varsayılan aktif yayın sunucusunu kullan
        return "https://2i4.d72577a9dd0ec71.cfd"
    except Exception as e:
        print(f"Domain çekme hatası: {e}")
        return "https://2i4.d72577a9dd0ec71.cfd"

def build_m3u():
    base_url = fetch_stream_base()
    
    # Sabit M3U Başlıkları
    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={TARGET_URL}",
        "#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        f"#EXT-X-REFERER:{TARGET_URL}",
        f"#EXT-X-ORIGIN:{TARGET_URL}",
        ""
    ]

    # Kanalları şablon yapınıza göre dizme
    for ch in CHANNELS:
        logo_str = f' tvg-logo="{ch["logo"]}"' if ch["logo"] else ""
        extinf = f'#EXTINF:-1 tvg-name="{ch["name"]}"{logo_str} group-title="{ch["group"]}",{ch["name"]}'
        stream_link = f"{base_url}/{ch['path']}"
        
        m3u_lines.append(extinf)
        m3u_lines.append(stream_link)

    # Dosyaya yazma
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
        
    print(f"{OUTPUT_FILE} başarıyla oluşturuldu ve güncellendi.")

if __name__ == "__main__":
    build_m3u()
