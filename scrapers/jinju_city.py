import logging

from scrapers.common import fetch_html, parse_generic_posts


logger = logging.getLogger(__name__)

PAGES = [
    "https://www.jinju.go.kr/00130/02730/05586.web",
    "https://www.jinju.go.kr/00130/02730/05583.web",
    "https://www.jinju.go.kr/00130/02730/05584.web",
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
                "진주시청",
                include_patterns=["amode=view", "idx=", "not_ancmt_mgt_no"],
            )
        )
    logger.info("진주시청 수집: %s건", len(posts))
    return posts
