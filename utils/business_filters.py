import re
from datetime import datetime, timedelta

from utils.filters import (
    clean_text,
    extract_application_period,
    extract_first_date,
    normalize_url,
    parse_date,
    stable_post_key,
)


BUSINESS_OFFICIAL_SOURCES = {
    "경남투자경제진흥원",
    "경남신용보증재단 소상공인종합지원",
    "경남창업포털",
    "경남테크노파크",
    "경상남도 해외마케팅 사업지원시스템",
}

BUSINESS_TOPIC_KEYWORDS = [
    "소상공인",
    "소기업",
    "자영업",
    "창업",
    "예비창업",
    "재창업",
    "스타트업",
    "창업기업",
    "마케팅",
    "디지털마케팅",
    "온라인",
    "쇼핑몰",
    "기획전",
    "전시회",
    "판로",
    "수출",
    "해외마케팅",
    "지원사업",
    "사업화",
    "정책자금",
    "경영안정",
    "컨설팅",
    "교육",
    "희망리턴패키지",
    "재도전",
    "보증",
    "융자",
    "참여기업",
    "참여 기업",
    "모집",
]

BUSINESS_REGION_KEYWORDS = [
    "경남",
    "경상남도",
    "도내",
    "진주",
    "진주시",
]

GENERIC_TITLES = {
    "사업공고",
    "지원사업",
    "지원사업안내",
    "마케팅지원",
    "중소기업지원",
    "소상공인종합지원",
    "해외마케팅 사업지원",
    "해외마케팅사업지원",
    "공지사항",
    "알림마당",
    "더보기",
    "바로가기",
}

NOTICE_ACTION_KEYWORDS = [
    "공고",
    "모집",
    "참여",
    "신청",
    "접수",
    "지원사업",
    "프로젝트",
    "패키지",
]

EXCLUDE_KEYWORDS = [
    "선정결과",
    "결과발표",
    "입찰결과",
    "평가위원",
    "위탁용역",
    "용역",
    "시스템 고도화",
    "기념",
    "이벤트",
    "행사 안내",
    "채용",
    "인사",
    "일경험",
    "평가위원회",
]


DATE_PATTERNS = [
    re.compile(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
]


def is_business_candidate(post: dict, today=None) -> bool:
    today = today or datetime.now().date()
    text = _business_content_text(post)
    title = clean_text(post.get("title"))
    if not text or title in GENERIC_TITLES:
        return False
    if not any(keyword in title for keyword in NOTICE_ACTION_KEYWORDS):
        return False
    if not post.get("published_at") and not post.get("application_period"):
        if not any(marker in text for marker in ["2026", "2025", "D-", "D -", "오늘 마감", "접수중", "진행중"]):
            return False
    if any(keyword in text for keyword in EXCLUDE_KEYWORDS):
        return False
    if "종료" in text and not any(keyword in text for keyword in ["진행중", "접수중", "모집중", "예산 소진시"]):
        return False
    if "마감" in text and "오늘 마감" not in text and "마감임박" not in text:
        return False
    if not any(keyword in text for keyword in BUSINESS_TOPIC_KEYWORDS):
        return False
    if infer_business_category(post) == "확인 필요":
        return False
    period_end = _period_end_date(post.get("application_period") or extract_application_period(text))
    if period_end and period_end < today:
        return False
    published_at = parse_date(post.get("published_at") or extract_first_date(text))
    if not period_end and not published_at:
        return False
    if not period_end and published_at and published_at < today - timedelta(days=30):
        return False
    if post.get("source") in BUSINESS_OFFICIAL_SOURCES:
        return True
    return any(keyword in text for keyword in BUSINESS_REGION_KEYWORDS)


def enrich_business_post(post: dict) -> dict:
    enriched = dict(post)
    text = _post_text(enriched)
    enriched["title"] = clean_text(enriched.get("title")) or "제목 확인 필요"
    enriched["url"] = normalize_url(enriched.get("url"))
    enriched["published_at"] = enriched.get("published_at") or extract_first_date(text)
    enriched["application_period"] = enriched.get("application_period") or extract_application_period(text) or "확인 필요"
    enriched["business_category"] = infer_business_category(enriched)
    enriched["target"] = infer_business_target(enriched)
    enriched["checkpoints"] = build_business_checkpoints(enriched)
    enriched["key"] = stable_post_key({**enriched, "source": f"business:{enriched.get('source')}"})
    return enriched


def dedupe_business_posts(posts: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for post in posts:
        enriched = enrich_business_post(post)
        keys = {enriched["key"], clean_text(enriched.get("title")).lower()}
        if seen.intersection(keys):
            continue
        seen.update(keys)
        result.append(enriched)
    return result


def infer_business_category(post: dict) -> str:
    text = _business_content_text(post)
    categories = []
    if any(keyword in text for keyword in ["소상공인", "자영업"]):
        categories.append("소상공인")
    if any(keyword in text for keyword in ["창업", "스타트업", "예비창업", "창업기업"]):
        categories.append("창업")
    if any(keyword in text for keyword in ["마케팅", "판로", "쇼핑몰", "기획전", "수출", "해외"]):
        categories.append("마케팅·판로")
    if any(keyword in text for keyword in ["전시회", "박람회 참가"]):
        categories.append("마케팅·판로")
    if any(keyword in text for keyword in ["정책자금", "융자", "보증", "경영안정"]):
        categories.append("자금·보증")
    if any(keyword in text for keyword in ["희망리턴패키지", "재도전"]):
        categories.append("소상공인")
    if "교육" in text:
        categories.append("교육·컨설팅")
    return " / ".join(dict.fromkeys(categories)) if categories else "확인 필요"


def infer_business_target(post: dict) -> str:
    text = _business_content_text(post)
    targets = []
    if "소상공인" in text:
        targets.append("소상공인")
    if "창업기업" in text or "스타트업" in text:
        targets.append("창업기업")
    if "예비창업" in text:
        targets.append("예비창업자")
    if "중소기업" in text:
        targets.append("중소기업")
    if "도내" in text or "경남" in text or "경상남도" in text:
        targets.append("경남 소재 사업자 확인 필요")
    return " / ".join(dict.fromkeys(targets)) if targets else "확인 필요"


def build_business_checkpoints(post: dict) -> str:
    text = _business_content_text(post)
    checks = ["신청기간", "지원대상", "제출서류", "원문 공고문"]
    if any(keyword in text for keyword in ["마케팅", "판로", "쇼핑몰", "기획전"]):
        checks.extend(["지원항목", "자부담 여부", "증빙자료"])
    if any(keyword in text for keyword in ["정책자금", "융자", "보증"]):
        checks.extend(["한도", "금리", "보증요건"])
    if any(keyword in text for keyword in ["창업", "스타트업"]):
        checks.extend(["업력 기준", "소재지 기준", "선정평가"])
    return ", ".join(dict.fromkeys(checks))


def _post_text(post: dict) -> str:
    fields = [
        post.get("title"),
        post.get("summary"),
        post.get("body"),
        post.get("source"),
        post.get("published_at"),
        post.get("application_period"),
    ]
    return clean_text(" ".join(str(field) for field in fields if field))


def _business_content_text(post: dict) -> str:
    fields = [
        post.get("title"),
        post.get("summary"),
        post.get("body"),
        post.get("published_at"),
        post.get("application_period"),
    ]
    return clean_text(" ".join(str(field) for field in fields if field))


def _period_end_date(period: str | None):
    if not period:
        return None
    matches = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(period):
            parsed = parse_date(match.group(0))
            if parsed:
                matches.append(parsed)
    return max(matches) if matches else None
