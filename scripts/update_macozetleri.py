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

OZET_PAGE_RE = re.compile(
    r"/lig/super-lig/ozet/(\d{4}-\d{4})/(\d+)/([^/?#]+)",
    re.IGNORECASE,
)

MEDIA_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]+?\.(?:mp4|m3u8)(?:\?[^\s\"'<>\\]*)?",
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


def normalize_team(slug: str) -> str:
    key = slug.strip().lower()
    if key in TEAM_LABELS:
        return TEAM_LABELS[key]
    return " ".join(part.capitalize() for part in key.split("-") if part)


def parse_ozet_page_url(page_url: str) -> dict[str, str] | None:
    path = urlparse(page_url).path
    match = OZET_PAGE_RE.search(path)
    if not match:
        return None

    season, week_num, match_slug = match.groups()
    clean_slug = re.sub(r"-mac-ozeti$", "", match_slug, flags=re.IGNORECASE)

    # Örnek: istanbul-basaksehir-4-2-corumspor
    score_match = re.match(r"^(.+?)-(\d+)-(\d+)-(.+)$", clean_slug)
    if score_match:
        home_raw, home_score, away_score, away_raw = score_match.groups()
        home_team = normalize_team(home_raw)
        away_team = normalize_team(away_raw)
        tvg_name = f"{home_team} - {away_team}"
        title = f"{home_team} {home_score} - {away_score} {away_team} (Maç Özeti)"
    else:
        parts = clean_slug.split("-vs-")
        if len(parts) == 2:
            home_team = normalize_team(parts[0])
            away_team = normalize_team(parts[1])
            tvg_name = f"{home_team} - {away_team}"
            title = f"{tvg_name} (Maç Özeti)"
        else:
            tvg_name = normalize_team(clean_slug)
            title = f"{tvg_name} (Maç Özeti)"

    tvg_id = f"superlig_{week_num}_{slugify(tvg_name)}"
    return {
        "season": season,
        "week_num": week_num,
        "group": f"{week_num}. Hafta",
        "tvg_id": tvg_id,
        "tvg_name": tvg_name,
        "title": title,
    }


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_media_url(page_html: str) -> str:
    unescaped = unquote(page_html).replace("\\/", "/").replace("\\u0026", "&")
    candidates = MEDIA_URL_RE.findall(unescaped)

    cleaned_urls: list[str] = []
    for raw in candidates:
        u = raw.rstrip("\\\"',;)]}")
        if is_valid_url(u) and u not in cleaned_urls:
            cleaned_urls.append(u)

    # Önce Akamai / hdnts içeren mp4 veya m3u8 akışlarını tercih et
    for u in cleaned_urls:
        low = u.lower()
        if "akamaized.net" in low or "hdnts=" in low:
            return u

    for u in cleaned_urls:
        low = u.lower()
        if low.endswith(".mp4") or ".mp4?" in low or ".m3u8" in low:
            return u

    return ""


def extract_logo(soup: BeautifulSoup, base_url: str, meta: dict[str, str]) -> str:
    week_prefix = f"{meta['week_num']}_"
    team_slug = slugify(meta["tvg_name"])

    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src:
            continue
        full_src = urljoin(base_url, src)
        low_src = full_src.lower()
        if "match_posters" in low_src and (
            week_prefix in low_src or team_slug in low_src
        ):
            return full_src

    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src:
            continue
        full_src = urljoin(base_url, src)
        low_src = full_src.lower()
        if any(ext in low_src for ext in (".jpg", ".jpeg", ".png", ".webp")):
            if "logo" not in low_src and "icon" not in low_src:
                return full_src

    return ""


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


def collect_ozet_links(main_html: str, base_url: str) -> list[tuple[str, dict[str, str]]]:
    soup = BeautifulSoup(main_html, "html.parser")
    found: list[tuple[str, dict[str, str]]] = []
    seen_pages: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_url, href)
        if "/lig/super-lig/ozet/" not in full_url:
            continue
        if full_url in seen_pages:
            continue

        meta = parse_ozet_page_url(full_url)
        if meta:
            seen_pages.add(full_url)
            found.append((full_url, meta))

    return found


def extract_new_entries(main_html: str, base_url: str) -> list[dict[str, str]]:
    main_soup = BeautifulSoup(main_html, "html.parser")
    ozet_pages = collect_ozet_links(main_html, base_url)
    entries: list[dict[str, str]] = []

    for page_url, meta in ozet_pages:
        try:
            page_html = fetch_html(page_url)
        except Exception as exc:
            print(f"Özet sayfası alınamadı ({page_url}): {exc}")
            continue

        media_url = extract_media_url(page_html)
        if not media_url:
            print(f"Medya bağlantısı bulunamadı ({page_url})")
            continue

        page_soup = BeautifulSoup(page_html, "html.parser")
        logo = extract_logo(page_soup, page_url, meta) or extract_logo(
            main_soup, base_url, meta
        )

        entries.append(
            {
                "tvg_id": meta["tvg_id"],
                "tvg_name": meta["tvg_name"],
                "tvg_logo": logo,
                "group": meta["group"],
                "title": meta["title"],
                "url": media_url,
            }
        )

    return entries


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
        main_html = fetch_html(SOURCE_URL)
        fresh = extract_new_entries(main_html, SOURCE_URL)
    except Exception as exc:
        print(f"Kaynak çekilirken hata oluştu: {exc}")
        if existing:
            write_m3u8(existing, OUTPUT_FILE)
            print("Mevcut liste korundu.")
            return
        raise

    merged: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for item in fresh + existing:
        item_key = item["tvg_id"] or item["url"]
        if item_key and item_key not in seen_ids and is_valid_url(item["url"]):
            seen_ids.add(item_key)
            merged.append(item)

    if not merged:
        raise RuntimeError(
            "Özet sayfasından medya URL'si çekilemedi; "
            "video oynatıcı verisi JS/API ile sonradan yükleniyor olabilir."
        )

    write_m3u8(merged, OUTPUT_FILE)
    print(f"Toplam {len(merged)} kayıt {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
