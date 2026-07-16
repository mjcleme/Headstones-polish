#!/usr/bin/env python3
"""Append a 'Spouse' column to Krakow_all.csv with a predicted spouse per person.

Prediction heuristic (Polish headstone conventions):
  1. SAME HEADSTONE/PLOT: people are grouped by the transcribe/separator rows;
     consecutive person rows between separators share a plot. Only pair within a plot.
  2. MATCHING SURNAME with gendered forms:
       - adjectival: -ski/-ska, -cki/-cka, -dzki/-dzka, plural -scy/-ccy/-dzcy
       - nominal feminine: -owa / -ówna  (e.g. Dzierwa -> Dzierwowa)
       - identical for non-gendered names (Nowak, Sala, Biel)
       - maiden name after "(" or "zd."/"z domu" is stripped before matching
  3. OPPOSITE GENDER (uses the Gender column).
  4. SAME GENERATION: husband/wife birth years within 15 years.
  When several candidates qualify, the closest birth year wins; a maiden-name
  marker (zd./parenthetical) strengthens a match and lets it stand when a birth
  year is missing. Spouse cell = the predicted partner's ID (its ID-column value).
"""
import csv, re

SRC = "Krakow_all.csv"
ENC = "utf-8-sig"
IDC, GIVEN, SUR, URL, BIRTH, GENDER = 0, 1, 2, 5, 6, 8
MAX_YEAR_GAP = 15         # normal husband/wife birth-year window
MAIDEN_YEAR_GAP = 25      # widened window when the wife has a maiden-name marker
                          # (zd. / z domu / parenthetical) confirming she is married

def is_person(r):
    return len(r) >= 3 and (r[GIVEN].strip() or r[SUR].strip())

def is_separator(r):
    return not is_person(r)

def birth_year(s):
    m = re.findall(r"(1[5-9]\d\d|20\d\d)", s)
    return int(m[-1]) if m else None

def has_maiden(sur):
    low = sur.lower()
    return "(" in sur or "zd" in low or "z domu" in low

def _strip_maiden(sur):
    s = sur.split("(")[0]
    low = s.lower()
    for mk in (" zd", " z domu", " z d"):
        i = low.find(mk)
        if i != -1:
            s = s[:i]
            break
    return s

def _letters(s):
    return "".join(ch for ch in s if not ch.isspace() and ch not in ".,-'0123456789").lower()

# adjectival gendered endings -> gender-neutral root token
_ADJ = [("scy", "sk"), ("ccy", "ck"), ("dzcy", "dzk"),
        ("ski", "sk"), ("ska", "sk"), ("cki", "ck"), ("cka", "ck"),
        ("dzki", "dzk"), ("dzka", "dzk")]

def root(sur):
    s = _letters(_strip_maiden(sur))
    for suf, rep in _ADJ:
        if s.endswith(suf):
            return s[:-len(suf)] + rep
    return s

def surname_match(male_sur, female_sur):
    rm, rf = root(male_sur), root(female_sur)
    if not rm or not rf:
        return False
    if rm == rf:
        return True
    # feminine nominal -owa / -ówna / -owna derived from husband's surname
    for suf in ("owa", "ówna", "owna"):
        if rf.endswith(suf):
            base = rf[:-len(suf)]
            if base and (rm == base or rm.startswith(base) or base.startswith(rm)):
                return True
    return False

def main():
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))
    header = rows[0]
    # locate the Spouse column by name (create it at the end if absent); reset it
    if "Spouse" in header:
        SIDX = header.index("Spouse")
    else:
        SIDX = len(header)
        header.append("Spouse")
        for r in rows[1:]:
            r.append("")
    for r in rows[1:]:
        while len(r) <= SIDX:
            r.append("")
        r[SIDX] = ""

    # split data rows into plot groups on separator rows
    groups, cur = [], []
    for r in rows[1:]:
        if is_separator(r):
            if cur:
                groups.append(cur); cur = []
        else:
            cur.append(r)
    if cur:
        groups.append(cur)

    def label(r):
        return (r[GIVEN].strip() + " " + _strip_maiden(r[SUR]).strip()).strip()

    predicted = 0
    for g in groups:
        males = [r for r in g if r[GENDER] == "Male"]
        females = [r for r in g if r[GENDER] == "Female"]
        edges = []  # (score, male_row, female_row)  lower score = better
        for m in males:
            for f in females:
                if not surname_match(m[SUR], f[SUR]):
                    continue
                ym, yf = birth_year(m[BIRTH]), birth_year(f[BIRTH])
                if ym and yf:
                    gap = abs(ym - yf)
                    limit = MAIDEN_YEAR_GAP if has_maiden(f[SUR]) else MAX_YEAR_GAP
                    if gap <= limit:
                        edges.append((gap, m, f))
                else:
                    # birth year missing: weaker; allow, boosted if maiden marker
                    base = 30 if has_maiden(f[SUR]) else 40
                    edges.append((base, m, f))
        edges.sort(key=lambda e: e[0])
        taken = set()
        for score, m, f in edges:
            if id(m) in taken or id(f) in taken:
                continue
            m[SIDX] = f[IDC]
            f[SIDX] = m[IDC]
            taken.add(id(m)); taken.add(id(f))
            predicted += 1

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    persons = sum(1 for r in rows[1:] if is_person(r))
    withsp = sum(1 for r in rows[1:] if is_person(r) and r[SIDX])
    print(f"Predicted {predicted} couples -> {withsp}/{persons} person rows have a spouse.")

if __name__ == "__main__":
    main()
