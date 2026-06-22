from __future__ import annotations

import logging
import textwrap

from config import settings

logger = logging.getLogger(__name__)


STRICT_AI_PROMPT = """
너는 공공 주거 공고 알림 요약 도우미다.
반드시 제공된 원문/제목/날짜/링크에 있는 내용만 사용한다.
접수기간, 자격요건, 지역, 대상이 명확하지 않으면 "확인 필요"라고 쓴다.
추측하지 말고, 신청 가능 여부를 단정하지 않는다.
청년/무주택자 관점에서 확인해야 할 항목만 한국어로 짧게 정리한다.
광고 문구나 출처가 불명확한 내용은 만들지 않는다.
"""


def format_console_message(posts: list[dict], tip: dict | None = None) -> str:
    lines = [
        "🏠 진주 청년/무주택 주거 알림",
        "",
        f"새 공고 {len(posts)}건 발견",
        "",
    ]
    for idx, post in enumerate(posts, start=1):
        item_lines = [
            f"{idx}) {post.get('title', '제목 확인 필요')}",
            f"- 출처: {post.get('source', '확인 필요')}",
            f"- 게시일: {post.get('published_at') or '확인 필요'}",
            f"- 접수: {post.get('application_period') or '확인 필요'}",
            f"- 진주 관련성: {post.get('region_relevance') or '확인 필요'}",
            f"- 대상: {post.get('target') or '확인 필요'}",
            f"- 체크: {post.get('checkpoints') or '원문 확인 필요'}",
        ]
        if post.get("change_reason"):
            item_lines.append(f"- 변경: {post.get('change_reason')}")
        item_lines.extend([f"- 링크: {post.get('url') or '확인 필요'}", ""])
        lines.extend(item_lines)
    if tip:
        lines.extend(format_tip_lines(tip))
    lines.extend(default_tips())
    return "\n".join(lines)


def format_kakao_feed(posts: list[dict], link_url: str | None = None, tip: dict | None = None) -> dict:
    first_url = link_url or posts[0].get("url") or "https://www.jinju.go.kr/"
    items = []
    for post in posts[:5]:
        item_name = _truncate(post.get("title") or "제목 확인 필요", 14)
        item_op = _truncate(post.get("source") or "출처 확인", 12)
        items.append({"item": item_name, "item_op": item_op})
    if tip:
        items.append({"item": _truncate(tip["title"], 14), "item_op": "오늘의 팁"})

    description = f"새 공고 {len(posts)}건 발견."
    if tip:
        description += f" 오늘의 팁: {_truncate(tip['title'], 24)}"
    description += " 상세 내용은 원문 링크와 콘솔 로그를 확인하세요."
    return {
        "object_type": "feed",
        "content": {
            "title": "진주 청년/무주택 주거 알림",
            "description": description,
            "link": {"web_url": first_url, "mobile_web_url": first_url},
        },
        "item_content": {
            "profile_text": "housing-alert-jinju",
            "items": items,
            "sum": "확인",
            "sum_op": f"{len(posts)}건",
        },
        "buttons": [
            {
                "title": "공고 보기",
                "link": {"web_url": first_url, "mobile_web_url": first_url},
            }
        ],
    }


def format_tip_console_message(tip: dict) -> str:
    return "\n".join(
        [
            "🏠 오늘의 청년/무주택 주거 팁",
            "",
            *format_tip_lines(tip),
        ]
    )


def format_tip_kakao_feed(tip: dict, link_url: str | None = None) -> dict:
    first_url = link_url or "https://github.com/djmonnar/housing-alert-jinju"
    checks = ", ".join(tip.get("checks", []))
    return {
        "object_type": "feed",
        "content": {
            "title": "오늘의 청년/무주택 주거 팁",
            "description": _truncate(f"{tip['title']} - {tip['body']}", 90),
            "link": {"web_url": first_url, "mobile_web_url": first_url},
        },
        "item_content": {
            "profile_text": "housing-alert-jinju",
            "items": [
                {"item": "주제", "item_op": _truncate(tip["title"], 12)},
                {"item": "체크", "item_op": _truncate(checks or "확인 필요", 12)},
            ],
            "sum": "확인",
            "sum_op": "1개",
        },
        "buttons": [
            {
                "title": "참고 보기",
                "link": {"web_url": first_url, "mobile_web_url": first_url},
            }
        ],
    }


def format_post_text_template(post: dict, index: int, total: int, link_url: str | None = None) -> dict:
    fallback_url = link_url or settings.kakao_web_link_url or "https://github.com/djmonnar/housing-alert-jinju"
    source = post.get("source") or "출처 확인"
    url = post.get("url") or "원문 확인 필요"
    title = _truncate(post.get("title") or "제목 확인 필요", 52)
    text = "\n".join(
        [
            f"🏠 진주 주거 공고 {index}/{total}",
            title,
            f"출처: {_truncate(source, 16)}",
            f"원문: {url}",
        ]
    )
    return {
        "object_type": "text",
        "text": _truncate(text, 195),
        "link": {"web_url": fallback_url, "mobile_web_url": fallback_url},
        "button_title": "참고 보기",
    }


