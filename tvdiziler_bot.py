import json
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
    response = requests.get(URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    dizi_listesi = []

    # Sitedeki son eklenen bölümlerin veya dizi kartlarının bulunduğu alanları seçiyoruz
    # Not: Sitenin güncel HTML etiket yapısına göre buradaki class isimleri güncellenebilir.
    bolum_kartlari = soup.find_all(
        'div', class_='col-xl-2'
    )  # Örnek kart yapısı

    if not bolum_kartlari:
      # Alternatif olarak genel başlıkları tarayalım
      bolum_kartlari = soup.find_all('article')

    for kart in soup.select('.card, .dizi-kutusu, article, li'):
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

        if baslik and len(baslik) > 2:
          # Göreceli linkleri tam URL'ye çevirelim
          if link.startswith('/'):
            link = 'https://tvdiziler.tv' + link

          dizi_listesi.append({'baslik': baslik, 'link': link})

    # Tekrarlayan kayıtları temizle
    unique_diziler = {d['link']: d for d in dizi_listesi}.values()
    return list(unique_diziler)

  except Exception as e:
    print(f'Veri çekilirken hata oluştu: {e}')
    return []


def kaydet(veriler):
  dosya = 'tvdiziler.json'
  with open(dosya, 'w', encoding='utf-8') as f:
    json.dump(veriler, f, ensure_ascii=False, indent=4)
  print(f'{len(veriler)} adet dizi bilgisi başarıyla kaydedildi.')


if __name__ == '__main__':
  veriler = dizileri_cek()
  if veriler:
    kaydet(veriler)
