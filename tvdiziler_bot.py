import os
import re
from bs4 import BeautifulSoup
import requests

URL = 'https://tvdiziler.tv/'


def temizle_baslik(ham_baslik):
  # Başlıktaki tekrarları ve gereksiz kelimeleri temizleyelim
  # Örn: "Uzak Şehir izleUzak Şehir 73.Bölüm izleBugün" -> "Uzak Şehir 73. Bölüm"
  temiz = ham_baslik.replace('\n', ' ').replace('\r', '').strip()

  # Sitedeki tekrarlayan birleşik metinleri ayıklamak için akıllı regex veya kelime temizliği
  # "izle", "Bugün", "Dün" gibi ifadeleri temizleyelim
  temiz = re.sub(r'(Bugün|Dün|\d{1,2}\s+[A-Za-z]+\s+\d{4})', '', temiz)
  temiz = temiz.replace('izle', ' ').replace('  ', ' ').strip()

  # Eğer aynı kelime ard arda iki kez yazıldıysa ilkini sadeleştir
  kelimeler = temiz.split()
  if len(kelimeler) > 4 and kelimeler[: int(len(kelimeler) / 2)] == kelimeler[int(len(kelimeler) / 2) : int(len(kelimeler) / 2) * 2]:
    temiz = ' '.join(kelimeler[: int(len(kelimeler) / 2)])

  return temiz if temiz else 'Dizi Bölümü'


def dizileri_cek():
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/122.0.0.0 Safari/537.36'
      )
  }

  try:
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    dizi_listesi = []

    # Sadece ana sayfadaki son eklenen dizi kartlarını hedefleyelim
    for kart in soup.select('.col-xl-2, .col-lg-3, .col-md-4, article'):
      baslik_elem = kart.find(['h2', 'h3', 'a', 'span'])
      if baslik_elem:
        baslik = baslik_elem.get_text(strip=True)
        link = (
            baslik_elem['href']
            if baslik_elem.name == 'a'
            else (kart.find('a')['href'] if kart.find('a') else '')
        )

        if not link:
          continue

        # -------------------------------------------------------------
        # KESİN FİLTRELEME: Menüleri, türleri, sosyal medyayı ve profilleri at
        # -------------------------------------------------------------
        yasakli_kokenler = [
            'profile/',
            'film/tur/',
            'dizi/tur/',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'kesfet',
            'takvim',
            'dizi-izle',
            'film-izle',
            'tartismalar',
            'oyuncular',
        ]
        if any(yasak in link for yasak in yasakli_kokenler) or link in [
            'https://tvdiziler.tv/',
            'https://tvdiziler.tv',
        ]:
          continue

        # Klasik menü kelimelerini içeren başlıkları ele
        haric_kelimeler = [
            'anasayfa',
            'keşfet',
            'takvim',
            'sinema',
            'tartışma',
            'oyuncu',
            'level',
            'puan',
            'giriş yap',
            'kayıt ol',
            'facebook',
            'twitter',
            'instagram',
            'komedi filmleri',
            'bilim kurgu',
            'macera filmleri',
        ]
        baslik_kucuk = baslik.lower()
        if any(kelime in baslik_kucuk for kelime in haric_kelimeler):
          continue

        # Sadece gerçek dizi bölüm linklerini alalım (Genellikle içinde '-bolum-izle' geçer)
        if 'bolum' in link or 'dizi/' in link:
          img_elem = kart.find('img')
          logo = ''
          if img_elem:
            logo = (
                img_elem.get('data-src')
                or img_elem.get('src')
                or img_elem.get('data-lazy-src')
                or ''
            )
            if logo.startswith('/'):
              logo = 'https://tvdiziler.tv' + logo
            elif logo and not logo.startswith('http'):
              logo = 'https://tvdiziler.tv/' + logo

          if link.startswith('/'):
            link = 'https://tvdiziler.tv' + link
          elif not link.startswith('http'):
            link = 'https://tvdiziler.tv/' + link

          temiz_ad = temizle_baslik(baslik)

          dizi_listesi.append({
              'baslik': temiz_ad,
              'link': link,
              'logo': logo,
          })

    unique_diziler = {d['link']: d for d in dizi_listesi}.values()
    return list(unique_diziler)

  except Exception as e:
    print(f'Veri çekilirken hata oluştu: {e}')
    return []


def m3u8_kaydet(veriler):
  dosya = 'tvdiziler.m3u8'
  with open(dosya, 'w', encoding='utf-8') as f:
    f.write('#EXTM3U\n')
    for item in veriler:
      baslik = item['baslik']
      logo_url = item['logo']
      video_link = item['link']

      # İstediğiniz özel format yapısı
      f.write(
          f'#EXTINF:-1 tvg-logo="{logo_url}"'
          f' group-title="Yerli - {baslik}", {baslik} Son Bölüm\n'
      )
      f.write('#EXTVLCOPT:http-referrer=https://tvdiziler.tv\n')
      f.write(f'{video_link}\n\n')

  print(
      f'{len(veriler)} adet tertemiz dizi tvdiziler.m3u8 dosyasına kaydedildi.'
  )


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    m3u8_kaydet(veriler)
