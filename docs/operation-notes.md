# NCC 운영 노트

이 문서는 실제 운영 과정에서 확정된 설정, 장애 원인, 유지보수 절차를 정리한 기록입니다. README는 설치와 사용법 중심이고, 이 문서는 운영 판단과 트러블슈팅 맥락을 보존하는 용도입니다.

## 최종 운영 구조

- 서버는 GUI 없는 Linux 환경에서 실행한다.
- Firefox는 `xvfb-run`으로 가상 디스플레이에서 실행한다.
- 네이버 로그인은 계정별 Firefox 프로필 세션을 우선 사용한다.
- JSON 쿠키 파일은 보조 수단이다.
- 비밀번호 직접 로그인은 기본 비활성화한다.

운영 실행 예시:

```bash
cd /free/home/naver/ncc

FIREFOX_PROFILE_ROOT=/free/home/naver/firefox-profiles \
MOZ_DISABLE_CONTENT_SANDBOX=1 \
xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
```

crontab 예시:

```cron
15 */1 * * * cd /free/home/naver/ncc && FIREFOX_PROFILE_ROOT=/free/home/naver/firefox-profiles MOZ_DISABLE_CONTENT_SANDBOX=1 /usr/bin/xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
```

정상 로그인 로그 예시:

```text
계정별 Firefox 프로필 사용: <account> -> /free/home/naver/firefox-profiles/<account>
Firefox 프로필 로그인 성공: <account>
```

## 계정별 Firefox 프로필

두 개 이상의 계정을 운영할 때는 계정별로 Firefox 프로필 디렉토리를 분리한다.

```text
/free/home/naver/firefox-profiles/<account-1>
/free/home/naver/firefox-profiles/<account-2>
```

`<account-1>`, `<account-2>`는 `config.py`의 `naver_login_info` 키와 같은 이름이어야 한다.

최초 1회 VNC에서 각 프로필을 열어 네이버에 로그인한다.

```bash
vncpasswd
vncserver :1 -geometry 1280x900 -depth 24

DISPLAY=:1 MOZ_DISABLE_CONTENT_SANDBOX=1 firefox --no-remote \
  --profile /free/home/naver/firefox-profiles/<account> \
  https://www.naver.com

vncserver -kill :1
```

주의사항:

- 로그인 후 Firefox 메뉴에서 정상 종료해야 세션이 프로필에 저장된다.
- cron 실행 시간에는 VNC에서 같은 프로필을 열어두지 않는다.
- 같은 프로필을 동시에 열면 프로필 잠금이나 세션 저장 문제가 생길 수 있다.

## 인증 흐름

현재 인증 우선순위는 다음과 같다.

1. 계정별 Firefox 프로필 세션 확인
2. `naver_cookies/<account>.json` 쿠키 적용
3. `ALLOW_PASSWORD_LOGIN=1`일 때만 pyautogui 직접 로그인

운영 기본값은 `ALLOW_PASSWORD_LOGIN=0`이다. 쿠키나 프로필이 실패했을 때 비밀번호 로그인을 반복하면 CAPTCHA가 쉽게 발생하므로 자동 운영에서는 꺼두는 쪽이 안전하다.

JSON 쿠키 저장 시에는 `NID_AUT`, `NID_SES`가 있는 경우에만 저장한다. 캠페인 마지막 페이지가 네이버가 아닌 도메인일 때 광고 도메인 쿠키 몇 개로 인증 쿠키 파일을 덮어쓰는 문제를 막기 위한 보호 장치다.

## VNC와 xvfb 역할

VNC는 최초 로그인용 화면을 사람이 보기 위한 도구다.

```bash
vncserver :1 -geometry 1280x900 -depth 24
```

xvfb는 cron 자동 실행 때 Firefox가 사용할 가상 디스플레이다.

```bash
xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
```

VNC는 로그인 세팅이 끝나면 꺼도 된다. 자동 실행은 VNC가 아니라 `xvfb-run`으로 수행한다.

## Firefox 프로필 캐시 관리

`firefox-profiles/<account>/cache2`는 Firefox 디스크 캐시다. 로그인 세션 자체는 주로 `cookies.sqlite`, `storage/`, `sessionstore` 계열에 저장된다.

Firefox가 종료된 상태라면 `cache2`는 삭제해도 보통 로그인 유지에 영향이 없다.

용량 확인:

```bash
du -sh /free/home/naver/firefox-profiles/*/cache2
du -sh /free/home/naver/firefox-profiles/*
```

수동 정리:

```bash
find /free/home/naver/firefox-profiles -mindepth 2 -maxdepth 2 -type d -name cache2 -exec rm -rf {} +
```

자동 정리 crontab 예시:

```cron
30 4 * * * find /free/home/naver/firefox-profiles -mindepth 2 -maxdepth 2 -type d -name cache2 -exec rm -rf {} +
```

