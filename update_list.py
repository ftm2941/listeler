import re
import urllib.request

# Hedef web sitesi ve kaydedilecek m3u8 dosyası
TARGET_URL = "https://taraftarium24.ch"
OUTPUT_FILE = "kanallar.m3u8"

# Tarayıcı gibi görünmek için User-Agent başlığı
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_channels():
    try:
        req = urllib.request.Request(TARGET_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # HTML/JS içeriğinden .m3u8 yayın bağlantılarını regex ile arama
        m3u8_links = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', html)
        
        # M3U8 Dosyası Başlığı
        m3u8_content = "#EXTM3U\n"
        
        if m3u8_links:
            # Bulunan bağlantıları M3U formatında listeleme
            for index, link in enumerate(set(m3u8_links), start=1):
                m3u8_content += f"#EXTINF:-1 tvg-id=\"taraftarium_{index}\", Taraftarium Kanal {index}\n"
                m3u8_content += f"{link}\n"
        else:
            # Eğer doğrudan .m3u8 linki bulunamazsa siteyi varsayılan kanal olarak ekle
            m3u8_content += f"#EXTINF:-1 tvg-id=\"taraftarium_main\", Taraftarium24 Canlı\n"
            m3u8_content += f"{TARGET_URL}\n"

        # Dosyayı yazma/güncelleme
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u8_content)
            
        print(f"{OUTPUT_FILE} başarıyla güncellendi.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    fetch_channels()
