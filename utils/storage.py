import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def load_seen_posts(path: Path) -> dict:
    if not path.exists():
        return {"posts": {}}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"posts": {}}
        data.setdefault("posts", {})
        return data
    except (OSError, json.JSONDecodeError):
        return {"posts": {}}


def filter_new_posts(posts: list[dict], seen_data: dict) -> list[dict]:
    seen_posts = seen_data.get("posts", {})
    new_or_changed = []
    for post in posts:
        key = post.get("key")
        previous = seen_posts.get(key)
        if not previous:
            new_or_changed.append(post)
            continue
        if previous.get("fingerprint") != post_fingerprint(post):
            changed = dict(post)
            changed["change_reason"] = "기존 공고의 제목/날짜/접수기간/체크포인트 변경 감지"
            new_or_changed.append(changed)
    return new_or_changed


def mark_posts_seen(path: Path, seen_data: dict, posts: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    seen_posts = seen_data.setdefault("posts", {})
    for post in posts:
        key = post.get("key")
        if not key:
            continue
        seen_posts[key] = {
            "title": post.get("title"),
            "source": post.get("source"),
            "url": post.get("url"),
            "fingerprint": post_fingerprint(post),
            "sent_at": now,
        }
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(seen_data, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def post_fingerprint(post: dict) -> str:
    fields = [
        post.get("title"),
        post.get("published_at"),
        post.get("application_period"),
        post.get("region_relevance"),
        post.get("target"),
        post.get("checkpoints"),
    ]
    raw = "|".join(str(field or "") for field in fields)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
