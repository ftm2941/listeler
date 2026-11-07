TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

# Kanal adları, URL kodları ve logoları
channels = [
    ("Bein Sports 1", "b1", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 2", "b2", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 3", "b3", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 4", "b4", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports 5", "b5", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports Max 1", "bm1", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("Bein Sports Max 2", "bm2", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("S Sport", "s1", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("S Sport 2", "s2", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("TRT Spor", "trt", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("TRT 1", "trt1", "https://resmim.net/cdn/2026/07/22/ETtrXH.png"),
    ("A Spor", "aspor", "https://resmim.net/cdn/2026/07/22/ETtrXH.png")
]

BASE_DOMAIN = "https://css.d6e3eds5e065t5.help/hls"

def generate_playlist():
    m3u_lines = [
        "#EXTM3U",
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        f"#EXTVLCOPT:http-referrer={TARGET_URL}",
        ""
    ]
    
    valid_count = 0
    
    for name, code, logo in channels:
        stream_url = f"{BASE_DOMAIN}/{code}.m3u8"
        # İstediğin IPTV formatı: tvg-name, tvg-logo ve group-title entegre edildi
        extinf = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="BeinSports",{name}'
        
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)
        valid_count += 1
        print(f"[+] Eklendi: {name} -> {stream_url}")

    # Dosyaya kaydet
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
    
    print(f"[✓] Toplam {valid_count} kanal logo destekli olarak '{OUTPUT_FILE}' dosyasına yazıldı.")

if __name__ == "__main__":
    generate_playlist()
