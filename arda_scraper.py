import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

captured_streams = set()

async def handle_request(request):
    url = request.url
    # Tüm m3u8, hls akışlarını ve gizli sunucu uzantılarını yakala
    if ".m3u8" in url or "/hls/" in url or ".help" in url or "stream" in url:
        if "batutest" not in url and url not in captured_streams:
            print(f"[+] Yeni Yayın Linki Yakalandı: {url}")
            captured_streams.add(url)

async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            bypass_csp=True
        )
        
        page = await context.new_page()
        page.on("request", handle_request)
        
        print(f"[*] Hedef siteye gidiliyor: {TARGET_URL}")
        try:
            await page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(6)
            
            # Sayfadaki olası kanal butonlarına veya liste elemanlarına tıklama simülasyonu
            print("[*] Kanal listesi taranıyor ve butonlar tetikleniyor...")
            
            # Sayfa genelindeki tıklanabilir tüm öğeleri ve butonları dene
            buttons = await page.query_selector_all("a, button, .channel-item, li")
            for btn in buttons[:25]: # İlk 25 potansiyel kanal butonunu tıkla
                try:
                    await btn.click(timeout=1000)
                    await asyncio.sleep(1)
                except Exception:
                    pass

            # İframe içindeki oynatıcıları ve içerikleri tetikle
            for frame in page.frames:
                try:
                    await frame.click("body", timeout=2000)
                except Exception:
                    pass

            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"[!] Hata oluştu: {e}")
            
        await browser.close()

    # Eğer canlı yakalanamazsa veya eksik kalırsa bilinen örnek hls adresini yedek olarak ekle
    if not captured_streams:
        captured_streams.add("https://css.d6e3eds5e065t5.help/hls/b1.m3u8")

    # M3U Dosyasını Düzenli Şekilde Oluştur
    if captured_streams:
        m3u_lines = [
            "#EXTM3U",
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            f"#EXTVLCOPT:http-referrer={TARGET_URL}",
            ""
        ]
        
        for idx, stream_url in enumerate(sorted(captured_streams), start=1):
            extinf = f'#EXTINF:-1 group-title="ArdaSpor",ArdaSpor Kanal {idx}'
            m3u_lines.append(extinf)
            m3u_lines.append(stream_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")
        print(f"[✓] Toplam {len(captured_streams)} yayın adresi '{OUTPUT_FILE}' dosyasına başarıyla yazıldı.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
