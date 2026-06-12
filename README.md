# housing-alert-jinju

진주 지역 청년/무주택자 주거 공고를 매일 확인하고, 새 공고가 있으면 카카오톡 "나에게 보내기"로 알림을 보내는 Python 자동화 프로젝트입니다.

공식/공공 사이트를 우선 수집하고, 실제 페이지에서 확인된 제목·날짜·링크를 기반으로만 메시지를 만듭니다. 명확하지 않은 접수기간, 대상, 자격요건은 `확인 필요`로 표시합니다.

## 수집 대상

- LH 청약플러스: 임대주택 공고/모집
- 마이홈포털: 임대주택 입주자 모집공고
- 진주시청: 고시/공고, 새소식, 주거·복지 관련 게시판
- 진주시 청년온라인플랫폼: 청년 정책, 주거지원, 새소식

## 동작 방식

1. 사이트별 스크래퍼가 공고 후보를 수집합니다.
2. 핵심 키워드와 진주/경남 관련성을 함께 확인합니다.
3. 마감된 공고, 광고성 글, 출처가 불명확한 글은 제외합니다.
4. URL과 제목 기준으로 중복을 제거합니다.
5. `data/seen_posts.json`에 이미 발송한 공고가 있으면 다시 보내지 않습니다.
6. 같은 URL이라도 제목, 게시일, 접수기간, 체크포인트가 바뀌면 변경사항으로 다시 알립니다.
7. 새 공고가 있으면 최대 5건까지 카카오톡 메시지를 보냅니다.
8. 발송 성공 후에만 `seen_posts.json`에 저장합니다.

새 공고가 없더라도 `SEND_DAILY_TIP=true`이면 행복주택, 청년주택, 임대주택 관련 오늘의 주거 팁을 하루 1회 보냅니다. 이 기능을 끄려면 `.env` 또는 GitHub Actions 변수에 `SEND_DAILY_TIP=false`를 설정하세요.

## 설치

```bash
git clone <your-repo-url>
cd housing-alert-jinju
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell에서는 다음처럼 실행할 수 있습니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## .env 예시

```dotenv
KAKAO_REST_API_KEY=
KAKAO_CLIENT_SECRET=
KAKAO_REFRESH_TOKEN=
KAKAO_REDIRECT_URI=
KAKAO_WEB_LINK_URL=

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini

DRY_RUN=true
SEND_DAILY_TIP=true
LOG_LEVEL=INFO
```

`OPENAI_API_KEY`는 선택사항입니다. 값이 있으면 새 공고 체크포인트를 AI로 더 짧게 정리하고, 없으면 규칙 기반 템플릿을 씁니다. AI 사용 시에도 프롬프트는 원문에 없는 사실을 만들지 않도록 제한되어 있습니다.

## 로컬 실행

먼저 발송 없이 확인합니다.

```bash
DRY_RUN=true python main.py
```

PowerShell:

```powershell
$env:DRY_RUN="true"
python main.py
```

실제 발송:

```bash
DRY_RUN=false python main.py
```

## GitHub Secrets 설정

GitHub 저장소에서 `Settings > Secrets and variables > Actions`로 이동해 아래 Secret을 추가합니다.

- `KAKAO_REST_API_KEY`
- `KAKAO_CLIENT_SECRET` 클라이언트 시크릿을 활성화한 경우
- `KAKAO_REFRESH_TOKEN`
- `KAKAO_REDIRECT_URI`
- `KAKAO_WEB_LINK_URL` 선택
- `OPENAI_API_KEY` 선택

변수로 아래 값을 둘 수 있습니다.

- `DRY_RUN`: 테스트 중이면 `true`, 실제 운영이면 `false`
- `SEND_DAILY_TIP`: 새 공고가 없어도 하루 1회 주거 팁을 받으려면 `true`
- `OPENAI_MODEL`: 기본값은 `gpt-4.1-mini`

API 키, 토큰, 개인정보는 코드에 넣지 않습니다.

## 카카오 디벨로퍼스 설정

자세한 최초 토큰 발급 절차는 [docs/kakao-token.md](docs/kakao-token.md)를 보세요.

필수 요약:

1. Kakao Developers에서 앱 생성
2. REST API 키 확인
3. 클라이언트 시크릿을 활성화했다면 Client Secret 확인
4. 카카오 로그인 활성화
5. Redirect URI 등록
6. 동의항목에서 `talk_message` 설정
7. 인증 코드로 `refresh_token` 발급
8. GitHub Secret에 저장

카카오 기본 템플릿의 링크 버튼은 Product Link 웹 도메인 등록 조건을 탑니다. 원문 버튼을 바로 열려면 LH, 마이홈, 진주시청, 진주시 청년온라인플랫폼 도메인을 앱 설정에 등록하세요. 어렵다면 `KAKAO_WEB_LINK_URL`에 본인이 등록 가능한 고정 URL을 넣으세요.

## GitHub Actions

워크플로 파일은 `.github/workflows/daily.yml`입니다.

- 매일 오전 9시 KST 실행
- UTC 기준 `0 0 * * *`
- `workflow_dispatch`로 수동 실행 가능
- 실행 후 새 공고가 발송되면 `data/seen_posts.json`을 커밋해 중복 발송을 막습니다.
- 오늘의 주거 팁 발송 여부는 `data/tip_state.json`에 저장합니다.

## 로그 확인

GitHub Actions의 실행 상세 화면에서 다음을 확인하세요.

- 사이트별 수집 건수
- 네트워크 오류 여부
- 후보 공고 수
- 새 공고 수
- 카카오 토큰 갱신 실패 여부
- 카카오 발송 응답 코드와 본문

사이트 하나가 실패해도 전체 프로그램은 중단하지 않고 나머지 사이트를 계속 확인합니다.

## 필터 기준

핵심 키워드 중 하나 이상이 포함되고, 동시에 진주/경남/진주시 관련성이 있어야 후보가 됩니다.

주요 키워드:

- 진주, 진주시, 경남
- 행복주택, 청년주택, 전세임대, 매입임대, 국민임대, 공공임대, 임대주택
- 무주택, 신혼부부
- 청년월세, 월세지원
- 전세보증금, 보증료 지원, 반환보증

제외 기준:

- 명확히 마감된 공고
- 진주와 무관한 타지역 단독 공고
- 부동산 광고성 글
- 블로그/카페 홍보글
- 출처가 불명확한 글

## 카카오톡보다 쉬운 대안

개인 자동화라면 카카오톡보다 아래가 훨씬 쉽습니다.

- Telegram Bot: 토큰과 채팅 ID만 있으면 발송 가능, GitHub Actions와 궁합이 좋음
- Discord Webhook: 웹훅 URL 하나로 끝나 가장 단순함
- Slack Incoming Webhook: 워크스페이스를 쓰고 있다면 설정이 간단함
- 이메일 SMTP: Gmail 앱 비밀번호 또는 SendGrid/Resend 같은 서비스를 사용

그래도 한국에서 매일 보는 알림 채널이 카카오톡이라면 이 프로젝트처럼 refresh_token 기반으로 운영할 수 있습니다.
