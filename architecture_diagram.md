# NCC 아키텍처 다이어그램

이 문서는 현재 `run_firefox.py` 기준의 실행 구조를 설명합니다. 핵심 인증 방식은 계정별 Firefox 프로필 세션을 우선 사용하고, 보조 수단으로 `naver_cookies/<account>.json` 쿠키를 적용하는 방식입니다.

## 전체 실행 플로우

```mermaid
graph TD
    A[프로그램 시작] --> B[avoid_overlap: PID 락]
    B --> C[setup_logging: 로그 초기화]
    C --> D[NaverCoinScraper 생성]

    D --> E[초기화]
    E --> E1[작업 디렉토리 설정]
    E --> E2[visited_urls.txt / break-point.html / naver_cookies 경로 설정]
    E --> E3[config.py 및 환경변수 로드]
    E --> E4[휴면 파일 검사]
    E --> E5[방문 기록 로드]

    E --> F[post_scrap 실행]
    F --> G[게시판 목록 수집]
    G --> H[네이버 관련 게시글 필터링]
    H --> I[게시글 본문에서 캠페인 URL 추출]
    I --> J{캠페인 링크 있음?}

    J -->|No| Z[방문 기록 저장 후 종료]
    J -->|Yes| K[get_coin 실행]
    K --> L[계정별 Firefox 실행]
    L --> M[프로필/쿠키 기반 로그인 확인]
    M --> N{로그인 성공?}
    N -->|No| O[해당 계정 건너뜀]
    N -->|Yes| P[캠페인 링크 방문]
    P --> Q[포인트 버튼 처리 및 체류]
    Q --> R[네이버 쿠키 갱신 저장]
    R --> Z
```

## 인증 및 세션 플로우

```mermaid
graph TD
    A["계정 처리 시작"] --> B["Firefox 드라이버 생성"]
    B --> C{"계정별 프로필 루트 설정"}
    C -->|"Yes"| D["계정별 프로필 사용"]
    C -->|"No"| E{"단일 프로필 경로 설정"}
    E -->|"Yes"| F["단일 지정 프로필 사용"]
    E -->|"No"| G["임시 또는 기본 프로필 사용"]

    D --> H["프로필 세션 확인"]
    F --> H
    G --> H

    H -->|"성공"| I["프로필 로그인 성공"]
    I --> J["네이버 인증 쿠키 갱신"]
    J --> K["캠페인 방문"]

    H -->|"실패"| L["JSON 쿠키 적용"]
    L --> M{"쿠키 로그인 성공"}
    M -->|"Yes"| J
    M -->|"No"| N{"직접 로그인 허용"}
    N -->|"No"| O["계정 건너뜀"]
    N -->|"Yes"| P["직접 로그인 시도"]
    P --> Q{"로그인 성공"}
    Q -->|"Yes"| J
    Q -->|"No"| O
```

## 서버 운영 구조

```mermaid
flowchart LR
    subgraph Server["서버"]
        A["crontab"]
        B["xvfb 실행"]
        C["스크래퍼"]
        D["계정 1 Firefox 프로필"]
        E["계정 2 Firefox 프로필"]
        F["JSON 쿠키 파일"]
        G["로그 파일"]
    end

    subgraph Setup["최초 설정"]
        H["VNC 서버"]
        I["Firefox 수동 로그인"]
    end

    H --> I
    I --> D
    I --> E
    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
```

서버 실행 예시는 다음 형태입니다.

```bash
FIREFOX_PROFILE_ROOT=/free/home/naver/firefox-profiles \
MOZ_DISABLE_CONTENT_SANDBOX=1 \
xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
```

## 클래스 구조

```mermaid
classDiagram
    class NaverCoinScraper {
        -logger: Logger
        -work_dir: Path
        -visited_urls_file: Path
        -break_point_file: Path
        -cookies_dir: Path
        -temp_profile_dirs: List[Path]
        -gecko_path: str
        -delay_hours: int
        -min_dwell_time: int
        -request_timeout: tuple
        -request_max_retries: int
        -allow_password_login: bool
        -request_ua: str
        -firefox_ua: str
        -visited_urls: Set[str]

        +post_scrap()
        +campaign_scrap(posts)
        +get_coin(campaign_links)
        +click_point_and_dwell(driver, dwell_seconds)
        +dwell_and_scroll(driver, min_seconds)
        -_get_with_retries(url, purpose)
        -_get_naver_accounts()
        -_prepare_firefox_profile(account_id)
        -_create_firefox_driver(account_id)
        -_is_logged_in(driver)
        -_load_cookies(account_id)
        -_apply_cookies(driver, account_id)
        -_save_cookies(driver, account_id)
        -_collect_naver_cookies(driver)
        -_has_required_auth_cookies(cookies)
        -_login_naver(driver, account_id, password)
        -_visit_campaign_links(driver, campaign_links, account_id)
        -_process_campaign_site(driver)
        -_cleanup_driver(driver)
    }

    class Config {
        +naver_login_info: Dict
        +GECKODRIVER_PATH: str
        +DELAY_HOURS: int
        +MIN_DWELL_TIME: int
        +REQUEST_USER_AGENT: str
        +FIREFOX_USER_AGENT: str
        +SCRAPING_SITES: Dict
    }

    NaverCoinScraper --> Config : imports
```

