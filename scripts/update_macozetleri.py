import os
import re
from urllib.parse import unquote, urlparse

from playwright.sync_api import Page, sync_playwright

SOURCE_URL = os.getenv(
    "SOURCE_URL", "https://beinsports.com.tr/mac-ozetleri-goller/super-lig"
)
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "macozetleri.m3u8")
MIN_DURATION_SEC = int(os.getenv("MIN_DURATION_SEC", "540"))  # 9 dk 00 sn
MAX_DURATION_SEC = int(os.getenv("MAX_DURATION_SEC", "660"))  # 11 dk 00 sn
REQUIRE_DURATION = os.getenv("REQUIRE_DURATION", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)

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

MEDIA_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]+?\.(?:mp4|m3u8)(?:\?[^\s\"'<>\\]*)?",
    re.IGNORECASE,
)

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
    return text.replace("İ", "i").replace("I", "ı").lower().strip()


def decode_escaped_text(raw_text: str) -> str:
    text = unquote(raw_text).replace("\\/", "/").replace("\\u0026", "&")
    text = re.sub(
        r"\\u([0-9a-fA-F]{4})",
        lambda m: chr(int(m.group(1), 16)),
        text,
    )
    return text


def parse_card_from_lines(lines: list[str], index_num: int) -> dict[str, str]:
    filtered: list[str] = []
    scores: list[str] = []

    for line in lines:
        cleaned = re.sub(r"\s+", " ", line).strip()
        if not cleaned:
            continue
        low = normalize_tr(cleaned)
        if low in NOISE_LINES:
            continue
        if re.search(r"\b20\d{2}\b", cleaned) and ":" in cleaned:
            continue
        if cleaned.isdigit():
            scores.append(cleaned)
            continue
        if not filtered or filtered[-1] != cleaned:
            filtered.append(cleaned)

    if len(filtered) >= 2:
        home_team = filtered[0]
        away_team = filtered[-1]
        if len(scores) >= 2:
            title = f"{home_team} {scores[0]} - {scores[1]} {away_team} (Maç Özeti)"
        else:
            title = f"{home_team} - {away_team} (Maç Özeti)"
        tvg_name = f"{home_team} - {away_team}"
    else:
        tvg_name = f"Süper Lig Maçı {index_num}"
        title = f"{tvg_name} (Maç Özeti)"

    return {
        "home_slug": slugify(filtered[0] if filtered else ""),
        "away_slug": slugify(filtered[-1] if len(filtered) >= 2 else ""),
        "group": "Süper Lig Özetleri",
        "tvg_id": f"superlig_{index_num}_{slugify(tvg_name)}",
        "tvg_name": tvg_name,
        "title": title,
    }


def read_player_duration_seconds(target_page: Page) -> int | None:
    """
    Ana sayfa ve tüm iframe'lerdeki <video> oynatıcıların gerçek süresini okur.
    """
    frames = [target_page.main_frame] + [
        f for f in target_page.frames if f != target_page.main_frame
    ]

    for frame in frames:
        try:
            dur = frame.evaluate(
                """async () => {
                    const videos = Array.from(document.querySelectorAll('video'));
                    for (const v of videos) {
                        if (Number.isFinite(v.duration) && v.duration > 0) {
                            return Math.round(v.duration);
                        }
                        await new Promise((resolve) => {
                            const timer = setTimeout(resolve, 1200);
                            v.addEventListener('loadedmetadata', () => {
                                clearTimeout(timer);
                                resolve();
                            }, { once: true });
                        });
                        if (Number.isFinite(v.duration) && v.duration > 0) {
                            return Math.round(v.duration);
                        }
                    }
                    return null;
                }"""
            )
            if isinstance(dur, (int, float)) and dur > 0:
                return int(round(dur))
        except Exception:
            continue

    return None


def is_target_duration(duration_sec: int | None) -> tuple[bool, str]:
    if duration_sec is None:
        if REQUIRE_DURATION:
            return False, "oynatıcı süresi okunamadı"
        return True, "oynatıcı süresi okunamadı (izinli)"

    if MIN_DURATION_SEC <= duration_sec <= MAX_DURATION_SEC:
        return True, f"oynatıcı süresi uygun ({duration_sec} sn)"
    return (
        False,
        f"oynatıcı süresi {duration_sec} sn ({MIN_DURATION_SEC}-{MAX_DURATION_SEC} sn dışında)",
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

    hints = build_match_hints(meta)
    matched_hints = sum(1 for h in hints if h in low)
    score += matched_hints * 30
    return score


def pick_best_media_url(
    candidates: list[str], meta: dict[str, str], used_urls: set[str]
) -> str:
    unique: list[str] = []
    for raw in candidates:
        u = raw.strip().rstrip("\\\"',;)]}")
        if is_valid_url(u) and u not in unique and u not in used_urls:
            unique.append(u)

    if not unique:
        return ""

    ranked = sorted(
        unique,
        key=lambda u: score_candidate_url(u, meta, used_urls),
        reverse=True,
    )
    return ranked[0]


def collect_media_from_text(text: str) -> list[str]:
    decoded = decode_escaped_text(text)
    return MEDIA_URL_RE.findall(decoded)


def dismiss_consent_popups(page: Page) -> None:
    patterns = [
        r"tümünü kabul et",
        r"kabul et",
        r"onayla",
        r"accept all",
        r"accept",
        r"tamam",
    ]
    for pat in patterns:
        try:
            btn = page.get_by_role("button", name=re.compile(pat, re.IGNORECASE)).first
            if btn.is_visible(timeout=400):
                btn.click(timeout=1000)
                page.wait_for_timeout(300)
                return
        except Exception:
            pass


def scroll_page_to_load_all(page: Page, steps: int = 4) -> None:
    for _ in range(steps):
        page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.9))")
        page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(400)


