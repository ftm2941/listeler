import os
import urllib.request

url = "https://mahsun-amp.click"
hedef_dosya = "kanallar2.m3u8"

try:
    # 1. Adresten içeriği ham haliyle çek
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        yeni_veri = response.read().decode('utf-8')

    # 2. Dosyanın mevcut yapısını bozmadan doğrudan kaydet
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.write(yeni_veri)

    print(f"İşlem başarılı. İçerik {hedef_dosya} dosyasına yapısı bozulmadan yazıldı.")

except Exception as e:
    print(f"Hata oluştu: {e}")
