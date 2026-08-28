import re
import requests
from playwright.sync_api import sync_playwright

# Başlangıç domain mantığı
BASE_DOMAIN_PREFIX = "https://taraftarium"
BASE_DOMAIN_SUFFIX = ".xyz"

# Aranacak sayaç aralığı (En son bilinen adresten ileriye doğru dener)
START_INDEX = 1081
MAX_TRY_COUNT = 30  # Gelecekte 1082, 1083, 1084... değiştikçe otomatik bulur

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

def get_active_taraftarium_url():
    """Sırayla taraftarium1081.xyz, taraftarium1082.xyz ... adreslerini kontrol ederek ilk aktif olanı bulur."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    }
    for i in range(START_INDEX, START_INDEX + MAX_TRY_COUNT):
        test_url = f"{BASE_DOMAIN_PREFIX}{i}{BASE_DOMAIN_SUFFIX}"
        try:
            res = requests.get(test_url, headers=headers, timeout=5, allow_redirects=True)
            if res.status_code == 200:
                print(f"[+] Aktif Taraftarium Adresi Bulundu: {res.url.rstrip('/')}")
                return res.url.rstrip('/')
        except Exception:
            continue
    return f"{BASE_DOMAIN_PREFIX}{START_INDEX}{BASE_DOMAIN_SUFFIX}"

def extract_cdn_from_player(active_url):
    """Bulunan aktif adrese Playwright ile bağlanıp arka plandaki yayın CDN adresini yakalar."""
    cdn_domain = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def handle_request(request):
            nonlocal cdn_domain
            url = request.url
            # Akış yapan m3u8 veya sunucu domainlerini (cfd, xyz, online, site vb.) yakala
            if "mono.m3u8" in url or "/patron/" in url or re.search(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click)/', url):
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click))', url)
                if match and "taraftarium" not in match.group(1):
                    cdn_domain = match.group(1)

        page.on("request", handle_request)

        try:
            print(f"[+] Playwright ile siteye giriş yapılıyor: {active_url}")
            page.goto(active_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(4000)

            # Çerçevelerdeki (iframe) adresleri tara
            for frame in page.frames:
                frame_url = frame.url
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click))', frame_url)
                if match and "taraftarium" not in match.group(1):
                    cdn_domain = match.group(1)
                    break
        except Exception as e:
            print(f"[-] Playwright Hatası: {e}")
        finally:
            browser.close()

    return cdn_domain

def build_m3u():
    active_main_url = get_active_taraftarium_url()
    stream_cdn = extract_cdn_from_player(active_main_url)

    if not stream_cdn:
        print("[!] Özel CDN bulunamadı, ana domain kullanılıyor.")
        stream_cdn = active_main_url

    print(f"[✓] Tam Doğru Yayın Sunucusu: {stream_cdn}")

    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={active_main_url}/",
        "#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXT-X-REFERER:{active_main_url}/",
        f"#EXT-X-ORIGIN:{active_main_url}",
        ""
    ]

    for ch in CHANNELS:
        logo_str = f' tvg-logo="{ch["logo"]}"' if ch["logo"] else ' tvg-logo=""'
        extinf = f'#EXTINF:-1 tvg-name="{ch["name"]}"{logo_str} group-title="{ch["group"]}",{ch["name"]}'
        stream_link = f"{stream_cdn.rstrip('/')}/{ch['path']}"

        m3u_lines.append(extinf)
        m3u_lines.append(stream_link)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    print(f"[✓] {OUTPUT_FILE} güncellendi.")

if __name__ == "__main__":
    build_m3u()
