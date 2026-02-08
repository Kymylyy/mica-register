from scripts.check_esma_update import _parse_last_update_from_text


def test_parse_last_update_from_text_success():
    parsed = _parse_last_update_from_text("Last update: 23 December 2025")
    assert parsed is not None
    assert parsed.year == 2025
    assert parsed.month == 12
    assert parsed.day == 23


def test_parse_last_update_from_text_returns_none_on_missing_pattern():
    parsed = _parse_last_update_from_text("No update date on this page")
    assert parsed is None


def test_parse_last_update_from_text_with_html_like_spacing():
    parsed = _parse_last_update_from_text("Last update - 7 January 2026")
    assert parsed is not None
    assert parsed.year == 2026
    assert parsed.month == 1
    assert parsed.day == 7
