import os
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SOURCE_URL = os.getenv(
    "SOURCE_URL", "https://beinsports.com.tr/mac-ozetleri-goller/super-lig"
)
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "macozetleri.m3u8")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://beinsports.com.tr/",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_entries(html: str, base_url: str) -> list[tuple[str, str]]:
    """
    (baslik, akis_veya_sayfa_url) ikililerinin listesini döndürür.
    Sayfa yapısına göre seçicileri ve URL filtrelerini güncellemen gerekir.
    """
    soup = BeautifulSoup(html, "html.parser")
    entries: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        full_url = urljoin(base_url, href)

        # Örnek filtre: özet/gol içeren bağlantıları ayıkla
        if any(k in full_url.lower() for k in ("ozet", "gol", ".m3u8")):
            title = re.sub(r"\s+", " ", link.get_text(" ", strip=True))
            if not title:
                title = link.get("title", "").strip() or "Süper Lig Özeti"

            if full_url not in seen_urls:
                seen_urls.add(full_url)
                entries.append((title, full_url))

    return entries


def write_m3u8(entries: list[tuple[str, str]], output_path: str) -> None:
    lines = ["#EXTM3U"]
    for title, url in entries:
        clean_title = title.replace("\n", " ").replace(",", " -")
        lines.append(f'#EXTINF:-1 group-title="Süper Lig Özetleri",{clean_title}')
        lines.append(url)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def main() -> None:
    html = fetch_html(SOURCE_URL)
    entries = extract_entries(html, SOURCE_URL)
    if not entries:
        raise RuntimeError("Hiç kayıt bulunamadı; sayfa yapısı veya bot koruması kontrol edilmeli.")
    write_m3u8(entries, OUTPUT_FILE)
    print(f"{len(entries)} kayıt {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
