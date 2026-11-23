import codecs
import os
import re
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCE_URL = os.getenv(
    "SOURCE_URL", "https://beinsports.com.tr/mac-ozetleri-goller/super-lig"
)
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "macozetleri.m3u8")
REFRESH_EXISTING = os.getenv("REFRESH_EXISTING", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

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

SHORT_CODES = {
    "besiktas": ["bjk"],
    "galatasaray": ["gs"],
    "fenerbahce": ["fb"],
    "trabzonspor": ["ts"],
    "istanbul-basaksehir": ["bas"],
    "corumspor": ["cor"],
    "genclerbirligi": ["genc"],
    "corendon-alanyaspor": ["ala"],
    "caykur-rizespor": ["rize", "rizee"],
    "bsb-erzurumspor": ["erz"],
    "amedspor": ["amed"],
    "goztepe": ["goz"],
    "samsunspor": ["sam"],
    "ittifak-holding-konyaspor": ["kon"],
    "eyupspor": ["eyup"],
    "kocaelispor": ["koca"],
    "gaziantep-fk": ["gazi", "ant"],
    "kasimpasa": ["kas", "ppasa"],
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

    home_slug = ""
    away_slug = ""
    score_match = re.match(r"^(.+?)-(\d+)-(\d+)-(.+)$", clean_slug)
    if score_match:
        home_slug, home_score, away_score, away_slug = score_match.groups()
        home_team = normalize_team(home_slug)
        away_team = normalize_team(away_slug)
        tvg_name = f"{home_team} - {away_team}"
        title = f"{home_team} {home_score} - {away_score} {away_team} (Maç Özeti)"
    else:
        parts = clean_slug.split("-vs-")
        if len(parts) == 2:
            home_slug, away_slug = parts[0], parts[1]
            home_team = normalize_team(home_slug)
            away_team = normalize_team(away_slug)
            tvg_name = f"{home_team} - {away_team}"
            title = f"{tvg_name} (Maç Özeti)"
        else:
            tvg_name = normalize_team(clean_slug)
            title = f"{tvg_name} (Maç Özeti)"

    tvg_id = f"superlig_{week_num}_{slugify(tvg_name)}"
    return {
        "season": season,
        "week_num": week_num,
        "home_slug": slugify(home_slug),
        "away_slug": slugify(away_slug),
        "group": f"{week_num}. Hafta",
        "tvg_id": tvg_id,
        "tvg_name": tvg_name,
        "title": title,
    }


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def decode_escaped_text(raw_text: str) -> str:
    text = unquote(raw_text).replace("\\/", "/").replace("\\u0026", "&")
    if "\\u00" in text or "\\x" in text:
        try:
            text = codecs.decode(text, "unicode_escape")
        except Exception:
            pass
    return text


def build_match_hints(meta: dict[str, str]) -> list[str]:
    hints: list[str] = []
    for team_slug in (meta.get("home_slug", ""), meta.get("away_slug", "")):
        if not team_slug:
            continue
        hints.append(team_slug)
        hints.extend(SHORT_CODES.get(team_slug, []))
        first_part = team_slug.split("-", 1)[0]
        if len(first_part) >= 3:
            hints.append(first_part)
    return [h.lower() for h in hints if h]


def score_candidate_url(url: str, meta: dict[str, str], used_urls: set[str]) -> int:
    low = url.lower()
    if url in used_urls:
        return -999

    score = 0
    if "akamaized.net" in low:
        score += 35
    if "hdnts=" in low:
        score += 25
    if ".mp4" in low:
        score += 15
    elif ".m3u8" in low:
        score += 10

    week_num = meta.get("week_num", "")
    if week_num and re.search(rf"(?:^|[_/-]){re.escape(week_num)}(?:[_/-]|$)", low):
        score += 15

    hints = build_match_hints(meta)
    matched_hints = sum(1 for h in hints if h in low)
    score += matched_hints * 30
    return score


def extract_media_url(
    page_html: str, meta: dict[str, str], used_urls: set[str]
) -> str:
    decoded = decode_escaped_text(page_html)
    candidates = MEDIA_URL_RE.findall(decoded)

    unique_candidates: list[str] = []
    for raw in candidates:
        u = raw.rstrip("\\\"',;)]}")
        if is_valid_url(u) and u not in unique_candidates:
            unique_candidates.append(u)

    if not unique_candidates:
        return ""

    ranked = sorted(
        unique_candidates,
        key=lambda u: score_candidate_url(u, meta, used_urls),
        reverse=True,
    )
    best = ranked[0]
    if best in used_urls:
        return ""
    return best


def extract_logo(soup: BeautifulSoup, base_url: str, meta: dict[str, str]) -> str:
    week_prefix = f"{meta['week_num']}_"
    hints = build_match_hints(meta)

    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src:
            continue
        full_src = urljoin(base_url, src)
        low_src = full_src.lower()
        if "match_posters" in low_src and (
            week_prefix in low_src or any(h in low_src for h in hints)
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
            if not url.startswith("#"):
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
    decoded = decode_escaped_text(main_html)
    soup = BeautifulSoup(decoded, "html.parser")
    found: list[tuple[str, dict[str, str]]] = []
    seen_pages: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(base_url, href)
        if "/lig/super-lig/ozet/" not in full_url or full_url in seen_pages:
            continue

        meta = parse_ozet_page_url(full_url)
        if meta:
            seen_pages.add(full_url)
            found.append((full_url, meta))

    if not found:
        for match in re.finditer(
            r"https?://[^\s\"'<>\\]+/lig/super-lig/ozet/[^\s\"'<>\\]+|/lig/super-lig/ozet/[^\s\"'<>\\]+",
            decoded,
            re.IGNORECASE,
        ):
            full_url = urljoin(base_url, match.group(0).rstrip("\\\"',;)]}"))
            if full_url in seen_pages:
                continue
            meta = parse_ozet_page_url(full_url)
            if meta:
                seen_pages.add(full_url)
                found.append((full_url, meta))

    return found


def needs_fetch(
    meta: dict[str, str], existing_by_id: dict[str, dict[str, str]]
) -> tuple[bool, str]:
    tvg_id = meta["tvg_id"]
    existing_item = existing_by_id.get(tvg_id)
    if not existing_item:
        return True, "yeni maç"

    current_url = existing_item.get("url", "")
    if not is_valid_url(current_url):
        return True, "geçersiz veya eksik URL"

    if REFRESH_EXISTING:
        return True, "REFRESH_EXISTING aktif"

    return False, "zaten güncel"


def extract_delta_entries(
    main_html: str, base_url: str, existing_by_id: dict[str, dict[str, str]]
) -> list[dict[str, str]]:
    main_soup = BeautifulSoup(decode_escaped_text(main_html), "html.parser")
    ozet_pages = collect_ozet_links(main_html, base_url)
    print(f"Ana sayfada {len(ozet_pages)} adet /lig/super-lig/ozet/ linki bulundu.")

    used_urls: set[str] = {
        item["url"]
        for item in existing_by_id.values()
        if is_valid_url(item.get("url", "")) and not REFRESH_EXISTING
    }

    updated_or_new: list[dict[str, str]] = []
    skipped_count = 0

    for page_url, meta in ozet_pages:
        should_fetch, reason = needs_fetch(meta, existing_by_id)
        if not should_fetch:
            skipped_count += 1
            print(f"[ATLA] {meta['title']} ({reason})")
            continue

        try:
            page_html = fetch_html(page_url)
        except Exception as exc:
            print(f"[HATA] Özet sayfası alınamadı ({page_url}): {exc}")
            continue

        media_url = extract_media_url(page_html, meta, used_urls)
        if not media_url:
            print(f"[UYARI] Medya URL bulunamadı ({reason}): {meta['title']} -> {page_url}")
            continue

        used_urls.add(media_url)
        page_soup = BeautifulSoup(decode_escaped_text(page_html), "html.parser")
        logo = extract_logo(page_soup, page_url, meta) or extract_logo(
            main_soup, base_url, meta
        )
        if not logo and meta["tvg_id"] in existing_by_id:
            logo = existing_by_id[meta["tvg_id"]].get("tvg_logo", "")

        print(f"[GÜNCEL/YENİ] {meta['title']} ({reason}) -> {media_url}")
        updated_or_new.append(
            {
                "tvg_id": meta["tvg_id"],
                "tvg_name": meta["tvg_name"],
                "tvg_logo": logo,
                "group": meta["group"],
                "title": meta["title"],
                "url": media_url,
            }
        )

    print(
        f"Özet taraması tamamlandı: {len(updated_or_new)} yeni/güncel maç, "
        f"{skipped_count} mevcut maç atlandı."
    )
    return updated_or_new


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
    existing_by_id = {
        item["tvg_id"]: item for item in existing if item.get("tvg_id")
    }

    try:
        main_html = fetch_html(SOURCE_URL)
        delta = extract_delta_entries(main_html, SOURCE_URL, existing_by_id)
    except Exception as exc:
        print(f"Kaynak çekilirken hata oluştu: {exc}")
        if existing:
            write_m3u8(existing, OUTPUT_FILE)
            print("Mevcut liste korundu.")
            return
        raise

    if not delta and existing:
        print("Yeni veya yenilenecek maç bulunamadı; mevcut liste korunuyor.")
        write_m3u8(existing, OUTPUT_FILE)
        return

    merged_by_id: dict[str, dict[str, str]] = {}
    for item in delta:
        key = item["tvg_id"] or item["url"]
        if key and is_valid_url(item["url"]):
            merged_by_id[key] = item

    for old_item in existing:
        key = old_item["tvg_id"] or old_item["url"]
        if key and key not in merged_by_id and is_valid_url(old_item["url"]):
            merged_by_id[key] = old_item

    merged = list(merged_by_id.values())
    if not merged:
        raise RuntimeError("Listeye yazılacak geçerli kayıt bulunamadı.")

    write_m3u8(merged, OUTPUT_FILE)
    print(f"Toplam {len(merged)} kayıt {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
