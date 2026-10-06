#!/usr/bin/env python3
"""Excel tablosunu (veri/Universite_Basvuru_Tablosu.xlsx) uygulamanın okuduğu data.js dosyasına çevirir.

Kullanım:
    pip install openpyxl
    python3 tools/excel_to_data.py [excel_yolu]

Tabloyu güncelledikten sonra bu komutu çalıştırman yeterli; kitaplar yeni bilgilerle dolar.
"""
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = ROOT / "veri" / "Universite_Basvuru_Tablosu.xlsx"
OUT = ROOT / "data.js"

# Kitap sırtına sığacak kısa adlar. Tabloya yeni üniversite eklenirse burada yoksa
# otomatik olarak adın ilk kısmı kullanılır.
SHORT_NAMES = {
    "TUM – Technical University of Munich": "TUM",
    "KU Leuven (Group T)": "KU Leuven",
    "Charles University (FSV)": "Charles",
    "CTU – Czech Technical University": "ČVUT · CTU",
    "DTU – Technical University of Denmark": "DTU",
    "Aalto University": "Aalto",
    "École Polytechnique": "Polytechnique",
    "UvA – University of Amsterdam": "UvA",
    "VU Amsterdam": "VU Amsterdam",
    "TU Eindhoven (TU/e)": "TU/e",
    "University of Groningen": "Groningen",
    "University of Twente": "Twente",
    "Tilburg University": "Tilburg",
    "Universitat Pompeu Fabra (UPF)": "UPF",
    "UPF + UPC": "UPF + UPC",
    "Universidad Carlos III de Madrid (UC3M)": "UC3M",
    "Lund University": "Lund",
    "Università di Bologna": "Bologna",
}

COUNTRY_CODES = {
    "Almanya": "de", "Belçika": "be", "Çekya": "cz", "Danimarka": "dk",
    "Finlandiya": "fi", "Fransa": "fr", "Hollanda": "nl", "İspanya": "es",
    "İsveç": "se", "İtalya": "it",
}

HEADER_KEYS = {
    "Üniversite": "name",
    "Bölüm": "program",
    "Ülke": "country",
    "Şehir": "city",
    "Başvuru açılış": "open",
    "Başvuru kapanış": "close",
    "Yıllık ücret (AB dışı)": "fee",
    "QS sırası (2027)": "qs",
    "THE sırası (2026)": "the",
    "Eksiklerim": "todo",
    "Tahmini kabul oranı": "acceptance",
    "Not / kaynak": "note",
}


def clean(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def split_todo(text):
    """Eksiklerim metnini maddelere böler (';' ve cümle sonları), parantez içini bölmez."""
    if not text:
        return []
    parts, buf, depth = [], "", 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if depth == 0 and ch == ";":
            parts.append(buf)
            buf = ""
        elif (depth == 0 and ch == "." and i + 2 < len(text) and text[i + 1] == " "
              and not (buf[-1:].isdigit() and (len(buf) < 2 or not buf[-2].isdigit()))
              and (text[i + 2].isupper() or text[i + 2] in "ÇĞİÖŞÜ")
              and not re.search(r"\b(no|vb|örn|sn)$", buf, re.I)):
            parts.append(buf)
            buf = ""
        else:
            buf += ch
        i += 1
    parts.append(buf)
    items = [p.strip().rstrip(".").strip() for p in parts if p.strip()]
    return [tr_capitalize(p) for p in items]


def tr_capitalize(s):
    first = {"i": "İ", "ı": "I"}.get(s[0], s[0].upper())
    return first + s[1:]


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_XLSX
    ws = openpyxl.load_workbook(xlsx, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    # Başlık satırı ilk "Üniversite" satırıdır; tabloda bölüm başlıkları ("Ana liste", "Yedekler")
    # ve tekrar eden başlık satırları olabilir.
    start = next(i for i, r in enumerate(rows) if clean(r[0]) == "Üniversite")
    header = [clean(h) for h in rows[start]]
    keys = [HEADER_KEYS.get(h) for h in header]

    unis, notes = [], []
    group = "ana"
    for r in rows:
        first = clean(r[0])
        if first and not any(clean(v) for v in r[1:]):
            low = first.lower()
            if low.startswith("ana liste"):
                group = "ana"
                continue
            if low.startswith("yedek"):
                group = "yedek"
                continue
        if first == "Üniversite":
            continue
        rec = {k: clean(v) for k, v in zip(keys, r) if k}
        # Ülkesi olmayan satırlar alttaki açıklama satırlarıdır.
        if not rec.get("country"):
            if rec.get("name") and rec["name"] != "Açıklama" and rows.index(r) > start:
                notes.append(rec["name"])
            continue
        name = rec["name"]
        rec["group"] = group
        rec["short"] = SHORT_NAMES.get(name, re.split(r"[–(]", name)[0].strip())
        rec["code"] = COUNTRY_CODES.get(rec["country"], "")
        rec["todoItems"] = split_todo(rec.get("todo"))
        rec["id"] = len(unis) + 1
        unis.append(rec)

    payload = {"universities": unis, "notes": notes}
    OUT.write_text(
        "// Bu dosya tools/excel_to_data.py ile Excel tablosundan üretilir; elle düzenleme yerine tabloyu güncelle.\n"
        "window.LIBRARY_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"{len(unis)} üniversite -> {OUT}")


if __name__ == "__main__":
    main()
