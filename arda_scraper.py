TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

# Her kanalın kendi özel URL yolu (path) ve logosu
channels = [
    ("Bein Sports 1", "hls/b1.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 2", "b2/tracks-v1a1/mono.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 3", "hls/b3.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 4", "hls/b4.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 5", "hls/b5.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports Max 1", "hls/bm1.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports Max 2", "hls/bm2.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("S Sport", "hls/s1.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("S Sport 2", "hls/s2.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("TRT Spor", "hls/trt.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("TRT 1", "hls/trt1.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("A Spor", "hls/aspor.m3u8", "https://resmim.net/cdn/2026/07/22/ETtrXH.png")
]

BASE_DOMAIN = "https://css.d6e3eds5e065t5.help"

def generate_playlist():
    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={TARGET_URL}",
        ""
    ]
    
    valid_count = 0
    
    for name, path, logo in channels:
        # Tam akış adresini oluştur
        stream_url = f"{BASE_DOMAIN}/{path}"
        extinf = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="BeinSports",{name}'
        
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)
        valid_count += 1
        print(f"[+] Eklendi: {name} -> {stream_url}")

    # Dosyaya kaydet
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
    
    print(f"[✓] Toplam {valid_count} kanal özel yol desteğiyle '{OUTPUT_FILE}' dosyasına yazıldı.")

if __name__ == "__main__":
    generate_playlist()
