import codecs
import os
import re
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

SOURCE_URL = os.getenv(
    "SOURCE_URL", "https://beinsports.com.tr/mac-ozetleri-goller/super-lig"
)
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "macozetleri.m3u8")
MIN_DURATION_SEC = int(os.getenv("MIN_DURATION_SEC", "400"))  # ~6 dk 40 sn
MAX_DURATION_SEC = int(os.getenv("MAX_DURATION_SEC", "540"))  # 9 dk 00 sn
REQUIRE_DURATION = os.getenv("REQUIRE_DURATION", "false").strip().lower() in (
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

DURATION_FIELD_RE = re.compile(
    r"\"?(?:duration|durationSec|durationSeconds|videoDuration|sure)\"?\s*[:=]\s*\"?(\d{2,4})\"?",
    re.IGNORECASE,
)

MMSS_RE = re.compile(r"\b(0?[6789]):([0-5]\d)\b")

NOISE_LINES = {
    "özeti izle",
    "ozeti izle",
    "paylaş",
    "paylas",
    "share-button",
    "-",
}


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


def normalize_tr(text: str) -> str:
    return (
        text.replace("İ", "i")
        .replace("I", "ı")
        .lower()
        .strip()
    )


def normalize_team(slug: str) -> str:
    key = slug.strip().lower()
    if key in TEAM_LABELS:
        return TEAM_LABELS[key]
    return " ".join(part.capitalize() for part in key.split("-") if part)


def parse_card_details(anchor: Tag) -> dict[str, str]:
    """
    'ÖZETİ İZLE' linkini saran maç kartı bloğundan takım isimlerini ve skoru ayıklar.
    """
    container: Tag | None = anchor
    card_lines: list[str] = []

    for _ in range(6):
        if container is None or container.parent is None:
            break
        container = container.parent
        raw_lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in container.get_text("\n").splitlines()
        ]
        lines = [line for line in raw_lines if line]
        # Kart içinde genellikle skor rakamları ve 2 takım adı bulunur
        if 4 <= len(lines) <= 25 and any(
            "özeti izle" in normalize_tr(l) for l in lines
        ):
            card_lines = lines
            break

    if not card_lines:
        return {}

    filtered: list[str] = []
    scores: list[str] = []
    for line in card_lines:
        low = normalize_tr(line)
        if low in NOISE_LINES:
            continue
        if re.search(r"\b20\d{2}\b", line) and ":" in line:
            # Tarih satırı: "23 Kasım 2026, Pazartesi, 20:00"
            continue
        if line.isdigit():
            scores.append(line)
            continue
        if not filtered or filtered[-1] != line:
            filtered.append(line)

    if len(filtered) >= 2:
        home_team = filtered[0]
        away_team = filtered[-1]
        if len(scores) >= 2:
            title = f"{home_team} {scores[0]} - {scores[1]} {away_team} (Maç Özeti)"
        else:
            title = f"{home_team} - {away_team} (Maç Özeti)"
        return {
            "home_team": home_team,
            "away_team": away_team,
            "tvg_name": f"{home_team} - {away_team}",
            "title": title,
        }

    return {}


