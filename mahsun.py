import sys
import re
import requests
from playwright.sync_api import sync_playwright

# Yeni kaynak ve referans adresi
BASE_URL = "https://andro.evrenesoglu101.click"
OUTPUT_FILE = "kanallar.m3u8"
BEIN_LOGO = "https://resmim.net/cdn/2026/07/22/ETtrXH.png"

CHANNELS = [
    # BeinSports
    {"name": "BeIN Sports 1", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/batutest.m3u8"},
    {"name": "BeIN Sports 2", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebs2.m3u8"},
    {"name": "BeIN Sports 3", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebs3.m3u8"},
    {"name": "BeIN Sports 4", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebs4.m3u8"},
    {"name": "BeIN Sports 5", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebs5.m3u8"},
    {"name": "BeIN Sports 1 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebm1.m3u8"},
    {"name": "BeIN Sports 2 Max", "logo": BEIN_LOGO, "group": "BeinSports", "path": "checklist/androstreamlivebm2.m3u8"},
    
    # Exxen
    {"name": "Exxen Sports 1", "logo": "", "group": "Exxen", "path": "checklist/androstreamliveex1.m3u8"},
    {"name": "Exxen Sports 2", "logo": "", "group": "Exxen", "path": "checklist/androstreamliveex2.m3u8"},
    {"name": "Exxen Sports 3", "logo": "", "group": "Exxen", "path": "checklist/androstreamliveex3.m3u8"},
    {"name": "Exxen Sports 4", "logo": "", "group": "Exxen", "path": "checklist/androstreamliveex4.m3u8"},
    
    # S Sports
    {"name": "S Sports 1", "logo": "", "group": "S Sports", "path": "checklist/androstreams1.m3u8"},
    {"name": "S Sports 2", "logo": "", "group": "S Sports", "path": "checklist/androstreams2.m3u8"},
    
    # Tivibu
    {"name": "Tivibu Sports", "logo": "", "group": "Tivibu", "path": "checklist/androstreamt1.m3u8"},
    {"name": "Tivibu Sports 2", "logo": "", "group": "Tivibu", "path": "checklist/androstreamt2.m3u8"},
    {"name": "Tivibu Sports 3", "logo": "", "group": "Tivibu", "path": "checklist/androstreamt3.m3u8"},
    {"name": "Tivibu Sports 4", "logo": "", "group": "Tivibu", "path": "checklist/androstreamt4.m3u8"},
    
    # Spor
    {"name": "Smart Spor", "logo": "", "group": "Smart Sports", "path": "checklist/androstreamsmarts.m3u8"},
    {"name": "Smart Spor 2", "logo": "", "group": "Smart Sports", "path": "checklist/androstreamsms2.m3u8"},
    {"name": "TRT Spor", "logo": "", "group": "TRT", "path": "checklist/androstreamtrtspor.m3u8"},
    {"name": "TRT Spor Yıldız", "logo": "", "group": "TRT", "path": "checklist/androstreamtrtspor2.m3u8"},
    {"name": "NBA TV", "logo": "", "group": "NBA", "path": "checklist/androstreamnbatv.m3u8"},
    {"name": "Eurosport 1", "logo": "", "group": "Eurosport", "path": "checklist/androstreameu1.m3u8"},
    {"name": "Eurosport 2", "logo": "", "group": "Eurosport", "path": "checklist/androstreameu2.m3u8"},
    
    # Ulusal / Diğer
    {"name": "A Spor", "logo": "", "group": "Ulusal", "path": "checklist/androstreamas.m3u8"},
    {"name": "ATV", "logo": "", "group": "Ulusal", "path": "checklist/androstreamatv.m3u8"},
    {"name": "TV8", "logo": "", "group": "Ulusal", "path": "checklist/androstreamtv8.m3u8"},
    {"name": "TV8.5", "logo": "", "group": "Ulusal", "path": "checklist/androstreamtv85.m3u8"},
    {"name": "FB TV", "logo": "", "group": "Diğer", "path": "checklist/androstreamfbtv.m3u8"},
    {"name": "GS TV", "logo": "", "group": "Diğer", "path": "checklist/androstreamgstv.m3u8"},
    {"name": "TJK TV", "logo": "", "group": "Yarış", "path": "checklist/androstreamtjktv.m3u8"},
]

def extract_cdn_from_player():
    """Belirtilen adrese Playwright ile bağlanıp arka plandaki yayın CDN adresini yakalar."""
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
            if ".m3u8" in url or "/checklist/" in url or re.search(r'https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click)/', url):
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click))', url)
                if match and "evrenesoglu101" not in match.group(1):
                    cdn_domain = match.group(1)

        page.on("request", handle_request)

        try:
            print(f"[+] Playwright ile siteye giriş yapılıyor: {BASE_URL}")
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(4000)

            for frame in page.frames:
                frame_url = frame.url
                match = re.search(r'(https?://[a-zA-Z0-9\.\-]+\.(?:cfd|xyz|online|site|tech|cloud|click))', frame_url)
                if match and "evrenesoglu101" not in match.group(1):
                    cdn_domain = match.group(1)
                    break
        except Exception as e:
            print(f"[-] Playwright Hatası: {e}")
        finally:
            browser.close()

    return cdn_domain

def build_m3u():
    stream_cdn = extract_cdn_from_player()

    if not stream_cdn:
        print("[!] Özel CDN bulunamadı, ana domain kullanılıyor.")
        stream_cdn = BASE_URL

    print(f"[✓] Yayın Sunucusu: {stream_cdn}")

    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={BASE_URL}/",
        "#EXT-X-USER-AGENT:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        f"#EXT-X-REFERER:{BASE_URL}/",
        f"#EXT-X-ORIGIN:{BASE_URL}",
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
