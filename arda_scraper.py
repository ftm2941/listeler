import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

captured_streams = set()

async def handle_request(request):
    url = request.url
    # Ağ trafiğindeki m3u8 veya m3u uzantılı akışları yakala
    if ".m3u8" in url or ".m3u" in url:
        if "batutest" not in url and url not in captured_streams:
            print(f"[+] Yayın Linki Yakalandı: {url}")
            captured_streams.add(url)

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            bypass_csp=True
        )
        
        page = await context.new_page()
        page.on("request", handle_request)
        
        print(f"[*] Hedef siteye gidiliyor: {TARGET_URL}")
        try:
            await page.goto(TARGET_URL, timeout=60000, wait_until="networkidle")
            print("[*] Sayfa yüklendi, oynatıcı etkileşimi bekleniyor...")
            
            # Sayfadaki olası video, player veya oynat butonlarına tıklama simülasyonu
            await asyncio.sleep(5)
            
            # Sayfa genelinde tıklanabilir olası video alanlarını tetikle
            try:
                await page.click("video", timeout=3000)
            except Exception:
                pass
                
            try:
                await page.click(".play-button, #play, .player", timeout=3000)
            except Exception:
                pass

            # İframe'lerin içindeki elementlere tıkla
            for frame in page.frames:
                try:
                    await frame.click("body", timeout=2000)
                except Exception:
                    pass

            # Yayın linklerinin düşmesi için ek süre tanı
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"[!] Hata oluştu: {e}")
            
        await browser.close()

    # M3U Dosyasını Oluştur veya boşsa hata önleyici boş dosya bırak
    if captured_streams:
        m3u_lines = [
            "#EXTM3U",
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            f"#EXTVLCOPT:http-referrer={TARGET_URL}",
            ""
        ]
        
        for idx, stream_url in enumerate(sorted(captured_streams), start=1):
            extinf = f'#EXTINF:-1 group-title="ArdaSpor",ArdaSpor Yayın {idx}'
            m3u_lines.append(extinf)
            m3u_lines.append(stream_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")
        print(f"[✓] Başarıyla {len(captured_streams)} yayın adresi '{OUTPUT_FILE}' dosyasına yazıldı.")
    else:
        print("[!] Hiçbir yayın bağlantısı yakalanamadı. Boş dosya oluşturuluyor.")
        # Git commit hatası vermemesi için boş bir dosya oluşturuyoruz
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")

if __name__ == "__main__":
    asyncio.run(run_scraper())
