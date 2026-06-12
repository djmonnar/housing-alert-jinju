import logging

from scrapers.common import fetch_html, parse_generic_posts


logger = logging.getLogger(__name__)

PAGES = [
    "https://young.jinju.go.kr/young/business/list/0",
    "https://young.jinju.go.kr/young/business/list/youth/0",
    "https://young.jinju.go.kr/young/board/notice/list/1",
]


def scrape() -> list[dict]:
    posts: list[dict] = []
    for url in PAGES:
        html = fetch_html(url)
        if not html:
            continue
        posts.extend(
            parse_generic_posts(
                html,
                url,
                "진주시 청년온라인플랫폼",
                include_patterns=["/read/", "business/read", "board/notice/read"],
            )
        )
    logger.info("진주시 청년온라인플랫폼 수집: %s건", len(posts))
    return posts