## 데이터 플로우

```mermaid
flowchart LR
    A[SCRAPING_SITES] --> B[_collect_posts_from_sites]
    B --> C[_collect_posts_from_site]
    C --> D[_is_naver_related_post]
    D --> E[campaign_scrap]
    E --> F[_extract_url_candidates]
    F --> G[_filter_campaign_urls]
    G --> H[get_coin]
    H --> I[Firefox 프로필/쿠키 로그인]
    I --> J[_visit_campaign_links]
    J --> K[_process_campaign_site]
    K --> L[방문 기록 저장]

    subgraph Files[파일 시스템]
        M[config.py]
        N[visited_urls.txt]
        O[scraper.log]
        P[naver_cookies/account.json]
        Q[login_screenshots/]
        R[break-point.html]
    end

    M --> A
    L --> N
    H --> P
    H --> Q
    O --> H
    R --> H
```

## 게시글 수집 플로우

```mermaid
sequenceDiagram
    participant NCS as NaverCoinScraper
    participant Site as 커뮤니티 사이트
    participant Parser as BeautifulSoup
    participant Logger as Logger

    NCS->>NCS: _collect_posts_from_sites()

    loop config.SCRAPING_SITES 순회
        NCS->>Site: _get_with_retries(site_url, "사이트 접근")
        alt 요청 성공
            Site-->>NCS: HTML
            NCS->>Parser: 목록 HTML 파싱
            Parser-->>NCS: 후보 요소
            NCS->>NCS: _extract_post_url()
            NCS->>NCS: _is_naver_related_post()
        else 3회 실패
            NCS->>Logger: 사이트 접근 최종 실패
            NCS->>NCS: 다음 사이트로 진행
        end
    end

    NCS->>NCS: campaign_scrap(posts)
```

## 캠페인 처리 플로우

```mermaid
graph TD
    A[캠페인 URL 방문] --> B{도메인/경로 판별}
    B -->|campaign2.naver.com click-point| C[네이버 포인트 캠페인]
    B -->|ofw.adison.co naverpay ads| D[Adison 광고]
    B -->|기타| E[일반 캠페인]

    C --> C1[포인트 버튼 selector 탐색]
    C1 --> C2{버튼 있음?}
    C2 -->|Yes| C3[클릭 및 URL 변경 대기]
    C2 -->|No| C4[이미 적립/기간 만료로 처리]

    C3 --> F[dwell_and_scroll]
    C4 --> F
    D --> F
    E --> F

    F --> G[자연스러운 스크롤]
    G --> H[PAGE_DOWN/PAGE_UP 입력]
    H --> I[최소 체류 시간 보장]
    I --> J[다음 링크]
```

## 에러 처리 및 보호 장치

```mermaid
graph TD
    A[프로그램 시작] --> B{PID 락 획득?}
    B -->|No| C[이미 실행 중, 종료]
    B -->|Yes| D{break-point.html 존재?}

    D -->|Yes| E{DELAY_HOURS 경과?}
    E -->|No| F[휴면 중, 종료]
    E -->|Yes| G[break-point.html 삭제]
    D -->|No| H[정상 진행]
    G --> H

    H --> I[게시글/캠페인 수집]
    I --> J[계정별 로그인 처리]
    J --> K{CAPTCHA 감지?}
    K -->|Yes| L[스크린샷 저장]
    K -->|No| M[캠페인 방문]

    J --> N{쿠키/프로필 로그인 실패?}
    N -->|ALLOW_PASSWORD_LOGIN=0| O[직접 로그인 생략]
    N -->|ALLOW_PASSWORD_LOGIN=1| P[pyautogui 직접 로그인 시도]

    M --> Q[방문 기록 저장]
    O --> Q
    L --> Q
```

## 주요 운영 포인트

- `FIREFOX_PROFILE_ROOT`가 설정되면 `FIREFOX_PROFILE_ROOT/<account_id>` 프로필을 계정별로 사용합니다.
- Firefox 프로필 세션이 가장 먼저 확인됩니다. 성공하면 JSON 쿠키 주입은 수행하지 않습니다.
- JSON 쿠키는 보조 수단입니다. `NID_AUT`, `NID_SES`가 없는 쿠키는 저장하지 않아 기존 인증 쿠키 파일을 덮어쓰지 않습니다.
- `ALLOW_PASSWORD_LOGIN` 기본값은 `0`입니다. 쿠키/프로필 로그인이 실패해도 직접 비밀번호 로그인으로 넘어가지 않아 CAPTCHA 루프를 줄입니다.
- GUI 없는 서버에서는 `xvfb-run`으로 자동 실행하고, 최초 프로필 로그인은 VNC에서 수행합니다.
- Cron 실행 시간에는 VNC에서 같은 Firefox 프로필을 열어두면 안 됩니다. 프로필 잠금 때문에 Firefox 실행이 실패하거나 세션 저장이 꼬일 수 있습니다.
