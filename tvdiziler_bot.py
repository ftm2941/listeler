def m3u8_kaydet(veriler):
  dosya = 'tvdiziler.m3u8'
  with open(dosya, 'w', encoding='utf-8') as f:
    f.write('#EXTM3U\n')
    for item in veriler:
      # Başlığı burada garanti olması için bir kez daha temizliyoruz
      baslik = temizle_baslik(item['baslik'])
      logo_url = item['logo']
      video_link = item['link']

      f.write(
          f'#EXTINF:-1 tvg-logo="{logo_url}"'
          f' group-title="Yeni Bölümler | {baslik}", {baslik}\n'
      )
      f.write('#EXTVLCOPT:http-referrer=https://tvdiziler.tv\n')
      f.write(f'{video_link}\n\n')

  print(
      f'{len(veriler)} adet tertemiz dizi bağlantısı tvdiziler.m3u8 dosyasına'
      ' kaydedildi.'
  )
