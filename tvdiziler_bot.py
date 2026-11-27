# -*- coding: utf-8 -*-
"""
tvdiziler.tv -> tvdiziler.m3u8

Neden bu sürüm?
  * Bölüm numarası korunur  -> "Taşacak Bu Deniz 40. Bölüm"
  * Tek bir "Yeni Bölümler" grubu -> player'ın "Yeni Bölümler" sekmesi dolar
  * Ana sayfa + AJAX arşivi  -> yeni diziler 36'lık pencereden kaçmaz
  * Hata olursa eski dosya bozulmaz, iş "failed" olur
"""

from __future__ import annotations

import argparse
import html as html_mod
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://tvdiziler.tv"
PLAYLIST = "tvdiziler.m3u8"
# True -> "Yeni Bölümler | Dizi Adı" (eski davranış, dizi bazlı grup)
# False -> tek "Yeni Bölümler" grubu (önerilen: player'ın "Yeni Bölümler" sekmesi dolar)
GRUP_PER_DIZI = True
GRUP_ADI = "Yeni Bölümler"

# 1 AJAX sayfası = 36 bölüm. 3 sayfa ~ son 108 bölüm.
SAYFA_SAYISI = 3
# Kaçtan az kayıt bulunursa dosya yazılmasın (site değişti/engelledi sinyali)
MIN_KAYIT = 5
ISTEK_ARASI = 0.35  # saniye, siteyi yormamak için
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Referer": BASE + "/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


@dataclass
class Bolum:
    slug: str          # dizi-bolum-izle
    dizi: str          # Taşacak Bu Deniz
    bolum_no: int | None
    logo: str
    tarih: datetime | None
    video: str = ""

    @property
    def ad(self) -> str:
        if self.bolum_no is None:
            return f"{self.dizi} (Son Bölüm)"
        return f"{self.dizi} {self.bolum_no}. Bölüm"


