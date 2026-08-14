from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from socialbot.threads_trend_drafts import (
    DraftParseError,
    DraftPost,
    extract_json,
    load_reference_notes,
    render_markdown,
)

JST = ZoneInfo("Asia/Tokyo")


def test_extract_json_parses_result_block() -> None:
    text = 'ここまでが調査です。\n<result>\n[{"topic": "a"}]\n</result>\n'
    assert extract_json(text) == [{"topic": "a"}]


def test_extract_json_raises_when_missing_tag() -> None:
    with pytest.raises(DraftParseError):
        extract_json("resultタグなしのテキスト")


def test_extract_json_raises_on_invalid_json() -> None:
    with pytest.raises(DraftParseError):
        extract_json("<result>not json</result>")


def test_load_reference_notes_skips_readme_and_non_text_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("読み込まれない", encoding="utf-8")
    (tmp_path / "notes.md").write_text("過去投稿メモ", encoding="utf-8")
    (tmp_path / "ignore.json").write_text('{"a": 1}', encoding="utf-8")

    notes = load_reference_notes(tmp_path)

    assert "過去投稿メモ" in notes
    assert "読み込まれない" not in notes
    assert "ignore.json" not in notes


def test_load_reference_notes_returns_empty_when_dir_missing(tmp_path: Path) -> None:
    assert load_reference_notes(tmp_path / "does-not-exist") == ""


def test_render_markdown_includes_draft_fields() -> None:
    draft = DraftPost(
        topic="模試シーズン",
        insight="秋の模試が本格化する時期",
        post_text="本文サンプル",
        suggested_datetime="2026-08-20T12:30:00+09:00",
        reasoning="平日昼が反応良い傾向",
        sources=["https://example.com"],
    )

    markdown = render_markdown([draft], datetime(2026, 8, 14, 9, 0, tzinfo=JST))

    assert "模試シーズン" in markdown
    assert "本文サンプル" in markdown
    assert "https://example.com" in markdown
    assert "2026-08-20T12:30:00+09:00" in markdown
