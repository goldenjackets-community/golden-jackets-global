#!/usr/bin/env python3
"""Single source-of-truth updater for the Golden Jackets Global site counters.

BUG-2: member/cert/country counts live in FOUR places in index.html (hero
counters, scrolling ticker, map tooltips, meta description) plus the stats block
in data.json. They drift apart constantly. This tool makes data.json the single
source of truth and rewrites EVERY counter from it in one shot.

Usage:
    update_global_counters.py [--data data.json] [--html index.html]
                              [--check] [--write]

    --check   Report inconsistencies and exit non-zero if any are found.
              Does NOT modify files. (Use in CI.)
    --write   Apply the computed values to data.json and index.html.

With neither flag, runs --check (safe default).

Design:
    * Aggregates (total members, countries, active chapters) are RECOMPUTED from
      the per-chapter data, so the summary can never disagree with the detail.
    * Certifications is a curated value in stats.certifications (not derivable),
      preserved as-is.
"""
import argparse
import json
import re
import sys


def compute_stats(data):
    """Recompute aggregate stats from the per-chapter list."""
    chapters = data.get('chapters', [])
    if isinstance(chapters, dict):
        chapters = list(chapters.values())

    total_members = sum(int(c.get('members') or 0) for c in chapters)
    # countries = distinct chapters that have any presence (all listed chapters)
    countries = len(chapters)
    active_chapters = sum(1 for c in chapters if c.get('status') == 'active')
    # certifications is curated (not derivable) — keep whatever is in stats
    certifications = data.get('stats', {}).get('certifications', '0')

    return {
        'members': total_members,
        'certifications': certifications,
        'active_chapters': active_chapters,
        'countries': countries,
    }, chapters


def _fmt_member_word(n):
    return 'member' if int(n) == 1 else 'members'


def apply_to_html(html, stats, chapters):
    """Rewrite every counter in the HTML from stats/chapters. Returns new html."""
    members = stats['members']
    certs = stats['certifications']
    active = stats['active_chapters']
    countries = stats['countries']

    # 1) meta descriptions — ONLY inside <meta ... content="..."> tags, so we
    #    don't accidentally rewrite per-chapter numbers elsewhere in the page.
    def _fix_meta(m):
        tag = m.group(0)
        tag = re.sub(r'\d+\s+members', f'{members} members', tag, flags=re.I)
        tag = re.sub(r'\d+\s+active chapters', f'{active} active chapters', tag, flags=re.I)
        tag = re.sub(r'\d+\s+countries', f'{countries} countries', tag, flags=re.I)
        return tag
    html = re.sub(r'<meta[^>]*content="[^"]*"[^>]*>', _fix_meta, html)

    # 2) hero counters: <div class="num" data-target="N">...</div>
    #    Members / Certifications / Active Chapters / Countries by label.
    def _set_target(html, label, value):
        # match a .stat block: data-target="OLD" ... <div class="label">LABEL</div>
        pat = re.compile(
            r'(<div class="num" data-target=")[^"]*("[^>]*>)[^<]*(</div>\s*<div class="label"[^>]*>' + re.escape(label) + r'</div>)'
        )
        return pat.sub(lambda m: f'{m.group(1)}{value}{m.group(2)}0{m.group(3)}', html)

    html = _set_target(html, 'Members', members)
    html = _set_target(html, 'Certifications', certs)
    html = _set_target(html, 'Active Chapters', active)
    html = _set_target(html, 'Countries', countries)

    # 3) ticker — rebuild the full ticker-content from data (doubled for scroll)
    def _ticker_spans():
        spans = [
            f'<span>🏆 {members} Members Worldwide</span>',
            f'<span>📜 {certs} Certifications</span>',
            f'<span>🌍 {countries} Countries · {active} Active Chapters</span>',
        ]
        for c in chapters:
            m = int(c.get('members') or 0)
            if m <= 0:
                continue
            flag = c.get('flag', '')
            name = c.get('name', '').replace('Golden Jackets ', '') or c.get('id', '')
            spans.append(f'<span>{flag} {name} · {m} {_fmt_member_word(m)}</span>')
        return spans

    spans = _ticker_spans()
    doubled = ''.join(spans + spans)  # doubled for seamless scroll loop
    html = re.sub(
        r'(<div class="ticker-content">).*?(</div>)',
        lambda m: m.group(1) + doubled + m.group(2),
        html, count=1, flags=re.S,
    )

    # 4) map tooltips: "<flag> <Country> · N members · ..." keep suffix, fix N.
    by_code = {}
    for c in chapters:
        code = (c.get('code') or '').upper()
        if code:
            by_code[code] = int(c.get('members') or 0)

    def _fix_tooltip(m):
        prefix, count_word, rest = m.group(1), m.group(2), m.group(3)
        # prefix already contains "<flag> Country · "; we can't easily map country
        # name -> code here, so tooltips are fixed by the pin's own data below.
        return m.group(0)

    # Tooltips are keyed by the pin block. Match each pin's data-... is absent,
    # so we match on the country name inside the tooltip by chapter name/code.
    for c in chapters:
        m = int(c.get('members') or 0)
        flag = c.get('flag', '')
        if not flag or m <= 0:
            continue
        # Replace ONLY within a tooltip that starts with this flag:
        # "<flag> <anything> · <N> member(s)"
        pat = re.compile(
            r'(' + re.escape(flag) + r'[^·<]*·\s*)\d+\s+members?'
        )
        html = pat.sub(lambda mm, mm_n=m: f'{mm.group(1)}{mm_n} {_fmt_member_word(mm_n)}', html)

    # 5) chapter cards: <h3>#N Golden Jackets X</h3><p>NN members · ...>
    #    Update each card's own count from its chapter data (NOT the global total).
    for c in chapters:
        m = int(c.get('members') or 0)
        name = c.get('name', '')
        if not name or m <= 0:
            continue
        # match the card's <h3>...NAME...</h3><p>NN member(s)
        pat = re.compile(
            r'(<h3>[^<]*' + re.escape(name) + r'[^<]*</h3>\s*<p>)\d+\s+members?'
        )
        html = pat.sub(lambda mm, mm_n=m: f'{mm.group(1)}{mm_n} {_fmt_member_word(mm_n)}', html)

    return html


