import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

captured_streams = {}

async def handle_request(request):
    url = request.url
    # .m3u8 veya .help içeren tüm hls akışlarını yakala
    if ".m3u8" in url or "/hls/" in url or ".help" in url:
        if "batutest" not in url:
            # Hangi kanal olduğunu anlamak için url'deki b1, b2 gibi anahtar kelimeleri veya genel sırayı kullanalım
            if url not in captured_streams.values():
                idx = len(captured_streams) + 1
                channel_name = f"ArdaSpor Kanal {idx}"
                
                # Eğer url içinde b1, b2 gibi ibareler varsa isimlendirmeyi özelleştir
                if "b1" in url: channel_name = "Bein Sports 1"
                elif "b2" in url: channel_name = "Bein Sports 2"
                elif "b3" in url: channel_name = "Bein Sports 3"
                elif "b4" in url: channel_name = "Bein Sports 4"
                elif "b5" in url: channel_name = "Bein Sports 5"
                elif "s1" in url or "ssport1" in url: channel_name = "S Sport"
                elif "s2" in url or "ssport2" in url: channel_name = "S Sport 2"
                elif "trt" in url: channel_name = "TRT Spor"
                
                print(f"[+] Yakalandı [{channel_name}]: {url}")
                captured_streams[channel_name] = url

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
            await asyncio.sleep(5)
            
            print("[*] Sitedeki tüm kanal butonları ve oynatıcılar tetikleniyor...")
            
            # Sayfadaki tüm tıklanabilir kanal öğelerini, linkleri ve butonları bul
            selectors = ["button", "a", ".channel", ".list-group-item", "li", "span"]
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                for el in elements[:30]:
                    try:
                        text = await el.inner_text()
                        if any(k in text.upper() for k in ["BEIN", "SPORT", "TRT", "SPOR", "A SPOR", "KANAL"]):
                            await el.click(timeout=1000)
                            await asyncio.sleep(2) # Her kanal geçişi arasında yayın yüklenmesi için bekleme
                    except Exception:
                        continue

            # Son ekrana geçişler için ekstra bekleme
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f"[!] Hata oluştu: {e}")
            
        await browser.close()

    # Eğer hiçbir şey yakalanamazsa en azından ana yayını yedek koy
    if not captured_streams:
        captured_streams["ArdaSpor Ana Yayın"] = "https://css.d6e3eds5e065t5.help/hls/b1.m3u8"

    # M3U Dosyasını Oluştur
    if captured_streams:
        m3u_lines = [
            "#EXTM3U",
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            f"#EXTVLCOPT:http-referrer={TARGET_URL}",
            ""
        ]
        
        for name, stream_url in captured_streams.items():
            extinf = f'#EXTINF:-1 group-title="ArdaSpor",{name}'
            m3u_lines.append(extinf)
            m3u_lines.append(stream_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")
        print(f"[✓] Toplam {len(captured_streams)} kanal başarıyla '{OUTPUT_FILE}' dosyasına yazıldı.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
