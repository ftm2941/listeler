import html
import re
import urllib.request

url = "https://mahsun-amp.click"
hedef_dosya = "kanallar2.m3u8"

try:
    # Adresten sayfayı çek
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        html_veri = response.read().decode('utf-8')

    # HTML etiketlerini (<html>, <body>, <div vb.) tamamen temizle
    temiz_metin = re.sub(r'<[^>]+>', '', html_veri)
    
    # HTML karakter kodlamalarını (örn: &amp;) normal karakterlere çevir
    temiz_metin = html.unescape(temiz_metin)

    # Temizlenen M3U yapısını dosyaya yaz
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.write(temiz_metin.strip())

    print(f"Başarılı: HTML etiketleri temizlendi ve M3U yapısı {hedef_dosya} dosyasına kaydedildi.")

except Exception as e:
    print(f"Hata oluştu: {e}")
