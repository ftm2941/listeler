import sys
import re
from playwright.sync_api import sync_playwright

TARGET_URL = "https://taraftarium24.ch"
OUTPUT_FILE = "kanallar.m3u8"

BEIN_LOGO = "https://resmim.net/cdn/2026/07/22/ETtrXH.png"

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

def find_stream_cdn():
    cdn_domain = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Sayfadan geçen tüm HTTP isteklerini dinle
        def handle_request(request):
            nonlocal cdn_domain
            url = request.url
            # Ağ trafiğinden geçen mono.m3u8 veya cfd/xyz uzantılı canlı akış isteklerini yakala
            if "mono.m3u8" in url or re.search(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online)/', url):
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online))', url)
                if match:
                    cdn_domain = match.group(1)

        page.on("request", handle_request)

        try:
            print(f"[+] {TARGET_URL} adresine bağlanılıyor...")
            page.goto(TARGET_URL, wait_until="networkidle", timeout=25000)
            
            # Sayfa içinde iframe veya oynatıcı düğmesi varsa tıklama simülasyonu yap
            page.wait_for_timeout(4000)
            
            # Çerçeve (iframe) kaynaklarını tara
            for frame in page.frames:
                frame_url = frame.url
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|site|online))', frame_url)
                if match and not cdn_domain:
                    cdn_domain = match.group(1)
                    
        except Exception as e:
            print(f"[-] Hata oluştu: {e}")
        finally:
            browser.close()

    return cdn_domain

def build_m3u():
    detected_cdn = find_stream_cdn()
    
    if not detected_cdn:
        print("[!] Ağ dinlemesinde otomatik CDN bulunamadı. Varsayılan adres deneniyor...")
        detected_cdn = TARGET_URL
        
    print(f"[✓] Bulunan Doğru CDN Adresi: {detected_cdn}")

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
        stream_link = f"{detected_cdn.rstrip('/')}/{ch['path']}"
        
        m3u_lines.append(extinf)
        m3u_lines.append(stream_link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
        
    print(f"[✓] {OUTPUT_FILE} başarıyla oluşturuldu.")

if __name__ == "__main__":
    build_m3u()
