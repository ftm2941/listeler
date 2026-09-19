import os
import urllib.request

url = "https://mahsun-amp.click"
hedef_dosya = "kanallar2.m3u8"

try:
    # 1. Kaynak adresten güncel ham veriyi çek
    req = urllib.request.Request(
        url, headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response:
        kaynak_veri = response.read().decode('utf-8')

    # Kaynaktaki linkleri satır satır ayıkla (başlıklar hariç http ile başlayanlar)
    yeni_linkler = [
        line.strip() for line in kaynak_veri.splitlines() 
        if line.strip() and not line.startswith("#")
    ]

    # 2. Yereldeki mevcut kanallar2.m3u8 şablonunu oku
    if os.path.exists(hedef_dosya):
        with open(hedef_dosya, "r", encoding="utf-8") as f:
            satirlar = f.readlines()
    else:
        print(f"Hata: {hedef_dosya} dosyası repoda bulunamadı!")
        exit()

    # 3. Yapıyı bozmadan sadece URL satırlarını yeni linklerle sırasıyla güncelle
    guncellenmis_satirlar = []
    link_index = 0

    for satir in satirlar:
        temiz_satir = satir.strip()
        # Eğer satır bir etiket (#EXTM3U, #EXTINF, vb.) veya boşluksa aynen koru
        if temiz_satir.startswith("#") or not temiz_satir or not temiz_satir.startswith("http"):
            guncellenmis_satirlar.append(satir if satir.endswith("\n") else satir + "\n")
        else:
            # Sıradaki yeni link ile değiştir
            if link_index < len(yeni_linkler):
                guncellenmis_satirlar.append(yeni_linkler[link_index] + "\n")
                link_index += 1
            else:
                guncellenmis_satirlar.append(satir if satir.endswith("\n") else satir + "\n")

    # 4. Dosyayı aynı yapı ve güncel linklerle tekrar kaydet
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        f.writelines(guncellenmis_satirlar)

    print(f"Başarılı: Kanal şablonu korundu, sadece içindeki linkler güncellendi.")

except Exception as e:
    print(f"Hata oluştu: {e}")
