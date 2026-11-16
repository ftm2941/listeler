import os
import re
from bs4 import BeautifulSoup
import requests

URL = 'https://tvdiziler.tv/'


def temizle_baslik(ham_baslik):
  # Başlıktaki tekrarları, "izle", "Bugün", "Dün" ve tarihleri temizleyelim
  temiz = ham_baslik.replace('\n', ' ').replace('\r', '').strip()
  temiz = re.sub(
      r'(Bugün|Dün|\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{1,2}\s+Kasım|\d{1,2}\s+Aralık)',
      '',
      temiz,
  )
  temiz = temiz.replace('izle', ' ').replace('  ', ' ').strip()

  # Eğer kelime içinde tekrar eden yapışmalar varsa sadeleştirelim
  kelimeler = temiz.split()
  yari = int(len(kelimeler) / 2)
  if len(kelimeler) > 4 and kelimeler[:yari] == kelimeler[yari : yari * 2]:
    temiz = ' '.join(kelimeler[:yari])

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

    for kart in soup.select('.col-xl-2, .col-lg-3, .col-md-4, article, .card'):
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

        # 1. KURAL: Afişi (img) olmayan hiçbir şeyi içeri alma!
        # Menülerin, profillerin ve sosyal medyanın afişi yoktur, bu sayede hepsi elenir.
        img_elem = kart.find('img')
        if not img_elem:
          continue

        logo = (
            img_elem.get('data-src')
            or img_elem.get('src')
            or img_elem.get('data-lazy-src')
            or ''
        )

        if not logo or 'uploads/series' not in logo:
          continue  # Sadece dizi afişi klasöründen gelenleri kabul et

        if logo.startswith('/'):
          logo = 'https://tvdiziler.tv' + logo
        elif not logo.startswith('http'):
          logo = 'https://tvdiziler.tv/' + logo

        if link.startswith('/'):
          link = 'https://tvdiziler.tv' + link
        elif not link.startswith('http'):
          link = 'https://tvdiziler.tv/' + link

        temiz_ad = temizle_baslik(baslik)

        dizi_listesi.append({'baslik': temiz_ad, 'link': link, 'logo': logo})

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

      # İstediğiniz format yapısı
      f.write(
          f'#EXTINF:-1 tvg-logo="{logo_url}"'
          f' group-title="Yerli - {baslik}", {baslik} Son Bölüm\n'
      )
      f.write('#EXTVLCOPT:http-referrer=https://tvdiziler.tv\n')
      f.write(f'{video_link}\n\n')

  print(
      f'{len(veriler)} adet saf dizi içeriği tvdiziler.m3u8 dosyasına'
      ' kaydedildi.'
  )


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    m3u8_kaydet(veriler)