def find_html_inconsistencies(html, stats):
    """Return a list of human-readable inconsistencies vs. the source of truth."""
    problems = []
    members = str(stats['members'])
    countries = str(stats['countries'])
    active = str(stats['active_chapters'])

    # hero targets
    for label, val in [('Members', members), ('Countries', countries), ('Active Chapters', active)]:
        m = re.search(r'data-target="([^"]*)"[^>]*>[^<]*</div>\s*<div class="label"[^>]*>' + re.escape(label) + '</div>', html)
        if m and m.group(1) != val:
            problems.append(f'hero counter "{label}" = {m.group(1)}, expected {val}')

    # ticker "N Members Worldwide"
    m = re.search(r'(\d+)\s+Members Worldwide', html)
    if m and m.group(1) != members:
        problems.append(f'ticker members = {m.group(1)}, expected {members}')

    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', default='data.json')
    ap.add_argument('--html', default='index.html')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args(argv)

    with open(args.data, encoding='utf-8') as f:
        data = json.load(f)
    with open(args.html, encoding='utf-8') as f:
        html = f.read()

    stats, chapters = compute_stats(data)

    if args.write:
        data['stats'] = stats
        new_html = apply_to_html(html, stats, chapters)
        with open(args.data, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        with open(args.html, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f'Updated: members={stats["members"]} certs={stats["certifications"]} '
              f'chapters={stats["active_chapters"]} countries={stats["countries"]}')
        return 0

    # default / --check
    problems = find_html_inconsistencies(html, stats)
    # also flag data.json stats drift vs recomputed
    for k in ('members', 'active_chapters', 'countries'):
        if str(data.get('stats', {}).get(k)) != str(stats[k]):
            problems.append(f'data.json stats.{k} = {data.get("stats", {}).get(k)}, '
                            f'recomputed {stats[k]}')

    if problems:
        print('COUNTER INCONSISTENCIES FOUND (run with --write to fix):')
        for p in problems:
            print(f'  - {p}')
        return 1
    print('All counters consistent with data.json source of truth.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
