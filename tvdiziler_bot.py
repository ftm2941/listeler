import os
import re
from bs4 import BeautifulSoup
import requests

URL = 'https://tvdiziler.tv/'


def temizle_baslik(ham_baslik):
  """Başlıktaki tekrarlayan birleşmeleri ve çöpleri kusursuz şekilde temizler"""
  temiz = ham_baslik.replace('\n', ' ').replace('\r', '').strip()
  
  # Tarihleri, Bugün, Dün, izle ve benzeri ifadeleri kaldır
  temiz = re.sub(r'(Bugün|Dün|\d{1,2}\s+[A-Za-z]+\s+\d{4}|\d{1,2}\s+[Kk]asım|\d{1,2}\s+[Aa]ralık|\d{1,2}\s+[Oo]cak|\d{1,2}\s+[Şş]ubat|\d{1,2}\s+[Mm]art|\d{1,2}\s+[Nn]isan|\d{1,2}\s+[Mm]ayıs|\d{1,2}\s+[Hh]aziran|\d{1,2}\s+[Tt]emmuz|\d{1,2}\s+[Aa]ğustos|\d{1,2}\s+[Ee]ylül|\d{1,2}\s+[Ee]kim)', '', temiz)
  temiz = temiz.replace('izle', ' ').replace('İzle', ' ').replace('FULL', '').replace('Full', '')
  temiz = re.sub(r'\d+\.Bölüm.*', '', temiz)
  temiz = re.sub(r'Son Bölüm.*', '', temiz)

  # Tekrarlayan kelime / karakter ikilenmelerini temizle
  uzunluk = len(temiz)
  if uzunluk > 4:
    yari = uzunluk // 2
    if temiz[:yari].strip().lower() == temiz[yari:].strip().lower():
      temiz = temiz[:yari].strip()
    else:
      kelimeler = temiz.split()
      if len(kelimeler) >= 4 and len(kelimeler) % 2 == 0:
        orta = len(kelimeler) // 2
        p1 = " ".join(kelimeler[:orta])
        p2 = " ".join(kelimeler[orta:])
        if p1.lower() == p2.lower():
          temiz = p1

  return temiz.strip() if temiz else 'Dizi Bölümü'


def ham_video_bul(detay_link):
  """Detay sayfasındaki .m3u8 (twimg vb.), .mp4 ve Yandex storage linklerini yakalar"""
  headers = {
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
          'AppleWebKit/537.36 (KHTML, like Gecko) '
          'Chrome/122.0.0.0 Safari/537.36'
      ),
      'Referer': URL,
      'X-Requested-With': 'XMLHttpRequest'
  }

  try:
    resp = requests.get(detay_link, headers=headers, timeout=10)
    if resp.status_code == 200:
      html = resp.text

      # 1. twimg veya diğer .m3u8 akış linklerini yakala (Parametreli dahil)
      m3u8_match = re.search(r'https?://[^\s<>"]+?\.m3u8(?:\?[^\s<>"]*)?', html)
      if m3u8_match:
        link = m3u8_match.group(0).rstrip('"\'\\').replace('\\/', '/')
        return link

      # 2. .mp4 video bağlantılarını yakala
      mp4_match = re.search(r'https?://[^\s<>"]+?\.mp4(?:\?[^\s<>"]*)?', html)
      if mp4_match:
        link = mp4_match.group(0).rstrip('"\'\\').replace('\\/', '/')
        return link

      # 3. Yandex storage linkleri
      yandex_match = re.search(r'https?://[^\s<>"]+?storage\.yandex\.net[^\s<>"]+', html)
      if yandex_match:
        link = yandex_match.group(0).rstrip('"\'\\').replace('\\/', '/')
        return link

      # 4. JavaScript script tagleri içindeki gizli m3u8/mp4 linkleri
      soup = BeautifulSoup(html, 'html.parser')
      for script in soup.find_all('script'):
        script_text = script.string or ''
        if '.m3u8' in script_text or '.mp4' in script_text:
          match = re.search(r'https?://[^\s<>"]+?\.(?:m3u8|mp4)(?:\?[^\s<>"]*)?', script_text)
          if match:
            return match.group(0).rstrip('"\'\\').replace('\\/', '/')

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
      'Referer': URL
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

      # Detay sayfasına arka planda girip twimg / m3u8 ham video bağlantısını çekiyoruz
      ham_link = ham_video_bul(link)
      
      # Sadece başarılı bir şekilde ham video linki bulunanları listeye alıyoruz
      if not ham_link:
        continue

      dizi_listesi.append({
          'baslik': temiz_ad,
          'link': ham_link,
          'logo': logo,
      })

    unique_diziler = {d['link']: d for d in dizi_listesi}.values()
    return list(unique_diziler)

  except Exception as e:
    print(f'Veri çekilirken hata oluştu: {e}')
