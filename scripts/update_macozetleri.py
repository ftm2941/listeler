import os
import re
from urllib.parse import unquote, urljoin, urlparse

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

TEAM_LABELS = {
    "bjk": "Beşiktaş",
    "besiktas": "Beşiktaş",
    "gs": "Galatasaray",
    "galatasaray": "Galatasaray",
    "fb": "Fenerbahçe",
    "fenerbahce": "Fenerbahçe",
    "ts": "Trabzonspor",
    "trabzonspor": "Trabzonspor",
    "bas": "İstanbul Başakşehir",
    "istanbul-basaksehir": "İstanbul Başakşehir",
    "cor": "Arca Çorum FK",
    "corumspor": "Arca Çorum FK",
    "genc": "Gençlerbirliği",
    "genclerbirligi": "Gençlerbirliği",
    "ala": "Corendon Alanyaspor",
    "corendon-alanyaspor": "Corendon Alanyaspor",
    "rize": "Çaykur Rizespor",
    "rizee": "Çaykur Rizespor",
    "caykur-rizespor": "Çaykur Rizespor",
    "erz": "Erzurumspor FK",
    "bsb-erzurumspor": "Erzurumspor FK",
    "amed": "Amed Sportif Faaliyetler",
    "amedspor": "Amed Sportif Faaliyetler",
    "goz": "Göztepe",
    "goztepe": "Göztepe",
    "sam": "Samsunspor",
    "samsunspor": "Samsunspor",
    "kon": "Tümosan Konyaspor",
    "ittifak-holding-konyaspor": "Tümosan Konyaspor",
    "eyup": "Eyüpspor",
    "eyupspor": "Eyüpspor",
    "koca": "Kocaelispor",
    "kocaelispor": "Kocaelispor",
    "gazi": "Gaziantep FK",
    "ant": "Gaziantep FK",
    "gaziantep-fk": "Gaziantep FK",
    "kas": "Kasımpaşa",
    "ppasa": "Kasımpaşa",
    "kasimpasa": "Kasımpaşa",
}

STREAM_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]+?\.mp4(?:\?[^\s\"'<>\\]*)?",
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def slugify(text: str) -> str:
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    cleaned = text.translate(tr_map).lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned).strip("-")
    return cleaned or "mac"


def normalize_team(code: str) -> str:
    key = code.strip().lower()
    return TEAM_LABELS.get(key, key.replace("-", " ").title())


def parse_stream_metadata(stream_url: str) -> dict[str, str]:
    clean_url = unquote(stream_url).replace("\\/", "/")
    path_name = urlparse(clean_url).path.rsplit("/", 1)[-1]
    stem = re.sub(r"\.mp4$", "", path_name, flags=re.IGNORECASE)

    # Örnek: ligtvcomtr_tauri_ozt_20262027_12_bas_cor_23kas_ip
    match = re.search(
        r"(?:ozt_)?(?:\d{8}_)?(\d+)_([a-z0-9-]+)_([a-z0-9-]+)_(?:\d+[a-z]+_)?ip$",
        stem,
        re.IGNORECASE,
    )
    if match:
        week_num = match.group(1)
        home_team = normalize_team(match.group(2))
        away_team = normalize_team(match.group(3))
        tvg_name = f"{home_team} - {away_team}"
        title = f"{tvg_name} (Maç Özeti)"
        group_title = f"{week_num}. Hafta"
        tvg_id = f"superlig_{slugify(week_num)}_{slugify(home_team)}_{slugify(away_team)}"
        return {
            "tvg_id": tvg_id,
            "tvg_name": tvg_name,
            "group": group_title,
            "title": title,
            "stem": stem,
        }

    return {
        "tvg_id": f"superlig_{slugify(stem)}",
        "tvg_name": stem,
        "group": "Süper Lig Özetleri",
        "title": f"{stem} (Maç Özeti)",
        "stem": stem,
    }


def find_logo_for_stem(soup: BeautifulSoup, base_url: str, stem: str) -> str:
    tokens = [t.lower() for t in re.split(r"[^a-z0-9]+", stem) if len(t) >= 3]
    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src:
            continue
        low_src = src.lower()
        if any(tok in low_src for tok in tokens):
            return urljoin(base_url, src)
    return ""


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_existing_m3u8(path: str) -> list[dict[str, str]]:
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip()]

    items: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF:") and i + 1 < len(lines):
            extinf = lines[i]
            url = lines[i + 1]
            if is_valid_url(url) and not url.startswith("#"):
                tvg_id = re.search(r'tvg-id="([^"]*)"', extinf)
                tvg_name = re.search(r'tvg-name="([^"]*)"', extinf)
                tvg_logo = re.search(r'tvg-logo="([^"]*)"', extinf)
                group = re.search(r'group-title="([^"]*)"', extinf)
                title_part = extinf.split(",", 1)[1] if "," in extinf else ""

                items.append(
                    {
                        "tvg_id": tvg_id.group(1) if tvg_id else "",
                        "tvg_name": tvg_name.group(1) if tvg_name else title_part,
                        "tvg_logo": tvg_logo.group(1) if tvg_logo else "",
                        "group": group.group(1) if group else "Süper Lig Özetleri",
                        "title": title_part,
                        "url": url,
                    }
                )
                i += 2
                continue
        i += 1
    return items


