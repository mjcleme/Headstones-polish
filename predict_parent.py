#!/usr/bin/env python3
"""Append a 'Mother' column to Krakow_all.csv: for each person predicted to be a
child on a shared headstone, store the MOTHER's unique ID (the ID column value).

Prediction (Polish headstone conventions):
  - SAME PLOT: grouped by transcribe/separator rows (as in predict_spouse.py).
  - FAMILY SURNAME: child shares the family surname with the mother's married
    surname (adjectival -ski/-ska/-scy, feminine nominal -owa/-ówna, maiden name
    stripped, non-gendered names identical).
  - MOTHER'S AGE 16-42: child's birth year minus the candidate mother's birth
    year must be in [16, 42]. Both birth years are required (hard rule).
  - The mother must be female and NOT the child's own predicted spouse.
When several women qualify, prefer one who is part of a predicted couple (an
actual parent), then the age closest to a typical ~27. Diminutive child names
(-ek, -uś, -sia, -cia, ...) are reported as a supporting signal.
"""
import csv, re
from predict_spouse import (root, has_maiden, birth_year, is_person, is_separator,
                            GIVEN, SUR, BIRTH, GENDER)

SRC = "Krakow_all.csv"
ENC = "latin-1"
IDC, SPOUSE = 0, 9
MIN_AGE, MAX_AGE = 16, 42

def fam_root(sur):
    s = root(sur)  # adjectival normalized + maiden stripped
    for suf in ("owa", "ówna", "owna"):
        if s.endswith(suf) and len(s) - len(suf) >= 3:
            s = s[:-len(suf)]
    return s

def fam_match(a, b):
    ra, rb = fam_root(a), fam_root(b)
    if not ra or not rb:
        return False
    if ra == rb:
        return True
    return len(ra) >= 4 and len(rb) >= 4 and (ra.startswith(rb) or rb.startswith(ra))

_DIM = ("ek", "uś", "us", "sia", "cia", "czek", "unia", "ynka", "usia", "iu", "ka")
def is_diminutive(given):
    g = given.strip().lower()
    return any(g.endswith(s) for s in _DIM)

def label(r):
    return (r[GIVEN].strip() + " " + r[SUR].split("(")[0].strip()).strip()

def main():
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))
    header = rows[0]
    # locate the Mother column by name (create it at the end if absent); reset it
    if "Mother" in header:
        MIDX = header.index("Mother")
    else:
        MIDX = len(header)
        header.append("Mother")
        for r in rows[1:]:
            r.append("")
    for r in rows[1:]:
        while len(r) <= MIDX:
            r.append("")
        r[MIDX] = ""

    groups, cur = [], []
    for r in rows[1:]:
        if is_separator(r):
            if cur:
                groups.append(cur); cur = []
        else:
            cur.append(r)
    if cur:
        groups.append(cur)

    assigned = 0
    dim_assigned = 0
    for g in groups:
        females = [r for r in g if r[GENDER] == "Female" and birth_year(r[BIRTH])]
        for child in g:
            cby = birth_year(child[BIRTH])
            if not cby:
                continue
            # a woman with a maiden-name marker married INTO the family: the shared
            # surname is her husband's, so any same-surname "mother" is a mother-in-law
            if child[GENDER] == "Female" and has_maiden(child[SUR]):
                continue
            cands = []
            for mom in females:
                if mom is child:
                    continue
                if child[SPOUSE] and child[SPOUSE] == mom[IDC]:
                    continue  # her spouse, not her child
                mby = birth_year(mom[BIRTH])
                age = cby - mby
                if MIN_AGE <= age <= MAX_AGE and fam_match(child[SUR], mom[SUR]):
                    coupled = 0 if mom[SPOUSE].strip() else 1
                    cands.append((coupled, abs(age - 27), mom))
            if cands:
                cands.sort(key=lambda c: (c[0], c[1]))
                mom = cands[0][2]
                child[MIDX] = mom[IDC]
                assigned += 1
                if is_diminutive(child[GIVEN]):
                    dim_assigned += 1

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    print(f"Assigned a mother to {assigned} person rows "
          f"({dim_assigned} of them have diminutive names).")

if __name__ == "__main__":
    main()
