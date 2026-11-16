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

    for kart in soup.select(
        '.card, .dizi-kutusu, article, .col-xl-2, .col-lg-3, .col-md-4'
    ):
      baslik_elem = kart.find(['h2', 'h3', 'a', 'span'])
      if baslik_elem:
        baslik = baslik_elem.get_text(strip=True)
        detay_link = (
            baslik_elem['href']
            if baslik_elem.name == 'a'
            else (
                kart.find('a')['href'] if kart.find('a') else URL.rstrip('/')
            )
        )

        # Filtreleme (Menüleri ve gereksizleri eleyelim)
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
        if any(kelime in baslik.lower() for kelime in haric_kelimeler):
          continue

        if baslik and len(baslik) > 3:
          # Afiş görselini yakala
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

          if detay_link.startswith('/'):
            detay_link = 'https://tvdiziler.tv' + detay_link
          elif not detay_link.startswith('http'):
            detay_link = 'https://tvdiziler.tv/' + detay_link

          # -------------------------------------------------------------
          # DETAY SAYFASINDAN HAM VİDEO LİNKİNİ ÇEKME ADIMI
          # -------------------------------------------------------------
          ham_video_link = detay_link  # Varsayılan olarak detay linki
          try:
            detay_resp = requests.get(detay_link, headers=headers, timeout=5)
            if detay_resp.status_code == 200:
              detay_soup = BeautifulSoup(detay_resp.text, 'html.parser')
              # Sitedeki video oynatıcı kaynaklarını (iframe veya video src) arayalım
              video_tag = detay_soup.find('video')
              iframe_tag = detay_soup.find('iframe')

              if video_tag and video_tag.get('src'):
                ham_video_link = video_tag.get('src')
              elif iframe_tag and iframe_tag.get('src'):
                ham_video_link = iframe_tag.get('src')
              else:
                # Script içindeki .m3u8 veya .mp4 uzantılı ham linkleri arayalım
                for script in detay_soup.find_all('script'):
                  script_text = script.string or ''
                  if '.m3u8' in script_text or '.mp4' in script_text:
                    # Basit bir string ayıklama yapılabilir
                    import re

                    match = re.search(
                        r'https?://[^\s<>"]+?\.(?:m3u8|mp4)', script_text
                    )
                    if match:
                      ham_video_link = match.group(0)
                      break
          except Exception:
            pass  # Detay sayfasına ulaşılamazsa ana linki kullanır

          dizi_listesi.append({
              'baslik': baslik,
              'link': ham_video_link,
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
      temiz_baslik = (
          item['baslik'].replace('\n', ' ').replace('\r', '').strip()
      )
      logo_url = item['logo']
      video_link = item['link']

      # Eksiksiz tvg-name, tvg-logo ve grup etiketleri ile ham oynatma adresi
      f.write(
          f'#EXTINF:-1 tvg-name="{temiz_baslik}" tvg-logo="{logo_url}"'
          f' group-title="TvDiziler",{temiz_baslik}\n'
      )
      f.write(f'{video_link}\n')

  print(
      f'{len(veriler)} adet dizi ham linkleri ve afişleri ile tvdiziler.m3u8'
      ' dosyasına kaydedildi.'
  )


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    m3u8_kaydet(veriler)
