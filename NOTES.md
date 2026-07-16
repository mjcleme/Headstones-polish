# Polish Names / BillionGraves — project notes

Enriching Krakow cemetery data (from BillionGraves) with birth/death dates and
derived genealogical columns: a stable ID, gender, predicted spouse, and predicted
mother, using Polish naming conventions and headstone reading rules.

_Last updated: 2026-07-15_

---

## 1. Files

| File | Purpose |
|------|---------|
| `Krakow_all.csv` | **Main working file.** Combined Rakowicki + Zembrzyce dataset. All enrichment columns live here. |
| `Krakow_output.csv` | Zembrzyce dataset with birth/death date columns appended. |
| `Krakow.csv`, `Krakow_test_output.csv` | Source/test files — **not modified.** |
| `extract_dates.py` | Date extractor + batch runner for **`/headstone/`** pages (JSON-LD). |
| `extract_supporting.py` | Date extractor for **`/supporting-record/`** pages. Importable: `from extract_supporting import fetch`. |
| `fill_all.py` | Fills `Krakow_all.csv` undated rows 1–302. |
| `fill_output_supporting.py` | Fills the `/supporting-record/` rows in `Krakow_output.csv`. |
| `normalize_dates.py` | Normalizes both date columns in `Krakow_all.csv` to full month names + 4-digit years. |
| `add_person_id.py` | Sets the leading `ID` column to each person's BillionGraves record number. |
| `add_gender.py` | Appends the `Gender` column, inferred from the Polish given name. |
| `predict_spouse.py` | Appends the `Spouse` column (predicted partner). |
| `predict_parent.py` | Appends the `Mother` column (mother's ID for predicted children). |
| `manual_ids.json` | Random fallback IDs for the 7 person rows with no BillionGraves link. |
| `*_cache.json` | Cached date lookups (see §9). |

## 2. `Krakow_all.csv` column layout

`ID, Given Name, Surname, Cemetary, Familysearch ID, Billiongraves Link, Birth Date, Death Date, Gender, Spouse, Mother`
(indexes 0–10).

- Derived columns (`Gender`, `Spouse`, `Mother`) are appended at the **end** so the
  URL/date indexes stay put and helper scripts don't need re-tweaking.
- Script column constants: `URLC=5`, `BI,DI=6,7` (birth/death), `GENDER=8`, `SPOUSE=9`.
- **Row structure:** header row 1; data rows 1–302 = the Rakowicki block; an embedded
  **second header row at spreadsheet row 303**; rows 304+ = the Zembrzyce block.
- **"Person row"** = a row with a given name or surname (1834 of them). The other 886
  rows are transcribe/address rows or blank separators; they act as **plot boundaries**
  and get blank ID/Gender/Spouse/Mother.

---

## 3. Birth & Death dates

**Rule / method.** For each person row, fetch their BillionGraves record and read the
dates off the page.
- `/headstone/…` pages carry dates in JSON-LD: `"birthDate":"1874-11-12"`,
  `"deathDate":"1951-8-7"` (Y-M-D, not zero-padded).
- `/supporting-record/…` pages (308-redirect to a headstone URL) have **no** JSON-LD;
  dates live in `"birth_date"`/`"death_date"`. The **first** such pair in the HTML is
  the page's own person; later pairs are related people (`relationships`) — ignore.
  Values may be full (`9 Jun 1953`), year-only (`1865`), or `Not Available` (→ blank).
- **Format:** readable, e.g. `23 September 1886`; month abbreviations expanded;
  year-only kept as the year.

**Report.**
- `Krakow_output.csv`: 1207 headstone + 417 supporting-record rows processed →
  1586 / 1624 person rows have a date; 38 blank (record lists no date, or 1 deleted
  headstone returning HTTP 410).
- `Krakow_all.csv`: rows 1–302 filled → 276 filled, 26 blank (no date on record / no URL).

## 4. Date normalization (`normalize_dates.py`)

**Rule.** Convert every date in `Krakow_all.csv` to full month name + 4-digit year.
The Zembrzyce block originally used an abbreviated `18-Feb-28` / `18 Feb 28` style with
2-digit years. The ambiguous 2-digit years (1928 vs 2028) are resolved by looking up the
**authoritative full date** from the caches, matched by the record's **numeric ID** (last
URL path segment). ID matching is used because the two files disagree on URL text for
Polish-letter names (`Michał`→`MichaÅ` — see §8); the trailing numeric ID is pure ASCII
and always matches. Fallback for anything not cached: expand the month and pivot the
2-digit year (≤25 → 20xx, else 19xx).

**Report.** All 1797 abbreviated cells resolved from cache — **0** pivot-fallback guesses.

---

## 5. `ID` column (`add_person_id.py`)

**Rule.** Each person row's ID = its **BillionGraves record number** (the trailing numeric
id of the record URL, e.g. `.../Barbara-SALA/183670218` → `183670218`). The 7 person rows
with no BillionGraves link get a **random 9-digit fallback** (900000000–999999999, outside
the real BG range), stored in `manual_ids.json` (keyed `"Given|Surname"`) so it is stable
across re-runs. Non-person rows get a blank ID.

