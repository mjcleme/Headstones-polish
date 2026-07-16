#!/usr/bin/env python3
"""Set the leading 'ID' column in Krakow_all.csv to each person's BillionGraves
record number (the trailing numeric id of their record URL).

Person rows = rows with a given name or surname. A person row whose URL has no
numeric record number (no BillionGraves link, or only a transcribe link) gets a
blank ID. Non-person rows (transcribe/address, blank/separator) also get blank.
"""
import csv, json, os
from collections import Counter

SRC = "Krakow_all.csv"
ENC = "utf-8-sig"
URLC = 5  # Billiongraves Link column (after leading ID column)
MANUAL = "manual_ids.json"  # fallback ids (keyed "Given|Surname") for person rows
                            # with no BillionGraves record number (random, stable)

def is_person(r):
    return len(r) >= 3 and (r[1].strip() or r[2].strip())

def rec_id(url):
    seg = url.strip().rstrip("/").split("/")[-1].split("?")[0]
    return seg if seg.isdigit() else ""

def main():
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))
    header = rows[0]
    if header[0] != "ID":
        header.insert(0, "ID")
        for r in rows[1:]:
            r.insert(0, "")

    manual = {}
    if os.path.exists(MANUAL):
        manual = json.load(open(MANUAL, encoding="utf-8"))

    assigned, fromrand, blank = 0, 0, []
    for r in rows[1:]:
        if is_person(r):
            rid = rec_id(r[URLC]) if len(r) > URLC else ""
            if rid:
                assigned += 1
            else:
                rid = manual.get(r[1].strip() + "|" + r[2].strip(), "")
                if rid:
                    fromrand += 1
                else:
                    blank.append((r[1], r[2]))
            r[0] = rid
        else:
            r[0] = ""

    ids = [r[0] for r in rows[1:] if r[0].strip()]
    dups = [k for k, v in Counter(ids).items() if v > 1]

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    print(f"Assigned BillionGraves record number to {assigned} person rows.")
    print(f"Assigned random fallback id to {fromrand} person rows.")
    print(f"Unique: {len(set(ids))}/{len(ids)}   Duplicates: {len(dups)}")
    print(f"Person rows still without any ID: {len(blank)}")
    for gn, sn in blank:
        print(f"   - {gn!r} {sn!r}")

if __name__ == "__main__":
    main()
