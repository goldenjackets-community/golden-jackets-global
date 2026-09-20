# Global site counters — single source of truth

`data.json` is the **source of truth** for all member/chapter/country counts on
the Golden Jackets Global site. Historically these numbers were duplicated by
hand in four places in `index.html` (hero counters, scrolling ticker, map
tooltips, meta description) and drifted apart (BUG-2).

`scripts/update_global_counters.py` recomputes the aggregates from the per-chapter
data and rewrites **every** counter in one shot.

## Usage

Check for drift (used in CI, exits non-zero if inconsistent):

```bash
python3 scripts/update_global_counters.py --check
```

Fix everything from `data.json`:

```bash
python3 scripts/update_global_counters.py --write
```

## How to update counts

1. Edit the `members` field of the relevant chapter(s) in `data.json`
   (and `stats.certifications`, which is curated / not derivable).
2. Run `python3 scripts/update_global_counters.py --write`.
3. Commit both `data.json` and `index.html`.

The tool recomputes `stats.members`, `stats.active_chapters` and
`stats.countries` from the chapter list, so the summary can never disagree with
the detail. Chapter cards and map tooltips get each chapter's own number; the
hero, ticker header and meta description get the global totals.
