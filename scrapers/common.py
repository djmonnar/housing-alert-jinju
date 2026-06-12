import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import settings
from utils.filters import clean_text, extract_application_period, extract_first_date


logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; housing-alert-jinju/1.0; +https://github.com/)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}


def fetch_html(url: str, params: dict | None = None) -> str | None:
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=settings.request_timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding
        return response.text
    except requests.RequestException as exc:
        logger.warning("수집 실패: %s (%s)", url, exc)
        return None


def parse_generic_posts(
    html: str,
    base_url: str,
    source: str,
    include_patterns: list[str] | None = None,
    limit: int = 80,
) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[dict] = []
    include_patterns = include_patterns or []

    skip_titles = {
        "본문 바로가기",
        "주메뉴 바로가기",
        "개인정보처리방침",
        "이메일무단수집거부",
        "목록",
        "TOP",
        "홈",
        "로그인",
        "회원가입",
        "나의 맞춤정보",
    }

    for anchor in soup.find_all("a", href=True):
        title = clean_text(anchor.get_text(" ", strip=True))
        href = anchor.get("href", "")
        if not title or len(title) < 4 or title in skip_titles:
            continue
        if include_patterns and not any(pattern in href or pattern in title for pattern in include_patterns):
            continue
        url = _normalize_link(base_url, href)
        if not url:
            continue
        container = anchor.find_parent(["tr", "li", "article"]) or anchor
        context = clean_text(container.get_text(" ", strip=True))
        if len(context) > 700:
            context = title
        posts.append(
            {
                "title": title,
                "source": source,
                "url": url,
                "published_at": extract_first_date(context),
                "application_period": extract_application_period(context),
                "summary": context,
            }
        )
        if len(posts) >= limit:
            break
    return posts


def _normalize_link(base_url: str, href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    if href.lower().startswith("javascript:"):
        ids = re.findall(r"['\"]?([A-Za-z0-9_-]{5,})['\"]?", href)
        return None if not ids else base_url
    return urljoin(base_url, href)
