from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Config

JST = ZoneInfo("Asia/Tokyo")

THREADS_MAX_CHARS = 480
_RESULT_PATTERN = re.compile(r"<result>(.*?)</result>", re.DOTALL)


class DraftParseError(RuntimeError):
    """Raised when Claude's response doesn't contain the expected <result> JSON block."""

    def __init__(self, message: str, raw_text: str):
        super().__init__(message)
        self.raw_text = raw_text


@dataclass
class DraftPost:
    topic: str
    insight: str
    post_text: str
    suggested_datetime: str
    reasoning: str
    sources: list[str]


def load_juken_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_reference_notes(reference_dir: Path) -> str:
    """Concatenate user-supplied .md/.txt files (excluding README) for extra prompt context."""
    if not reference_dir.exists():
        return ""
    chunks = []
    for path in sorted(reference_dir.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        if path.stem.upper() == "README":
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(f"### {path.name}\n{text}")
    return "\n\n".join(chunks)


def build_prompt(juken_config: dict, reference_notes: str, today: datetime) -> str:
    posts_per_run = juken_config.get("posts_per_run", 3)
    audience = juken_config.get("audience", "")
    tone = juken_config.get("tone", "")
    hashtags = juken_config.get("hashtags", [])
    topic_area = juken_config.get("topic_area", "中学受験")

    hashtags_line = (
        f"\n使用可能なハッシュタグ(任意、使う場合は文末に1〜2個まで): {' '.join(hashtags)}"
        if hashtags
        else ""
    )
    reference_block = (
        f"\n\n# 参考情報(ユーザー提供、可能であれば内容に反映してください)\n{reference_notes}\n"
        if reference_notes
        else ""
    )

    return f"""あなたは「{topic_area}」領域に詳しいSNS運用担当者です。
Web検索を使って、直近の{topic_area}に関するトレンドや話題(ニュース、SNSでの反応、時期的トピックなど)を調査してください。

本日の日付: {today:%Y-%m-%d}(JST)

ターゲット層: {audience}
文体・トーン: {tone}{hashtags_line}
{reference_block}
調査結果をもとに、Threads投稿の下書きを{posts_per_run}件作成してください。各下書きについて次の項目を用意してください。
- topic: 調査で見つけた具体的なトピック
- insight: そのトピックが今なぜ話題/重要なのか、ターゲット層のどんな関心・不安に刺さるかというインサイト
- post_text: Threads投稿文({THREADS_MAX_CHARS}文字以内。誇張や不確かな断定は避け、事実は調査結果に基づくこと。絵文字は0〜2個まで)
- suggested_datetime: 投稿に適した日時(ISO8601形式、JST、本日から2週間以内)
- reasoning: その日時を提案する理由
- sources: 参照した情報源のURL(配列)

必ず最後に、他のテキストを含めず <result> タグの中にJSON配列のみを出力してください。フォーマット:
<result>
[
  {{
    "topic": "...",
    "insight": "...",
    "post_text": "...",
    "suggested_datetime": "2026-08-20T12:30:00+09:00",
    "reasoning": "...",
    "sources": ["https://..."]
  }}
]
</result>
"""


def extract_json(text: str) -> list[dict]:
    match = _RESULT_PATTERN.search(text)
    if not match:
        raise DraftParseError("Claudeの応答から <result> タグを検出できませんでした", text)
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError as exc:
        raise DraftParseError(f"<result> 内のJSON解析に失敗しました: {exc}", text) from exc


def call_claude_research(config: Config, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    message = client.messages.create(
        model=config.anthropic_model,
        max_tokens=4096,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )


def research_and_draft(
    config: Config, juken_config_path: Path, reference_dir: Path
) -> tuple[list[DraftPost], str]:
    if not config.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY が設定されていません")

    juken_config = load_juken_config(juken_config_path)
    reference_notes = load_reference_notes(reference_dir)
    today = datetime.now(JST)
    prompt = build_prompt(juken_config, reference_notes, today)

    full_text = call_claude_research(config, prompt)
    raw_items = extract_json(full_text)

    drafts = [
        DraftPost(
            topic=item.get("topic", ""),
            insight=item.get("insight", ""),
            post_text=item.get("post_text", "")[:THREADS_MAX_CHARS],
            suggested_datetime=item.get("suggested_datetime", ""),
            reasoning=item.get("reasoning", ""),
            sources=item.get("sources", []),
        )
        for item in raw_items
    ]
    return drafts, full_text


def render_markdown(drafts: list[DraftPost], generated_at: datetime) -> str:
    lines = [
        f"# Threads下書き案 ({generated_at:%Y-%m-%d %H:%M} JST生成)",
        "",
        "> 自動生成された下書きです。内容を確認・修正のうえ、手動でThreadsに投稿してください。",
        "",
    ]
    for i, draft in enumerate(drafts, start=1):
        lines.append(f"## {i}. {draft.topic}")
        lines.append("")
        lines.append(f"**推奨投稿日時**: {draft.suggested_datetime}")
        lines.append("")
        lines.append(f"**インサイト**: {draft.insight}")
        lines.append("")
        lines.append(f"**日時を提案する理由**: {draft.reasoning}")
        lines.append("")
        lines.append("**投稿文案**:")
        lines.append("")
        lines.append("```")
        lines.append(draft.post_text)
        lines.append("```")
        lines.append("")
        if draft.sources:
            lines.append("**参照元**:")
            for src in draft.sources:
                lines.append(f"- {src}")
            lines.append("")
    return "\n".join(lines)
