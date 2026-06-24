import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SEEN_POSTS_PATH = DATA_DIR / "seen_posts.json"
SEEN_BUSINESS_POSTS_PATH = DATA_DIR / "seen_business_posts.json"
TIP_STATE_PATH = DATA_DIR / "tip_state.json"

load_dotenv(BASE_DIR / ".env")


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    kakao_rest_api_key: str | None = os.getenv("KAKAO_REST_API_KEY")
    kakao_client_secret: str | None = os.getenv("KAKAO_CLIENT_SECRET")
    kakao_refresh_token: str | None = os.getenv("KAKAO_REFRESH_TOKEN")
    kakao_redirect_uri: str | None = os.getenv("KAKAO_REDIRECT_URI")
    kakao_access_token: str | None = os.getenv("KAKAO_ACCESS_TOKEN")
    kakao_web_link_url: str | None = os.getenv("KAKAO_WEB_LINK_URL")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    dry_run: bool = _truthy(os.getenv("DRY_RUN"), default=False)
    send_daily_tip: bool = _truthy(os.getenv("SEND_DAILY_TIP"), default=False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    max_alert_posts: int = int(os.getenv("MAX_ALERT_POSTS", "5"))
    max_business_alert_posts: int = int(os.getenv("MAX_BUSINESS_ALERT_POSTS", "3"))


settings = Settings()
