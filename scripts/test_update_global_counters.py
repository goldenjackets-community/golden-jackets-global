"""Tests for update_global_counters (BUG-2 / issue #26).

Pure logic, no network. Verifies the single-source-of-truth updater rewrites
all counter locations consistently and that --check detects drift.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_global_counters as ugc  # noqa: E402


DATA = {
    "chapters": [
        {"id": "brazil", "name": "Golden Jackets Brazil", "code": "BR",
         "flag": "🇧🇷", "status": "active", "members": 92},
        {"id": "poland", "name": "Golden Jackets Poland", "code": "PL",
         "flag": "🇵🇱", "status": "active", "members": 2},
        {"id": "italy", "name": "Golden Jackets Italy", "code": "IT",
         "flag": "🇮🇹", "status": "active", "members": 1},
        {"id": "japan", "name": "Golden Jackets Japan", "code": "JP",
         "flag": "🇯🇵", "status": "planned", "members": 0},
    ],
    "stats": {"members": 999, "certifications": "2512+",
              "active_chapters": 1, "countries": 2},
}

HTML = """<html><head>
<meta name="description" content="... 999 members, 1 active chapters, 2 countries.">
</head><body>
<div class="ticker"><div class="ticker-content" id="ticker-content"><span>old</span></div></div>
<div class="stat"><div class="num" data-target="999">0</div><div class="label">Members</div></div>
<div class="stat"><div class="num" data-target="2">0</div><div class="label">Countries</div></div>
<div class="stat"><div class="num" data-target="1">0</div><div class="label">Active Chapters</div></div>
<div class="pin"><div class="tooltip">🇧🇷 Brazil · 50 members · Founded 2024</div></div>
<div class="pin"><div class="tooltip">🇮🇹 Italy · 9 members</div></div>
<div class="info"><h3>#1 Golden Jackets Brazil</h3><p>50 members · Lead: X</p></div>
<div class="info"><h3>#3 Golden Jackets Italy</h3><p>9 members · Lead: Y</p></div>
</body></html>"""


def test_compute_stats_recomputes_from_chapters():
    stats, chapters = ugc.compute_stats(DATA)
    assert stats["members"] == 95        # 92+2+1+0
    assert stats["countries"] == 4       # all listed chapters
    assert stats["active_chapters"] == 3  # brazil, poland, italy
    assert stats["certifications"] == "2512+"  # curated, preserved


def test_apply_updates_hero_counters():
    stats, chapters = ugc.compute_stats(DATA)
    out = ugc.apply_to_html(HTML, stats, chapters)
    assert 'data-target="95">0</div><div class="label">Members</div>' in out
    assert 'data-target="4">0</div><div class="label">Countries</div>' in out
    assert 'data-target="3">0</div><div class="label">Active Chapters</div>' in out


def test_apply_updates_meta_only_globally():
    stats, chapters = ugc.compute_stats(DATA)
    out = ugc.apply_to_html(HTML, stats, chapters)
    assert "95 members, 3 active chapters, 4 countries" in out


def test_apply_updates_ticker_from_chapters():
    stats, chapters = ugc.compute_stats(DATA)
    out = ugc.apply_to_html(HTML, stats, chapters)
    assert "🏆 95 Members Worldwide" in out
    assert "🇧🇷 Brazil · 92 members" in out
    assert "🇮🇹 Italy · 1 member" in out   # singular
    # planned chapter with 0 members is skipped
    assert "Japan" not in out


def test_apply_fixes_tooltips_per_chapter():
    stats, chapters = ugc.compute_stats(DATA)
    out = ugc.apply_to_html(HTML, stats, chapters)
    assert "🇧🇷 Brazil · 92 members · Founded 2024" in out
    assert "🇮🇹 Italy · 1 member" in out


def test_apply_fixes_chapter_cards_individually_not_global():
    stats, chapters = ugc.compute_stats(DATA)
    out = ugc.apply_to_html(HTML, stats, chapters)
    # cards keep the chapter's own number, NOT the global total (95)
    assert "<h3>#1 Golden Jackets Brazil</h3><p>92 members" in out
    assert "<h3>#3 Golden Jackets Italy</h3><p>1 member" in out


def test_check_detects_stats_drift():
    problems = ugc.find_html_inconsistencies(HTML, {"members": 95, "countries": 4, "active_chapters": 3})
    # HTML has data-target="999" for Members -> should be flagged
    assert any("Members" in p for p in problems)


def test_singular_plural_word():
    assert ugc._fmt_member_word(1) == "member"
    assert ugc._fmt_member_word(0) == "members"
    assert ugc._fmt_member_word(5) == "members"


def test_apply_writes_category_breakdown_when_present():
    """Cards using the detailed 'N golden · N alumni · ...' format get rewritten
    from the chapter's breakdown dict."""
    data = {
        "chapters": [
            {"id": "brazil", "name": "Golden Jackets Brazil", "code": "BR",
             "flag": "🇧🇷", "status": "active", "members": 93,
             "breakdown": {"golden": 57, "alumni": 2, "challenger": 19, "rising": 15}},
        ],
        "stats": {"members": 93, "certifications": "0", "active_chapters": 1, "countries": 1},
    }
    html = ('<div class="info"><h3>#1 Golden Jackets Brazil</h3>'
            '<p>53 golden · 2 alumni · 18 challengers · 9 rising · Founded April 2026</p></div>')
    stats, chapters = ugc.compute_stats(data)
    out = ugc.apply_to_html(html, stats, chapters)
    assert "57 golden · 2 alumni · 19 challengers · 15 rising" in out
    assert "Founded April 2026" in out  # suffix preserved
    assert "53 golden" not in out