def collect_target_elements_js() -> str:
    return """() => {
        const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim().toLowerCase();
        const nodes = Array.from(document.querySelectorAll('a, button, [role="button"], div, span'));
        const summaryMatches = nodes.filter(el => {
            const txt = norm(el.innerText || el.textContent);
            const aria = norm(el.getAttribute('aria-label'));
            const title = norm(el.getAttribute('title'));
            const combined = `${txt} ${aria} ${title}`;
            const hit = combined.includes('özeti izle') || combined.includes('ozeti izle');
            if (!hit) return false;
            const childHits = Array.from(el.children).filter(ch => {
                const ctxt = norm((ch.innerText || ch.textContent) + ' ' + (ch.getAttribute('aria-label') || ''));
                return ctxt.includes('özeti izle') || ctxt.includes('ozeti izle');
            }).length;
            return childHits === 0;
        });
        if (summaryMatches.length > 0) return summaryMatches;

        return Array.from(document.querySelectorAll('a[href*="/ozet/"]'));
    }"""


def count_target_matches(page: Page) -> int:
    return page.evaluate(f"() => {{ const fn = {collect_target_elements_js()}; return fn().length; }}")


def get_card_lines_for_index(page: Page, idx: int) -> list[str]:
    return page.evaluate(
        f"""(index) => {{
            const fn = {collect_target_elements_js()};
            const matches = fn();
            const target = matches[index];
            if (!target) return [];

            let cur = target;
            for (let i = 0; i < 8; i++) {{
                if (!cur.parentElement) break;
                cur = cur.parentElement;
                const lines = (cur.innerText || cur.textContent || '')
                    .split('\\n')
                    .map(s => s.replace(/\\s+/g, ' ').trim())
                    .filter(Boolean);
                if (lines.length >= 3 && lines.length <= 35) {{
                    return lines;
                }}
            }}
            return [];
        }}""",
        idx,
    )


def click_target_by_index(page: Page, idx: int) -> bool:
    return page.evaluate(
        f"""(index) => {{
            const fn = {collect_target_elements_js()};
            const matches = fn();
            const target = matches[index];
            if (!target) return false;
            target.scrollIntoView({{ behavior: 'instant', block: 'center' }});
            target.click();
            return true;
        }}""",
        idx,
    )


