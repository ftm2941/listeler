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
  temiz = re.sub(r'HD', '', temiz)

  # Tekrarlayan kelime / karakter ikilenmelerini temizle (Örn: "Altı Üstü İstanbulAltı Üstü istanbul")
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


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Referer': URL,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
}


def ham_video_bul(detay_link):
  """Detay sayfasındaki player (data-hhs) üzerinden ham video linkini (.m3u8/.mp4) çeker"""
  try:
    resp = requests.get(detay_link, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
      return None
    html = resp.text

    # Player bağlantılarını (data-hhs) topla; varsa "Tek Part" tercih et
    player_links = re.findall(r'data-hhs="([^"]+)"', html)
    if not player_links:
      return None

    titled = re.findall(r'data-hhs="([^"]+)"[^>]*title="([^"]*)"', html)
    chosen = None
    for link, title in titled:
      if 'Tek Part' in title or 'Part' in title:
        chosen = link
        break
    if not chosen:
      chosen = player_links[0]

    if chosen.startswith('/'):
      player_url = 'https://tvdiziler.tv' + chosen
    elif chosen.startswith('http'):
      player_url = chosen
    else:
      player_url = 'https://tvdiziler.tv/' + chosen

    r2 = requests.get(player_url, headers=HEADERS, timeout=15)
    if r2.status_code != 200:
      return None
    player_html = r2.text

    # jwplayer sources: [{file:"..."}]
    m = re.search(r'sources:\s*\[\s*\{\s*file:\s*"([^"]+)"', player_html)
    if m:
      return m.group(1).replace('\\/', '/')

    # Genel .m3u8 / .mp4 araması
    m2 = re.search(r'https?://[^\s<>"\']+?\.(?:m3u8|mp4)(?:\?[^\s<>"\']*)?', player_html)
    if m2:
      return m2.group(0).replace('\\/', '/')

  except Exception:
    pass

  return None


def dizileri_cek():
  headers = HEADERS

  try:
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    dizi_listesi = []

    for a_tag in soup.find_all('a', href=True):
      link = a_tag['href']
      baslik = a_tag.get_text(strip=True)

      if 'bolum' not in link and '/dizi/' not in link:
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

      if not logo or ('uploads/series' not in logo and 'uploads/cover' not in logo):
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

      # Detay sayfasına girip ham video linkini çekiyoruz
      ham_link = ham_video_bul(link)

      # KESİN KURAL: Eğer ham video (.m3u8 / .mp4) bulunamadıysa site linkini ASLA yazma, atla!
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
    return []


def m3u8_kaydet(veriler):
  dosya = 'tvdiziler.m3u8'
  with open(dosya, 'w', encoding='utf-8') as f:
    f.write('#EXTM3U\n')
    for item in veriler:
      baslik = temizle_baslik(item['baslik'])
      logo_url = item['logo']
      video_link = item['link']

      # İstediğiniz kusursuz format yapısı
      f.write(
          f'#EXTINF:-1 tvg-logo="{logo_url}"'
          f' group-title="Yeni Bölümler | {baslik}", {baslik}\n'
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
