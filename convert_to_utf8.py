#!/usr/bin/env python3
"""One-time: convert Krakow_all.csv from its mixed byte encoding to clean UTF-8
(with BOM). Name columns are UTF-8 bytes; the Cemetary column is single-byte
(cp1250/latin, e.g. 0xf3 = ó). Decode each cell to real Unicode (UTF-8 first,
cp1250 fallback for single-byte cells), then rewrite as utf-8-sig so Excel and
other tools auto-detect UTF-8. Idempotent guard: refuses if a BOM is present.
"""
import csv

SRC = "Krakow_all.csv"

def to_unicode(s):
    b = s.encode("latin-1")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1250")

def main():
    if open(SRC, "rb").read(3) == b"\xef\xbb\xbf":
        print("Already UTF-8 with BOM; nothing to do.")
        return
    with open(SRC, newline="", encoding="latin-1") as f:
        rows = [[to_unicode(c) for c in row] for row in csv.reader(f)]
    with open(SRC, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)
    print(f"Converted {len(rows)} rows to UTF-8 with BOM.")

if __name__ == "__main__":
    main()
