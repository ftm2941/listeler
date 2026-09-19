import urllib.request

url = "https://mahsun-amp.click"
hedef_dosya = "kanallar2.m3u8"

try:
    # Kaynak adresten güncel içeriği ham haliyle çek
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        canli_veri = response.read().decode('utf-8')

    # Gelen veriyi yapı hiç bozulmadan kanallar2.m3u8 dosyasına yaz
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.write(canli_veri)

    print(f"Başarılı: Yapı korundu ve canlı linkler {hedef_dosya} dosyasına işlendi.")

except Exception as e:
    print(f"Hata oluştu: {e}")