def scrape_with_playwright(source_url: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    used_urls: set[str] = set()
    seen_ids: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
            viewport={"width": 1366, "height": 900},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = context.new_page()
        page.set_default_timeout(15000)

        print("Ana sayfa açılıyor...")
        page.goto(source_url, wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(1500)
        dismiss_consent_popups(page)
        scroll_page_to_load_all(page)

        total = count_target_matches(page)
        print(f"Sayfada {total} adet hedef ('ÖZETİ İZLE' / özet) elemanı bulundu.")

        for idx in range(total):
            card_lines = get_card_lines_for_index(page, idx)
            meta = parse_card_from_lines(card_lines, idx + 1)

            if meta["tvg_id"] in seen_ids:
                continue

            captured_urls: list[str] = []

            def on_request(req):
                u = req.url
                if re.search(r"\.(?:mp4|m3u8)(?:\?|$)", u, re.IGNORECASE):
                    captured_urls.append(u)

            def on_response(res):
                u = res.url
                if re.search(r"\.(?:mp4|m3u8)(?:\?|$)", u, re.IGNORECASE):
                    captured_urls.append(u)
                ct = (res.headers.get("content-type") or "").lower()
                if any(k in ct for k in ("json", "javascript", "text", "xml", "mpegurl")):
                    try:
                        body = res.text()
                        if "akamaized.net" in body or ".mp4" in body or ".m3u8" in body:
                            captured_urls.extend(collect_media_from_text(body))
                    except Exception:
                        pass

            context.on("request", on_request)
            context.on("response", on_response)

            active_page = page
            popup_page = None
            start_url = page.url

            try:
                try:
                    with context.expect_page(timeout=2000) as popup_info:
                        clicked = click_target_by_index(page, idx)
                        if not clicked:
                            raise RuntimeError("Eleman tıklanamadı")
                    popup_page = popup_info.value
                    popup_page.wait_for_load_state("domcontentloaded", timeout=12000)
                    popup_page.wait_for_timeout(1500)
                    active_page = popup_page
                except Exception:
                    page.wait_for_timeout(1500)

                try:
                    dom_html = active_page.content()
                    captured_urls.extend(collect_media_from_text(dom_html))
                except Exception:
                    pass

                duration_sec = read_player_duration_seconds(active_page)
                duration_ok, duration_reason = is_target_duration(duration_sec)
                if not duration_ok:
                    print(f"[ATLA - SÜRE] {meta['title']} -> {duration_reason}")
                    continue

                media_url = pick_best_media_url(captured_urls, meta, used_urls)
                if not media_url:
                    print(f"[UYARI] Tıklama sonrası medya URL bulunamadı: {meta['title']}")
                    continue

                used_urls.add(media_url)
                seen_ids.add(meta["tvg_id"])
                print(f"[OK] {meta['title']} ({duration_reason}) -> {media_url}")

                entries.append(
                    {
                        "tvg_id": meta["tvg_id"],
                        "tvg_name": meta["tvg_name"],
                        "tvg_logo": "",
                        "group": meta["group"],
                        "title": meta["title"],
                        "url": media_url,
                    }
                )

            except Exception as exc:
                print(f"[HATA] {meta['title']} için tıklama/yakalama hatası: {exc}")
            finally:
                context.remove_listener("request", on_request)
                context.remove_listener("response", on_response)
                if popup_page is not None and not popup_page.is_closed():
                    try:
                        popup_page.close()
                    except Exception:
                        pass
                if page.url != start_url:
                    try:
                        page.goto(start_url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(1000)
                    except Exception:
                        pass

        browser.close()

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
    fresh_entries = scrape_with_playwright(SOURCE_URL)
    if not fresh_entries:
        raise RuntimeError(
            "10 dakikalık aralığa uyan yeni video akışı yakalanamadı."
        )

    write_m3u8(fresh_entries, OUTPUT_FILE)
    print(f"Yalnızca {len(fresh_entries)} yeni kayıt {OUTPUT_FILE} dosyasına yazıldı.")


if __name__ == "__main__":
    main()
