import os
import cloudscraper

# Cloudflare ve bot engellerini aşan scraper nesnesi
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'desktop': False
    }
)

# Kanal listeniz (watch?live= sonrasındaki ID'ler)
CHANNELS = [
    {"name": "Kanal D", "id": "3828793616b62b9cc5834c"},
    # Diğer kanalları buraya ekleyebilirsiniz:
    # {"name": "Star TV", "id": "BURAYA_ID"},
    # {"name": "ATV", "id": "BURAYA_ID"},
]

def get_direct_stream(live_id):
    """Vavoo sunucusundan m3u8 akış adresini çözer."""
    urls = [
        f"https://vavoo.to/live2/index.m3u8?id={live_id}",
        f"https://vavoo.to/live/index.m3u8?id={live_id}"
    ]
    
    headers = {
        "User-Agent": "VAVOO/2.6",
        "Accept": "*/*"
    }

    for url in urls:
        try:
            res = scraper.get(url, headers=headers, timeout=15)
            print(f"[*] Kanal deneme ({live_id[:8]}...): Status {res.status_code}")
            
            if res.status_code == 200 and not any(bad in res.url for bad in ["vypn.net", "weiterschauen"]):
                return res.url
        except Exception as e:
            print(f"[-] Scraper hatasi ({url}): {e}")
            
    return None

def generate_m3u():
    m3u_lines = ["#EXTM3U"]
    success_count = 0

    for ch in CHANNELS:
        print(f"\n[*] Cozuluyor: {ch['name']} ({ch['id']})")
        stream_url = get_direct_stream(ch["id"])
        
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
