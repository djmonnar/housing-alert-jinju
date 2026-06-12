import json
import logging

import requests

from config import settings


logger = logging.getLogger(__name__)

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


class KakaoNotifier:
    def __init__(self) -> None:
        self.rest_api_key = settings.kakao_rest_api_key
        self.client_secret = settings.kakao_client_secret
        self.refresh_token = settings.kakao_refresh_token
        self.redirect_uri = settings.kakao_redirect_uri
        self.access_token = settings.kakao_access_token

    def send_feed(self, template_object: dict) -> bool:
        access_token = self.access_token or self.refresh_access_token()
        if not access_token:
            logger.error("카카오 access_token을 준비하지 못했습니다.")
            return False

        try:
            response = requests.post(
                SEND_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
                },
                data={"template_object": json.dumps(template_object, ensure_ascii=False)},
                timeout=settings.request_timeout,
            )
            if response.status_code == 200 and response.json().get("result_code") == 0:
                logger.info("카카오톡 알림 발송 성공")
                return True
            logger.error("카카오톡 알림 발송 실패: %s %s", response.status_code, response.text)
            return False
        except requests.RequestException as exc:
            logger.error("카카오톡 알림 요청 실패: %s", exc)
            return False

    def refresh_access_token(self) -> str | None:
        if not self.rest_api_key or not self.refresh_token:
            logger.error("KAKAO_REST_API_KEY 또는 KAKAO_REFRESH_TOKEN이 없습니다.")
            return None

        data = {
            "grant_type": "refresh_token",
            "client_id": self.rest_api_key,
            "refresh_token": self.refresh_token,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri

        try:
            response = requests.post(TOKEN_URL, data=data, timeout=settings.request_timeout)
            if response.status_code != 200:
                logger.error("카카오 access_token 갱신 실패: %s %s", response.status_code, response.text)
                return None
            payload = response.json()
            access_token = payload.get("access_token")
            if payload.get("refresh_token"):
                logger.warning("새 refresh_token이 발급되었습니다. GitHub Secret을 갱신하세요.")
            self.access_token = access_token
            return access_token
        except requests.RequestException as exc:
            logger.error("카카오 토큰 갱신 요청 실패: %s", exc)
            return None
