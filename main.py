import logging
from datetime import datetime

from config import SEEN_POSTS_PATH, settings
from notifier.kakao import KakaoNotifier
from scrapers import jinju_city, jinju_youth, lh, myhome
from utils.filters import dedupe_posts, enrich_post, is_candidate
from utils.formatter import format_console_message, format_kakao_feed, maybe_ai_summarize_posts
from utils.storage import filter_new_posts, load_seen_posts, mark_posts_seen


SCRAPERS = [
    ("LH 청약플러스", lh.scrape),
    ("마이홈포털", myhome.scrape),
    ("진주시청", jinju_city.scrape),
    ("진주시 청년온라인플랫폼", jinju_youth.scrape),
]


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def collect_posts() -> list[dict]:
    collected: list[dict] = []
    for name, scraper in SCRAPERS:
        try:
            posts = scraper()
            logging.info("%s 완료: %s건", name, len(posts))
            collected.extend(posts)
        except Exception as exc:  # noqa: BLE001 - one site must not stop the job.
            logging.exception("%s 수집 중 오류, 다음 사이트로 진행합니다: %s", name, exc)
    return collected


def main() -> int:
    configure_logging()
    logging.info("진주 주거 공고 알림 시작: %s", datetime.now().isoformat(timespec="seconds"))

    raw_posts = collect_posts()
    candidates = [enrich_post(post) for post in raw_posts if is_candidate(post)]
    candidates = dedupe_posts(candidates)
    logging.info("후보 공고: %s건", len(candidates))

    seen_data = load_seen_posts(SEEN_POSTS_PATH)
    new_posts = filter_new_posts(candidates, seen_data)
    new_posts = new_posts[: settings.max_alert_posts]

    if not new_posts:
        logging.info("새 공고가 없어 카카오톡을 보내지 않습니다.")
        return 0

    new_posts = maybe_ai_summarize_posts(new_posts)
    console_message = format_console_message(new_posts)
    _safe_print(console_message)

    if settings.dry_run:
        logging.info("DRY_RUN=true 이므로 카카오톡을 보내지 않고 종료합니다.")
        return 0

    link_url = settings.kakao_web_link_url or new_posts[0].get("url")
    template = format_kakao_feed(new_posts, link_url=link_url)
    sent = KakaoNotifier().send_feed(template)
    if sent:
        mark_posts_seen(SEEN_POSTS_PATH, seen_data, new_posts)
        return 0

    logging.error("발송 실패로 seen_posts.json을 갱신하지 않았습니다.")
    return 1


def _safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.replace("🏠", "[주거]"))


if __name__ == "__main__":
    raise SystemExit(main())