def parse_ozet_page_url(page_url: str, card_info: dict[str, str]) -> dict[str, str]:
    path = urlparse(page_url).path
    match = OZET_PAGE_RE.search(path)

    season = ""
    week_num = ""
    home_slug = ""
    away_slug = ""
    url_tvg_name = ""
    url_title = ""

    if match:
        season, week_num, match_slug = match.groups()
        clean_slug = re.sub(r"-mac-ozeti$", "", match_slug, flags=re.IGNORECASE)
        score_match = re.match(r"^(.+?)-(\d+)-(\d+)-(.+)$", clean_slug)
        if score_match:
            home_slug, home_score, away_score, away_slug = score_match.groups()
            home_team = normalize_team(home_slug)
            away_team = normalize_team(away_slug)
            url_tvg_name = f"{home_team} - {away_team}"
            url_title = f"{home_team} {home_score} - {away_score} {away_team} (Maç Özeti)"
        else:
            url_tvg_name = normalize_team(clean_slug)
            url_title = f"{url_tvg_name} (Maç Özeti)"

    tvg_name = card_info.get("tvg_name") or url_tvg_name or "Süper Lig Özeti"
    title = card_info.get("title") or url_title or f"{tvg_name} (Maç Özeti)"
    group = f"{week_num}. Hafta" if week_num else "Süper Lig Özetleri"
    id_prefix = f"superlig_{week_num}" if week_num else "superlig"

    if not home_slug and card_info.get("home_team"):
        home_slug = slugify(card_info["home_team"])
    if not away_slug and card_info.get("away_team"):
        away_slug = slugify(card_info["away_team"])

    return {
        "season": season,
        "week_num": week_num,
        "home_slug": slugify(home_slug),
        "away_slug": slugify(away_slug),
        "group": group,
        "tvg_id": f"{id_prefix}_{slugify(tvg_name)}",
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


def extract_duration_seconds(decoded_html: str) -> int | None:
    for m in DURATION_FIELD_RE.finditer(decoded_html):
        val = int(m.group(1))
        if 120 <= val <= 3600:
            return val

    for m in MMSS_RE.finditer(decoded_html):
        mins = int(m.group(1))
        secs = int(m.group(2))
        total = mins * 60 + secs
        if 120 <= total <= 3600:
            return total

    return None


def is_target_duration(duration_sec: int | None) -> tuple[bool, str]:
    if duration_sec is None:
        if REQUIRE_DURATION:
            return False, "süre bilgisi yok"
        return True, "süre bilgisi yok (izinli)"

    if MIN_DURATION_SEC <= duration_sec <= MAX_DURATION_SEC:
        return True, f"uygun süre ({duration_sec} sn)"
    return (
        False,
        f"süre {duration_sec} sn ({MIN_DURATION_SEC}-{MAX_DURATION_SEC} sn dışında)",
    )


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
    decoded_html: str, meta: dict[str, str], used_urls: set[str]
) -> str:
    candidates = MEDIA_URL_RE.findall(decoded_html)

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
    week_prefix = f"{meta['week_num']}_" if meta.get("week_num") else ""
    hints = build_match_hints(meta)

    for img in soup.find_all("img"):
        src = (img.get("data-src") or img.get("src") or "").strip()
        if not src:
            continue
        full_src = urljoin(base_url, src)
        low_src = full_src.lower()
        if "match_posters" in low_src and (
            (week_prefix and week_prefix in low_src)
            or any(h in low_src for h in hints)
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


def collect_ozeti_izle_links(
    main_html: str, base_url: str
) -> list[tuple[str, dict[str, str]]]:
    """
    Sadece metni veya etiketi 'ÖZETİ İZLE' olan buton/linkleri toplar.
    """
    decoded = decode_escaped_text(main_html)
    soup = BeautifulSoup(decoded, "html.parser")
    found: list[tuple[str, dict[str, str]]] = []
    seen_pages: set[str] = set()

    for a in soup.find_all("a", href=True):
        link_text = normalize_tr(re.sub(r"\s+", " ", a.get_text(" ", strip=True)))
        aria_label = normalize_tr(a.get("aria-label", ""))
        title_attr = normalize_tr(a.get("title", ""))

        if (
            "özeti izle" not in link_text
            and "ozeti izle" not in link_text
            and "özeti izle" not in aria_label
            and "özeti izle" not in title_attr
        ):
            continue

        href = a["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen_pages:
            continue

        seen_pages.add(full_url)
        card_info = parse_card_details(a)
        meta = parse_ozet_page_url(full_url, card_info)
        found.append((full_url, meta))

    return found


def extract_fresh_entries(main_html: str, base_url: str) -> list[dict[str, str]]:
    main_soup = BeautifulSoup(decode_escaped_text(main_html), "html.parser")
    ozet_pages = collect_ozeti_izle_links(main_html, base_url)
    print(f"Ana sayfada {len(ozet_pages)} adet 'ÖZETİ İZLE' bağlantısı bulundu.")

    entries: list[dict[str, str]] = []
    used_urls: set[str] = set()
    seen_ids: set[str] = set()

    for page_url, meta in ozet_pages:
        if meta["tvg_id"] in seen_ids:
            continue

        try:
            page_html = fetch_html(page_url)
        except Exception as exc:
            print(f"[HATA] Özet sayfası alınamadı ({page_url}): {exc}")
            continue

        decoded_page = decode_escaped_text(page_html)
        duration_sec = extract_duration_seconds(decoded_page)
        duration_ok, duration_reason = is_target_duration(duration_sec)
        if not duration_ok:
            print(f"[ATLA - SÜRE] {meta['title']} -> {duration_reason}")
            continue

        media_url = extract_media_url(decoded_page, meta, used_urls)
        if not media_url:
            print(f"[UYARI] Medya URL bulunamadı: {meta['title']} -> {page_url}")
            continue

        used_urls.add(media_url)
        seen_ids.add(meta["tvg_id"])
        page_soup = BeautifulSoup(decoded_page, "html.parser")
        logo = extract_logo(page_soup, page_url, meta) or extract_logo(
            main_soup, base_url, meta
        )

        print(f"[OK] {meta['title']} ({duration_reason}) -> {media_url}")
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
    main_html = fetch_html(SOURCE_URL)
    fresh_entries = extract_fresh_entries(main_html, SOURCE_URL)

    if not fresh_entries:
        raise RuntimeError(
            "'ÖZETİ İZLE' bağlantılarından 7-8 dakikalık yeni video bulunamadı."
        )

    write_m3u8(fresh_entries, OUTPUT_FILE)
    print(f"Sadece {len(fresh_entries)} yeni özet {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
