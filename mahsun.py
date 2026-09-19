import urllib.request

# Veriyi çekeceğiniz adres
url = "https://mahsun-amp.click"
hedef_dosya = "links.txt"

try:
    # İstek atma ve User-Agent ekleme
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        yeni_veri = response.read().decode('utf-8')

    # Gelen veriyi dosyaya yazma
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.write(yeni_veri)

    print("Veriler başarıyla mahsun-amp.click adresinden çekildi ve kaydedildi.")
    
except Exception as e:
    print(f"Hata oluştu: {e}")