def test_apply_leaves_simple_cards_alone_without_breakdown():
    """A chapter WITHOUT a breakdown dict keeps the simple 'N members' card."""
    data = {
        "chapters": [
            {"id": "uk", "name": "Golden Jackets UK", "code": "UK",
             "flag": "🇬🇧", "status": "active", "members": 17},
        ],
        "stats": {"members": 17, "certifications": "0", "active_chapters": 1, "countries": 1},
    }
    html = ('<div class="info"><h3>#3 Golden Jackets UK</h3>'
            '<p>15 members · Lead: X</p></div>')
    stats, chapters = ugc.compute_stats(data)
    out = ugc.apply_to_html(html, stats, chapters)
    assert "17 members" in out


def test_apply_updates_recent_activity_total_only():
    """The tagged recent-total line is rewritten; historical lines are untouched."""
    data = {
        "chapters": [
            {"id": "brazil", "name": "Golden Jackets Brazil", "code": "BR",
             "flag": "🇧🇷", "status": "active", "members": 100},
            {"id": "uk", "name": "Golden Jackets UK", "code": "UK",
             "flag": "🇬🇧", "status": "active", "members": 30},
        ],
        "stats": {"members": 130, "certifications": "0", "active_chapters": 2, "countries": 2},
    }
    html = (
        '<div class="recent">'
        '<p data-auto="recent-total" style="color:#888;">🌍 <span>1 members · 1 active chapters · 1 countries</span> <span>· Jan 01</span></p>'
        '<p style="color:#888;">🇨🇷 <span>Costa Rica in negotiation · 191 members</span> <span>· Aug 27</span></p>'
        '</div>'
    )
    stats, chapters = ugc.compute_stats(data)
    out = ugc.apply_to_html(html, stats, chapters)
    # tagged line updated to the live total
    assert "130 members · 2 active chapters · 2 countries" in out
    # historical line preserved verbatim
    assert "Costa Rica in negotiation · 191 members" in out
    assert "· Aug 27" in out


def test_recent_activity_noop_when_no_marker():
    """If there's no data-auto marker, the timeline is left completely alone."""
    data = {
        "chapters": [{"id": "uk", "name": "Golden Jackets UK", "code": "UK",
                      "flag": "🇬🇧", "status": "active", "members": 17}],
        "stats": {"members": 17, "certifications": "0", "active_chapters": 1, "countries": 1},
    }
    html = '<div class="recent"><p>🌍 old milestone · Aug 27</p></div>'
    stats, chapters = ugc.compute_stats(data)
    out = ugc.apply_to_html(html, stats, chapters)
    assert out.count("<p>🌍 old milestone · Aug 27</p>") == 1


def test_members_exclude_non_active_chapters():
    """In-negotiation / planned countries appear for map reach but must NOT
    count toward the member total (community counting rule)."""
    data = {
        "chapters": [
            {"id": "brazil", "name": "Golden Jackets Brazil", "code": "BR",
             "flag": "🇧🇷", "status": "active", "members": 93},
            {"id": "uk", "name": "Golden Jackets UK", "code": "UK",
             "flag": "🇬🇧", "status": "active", "members": 17},
            {"id": "japan", "name": "Golden Jackets Japan", "code": "JP",
             "flag": "🇯🇵", "status": "negotiation", "members": 1},
            {"id": "kenya", "name": "Golden Jackets Kenya", "code": "KE",
             "flag": "🇰🇪", "status": "negotiation", "members": 1},
        ],
        "stats": {},
    }
    stats, _ = ugc.compute_stats(data)
    assert stats["members"] == 110          # 93 + 17, NOT 112
    assert stats["active_chapters"] == 2
    assert stats["countries"] == 4          # all listed, for map reach
