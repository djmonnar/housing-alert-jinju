from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


KST = timezone(timedelta(hours=9))


HOUSING_TIPS = [
    {
        "title": "행복주택은 공고문 자격표부터 확인",
        "body": "청년, 신혼부부, 고령자 등 공급유형마다 소득·자산·무주택 기준이 다릅니다. 제목만 보고 판단하지 말고 공고문의 공급대상 표를 먼저 확인하세요.",
        "checks": ["공급유형", "무주택 기준", "소득·자산 기준", "세대구성"],
    },
    {
        "title": "전세임대는 선정 후 집을 직접 찾아야 함",
        "body": "청년 전세임대는 당첨이 곧 입주 가능한 집 확정을 뜻하지 않습니다. 선정 후 한도, 보증부 월세 가능 여부, 권리관계, 집주인 동의 조건을 함께 확인해야 합니다.",
        "checks": ["지원한도", "권리관계", "집주인 동의", "중개 일정"],
    },
    {
        "title": "마감일보다 첫날 일정이 더 중요할 때가 있음",
        "body": "일부 임대주택 신청은 접속 지연이나 서류 준비 때문에 마감일에 몰리면 위험합니다. 관심 공고는 접수 첫날에 신청 자격과 필요서류를 정리해두는 편이 안전합니다.",
        "checks": ["접수 시작일", "공동인증서", "제출서류", "마감 시간"],
    },
    {
        "title": "청년월세지원은 주소와 계약서 기준을 먼저 봄",
        "body": "청년월세지원은 나이와 소득뿐 아니라 임대차계약서, 전입 여부, 월세 납부 증빙, 부모와의 별도 거주 같은 조건이 중요할 수 있습니다.",
        "checks": ["전입신고", "임대차계약서", "월세 납부내역", "소득 기준"],
    },
    {
        "title": "전세보증금 반환보증 보증료 지원은 선가입 여부 확인",
        "body": "보증료 지원사업은 보증보험 가입 후 납부한 보증료를 지원하는 방식인 경우가 많습니다. 신청 전에 보증기관, 가입일, 납부영수증 인정 여부를 확인하세요.",
        "checks": ["보증기관", "가입일", "납부영수증", "소득·주택 기준"],
    },
    {
        "title": "무주택 기준은 본인만 보는 게 아닐 수 있음",
        "body": "공고에 따라 본인, 배우자, 세대원, 예비배우자까지 주택 소유 여부를 확인할 수 있습니다. 세대분리 여부만으로 단정하지 말고 공고문 기준을 확인하세요.",
        "checks": ["세대원 범위", "배우자", "주택 소유 이력", "분양권"],
    },
    {
        "title": "예비입주자는 당장 입주가 아닐 수 있음",
        "body": "예비입주자 모집은 순번을 받아 공가 발생 시 입주하는 구조일 수 있습니다. 순번 유효기간과 실제 입주 예상 시점은 반드시 확인이 필요합니다.",
        "checks": ["예비순번", "유효기간", "공가 발생", "계약 안내 방식"],
    },
    {
        "title": "국민임대는 소득 분위와 자산 기준이 핵심",
        "body": "국민임대는 무주택 여부와 함께 소득, 총자산, 자동차가액 기준을 보는 경우가 많습니다. 본인 상황을 공고문의 기준금액과 비교해보세요.",
        "checks": ["월평균소득", "총자산", "자동차가액", "세대구성"],
    },
    {
        "title": "매입임대는 주택 위치와 관리비도 같이 봄",
        "body": "매입임대는 임대료만 보고 결정하기보다 위치, 교통, 관리비, 주택 상태, 계약 조건을 함께 확인하는 게 좋습니다.",
        "checks": ["주택 위치", "관리비", "계약 조건", "주택 상태"],
    },
    {
        "title": "공고문 첨부파일이 본문보다 중요할 때가 많음",
        "body": "게시글 본문은 요약이고, 실제 자격·일정·서류는 PDF나 HWP 첨부 공고문에 들어있는 경우가 많습니다. 신청 전 첨부파일을 꼭 확인하세요.",
        "checks": ["공고문 PDF", "신청서식", "제출서류", "문의처"],
    },
]


def today_kst() -> str:
    return datetime.now(KST).date().isoformat()


def get_tip_for_date(date_text: str | None = None) -> dict:
    date_text = date_text or today_kst()
    ordinal = datetime.fromisoformat(date_text).toordinal()
    return HOUSING_TIPS[ordinal % len(HOUSING_TIPS)]


def should_send_tip(path: Path, date_text: str | None = None) -> bool:
    date_text = date_text or today_kst()
    state = load_tip_state(path)
    return not state.get("sent_dates", {}).get(date_text)


def mark_tip_sent(path: Path, date_text: str | None = None) -> None:
    date_text = date_text or today_kst()
    state = load_tip_state(path)
    state.setdefault("sent_dates", {})[date_text] = {
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "title": get_tip_for_date(date_text)["title"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def load_tip_state(path: Path) -> dict:
    if not path.exists():
        return {"sent_dates": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"sent_dates": {}}
        data.setdefault("sent_dates", {})
        return data
    except (OSError, json.JSONDecodeError):
        return {"sent_dates": {}}
