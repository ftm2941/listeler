import requests

TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

# Türetilecek kanal listesi ve M3U içindeki görünen isimleri
channels = [
    ("Bein Sports 1", "b1"),
    ("Bein Sports 2", "b2"),
    ("Bein Sports 3", "b3"),
    ("Bein Sports 4", "b4"),
    ("Bein Sports 5", "b5"),
    ("Bein Sports Max 1", "bm1"),
    ("Bein Sports Max 2", "bm2"),
    ("S Sport", "s1"),
    ("S Sport 2", "s2"),
    ("TRT Spor", "trt"),
    ("TRT 1", "trt1"),
    ("A Spor", "aspor")
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
    
    for name, code in channels:
        stream_url = f"{BASE_DOMAIN}/{code}.m3u8"
        
        # İsteğe bağlı: Linkin gerçekten çalışıp çalışmadığını (200 OK döndüğünü) kontrol edebiliriz
        try:
            response = requests.head(stream_url, timeout=3)
            # İsteğin aktif olduğunu doğrulayarak ekle veya direkt listeye dahil et
            extinf = f'#EXTINF:-1 group-title="ArdaSpor",{name}'
            m3u_lines.append(extinf)
            m3u_lines.append(stream_url)
            valid_count += 1
            print(f"[+] Eklendi: {name} -> {stream_url}")
        except Exception as e:
            print(f"[!] Hata ({name}): {e}")

    # Dosyaya yaz
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")
    
    print(f"[✓] Toplam {valid_count} kanal başarıyla '{OUTPUT_FILE}' dosyasına türetilerek yazıldı.")

if __name__ == "__main__":
    generate_playlist()