def format_business_console_message(posts: list[dict]) -> str:
    lines = [
        "💼 경남 소상공인/창업/마케팅 지원 알림",
        "",
        f"새 사업지원 공고 {len(posts)}건 발견",
        "",
    ]
    for idx, post in enumerate(posts, start=1):
        lines.extend(
            [
                f"{idx}) {post.get('title', '제목 확인 필요')}",
                f"- 출처: {post.get('source', '확인 필요')}",
                f"- 게시일: {post.get('published_at') or '확인 필요'}",
                f"- 신청/접수: {post.get('application_period') or '확인 필요'}",
                f"- 분야: {post.get('business_category') or '확인 필요'}",
                f"- 대상: {post.get('target') or '확인 필요'}",
                f"- 체크: {post.get('checkpoints') or '원문 확인 필요'}",
                f"- 링크: {post.get('url') or '확인 필요'}",
                "",
            ]
        )
    return "\n".join(lines)


def format_business_text_template(post: dict, index: int, total: int, link_url: str | None = None) -> dict:
    fallback_url = link_url or settings.kakao_web_link_url or "https://github.com/djmonnar/housing-alert-jinju"
    source = post.get("source") or "출처 확인"
    url = post.get("url") or "원문 확인 필요"
    category = post.get("business_category") or "분야 확인"
    title = _truncate(post.get("title") or "제목 확인 필요", 48)
    text = "\n".join(
        [
            f"💼 경남 사업지원 {index}/{total}",
            title,
            f"분야: {_truncate(category, 18)}",
            f"출처: {_truncate(source, 16)}",
            f"원문: {url}",
        ]
    )
    return {
        "object_type": "text",
        "text": _truncate(text, 195),
        "link": {"web_url": fallback_url, "mobile_web_url": fallback_url},
        "button_title": "참고 보기",
    }


def format_tip_text_template(tip: dict, link_url: str | None = None) -> dict:
    fallback_url = link_url or settings.kakao_web_link_url or "https://github.com/djmonnar/housing-alert-jinju"
    checks = ", ".join(tip.get("checks", []))
    text = "\n".join(
        [
            "💡 오늘의 주거 팁",
            _truncate(tip["title"], 44),
            f"체크: {_truncate(checks or '확인 필요', 80)}",
        ]
    )
    return {
        "object_type": "text",
        "text": _truncate(text, 195),
        "link": {"web_url": fallback_url, "mobile_web_url": fallback_url},
        "button_title": "참고 보기",
    }


def format_tip_lines(tip: dict) -> list[str]:
    checks = ", ".join(tip.get("checks", [])) or "확인 필요"
    return [
        "오늘의 주거 팁:",
        f"- 주제: {tip['title']}",
        f"- 내용: {tip['body']}",
        f"- 체크: {checks}",
        "",
    ]


def maybe_ai_summarize_posts(posts: list[dict]) -> list[dict]:
    if not settings.openai_api_key:
        return posts
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        enriched = []
        for post in posts:
            prompt = _build_ai_input(post)
            response = client.responses.create(
                model=settings.openai_model,
                instructions=STRICT_AI_PROMPT,
                input=prompt,
            )
            summary = getattr(response, "output_text", "").strip()
            updated = dict(post)
            if summary:
                updated["checkpoints"] = summary
            enriched.append(updated)
        return enriched
    except Exception as exc:  # noqa: BLE001 - optional AI must never block alerts.
        logger.warning("AI 요약 실패, 규칙 기반 요약으로 진행합니다: %s", exc)
        return posts


def default_tips() -> list[str]:
    return [
        "꿀팁:",
        "- LH 공고는 접수기간보다 자격요건 확인이 먼저입니다.",
        "- 전세임대는 선정 후 직접 집을 구해야 하므로 권리관계 확인이 중요합니다.",
        "- 마감일에는 접속이 몰릴 수 있어 가능하면 초반에 신청하세요.",
    ]


def _build_ai_input(post: dict) -> str:
    body = textwrap.shorten(post.get("body") or post.get("summary") or "", width=2500, placeholder="...")
    return "\n".join(
        [
            f"제목: {post.get('title')}",
            f"출처: {post.get('source')}",
            f"게시일: {post.get('published_at') or '확인 필요'}",
            f"접수기간: {post.get('application_period') or '확인 필요'}",
            f"링크: {post.get('url')}",
            f"본문: {body}",
            "",
            "체크포인트만 2~4개 bullet로 작성해줘.",
        ]
    )


def _truncate(text: str, max_len: int) -> str:
    text = str(text).strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"
