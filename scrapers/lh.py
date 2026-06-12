import logging

from scrapers.common import fetch_html, parse_generic_posts


logger = logging.getLogger(__name__)

LIST_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do"


def scrape() -> list[dict]:
    params = {"mi": "1026"}
    html = fetch_html(LIST_URL, params=params)
    if not html:
        return []
    posts = parse_generic_posts(
        html,
        LIST_URL,
        "LH 청약플러스",
        include_patterns=["selectWrtancInfo", "panId", "공고", "모집", "임대", "행복주택"],
    )
    logger.info("LH 청약플러스 수집: %s건", len(posts))
    return posts