def oturum() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def temiz_metin(s: str) -> str:
    s = html_mod.unescape(s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dizi_adini_temizle(ad: str) -> str:
    ad = temiz_metin(ad)
    ad = re.sub(r"\b(izle|İzle|FULL|Full|HD)\b", " ", ad)
    ad = re.sub(r"\s+", " ", ad).strip(" -·|")
    return ad or "Dizi"


def bolum_no_bul(metin: str) -> int | None:
    metin = temiz_metin(metin)
    for kalip in (
        r"(\d+)\s*\.\s*B[oö]l[uü]m",   # 40.Bölüm / 40. Bölüm
        r"B[oö]l[uü]m\s*(\d+)",        # Bölüm 40
    ):
        m = re.search(kalip, metin, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


AYLAR = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8,
    "agustos": 8, "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11,
    "kasim": 11, "aralık": 12, "aralik": 12,
}


def tarih_bul(kart) -> datetime | None:
    t = kart.find("time")
    if not t:
        return None
    # 1) attribute'lar
    for attr in ("datetime", "title"):
        deger = (t.get(attr) or "").strip()
        if not deger:
            continue
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(deger, fmt)
            except ValueError:
                continue
    # 2) Türkçe metin: "28 Kasım 2026"
    metin = t.get_text(" ", strip=True)
    m = re.search(r"(\d{1,2})\s+([A-Za-zÇŞĞİÖÜçşğioöü]+)\s+(\d{4})", metin)
    if m:
        gun, ay, yil = m.groups()
        ay_no = AYLAR.get(ay.casefold())
        if ay_no:
            try:
                return datetime(int(yil), ay_no, int(gun))
            except ValueError:
                pass
    # 3) Bugün / Dün
    if "bugün" in metin.casefold():
        return datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    if "dün" in metin.casefold():
        d = datetime.now() - timedelta(days=1)
        return d.replace(hour=23, minute=59, second=59, microsecond=0)
    return None


def logo_duzelt(logo: str) -> str:
    logo = temiz_metin(logo)
    if not logo or "uploads/" not in logo:
        return ""
    if logo.startswith("//"):
        return "https:" + logo
    if logo.startswith("/"):
        return BASE + logo
    if not logo.startswith("http"):
        return f"{BASE}/{logo}"
    return logo


def slug_duzelt(href: str) -> str:
    href = temiz_metin(href)
    if href.startswith("http"):
        href = href.split("tvdiziler.tv", 1)[-1]
    return href.lstrip("/")


def kart_oku(a_tag) -> Bolum | None:
    """Bir <a> etiketinden bölüm bilgisini yapısal alanlardan okur."""
    slug = slug_duzelt(a_tag.get("href", ""))
    if not slug or "bolum" not in slug:
        return None

    kart = a_tag
    for _ in range(4):  # <li> / .poster-xs / .poster-media seviyesine çık
        if kart.parent is None:
            break
        kart = kart.parent
        if kart.name in ("li", "article") or "poster" in " ".join(kart.get("class", [])):
            break

    # Dizi adı: önce itemprop="name", yoksa ilk h2
    ad_el = kart.find(attrs={"itemprop": "name"}) or kart.find("h2")
    dizi = dizi_adini_temizle(ad_el.get_text(" ", strip=True) if ad_el else "")

    # Bölüm metni: <p> içindeki "40.Bölüm izle"
    p_el = kart.find("p")
    metin = p_el.get_text(" ", strip=True) if p_el else ""
    bolum_no = bolum_no_bul(metin) or bolum_no_bul(a_tag.get_text(" ", strip=True))

    if not dizi or dizi == "Dizi":
        # son çare: slug'dan üret
        dizi = dizi_adini_temizle(slug.rsplit("-bolum", 1)[0].replace("-", " ").title())

    img = kart.find("img")
    logo = ""
    if img:
        logo = logo_duzelt(
            img.get("data-src") or img.get("src") or img.get("data-lazy-src") or ""
        )
    if not logo:
        return None  # logolu olmayan (menü/footer) bağlantıları at

    return Bolum(slug=slug, dizi=dizi, bolum_no=bolum_no, logo=logo, tarih=tarih_bul(kart))


def ana_sayfa_bolumleri(s: requests.Session) -> list[Bolum]:
    r = s.get(BASE + "/", timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    sonuc: list[Bolum] = []
    for a in soup.find_all("a", href=True):
        b = kart_oku(a)
        if b:
            sonuc.append(b)
    return sonuc


def ajax_bolumleri(s: requests.Session, sayfa: int) -> list[Bolum]:
    """Ana sayfadaki 'Daha fazla göster' butonunun kullandığı servis."""
    r = s.post(
        BASE + "/ajax/service",
        data={
            "_t": "1",
            "_t_id": "",
            "stable": "",
            "page": str(sayfa),
            "type": "loadEpisode",
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": BASE + "/",
        },
        timeout=25,
    )
    if r.status_code != 200:
        print(f"  ! ajax sayfa {sayfa}: HTTP {r.status_code}")
        return []
    try:
        veri = r.json()
    except ValueError:
        print(f"  ! ajax sayfa {sayfa}: JSON değil")
        return []
    if not veri.get("success") or not veri.get("theme"):
        return []
    soup = BeautifulSoup(veri["theme"], "html.parser")
    sonuc: list[Bolum] = []
    for a in soup.find_all("a", href=True):
        b = kart_oku(a)
        if b:
            sonuc.append(b)
    return sonuc


def ham_video_bul(s: requests.Session, slug: str) -> str | None:
    """Detay sayfası -> player (/vid/ply/...) -> m3u8/mp4"""
    try:
        r = s.get(f"{BASE}/{slug}", timeout=25)
        if r.status_code != 200:
            return None
        html = r.text

        # (link, başlık) çiftleri: "Tek Part" > "1.Part" > ilk
        oynaticilar = re.findall(
            r'data-hhs="([^"]+)"[^>]*?title="([^"]*)"', html
        ) or [(m, "") for m in re.findall(r'data-hhs="([^"]+)"', html)]
        if not oynaticilar:
            return None

        secili = None
        for link, baslik in oynaticilar:
            if "tek part" in baslik.lower():
                secili = link
                break
        if not secili:
            for link, baslik in oynaticilar:
                if "part" in baslik.lower():
                    secili = link
                    break
        if not secili:
            secili = oynaticilar[0][0]

        if secili.startswith("//"):
            player_url = "https:" + secili
        elif secili.startswith("/"):
            player_url = BASE + secili
        elif secili.startswith("http"):
            player_url = secili
        else:
            player_url = f"{BASE}/{secili}"

        pr = s.get(player_url, timeout=25, headers={"Referer": f"{BASE}/{slug}"})
        if pr.status_code != 200:
            return None
        player_html = pr.text

        kalip = (
            r"""sources\s*:\s*\[\s*\{\s*file\s*:\s*["']([^"']+)["']""",
            r"""file\s*:\s*["']([^"']+\.(?:m3u8|mp4)[^"']*)["']""",
            r"""["'](https?://[^"'<>\\]+?\.(?:m3u8|mp4)(?:\?[^"'<>\\]*)?)["']""",
        )
        for k in kalip:
            m = re.search(k, player_html)
            if m:
                url = m.group(1).replace("\\/", "/").strip()
                if url.startswith("//"):
                    url = "https:" + url
                if url.startswith("http"):
                    return url
    except requests.RequestException as e:
        print(f"  ! {slug}: {e.__class__.__name__}")
    return None


def topla(s: requests.Session, sayfa_sayisi: int = SAYFA_SAYISI) -> list[Bolum]:
    adaylar: list[Bolum] = []
    print("Ana sayfa okunuyor...")
    adaylar += ana_sayfa_bolumleri(s)

    for sayfa in range(1, sayfa_sayisi + 1):
        print(f"Ajax arşivi sayfa {sayfa}...")
        adaylar += ajax_bolumleri(s, sayfa)
        time.sleep(ISTEK_ARASI)

    # tekilleştir: önce slug, sonra (dizi, bölüm). Zengin olanı (tarih/bölüm no) tut.
    by_slug: dict[str, Bolum] = {}
    for b in adaylar:
        mevcut = by_slug.get(b.slug)
        if mevcut is None:
            by_slug[b.slug] = b
        else:
            # daha iyi olanı seç
            if (b.tarih is not None and mevcut.tarih is None) or (
                b.bolum_no is not None and mevcut.bolum_no is None
            ):
                by_slug[b.slug] = b

    # slug farklı ama (dizi, bölüm) aynı olanları da tekilleştir
    gorulen: set[tuple] = set()
    temiz: list[Bolum] = []
    for b in by_slug.values():
        anahtar = (b.dizi.casefold(), b.bolum_no)
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        temiz.append(b)

    # yeni -> eski
    temiz.sort(
        key=lambda b: (b.tarih or datetime.min, b.bolum_no or 0),
        reverse=True,
    )
    return temiz


def yaz(bolumler: list[Bolum]) -> None:
    gecici = PLAYLIST + ".tmp"
    with open(gecici, "w", encoding="utf-8", newline="\n") as f:
        f.write("#EXTM3U\n")
        for b in bolumler:
            f.write(
                f'#EXTINF:-1 tvg-id="{b.slug}" tvg-name="{b.ad}" '
                f'tvg-logo="{b.logo}" group-title="{"Yeni Bölümler" if not GRUP_PER_DIZI else "Yeni Bölümler | " + b.dizi}", {b.ad}\n'
            )
            f.write("#EXTVLCOPT:http-referrer=https://tvdiziler.tv/\n")
            f.write(f"{b.video}\n\n")
    os.replace(gecici, PLAYLIST)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="test için en fazla N bölüm")
    ap.add_argument("--sayfa", type=int, default=SAYFA_SAYISI, help="kaç AJAX sayfası taransın")
    args = ap.parse_args()

    s = oturum()
    adaylar = topla(s, args.sayfa)
    print(f"\n{len(adaylar)} benzersiz bölüm adayı bulundu, video linkleri çekiliyor...")

    if args.limit:
        adaylar = adaylar[: args.limit]

    hazir: list[Bolum] = []
    hata = 0
    for i, b in enumerate(adaylar, 1):
        video = ham_video_bul(s, b.slug)
        if video:
            b.video = video
            hazir.append(b)
            print(f"  [{i}/{len(adaylar)}] OK   {b.ad}")
        else:
            hata += 1
            print(f"  [{i}/{len(adaylar)}] ATLA {b.ad}")
        time.sleep(ISTEK_ARASI)

    print(f"\nBaşarılı: {len(hazir)}  Atlanan: {hata}")

    if len(hazir) < MIN_KAYIT:
        print(
            f"HATA: sadece {len(hazir)} kayıt bulundu (eşik {MIN_KAYIT}). "
            "Site yapısı değişmiş veya istekler engellenmiş olabilir. "
            "Mevcut m3u8 KORUNDU.",
            file=sys.stderr,
        )
        return 1

    yaz(hazir)
    print(f"{len(hazir)} bölüm {PLAYLIST} dosyasına yazıldı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
