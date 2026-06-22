import logging

from scrapers.common import fetch_html, parse_generic_posts


logger = logging.getLogger(__name__)

PAGES = [
    {
        "url": "https://giba.or.kr/fe/bizinfo/bizannounce/NR_list.do?bbsCd=11",
        "source": "경남투자경제진흥원",
        "patterns": ["NR_view", "nttId", "소상공인", "마케팅", "창업", "지원", "모집", "공고"],
    },
    {
        "url": "https://dream.gnsinbo.or.kr/",
        "source": "경남신용보증재단 소상공인종합지원",
        "patterns": ["board", "notice", "공고", "모집", "소상공인", "창업", "지원"],
    },
    {
        "url": "https://www.gnstartup.kr/",
        "source": "경남창업포털",
        "patterns": ["business", "창업", "스타트업", "지원", "모집", "공고", "마케팅"],
    },
    {
        "url": "https://www.gntp.or.kr/biz/apply",
        "source": "경남테크노파크",
        "patterns": ["biz", "apply", "지원", "모집", "공고", "사업", "기업"],
    },
    {
        "url": "https://www.gyeongnam.go.kr/trade/index.gyeong",
        "source": "경상남도 해외마케팅 사업지원시스템",
        "patterns": ["trade", "마케팅", "수출", "해외", "지원", "모집", "공고"],
    },
]


def scrape() -> list[dict]:
    posts: list[dict] = []
    for page in PAGES:
        html = fetch_html(page["url"])
        if not html:
            continue
        posts.extend(
            parse_generic_posts(
                html,
                page["url"],
                page["source"],
                include_patterns=page["patterns"],
                limit=60,
            )
        )
    logger.info("경남 사업지원 수집: %s건", len(posts))
    return posts
