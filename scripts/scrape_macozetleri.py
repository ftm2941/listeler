#!/usr/bin/env python3
"""
BeIN Sports Super Lig mac ozetlerini cekip macozetleri.m3u8 playlist'ini gunceller.

Kullanim:
    python scrape_macozetleri.py
    OUTPUT=/path/to/macozetleri.m3u8 python scrape_macozetleri.py
"""
import html
import json
import os
import re
import sys
import time
import urllib.request

LIST_URL = "https://beinsports.com.tr/mac-ozetleri-goller/super-lig"
BASE = "https://beinsports.com.tr"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
GROUP = "Süper Lig Özetleri"
PLACEHOLDER_MARKERS = ("ligtvcomtr_tauri_haber_26_11_bas11_23kas_ip",)


def fetch(url):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read().decode("utf-8", errors="replace")
                return data, r.geturl()
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def get_summary_paths():
    text, _ = fetch(LIST_URL)
    paths = set(re.findall(r"/lig/super-lig/ozet/[A-Za-z0-9/_-]+", text))
    paths |= set(re.findall(r"/mac-ozetleri-goller/super-lig/ozet/[A-Za-z0-9/_-]+", text))
    return sorted(p.rstrip("/") for p in paths)


def parse_match(path):
    url = BASE + path
    text, _ = fetch(url)

    content_url = None
    thumb = ""
    name = None
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
                         text, re.S):
        try:
            obj = json.loads(m.group(1))
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("@type") == "VideoObject":
            content_url = html.unescape(obj.get("contentUrl") or "")
            thumbs = obj.get("thumbnailUrl") or []
            if isinstance(thumbs, list) and thumbs:
                thumb = thumbs[0]
            elif isinstance(thumbs, str):
                thumb = thumbs
            name = obj.get("name")

    if not name:
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S)
        if m:
            name = m.group(1).split("|")[0].strip()

    if name:
        name = re.sub(r"\s*Maç Özeti.*", "", name, flags=re.I).strip()
        name = re.sub(r"\s+", " ", name)

    # resolve redirect -> direct mp4
    video_url = content_url
    if content_url:
        try:
            req = urllib.request.Request(content_url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                video_url = r.geturl()
        except Exception as e:
            print("WARN resolve redirect failed:", path, e, file=sys.stderr)

    slug = path.rstrip("/").split("/")[-1]
    tvg_id = "superlig_" + slug
    display = (name + " (Maç Özeti)") if name else (slug + " (Maç Özeti)")
    return slug, tvg_id, name or slug, display, video_url or "", thumb or ""


def is_placeholder(entry):
    url = entry.get("url", "")
    name = entry.get("tvg_name", "")
    if any(m in url for m in PLACEHOLDER_MARKERS):
        return True
    if name.startswith("Süper Lig Maçı ") and "super-lig-maci-" in entry.get("tvg_id", ""):
        return True
    return False


def parse_existing(lines):
    entries = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip("\n")
        if line.lstrip().startswith("#EXTINF"):
            tvg_id = (re.search(r'tvg-id="([^"]*)"', line) or [None, ""])[1] if False else None
            m_id = re.search(r'tvg-id="([^"]*)"', line)
            m_name = re.search(r'tvg-name="([^"]*)"', line)
            m_logo = re.search(r'tvg-logo="([^"]*)"', line)
            display = line.split(",", 1)[-1].strip() if "," in line else ""
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            url = lines[j].strip() if j < n else ""
            entries.append({
                "tvg_id": m_id.group(1) if m_id else "",
                "tvg_name": m_name.group(1) if m_name else "",
                "logo": m_logo.group(1) if m_logo else "",
                "display": display,
                "url": url,
            })
            i = j + 1 if j < n else n
        else:
            i += 1
    return entries


def main():
    out_path = os.environ.get("OUTPUT", "macozetleri.m3u8")

    # load existing
    existing_entries = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing_entries = parse_existing(f.read().splitlines())

    # keep real existing entries (drop placeholders)
    kept = [e for e in existing_entries if not is_placeholder(e)]
    kept_ids = {e["tvg_id"] for e in kept}

    # scrape
    new_entries = []
    try:
        paths = get_summary_paths()
    except Exception as e:
        print("ERROR fetching list page:", e, file=sys.stderr)
        paths = []

    for path in paths:
        try:
            slug, tvg_id, name, display, video_url, thumb = parse_match(path)
        except Exception as e:
            print("ERROR parsing", path, e, file=sys.stderr)
            continue
        if not video_url:
            print("WARN no video url:", path, file=sys.stderr)
            continue
        if tvg_id in kept_ids:
            # update url/logo in case changed
            for e in kept:
                if e["tvg_id"] == tvg_id:
                    e["url"] = video_url
                    if thumb:
                        e["logo"] = thumb
                    e["tvg_name"] = name
                    e["display"] = display
            continue
        kept_ids.add(tvg_id)
        new_entries.append({
            "tvg_id": tvg_id,
            "tvg_name": name,
            "logo": thumb,
            "display": display,
            "url": video_url,
        })

    # new first
    all_entries = new_entries + kept

    # write
    lines = ["#EXTM3U"]
    for e in all_entries:
        lines.append(
            '#EXTINF:-1 tvg-id="{tid}" tvg-name="{tn}" tvg-logo="{logo}" '
            'group-title="{group}",{disp}'.format(
                tid=e["tvg_id"], tn=e["tvg_name"], logo=e["logo"],
                group=GROUP, disp=e["display"]))
        lines.append(e["url"])
    content = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("Wrote", len(all_entries), "entries to", out_path)


if __name__ == "__main__":
    main()
