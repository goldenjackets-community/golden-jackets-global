# Global site counters — single source of truth

`data.json` is the **source of truth** for all member/chapter/country counts on
the Golden Jackets Global site. Historically these numbers were duplicated by
hand in several places in `index.html` (hero counters, scrolling ticker, map
tooltips, meta description, chapter cards) and drifted apart (BUG-2).

`scripts/update_global_counters.py` recomputes the aggregates from the
per-chapter data and rewrites **every** counter in one shot.

## Automatic (default)

You normally **don't** run this by hand. The `Update Global Stats` workflow
(`.github/workflows/update-stats.yml`) runs **every 6 hours** (and on-demand):

1. Scans each active chapter's live site and counts member cards per category
   (golden / alumni / challenger / rising).
2. Writes each chapter's `members` and `breakdown` into `data.json`
   (with a per-chapter never-decrease guard).
3. Runs `update_global_counters.py --write` to rewrite all counters.
4. Commits `data.json` + `index.html`; Pages redeploys.

## Manual usage

Check for drift (also used in CI — exits non-zero if inconsistent):

```bash
python3 scripts/update_global_counters.py --check
```

Fix everything from `data.json`:

```bash
python3 scripts/update_global_counters.py --write
```

## What it rewrites

From the per-chapter data it recomputes and rewrites:

- **Aggregates** — `stats.members` (active chapters only; in-negotiation
  countries show on the map but don't inflate the total), `active_chapters`,
  `countries`. `stats.certifications` is curated (counted by the workflow).
- **index.html** — hero counters, scrolling ticker, map tooltips, meta
  description, per-chapter cards, the category **breakdown** cards
  (`N golden · N alumni · N challengers · N rising`, driven by each chapter's
  `breakdown` field), and the top **Recent Activity** timeline entry (tagged
  `data-auto="recent-total"`; historical milestones are never touched).

## Adding a member manually (rare)

1. Edit the chapter's `members` (and `breakdown`, if the card uses the detailed
   format) in `data.json`.
2. Run `python3 scripts/update_global_counters.py --write`.
3. Commit both `data.json` and `index.html`.

In practice the 6-hourly workflow does all of this for you.

## Tests

```bash
python3 -m pytest scripts/test_update_global_counters.py -q
```
