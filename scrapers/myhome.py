import logging

from scrapers.common import fetch_html, parse_generic_posts


logger = logging.getLogger(__name__)

LIST_URL = "https://www.myhome.go.kr/hws/portal/sch/selectRsdtRcritNtcView.do"


def scrape() -> list[dict]:
    html = fetch_html(LIST_URL)
    if not html:
        return []
    posts = parse_generic_posts(
        html,
        LIST_URL,
        "마이홈포털",
        include_patterns=["selectRsdtRcritNtcDetailView", "pblancId", "모집", "임대", "행복주택"],
    )
    logger.info("마이홈포털 수집: %s건", len(posts))
    return posts
