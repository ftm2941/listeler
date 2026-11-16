import os
import re
from bs4 import BeautifulSoup
import requests

URL = 'https://tvdiziler.tv/'


def temizle_baslik(ham_baslik):
  temiz = ham_baslik.replace('\n', ' ').replace('\r', '').strip()
  temiz = re.sub(r'(Bugün|Dün|\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{1,2}\s+[Kk]asım|\d{1,2}\s+[Aa]ralık|\d{1,2}\s+[Oo]cak|\d{1,2}\s+[Şş]ubat|\d{1,2}\s+[Mm]art|\d{1,2}\s+[Nn]isan|\d{1,2}\s+[Mm]ayıs|\d{1,2}\s+[Hh]aziran|\d{1,2}\s+[Tt]emmuz|\d{1,2}\s+[Aa]ğustos|\d{1,2}\s+[Ee]ylül|\d{1,2}\s+[Ee]kim)', '', temiz)
  temiz = temiz.replace('izle', ' ').replace('İzle', ' ').replace('FULL', '').replace('Full', '')
  temiz = re.sub(r'\d+\.Bölüm.*', '', temiz)

  kelimeler = temiz.split()
  if len(kelimeler) >= 4:
    yari = int(len(kelimeler) / 2)
    if " ".join(kelimeler[:yari]).lower() == " ".join(kelimeler[yari:]).lower():
      temiz = " ".join(kelimeler[:yari])

  return temiz.strip() if temiz else 'Dizi Bölümü'


def ham_video_bul(detay_link, headers):
  """Detay sayfasına arka planda girip Yandex storage veya ham .mp4 / .m3u8 linkini yakalar"""
  try:
    resp = requests.get(detay_link, headers=headers, timeout=8)
    if resp.status_code == 200:
      html = resp.text

      # 1. Yandex storage veya mds linklerini arayalım
      yandex_match = re.search(r'https?://[^\s<>"]+?storage\.yandex\.net[^\s<>"]+', html)
      if yandex_match:
        return yandex_match.group(0).rstrip('"\'\\')

      # 2. .mp4 veya .m3u8 ham video bağlantılarını yakala
      video_match = re.search(r'https?://[^\s<>"]+?\.(?:m3u8|mp4)(?:\?[^\s<>"]*)?', html)
      if video_match:
        return video_match.group(0).rstrip('"\'\\')

      # 3. İframe kaynaklarını tarayalım
      soup = BeautifulSoup(html, 'html.parser')
      for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if 'yandex' in src or '.mp4' in src or '.m3u8' in src:
          return src

  except Exception:
    pass

  return None


def dizileri_cek():
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/122.0.0.0 Safari/537.36'
      ),
      'Referer': 'https://tvdiziler.tv/'
  }

  try:
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    dizi_listesi = []

    for a_tag in soup.find_all('a', href=True):
      link = a_tag['href']
      baslik = a_tag.get_text(strip=True)

      if 'bolum' not in link:
        continue

      kart = a_tag.find_parent(['article', 'div', 'li'])
      img_elem = kart.find('img') if kart else a_tag.find('img')

      logo = ''
      if img_elem:
        logo = (
            img_elem.get('data-src')
            or img_elem.get('src')
            or img_elem.get('data-lazy-src')
            or ''
        )

      if not logo or 'uploads/series' not in logo:
        continue

      if logo.startswith('/'):
        logo = 'https://tvdiziler.tv' + logo
      elif logo and not logo.startswith('http'):
        logo = 'https://tvdiziler.tv/' + logo

      if link.startswith('/'):
        link = 'https://tvdiziler.tv' + link
      elif not link.startswith('http'):
        link = 'https://tvdiziler.tv/' + link

      temiz_ad = temizle_baslik(baslik)

      # Detay sayfasına arka planda girip ham video linkini çözüyoruz
      ham_link = ham_video_bul(link, headers)
      
      # Eğer ham link çözülebildiyse doğrudan onu yazıyoruz, böylece player direkt açılır
      oynatilacak_link = ham_link if ham_link else link

      dizi_listesi.append({
          'baslik': temiz_ad,
          'link': oynatilacak_link,
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

      # Kategorize ve doğrudan player uyumlu yapı
      f.write(
          f'#EXTINF:-1 tvg-logo="{logo_url}"'
          f' group-title="Yeni Bölümler | {baslik}", {baslik} Son Bölüm\n'
      )
      f.write('#EXTVLCOPT:http-referrer=https://tvdiziler.tv\n')
      f.write(f'{video_link}\n\n')

  print(
      f'{len(veriler)} adet ham video bağlantılı dizi tvdiziler.m3u8 dosyasına'
      ' kaydedildi.'
  )


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    m3u8_kaydet(veriler)
