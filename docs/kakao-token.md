# 카카오 refresh_token 최초 발급 안내

이 문서는 `housing-alert-jinju`에서 카카오톡 "나에게 보내기" API를 쓰기 위해 최초 1회 `refresh_token`을 발급받는 절차입니다.

## 1. 카카오 디벨로퍼스 앱 생성

1. [Kakao Developers](https://developers.kakao.com/)에 로그인합니다.
2. `내 애플리케이션`에서 앱을 생성합니다.
3. 앱의 `REST API 키`를 복사해 `KAKAO_REST_API_KEY`로 사용합니다.
4. REST API 키에 클라이언트 시크릿을 활성화했다면 `Client Secret`도 복사해 `KAKAO_CLIENT_SECRET`으로 사용합니다.

## 2. 플랫폼과 Redirect URI 등록

1. 앱 설정에서 `플랫폼 > Web`을 추가합니다.
2. 사이트 도메인은 테스트용으로 `http://localhost`를 등록할 수 있습니다.
3. `카카오 로그인 > Redirect URI`에 예를 들어 아래 값을 등록합니다.

```text
http://localhost:8000/oauth
```

이 값을 `.env` 또는 GitHub Secret의 `KAKAO_REDIRECT_URI`에 동일하게 넣습니다.

## 3. 카카오 로그인 활성화와 동의항목 설정

1. `카카오 로그인`을 활성화합니다.
2. `동의항목`에서 `카카오톡 메시지 전송(talk_message)` 권한을 설정합니다.
3. "나에게 보내기"는 내 카카오 계정의 나와의 채팅방으로만 보냅니다.

## 4. 인증 코드 받기

아래 URL을 브라우저에 붙여넣습니다. `{REST_API_KEY}`와 `{REDIRECT_URI}`는 본인 값으로 바꿉니다.

```text
https://kauth.kakao.com/oauth/authorize?client_id={REST_API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&scope=talk_message
```

로그인과 동의를 마치면 브라우저가 등록한 Redirect URI로 이동합니다. 주소창에 다음처럼 `code`가 붙습니다.

```text
http://localhost:8000/oauth?code=받은_인증코드
```

`code=` 뒤 값을 복사합니다.

## 5. access_token / refresh_token 교환

PowerShell에서 아래 명령을 실행합니다.

```powershell
$REST_API_KEY="본인_REST_API_KEY"
$REDIRECT_URI="http://localhost:8000/oauth"
$CODE="방금_받은_code"

Invoke-RestMethod `
  -Method Post `
  -Uri "https://kauth.kakao.com/oauth/token" `
  -ContentType "application/x-www-form-urlencoded;charset=utf-8" `
  -Body @{
    grant_type="authorization_code"
    client_id=$REST_API_KEY
    redirect_uri=$REDIRECT_URI
    code=$CODE
  }
```

클라이언트 시크릿을 활성화한 REST API 키라면 아래처럼 `client_secret`도 포함합니다.

```powershell
$REST_API_KEY="본인_REST_API_KEY"
$CLIENT_SECRET="본인_CLIENT_SECRET"
$REDIRECT_URI="http://localhost:8000/oauth"
$CODE="방금_받은_code"

Invoke-RestMethod `
  -Method Post `
  -Uri "https://kauth.kakao.com/oauth/token" `
  -ContentType "application/x-www-form-urlencoded;charset=utf-8" `
  -Body @{
    grant_type="authorization_code"
    client_id=$REST_API_KEY
    client_secret=$CLIENT_SECRET
    redirect_uri=$REDIRECT_URI
    code=$CODE
  }
```

응답의 `refresh_token`을 GitHub Secret `KAKAO_REFRESH_TOKEN`에 저장합니다. `access_token`은 짧게 만료되므로 저장하지 않아도 됩니다. 이 프로젝트는 매 실행 때 `refresh_token`으로 새 `access_token`을 갱신합니다.

## 6. Product Link 웹 도메인 주의

카카오 기본 템플릿 메시지의 버튼/본문 링크는 앱 설정의 Product Link 웹 도메인에 등록된 도메인만 안정적으로 열립니다.

원문 링크 버튼을 쓰려면 아래 도메인을 등록해두는 것을 권장합니다.

```text
https://apply.lh.or.kr
https://www.myhome.go.kr
https://www.jinju.go.kr
https://young.jinju.go.kr
```

등록이 어렵거나 실패한다면 `KAKAO_WEB_LINK_URL`에 본인 GitHub 저장소, 노션 페이지, 또는 등록 가능한 고정 URL을 넣으세요. 원문 URL은 콘솔 로그에 그대로 남습니다.

## 7. 토큰 갱신 실패 시 확인

- `KAKAO_REST_API_KEY`가 REST API 키인지 확인합니다.
- 클라이언트 시크릿을 활성화했다면 `KAKAO_CLIENT_SECRET`도 설정했는지 확인합니다.
- `KAKAO_REFRESH_TOKEN`이 전체 문자열로 저장됐는지 확인합니다.
- `KAKAO_REDIRECT_URI`가 최초 발급 때 사용한 URI와 같은지 확인합니다.
- 앱 동의항목에 `talk_message`가 설정되어 있는지 확인합니다.
- refresh_token도 장기 미사용 또는 재발급 상황에서 만료될 수 있습니다. 이 경우 인증 코드 발급부터 다시 진행합니다.