def extract_new_entries(html: str, base_url: str) -> list[dict[str, str]]:
    unescaped_html = html.replace("\\/", "/").replace("\\u0026", "&")
    soup = BeautifulSoup(unescaped_html, "html.parser")

    found_urls: list[str] = []
    seen_urls: set[str] = set()

    for match in STREAM_URL_RE.findall(unescaped_html):
        cleaned_url = match.rstrip("\\\"',;)]}")
        if "akamaized.net" in cleaned_url.lower() or "hdnts=" in cleaned_url.lower():
            if is_valid_url(cleaned_url) and cleaned_url not in seen_urls:
                seen_urls.add(cleaned_url)
                found_urls.append(cleaned_url)

    results: list[dict[str, str]] = []
    for url in found_urls:
        meta = parse_stream_metadata(url)
        logo = find_logo_for_stem(soup, base_url, meta["stem"])
        results.append(
            {
                "tvg_id": meta["tvg_id"],
                "tvg_name": meta["tvg_name"],
                "tvg_logo": logo,
                "group": meta["group"],
                "title": meta["title"],
                "url": url,
            }
        )

    return results


def write_m3u8(items: list[dict[str, str]], output_path: str) -> None:
    lines = ["#EXTM3U"]
    for item in items:
        lines.append(
            f'#EXTINF:-1 tvg-id="{item["tvg_id"]}" '
            f'tvg-name="{item["tvg_name"]}" '
            f'tvg-logo="{item["tvg_logo"]}" '
            f'group-title="{item["group"]}",{item["title"]}'
        )
        lines.append(item["url"])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    existing = parse_existing_m3u8(OUTPUT_FILE)
    try:
        html = fetch_html(SOURCE_URL)
        fresh = extract_new_entries(html, SOURCE_URL)
    except Exception as exc:
        print(f"Kaynak çekilirken hata oluştu: {exc}")
        if existing:
            write_m3u8(existing, OUTPUT_FILE)
            print("Mevcut liste korundu.")
            return
        raise

    merged: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for item in fresh + existing:
        key = item["tvg_id"] or item["url"]
        if key and key not in seen_keys and is_valid_url(item["url"]):
            seen_keys.add(key)
            merged.append(item)

    if not merged:
        raise RuntimeError(
            "Sayfa içeriğinde .mp4 akış bağlantısı bulunamadı; "
            "bağlantılar dinamik API veya ayrı oynatıcı isteğiyle dönüyor olabilir."
        )

    write_m3u8(merged, OUTPUT_FILE)
    print(f"Toplam {len(merged)} kayıt {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
