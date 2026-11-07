import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://ardaspor39.top/"
OUTPUT_FILE = "kanallar_arda.m3u8"

# Kanal adları ve linklerini eşleştirmek için sözlük
chan_mapping = {}
last_clicked_channel = "ArdaSpor Canlı Yayın"

async def handle_request(request):
    global last_clicked_channel
    url = request.url
    if ".m3u8" in url or "/hls/" in url or ".help" in url:
        if "batutest" not in url:
            print(f"[+] Yayın Yakalandı [{last_clicked_channel}]: {url}")
            chan_mapping[last_clicked_channel] = url

async def run_scraper():
    global last_clicked_channel
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
            
            # Sitedeki kanal butonlarını metinlerine göre bul ve sırayla tıkla
            print("[*] Kanal butonları taranıyor...")
            
            # BEIN SPORTS, S SPORT, TRT gibi kanal metinlerini içeren elementleri seç
            elements = await page.query_selector_all("button, a, div.channel, li, span")
            
            for el in elements:
                try:
                    text = await el.inner_text()
                    text_clean = text.strip()
                    # Belirttiğin popüler kanal başlıklarını yakala
                    if any(k in text_clean.upper() for k in ["BEIN", "SPORT", "TRT", "SPOR", "A SPOR"]):
                        if len(text_clean) < 30: # Çok uzun metinleri atla
                            last_clicked_channel = text_clean
                            print(f"[*] Tıklanan Kanal: {last_clicked_channel}")
                            await el.click(timeout=1500)
                            await asyncio.sleep(3) # Yayın linkinin düşmesi için kısa bekleme
                except Exception:
                    continue

            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[!] Hata oluştu: {e}")
            
        await browser.close()

    # Eğer hiçbir şey yakalanamazsa yedek olarak ana linki koy
    if not chan_mapping:
        chan_mapping["ArdaSpor Ana Yayın"] = "https://css.d6e3eds5e065t5.help/hls/b1.m3u8"

    # M3U Dosyasını Oluştur
    if chan_mapping:
        m3u_lines = [
            "#EXTM3U",
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            f"#EXTVLCOPT:http-referrer={TARGET_URL}",
            ""
        ]
        
        for name, stream_url in chan_mapping.items():
            extinf = f'#EXTINF:-1 group-title="ArdaSpor",{name}'
            m3u_lines.append(extinf)
            m3u_lines.append(stream_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines) + "\n")
        print(f"[✓] Toplam {len(chan_mapping)} kanal başarıyla '{OUTPUT_FILE}' dosyasına yazıldı.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
