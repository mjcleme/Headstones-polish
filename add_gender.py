#!/usr/bin/env python3
"""Append a 'Gender' column to Krakow_all.csv inferred from the Polish given name.

Rule (per https://en.wikipedia.org/wiki/Polish_name):
  - Female: given name ends in '-a'
  - Male:   otherwise
  - Exceptions: a few male given names end in '-a' (Barnaba, Bonawentura,
    Jarema, Kosma, Kuba, Saba) -> Male.
The surname is not used: this dataset stores it inconsistently (sometimes the
feminine -ska form, sometimes the masculine base -ski), so the given name is the
reliable signal. Non-person rows (no given/surname) get a blank Gender.
"""
import csv

SRC = "Krakow_all.csv"
ENC = "utf-8-sig"
GIVEN = 1  # Given Name column

MALE_A_EXCEPTIONS = {"barnaba", "bonawentura", "jarema", "kosma", "kuba", "saba"}

# Manual overrides for names the -a heuristic gets wrong: truncated / grammatically
# inflected / junk-suffixed female spellings that don't end in a plain -a.
# Keyed on the exact given-name string as stored (case-insensitive).
GENDER_OVERRIDES = {
    "maryanny": "Female",  # genitive of Marianna
    "ann": "Female",       # truncated Anna
    "irence": "Female",    # inflected Irena
    "rozalie": "Female",   # variant of Rozalia
    "helena22": "Female",  # Helena with stray digits
}

def is_person(r):
    return len(r) >= 3 and (r[1].strip() or r[2].strip())

def gender(given):
    g = given.strip()
    if not g:
        return ""
    if g.lower() in GENDER_OVERRIDES:
        return GENDER_OVERRIDES[g.lower()]
    first = g.replace("-", " ").split()[0].lower()
    if first in MALE_A_EXCEPTIONS:
        return "Male"
    return "Female" if g.lower().endswith("a") else "Male"

def main():
    rows = list(csv.reader(open(SRC, newline="", encoding=ENC)))
    header = rows[0]
    # locate the Gender column by name (create it at the end if absent)
    if "Gender" in header:
        GIDX = header.index("Gender")
    else:
        GIDX = len(header)
        header.append("Gender")
        for r in rows[1:]:
            r.append("")

    counts = {"Male": 0, "Female": 0, "": 0}
    for r in rows[1:]:
        while len(r) <= GIDX:
            r.append("")
        g = gender(r[GIVEN]) if is_person(r) else ""
        r[GIDX] = g
        counts[g] = counts.get(g, 0) + 1

    with open(SRC, "w", newline="", encoding=ENC) as f:
        csv.writer(f).writerows(rows)

    print(f"Gender assigned -> Male: {counts['Male']}  Female: {counts['Female']}  "
          f"blank(non-person): {counts['']}")

if __name__ == "__main__":
    main()
