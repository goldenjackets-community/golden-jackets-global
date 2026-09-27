# Golden Jackets — Global Dashboard 🧥🌍

World map showing all active Golden Jackets chapters across 21 countries.

**Live:** [goldenjackets.org](https://goldenjackets.org)

## Chapters (15 Active)

| # | Country | Status | Chapter Lead | Site |
|---|---------|--------|--------------|------|
| 1 | 🇧🇷 Brazil | ✅ Active | Ricardo Gulias | goldenjacketsbrazil.com |
| 2 | 🇵🇱 Poland | ✅ Active | Dawid Drabek | goldenjackets.pl |
| 3 | 🇬🇧 UK | ✅ Active | Daniel Gaina | goldenjackets.co.uk |
| 4 | 🇨🇱 Chile | ✅ Active | Oscar Gaviria | goldenjackets.cl |
| 5 | 🇮🇳 India | ✅ Active | Vishnu Rachapudi | goldenjackets.in |
| 6 | 🇫🇷 France | ✅ Active | Bangaly KABA | goldenjackets.fr |
| 7 | 🇮🇹 Italy | ✅ Active | Luca D'Addeo | goldenjackets.it |
| 8 | 🇵🇪 Peru | ✅ Active | Fernando Carrillo | goldenjackets.pe |
| 9 | 🇺🇸 USA | ✅ Active | Dr. Justin Cook | goldenjacketsus.com |
| 10 | 🇮🇱 Israel | ✅ Active | Eyal Tamir | goldenjackets.co.il |
| 11 | 🇧🇾 Belarus | ✅ Active | Vadim Sorokin | goldenjackets.by |
| 12 | 🇪🇨 Ecuador | ✅ Active | Bolivar David L. | goldenjackets.ec |
| 13 | 🇨🇴 Colombia | ✅ Active | Yidaido Rojas Barrantes | goldenjackets.co |
| 14 | 🇧🇪 Belgium | ✅ Active | Vivian Delplace | goldenjackets.be |
| 15 | 🇦🇪 UAE | ✅ Active | TBD | goldenjackets.ae |

## In Negotiation

| # | Country | Status |
|---|---------|--------|
| 16 | 🇯🇵 Japan | 🟡 Negotiation |
| 17 | 🇰🇪 Kenya | 🟡 Negotiation |
| 18 | 🇧🇴 Bolivia | 🟡 Negotiation |
| 19 | 🇦🇺 Australia | 🟡 Negotiation |
| 20 | 🇩🇪 Germany | 🟡 Negotiation |
| 21 | 🇨🇷 Costa Rica | 🟡 Negotiation |

> Countries "in negotiation" appear on the map for reach but do **not** count
> toward the member total.

## Stats

- **231 members** globally (active chapters only)
- **2754+ certifications**
- **15 active chapters**
- **21 countries** (including negotiation)

Numbers auto-update — see below.

## Membership categories

The community counts members across **four** categories, and **all** count
toward the total:

- 🏆 **Golden Jacket** — all 12 active AWS certifications
- 🎖️ **Alumni** — held all 12, some now expired
- ⚔️ **Challenger** — 10–11 certifications
- 🚀 **Rising** — 7–9 certifications

## Infrastructure & automation

- Hosted on GitHub Pages (branch: `master`), custom domain **goldenjackets.org**.
- `data.json` is the single source of truth for chapter metadata and stats.
- **Auto-update:** the `Update Global Stats` workflow (`.github/workflows/update-stats.yml`)
  runs **every 6 hours** (and on-demand via *Run workflow*). It:
  1. Scans every active chapter's live site, counting member cards per category
     (golden / alumni / challenger / rising).
  2. Recomputes the totals (active chapters only) and per-chapter `breakdown`.
  3. Rewrites **every** counter in `index.html` via `scripts/update_global_counters.py`
     — hero counters, ticker, map tooltips, meta, chapter cards, the Brazil-style
     category breakdown, and the top "Recent Activity" timeline entry.
  4. Commits; GitHub Pages redeploys automatically.
- Guards: per-chapter *never-decrease* + a global sanity check that aborts on a
  suspicious (>10%) drop, so a broken chapter deploy can't corrupt the totals.

So when any chapter adds a member, the global dashboard reflects it within ~6h
(or immediately if the workflow is triggered manually).

---

Golden Jackets Community · 2026
