import os
from bs4 import BeautifulSoup
import requests

URL = 'https://tvdiziler.tv/'


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

    # Sadece dizi kartlarının veya son bölüm listelerinin bulunduğu alanları hedefleyelim
    # Site yapısındaki ana içerik kapsayıcılarını tarıyoruz
    for kart in soup.select(
        '.card, .dizi-kutusu, article, .col-xl-2, .col-lg-3, .col-md-4'
    ):
      baslik_elem = kart.find(['h2', 'h3', 'a', 'span'])
      if baslik_elem:
        baslik = baslik_elem.get_text(strip=True)
        link = (
            baslik_elem['href']
            if baslik_elem.name == 'a'
            else (
                kart.find('a')['href'] if kart.find('a') else URL.rstrip('/')
            )
        )

        # -------------------------------------------------------------
        # FİLTRELEME: Menü linklerini, profilleri ve puanları dışarıda bırakalım
        # -------------------------------------------------------------
        haric_kelimeler = [
            'anasayfa',
            'keşfet',
            'takvim',
            'dizi listesi',
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
        ]

        baslik_kucuk = baslik.lower()
        if any(kelime in baslik_kucuk for kelime in haric_kelimeler):
          continue  # Bu başlıkları atla

        # Sadece gerçek dizi/bölüm niteliği taşıyanları alalım
        if baslik and len(baslik) > 3:
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

          dizi_listesi.append({'baslik': baslik, 'link': link, 'logo': logo})

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
      temiz_baslik = (
          item['baslik'].replace('\n', ' ').replace('\r', '').strip()
      )
      logo_url = item['logo']

      f.write(
          f'#EXTINF:-1 tvg-name="{temiz_baslik}" tvg-logo="{logo_url}"'
          f' group-title="TvDiziler",{temiz_baslik}\n'
      )
      f.write(f"{item['link']}\n")

  print(f'{len(veriler)} adet dizi başarıyla tvdiziler.m3u8 dosyasına yazıldı.')


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    m3u8_kaydet(veriler)
