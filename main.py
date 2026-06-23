import logging
from datetime import datetime

from config import SEEN_BUSINESS_POSTS_PATH, SEEN_POSTS_PATH, TIP_STATE_PATH, settings
from notifier.kakao import KakaoNotifier
from scrapers import gyeongnam_business, jinju_city, jinju_youth, lh, myhome
from utils.business_filters import dedupe_business_posts, enrich_business_post, is_business_candidate
from utils.filters import dedupe_posts, enrich_post, is_candidate
from utils.formatter import (
    format_business_console_message,
    format_business_text_template,
    format_console_message,
    format_post_text_template,
    format_tip_console_message,
    format_tip_text_template,
    maybe_ai_summarize_posts,
)
from utils.storage import filter_new_posts, load_seen_posts, mark_posts_seen
from utils.tips import get_tip_for_date, mark_tip_sent, should_send_tip


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


def collect_business_posts() -> list[dict]:
    try:
        posts = gyeongnam_business.scrape()
        logging.info("경남 사업지원 완료: %s건", len(posts))
        return posts
    except Exception as exc:  # noqa: BLE001 - business alerts must not block housing alerts.
        logging.exception("경남 사업지원 수집 중 오류, 주거 알림은 계속 진행합니다: %s", exc)
        return []


def main() -> int:
    configure_logging()
    logging.info("진주 주거 공고 알림 시작: %s", datetime.now().isoformat(timespec="seconds"))

    raw_posts = collect_posts()
    candidates = [enrich_post(post) for post in raw_posts if is_candidate(post)]
    candidates = dedupe_posts(candidates)
    logging.info("후보 공고: %s건", len(candidates))

    raw_business_posts = collect_business_posts()
    business_candidates = [
        enrich_business_post(post) for post in raw_business_posts if is_business_candidate(post)
    ]
    business_candidates = dedupe_business_posts(business_candidates)
    logging.info("후보 사업지원 공고: %s건", len(business_candidates))

    seen_data = load_seen_posts(SEEN_POSTS_PATH)
    new_posts = filter_new_posts(candidates, seen_data)
    new_posts = new_posts[: settings.max_alert_posts]

    seen_business_data = load_seen_posts(SEEN_BUSINESS_POSTS_PATH)
    new_business_posts = filter_new_posts(business_candidates, seen_business_data)
    new_business_posts = new_business_posts[: settings.max_business_alert_posts]

    tip = get_tip_for_date() if settings.send_daily_tip and should_send_tip(TIP_STATE_PATH) else None

    if not new_posts and not new_business_posts and not tip:
        logging.info("새 공고가 없고 오늘의 주거 팁도 이미 발송되어 카카오톡을 보내지 않습니다.")
        return 0

    console_messages = []
    if new_posts:
        new_posts = maybe_ai_summarize_posts(new_posts)
        console_messages.append(format_console_message(new_posts, tip=tip))
    if new_business_posts:
        console_messages.append(format_business_console_message(new_business_posts))
    if tip and not new_posts:
        console_messages.append(format_tip_console_message(tip))
    _safe_print("\n".join(console_messages))

    if settings.dry_run:
        logging.info("DRY_RUN=true 이므로 카카오톡을 보내지 않고 종료합니다.")
        return 0

    templates = []
    if new_posts:
        templates.extend(
            format_post_text_template(post, idx, len(new_posts), link_url=settings.kakao_web_link_url)
            for idx, post in enumerate(new_posts, start=1)
        )
    if new_business_posts:
        templates.extend(
            format_business_text_template(post, idx, len(new_business_posts), link_url=settings.kakao_web_link_url)
            for idx, post in enumerate(new_business_posts, start=1)
        )
    if tip:
        templates.append(format_tip_text_template(tip, link_url=settings.kakao_web_link_url))

    sent = KakaoNotifier().send_templates(templates)
    if sent:
        if new_posts:
            mark_posts_seen(SEEN_POSTS_PATH, seen_data, new_posts)
        if new_business_posts:
            mark_posts_seen(SEEN_BUSINESS_POSTS_PATH, seen_business_data, new_business_posts)
        if tip:
            mark_tip_sent(TIP_STATE_PATH)
        return 0

    logging.error("발송 실패로 상태 파일을 갱신하지 않았습니다.")
    return 1


def _safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        safe_message = (
            message.replace("🏠", "[주거]")
            .replace("💼", "[사업]")
            .replace("💡", "[팁]")
        )
        print(safe_message.encode("cp949", errors="replace").decode("cp949"))


if __name__ == "__main__":
    raise SystemExit(main())
