import hashlib
import re
from datetime import date, datetime
from urllib.parse import urldefrag


CORE_KEYWORDS = [
    "진주",
    "진주시",
    "경남",
    "경상남도",
    "행복주택",
    "청년주택",
    "청년 전세임대",
    "청년전세임대",
    "전세임대",
    "매입임대",
    "청년매입임대",
    "국민임대",
    "공공임대",
    "임대주택",
    "무주택",
    "신혼부부",
    "청년월세",
    "월세지원",
    "전세보증금",
    "보증료 지원",
    "반환보증",
]

REGION_KEYWORDS = ["진주", "진주시", "경남", "경상남도"]
DIRECT_JINJU_KEYWORDS = ["진주", "진주시"]
JINJU_OFFICIAL_SOURCES = {"진주시청", "진주시 청년온라인플랫폼"}

TOPIC_KEYWORDS = [
    "행복주택",
    "청년주택",
    "청년 전세임대",
    "청년전세임대",
    "전세임대",
    "매입임대",
    "청년매입임대",
    "국민임대",
    "공공임대",
    "임대주택",
    "임대",
    "무주택",
    "신혼부부",
    "청년월세",
    "월세지원",
    "월세",
    "전세보증금",
    "전세",
    "보증료 지원",
    "보증료",
    "반환보증",
    "주거지원",
    "주거",
]

EXCLUDE_KEYWORDS = [
    "블로그",
    "카페",
    "부동산 광고",
    "분양 광고",
    "홍보글",
]

DATE_PATTERNS = [
    re.compile(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
]


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    return urldefrag(url.strip())[0]


def stable_post_key(post: dict) -> str:
    url = normalize_url(post.get("url"))
    source = clean_text(post.get("source"))
    title = clean_text(post.get("title"))
    raw = url or f"{source}|{title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_date(value: str | None) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def extract_first_date(text: str | None) -> str | None:
    text = clean_text(text)
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            parsed = parse_date(match.group(0))
            return parsed.isoformat() if parsed else match.group(0)
    return None


def extract_application_period(text: str | None) -> str | None:
    text = clean_text(text)
    if not text:
        return None
    patterns = [
        r"(?:신청|접수|인터넷신청|현장접수|모집)\s*(?:기간|일정)?\s*[:：]?\s*(20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}.*?(?:~|-|부터).*?20?\d{0,2}[.\-/년]?\s*\d{1,2}[.\-/월]\s*\d{1,2})",
        r"(20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2}.*?(?:~|-).*?20\d{2}[.\-/년]\s*\d{1,2}[.\-/월]\s*\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return clean_text(match.group(1))
    return None


def _period_end_date(period: str | None) -> date | None:
    if not period:
        return None
    matches: list[date] = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(period):
            parsed = parse_date(match.group(0))
            if parsed:
                matches.append(parsed)
    return max(matches) if matches else None


def infer_region_relevance(post: dict) -> str:
    text = _post_text(post)
    found = [kw for kw in REGION_KEYWORDS if kw in text]
    if found:
        return ", ".join(dict.fromkeys(found))
    if post.get("source") in {"진주시청", "진주시 청년온라인플랫폼"}:
        return "진주시 공식 사이트 게시물"
    return "확인 필요"


def infer_target(post: dict) -> str:
    text = _post_text(post)
    targets = []
    if "청년" in text:
        targets.append("청년")
    if "무주택" in text:
        targets.append("무주택자")
    if "신혼부부" in text:
        targets.append("신혼부부")
    if not targets and any(word in text for word in ["국민임대", "공공임대", "임대주택"]):
        targets.append("일반 무주택자")
    return " / ".join(dict.fromkeys(targets)) if targets else "확인 필요"


def build_checkpoints(post: dict) -> str:
    text = _post_text(post)
    checks = []
    if any(word in text for word in ["행복주택", "국민임대", "공공임대", "임대주택"]):
        checks.extend(["무주택 요건", "소득·자산 기준", "세대구성"])
    if any(word in text for word in ["전세임대", "매입임대"]):
        checks.extend(["신청 순위", "대상 주택 조건", "권리관계"])
    if any(word in text for word in ["월세", "월세지원", "청년월세"]):
        checks.extend(["나이", "소득", "임대차계약서", "주민등록 기준"])
    if any(word in text for word in ["전세보증금", "반환보증", "보증료"]):
        checks.extend(["보증 가입기관", "기납부 보증료", "소득·주택 기준"])
    checks.append("원문 공고문 확인")
    return ", ".join(dict.fromkeys(checks))


def is_candidate(post: dict, today: date | None = None) -> bool:
    today = today or datetime.now().date()
    text = _post_text(post)
    if not text:
        return False
    if any(keyword in text for keyword in EXCLUDE_KEYWORDS):
        return False
    if "(마감)" in text or "접수마감" in text or "모집마감" in text:
        return False
    if not any(keyword in text for keyword in CORE_KEYWORDS):
        return False
    if not any(keyword in text for keyword in TOPIC_KEYWORDS):
        return False
    if post.get("source") in JINJU_OFFICIAL_SOURCES:
        region_related = True
    else:
        region_related = any(keyword in text for keyword in DIRECT_JINJU_KEYWORDS)
    if not region_related:
        return False
    period_end = _period_end_date(post.get("application_period"))
    if period_end and period_end < today:
        return False
    return True


def enrich_post(post: dict) -> dict:
    enriched = dict(post)
    text = _post_text(enriched)
    enriched["title"] = clean_text(enriched.get("title")) or "제목 확인 필요"
    enriched["url"] = normalize_url(enriched.get("url"))
    enriched["published_at"] = enriched.get("published_at") or extract_first_date(text)
    enriched["application_period"] = enriched.get("application_period") or extract_application_period(text) or "확인 필요"
    enriched["region_relevance"] = enriched.get("region_relevance") or infer_region_relevance(enriched)
    enriched["target"] = enriched.get("target") or infer_target(enriched)
    enriched["checkpoints"] = enriched.get("checkpoints") or build_checkpoints(enriched)
    enriched["key"] = stable_post_key(enriched)
    return enriched


def dedupe_posts(posts: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for post in posts:
        enriched = enrich_post(post)
        keys = {enriched["key"], clean_text(enriched.get("title")).lower()}
        if seen.intersection(keys):
            continue
        seen.update(keys)
        result.append(enriched)
    return result


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