## 루리웹 접근 실패 판단

서버에서 루리웹 접근이 반복적으로 실패했다.

대표 증상:

```text
Connection to bbs.ruliweb.com timed out. (connect timeout=10)
```

확인 결과:

- DNS는 정상적으로 해석된다.
- `curl`과 `nc`가 `103.24.8.4:443` TCP 연결 단계에서 timeout 난다.
- 로컬이나 다른 클라우드에서는 접속되는 경우가 있다.

판단:

- 코드, User-Agent, requests timeout 문제가 아니다.
- 서버 네트워크에서 루리웹 IP로 TCP 연결이 도달하지 않는 문제다.
- 특정 클라우드 리전, ASN, IP 대역, 라우팅 경로, 상대방 방화벽 정책 중 하나로 보는 것이 타당하다.

운영 결정:

- 현재 서버에서는 루리웹 수집을 제외한다.
- `config.py`의 루리웹 항목을 주석 처리하면 실행 시간이 줄고 timeout 로그도 사라진다.

## 게시판 목록 수집 선택자

게시판 목록 수집은 `config.py`의 사이트별 설정을 사용한다. 기존에는 `tag`와 `class`만으로 게시글 후보를 찾았지만, 다모앙처럼 목록 CSS 클래스가 바뀌는 사이트에서는 0개 수집이 발생할 수 있다.

현재 수집 코드는 `path_prefix`가 있으면 게시글 URL 경로도 함께 후보로 사용한다.

예시:

```python
"https://damoang.net/economy": {
    "tag": "a",
    "class": None,
    "path_prefix": "/economy/",
    "domain": "damoang.net"
}
```

수집 로그에는 다음 진단 정보가 남는다.

```text
게시글 후보 분석: <site> - 후보 <n>개, 키워드 <n>개, 링크 <n>개
```

판단 기준:

- 후보 0개: 선택자 또는 `path_prefix`가 현재 HTML과 맞지 않는다.
- 후보는 있는데 키워드 0개: 목록에 네이버/포인트 관련 글이 없거나 키워드 범위가 좁다.
- 키워드는 있는데 링크 0개: 링크 추출 로직이나 URL 경로 조건을 확인한다.

## GitHub Actions와 Ruff

이 저장소는 GitHub Actions에서 Ruff lint를 실행한다. push 후 Ruff workflow 실패 메일이 올 수 있다.

확인 명령:

```bash
gh repo set-default CjHayato/ncc
gh run list --branch dev --limit 5
gh run view --log-failed
```

발생했던 대표 이슈:

- 사용하지 않는 import
- bare `except`
- 문서 커밋 후 Actions 상태 확인

## 문서와 민감 정보

README와 아키텍처 문서에는 실제 계정명, 서버 IP, 비밀번호, 쿠키 값을 넣지 않는다.

프로필 예시는 다음처럼 일반화한다.

```text
account-1
account-2
<account>
```

과거 README 커밋에 실제 계정명이 들어간 적이 있어 `dev` 브랜치 히스토리를 한 번 재작성했다. 이후 문서에는 실제 계정명을 쓰지 않는 원칙을 유지한다.

## 서버 업데이트 주의사항

`dev` 브랜치 히스토리를 재작성한 적이 있으므로 서버에서 `git pull --ff-only origin dev`가 실패할 수 있다.

서버 로컬 변경을 보존해야 할 때:

```bash
cp config.py config.py.server.bak
git fetch origin
git reset --hard origin/dev
cp config.py.server.bak config.py
```

주의:

- `git reset --hard`는 추적 중인 파일의 로컬 변경을 날린다.
- 서버의 `config.py`는 먼저 백업한다.
- `naver_cookies/`, Firefox 프로필, 로그 파일은 보통 `.gitignore` 대상이라 영향이 없다.

## 운영 체크리스트

정기적으로 확인할 로그:

```bash
tail -n 100 /free/home/naver/ncc/scraper.log
```

정상 포인트:

```text
게시판 스크래핑 시작
캠페인 URL 추출 완료
계정별 Firefox 프로필 사용
Firefox 프로필 로그인 성공
[account] 방문 완료
스크래퍼 정상 종료
```

문제 신호:

```text
쿠키 로그인 실패, 직접 로그인 비활성화됨
Firefox 드라이버 생성 실패
캡차 감지
사이트 접근 최종 실패
```

대응 기준:

- 프로필 로그인 실패: VNC로 해당 계정 프로필을 열어 로그인 유지 확인
- Firefox 실행 실패: `xvfb-run`, Firefox 설치, 프로필 잠금 확인
- 특정 사이트 timeout: 서버에서 `curl`, `nc`, `mtr`로 네트워크 도달성 확인
- 캐시 증가: Firefox 종료 상태에서 `cache2` 정리
