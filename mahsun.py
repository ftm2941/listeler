import os
import re
import urllib.request

url = "https://mahsun-amp.click"
hedef_dosya = "kanallar2.m3u8"

try:
    # 1. Adresten içeriği çek
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        html_icerik = response.read().decode('utf-8')

    # 2. İçerikteki linkleri bul
    bulunan_linkler = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', html_icerik)
    yeni_linkler = set(bulunan_linkler)

    # 3. Eğer daha önceden kanallar2.m3u8 varsa eski linkleri oku
    eski_linkler = set()
    if os.path.exists(hedef_dosya):
        with open(hedef_dosya, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # M3U başlık satırlarını hariç tutarak sadece linkleri al
                if line and not line.startswith("#"):
                    eski_linkler.add(line)

    # 4. Yeni gelenler ile eski linkleri birleştir
    tum_linkler = list(yeni_linkler) + [l for l in eski_linkler if l not in yeni_linkler]

    # 5. Dosyaya M3U8 formatında yaz
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for link in tum_linkler:
            f.write(link + "\n")

    print(f"İşlem tamamlandı. Linkler {hedef_dosya} dosyasına kaydedildi.")

except Exception as e:
    print(f"Hata oluştu: {e}")