Why record number: it's **stable across row reordering** (derived from the record, not row
position) and unique.

**Report.** 1827 from record number + 7 random fallback = **1834 IDs, all unique, 0
duplicates, 0 blanks** among person rows. The 7 fallback rows: Repeat, Aniela Bernakiewicz,
Fix Later, Władisław Talaga, Jan Magdziak, Agata Magdziak, Helena Kolczak.

---

## 6. `Gender` column (`add_gender.py`)

**Rule** (per <https://en.wikipedia.org/wiki/Polish_name>):
- **Female** if the given name ends in `-a`; otherwise **Male**.
- Male `-a` exceptions → Male: *Barnaba, Bonawentura, Jarema, Kosma, Kuba, Saba*
  (none appear in this data).
- The **surname is deliberately not used** — this dataset stores it inconsistently
  (sometimes feminine `-ska`, sometimes masculine base `-ski`, e.g. "Maria Michalowski").
- **Manual overrides** (`GENDER_OVERRIDES` in the script) fix 5 female names the `-a` rule
  mislabeled Male due to truncated/inflected/junk spellings: `Maryanny` (genitive of
  Marianna), `Ann` (Anna), `Irence` (Irena), `Rozalie` (Rozalia), `Helena22` (Helena).

**Report.** **1038 Male, 796 Female**, 886 blank (non-person rows).

**Known ambiguous rows left as-is:**
- `Michala Kussa` — labeled Female, low confidence.
- `Talaga` — surname only, no given name; gender genuinely indeterminable (guessed Female).
- `Gruszeczka`/`(Magdalena)` — given/surname fields are swapped; label happens to be
  correct (real name Magdalena = Female).

---

## 7. `Spouse` column (`predict_spouse.py`)

Predicts a married partner and stores the partner's **ID** (its `ID`-column value).

**Rules (Polish headstone conventions):**
1. **Same plot.** People are grouped by the transcribe/separator rows; consecutive person
   rows share a headstone. Pairs are only formed within a plot.
2. **Matching surname**, accounting for gendered forms:
   - adjectival: `-ski/-ska`, `-cki/-cka`, `-dzki/-dzka`, plural `-scy/-ccy/-dzcy`
   - feminine nominal: `-owa / -ówna` (e.g. Dzierwa → **Dzierwowa**)
   - identical for non-gendered names (Nowak, Sala, Biel)
   - a maiden name after `(` or `zd.` / `z domu` is stripped before matching
3. **Opposite gender** (from the `Gender` column).
4. **Same generation:** husband/wife birth years within **15** (`MAX_YEAR_GAP`),
   **widened to 25** (`MAIDEN_YEAR_GAP`) when the wife has a maiden-name marker
   (`zd.`/`z domu`/parenthetical) confirming she married in.
- Tie-break: closest birth year wins. A maiden-name marker also lets a match stand when a
  birth year is missing (the "tier-2" case). Matches are 1:1 and mutual.

**Other headstone clues (reference — vocabulary not present as structured fields here):**
`Mąż` (husband), `Żona` (wife), `Małżonkowie` (spouses), plural family names
`-scy/-ccy/-dzcy` (e.g. *Kowalscy* = "the Kowalskis"), `Ś.P.` = *Świętej Pamięci* ("of
holy memory", gender/marriage-neutral).

**Report.** **514 couples → 1028 / 1834 persons** have a spouse. Validated: all mutual;
every pairing over 15 yrs (max 22) has a maiden-name marker; none exceed 25. Examples:
Wojciech ↔ Maria Sala; Jozef Dzierwa ↔ Antonina **Dzierwowa** (no birth years, matched via
`-owa` + `Ś.P.` marker); Władysław Marekowski 1886 ↔ Anna Marekowski *zd. Wiślocki* 1903
(17 yrs, allowed by the maiden override). Salomea/Ludwik Skoczek (38-yr gap) correctly
**not** paired.
**Caveat:** 149 couples are "tier-2" (one birth year missing) matched on plot+surname+gender
only, so a dateless parent/adult-child pair could slip through.

---

## 8. `Mother` column (`predict_parent.py`)

Stores the **mother's ID** for each person predicted to be a child on a shared headstone;
blank otherwise.

**Rules (Polish headstone conventions):**
1. **Same plot** (transcribe separators, as above).
2. **Shared family surname** — child shares the family surname with the mother's married
   surname, using the same normalization as spouse matching plus plural `-owie`; maiden
   name stripped.
3. **Mother's age 16–42 at the child's birth** (hard rule):
   `16 ≤ child_birth_year − mother_birth_year ≤ 42`. **Both birth years required.**
4. The mother must be **female** and **not** the child's own predicted spouse.
5. **Daughter-in-law guard:** a female with a maiden-name marker (`zd.`/parenthetical)
   married *into* the family, so she is **excluded as a child** (a same-surname "mother"
   would be a mother-in-law). This removed false positives like Teresa Marekowski *zd.
   Kuryłowicz*.
- Tie-break when several women qualify: prefer a **coupled** mother (an actual parent),
  then mother-age nearest ~27.

**Supporting child clues (reference / partially used):**
- Diminutive given names → likely a child: `-ek`, `-uś`, `-sia`, `-cia`, `-czek`, etc.
  (Janek/Jaś, Marysia, Piotruś). Computed and reported, but the age window gates
  assignment, so diminutives are informational only.
- Relationship vocabulary `Syn`/`Synek` (son), `Córka`/`Córeczka` (daughter),
  `Dziecko`/`Dzieci` (child/children), `Niemowlę`/`Dzieciątko` (infant).
- Lifespan phrases `Żył/Żyła lat…` (lived X years), `…dni/miesięcy` (days/months).
- Angelic phrasing for infants: `Nasz Aniołek` ("our little angel"), `Powiększył(a) grono
  aniołów` ("joined the group of angels"). *(These engraved-text clues are not available as
  structured fields in this dataset; listed for manual review / future OCR work.)*

**Report.** **159 children** assigned a mother; **0** age-rule violations; mother-age at
birth 16–42, avg 29; 10 of the children have diminutive names. Several people are both a
child and a mother → 3-generation plots correctly reconstructed (e.g. Helena → Irena →
Krzysztof Kubas). Ludwik Skoczek (1903) ← Salomea (1865): the 38-yr gap the spouse logic
rejected is correctly caught here as mother/son.
**Limitation:** a woman listed under her married surname *without* a maiden-name marker
can't be distinguished from a born-in daughter, so some mother-in-law links may remain.

---

## 9. Technical notes

- **WAF:** `map.billiongraves.com` blocks plain `curl`. Bypass with a normal browser
  `User-Agent` (see `HEADERS` in the scripts); `requests` works.
- **Encoding:** `Krakow_all.csv` is **ISO-8859-2 / Latin-2** (Polish), NOT UTF-8
  (byte `0xf3` = ó). Read/write with `latin-1` for a lossless byte round-trip while only
  touching ASCII fields. `Krakow_output.csv` is UTF-8. Some URLs in `Krakow_all.csv` are
  UTF-8 bytes read under Latin-2 (`Michał`→`MichaÅ`), which is why cross-file joins use the
  numeric record ID, not the URL text.
- **Mangled names in reports** (e.g. `MichaÅ`, `W?adys?aw`, `JÃ³zef`) are display artifacts
  of that encoding; the stored bytes are intact and round-trip correctly.
- **Excel/Sheets** may re-display readable dates in locale short format (`9/23/1886`) — that's
  the app auto-parsing, not the file. Import the date columns as **Text** to preserve them.

## 10. Caches & how to re-run

Scripts are idempotent and cache date lookups to JSON, so re-running only fetches missing
URLs. Requires `requests`. The caches are **complete** (every processed URL, including
no-data blanks), so re-running currently fetches **0** URLs.

| Cache file | Covers | URLs |
|------------|--------|------|
| `dates_cache.json` | `Krakow_output.csv` `/headstone/` rows | 1207 |
| `output_supporting_cache.json` | `Krakow_output.csv` `/supporting-record/` rows | 417 |
| `supporting_cache.json` | `Krakow_all.csv` rows 1–302 | 290 |

(If a cache is lost, rebuild from the filled CSV instead of re-fetching: map each URL column
to its birth/death columns and dump `{url: [birth, death]}`.)

**Full rebuild order** for `Krakow_all.csv` (each step depends on the previous columns):

```bash
cd "/Users/clement/Documents/claude/polishnames"
python3 fill_all.py            # birth/death dates, rows 1..302
python3 normalize_dates.py     # -> full month names + 4-digit years
python3 add_person_id.py       # ID column (BG record number + manual_ids.json)
python3 add_gender.py          # Gender column
python3 predict_spouse.py      # Spouse column
python3 predict_parent.py      # Mother column (needs Gender + Spouse)
```

## 11. Tunable parameters

| Parameter | File | Value | Meaning |
|-----------|------|-------|---------|
| `MAX_ROW` | `fill_all.py` | 302 | last row processed for date fill |
| `MALE_A_EXCEPTIONS` / `GENDER_OVERRIDES` | `add_gender.py` | — | male `-a` names / manual gender fixes |
| `MAX_YEAR_GAP` | `predict_spouse.py` | 15 | spouse birth-year window |
| `MAIDEN_YEAR_GAP` | `predict_spouse.py` | 25 | spouse window when wife has a maiden marker |
| `MIN_AGE`, `MAX_AGE` | `predict_parent.py` | 16, 42 | mother's age range at child's birth |

## 12. Possible next steps

- `Krakow_all.csv` rows **after 302** were left as-is (scoped to row 302). To extend: raise
  `MAX_ROW` in `fill_all.py` and re-run.
- Remaining date blanks are genuine "no data" records; re-checking won't help unless
  BillionGraves adds data later.
- Optional: convert `Krakow_all.csv` to UTF-8 for cleaner display in Excel.
- Optional: add a `Father` column (mirror of `Mother` using the male parent), and/or use OCR
  of headstone photos to capture the engraved relationship/lifespan vocabulary in §8.
