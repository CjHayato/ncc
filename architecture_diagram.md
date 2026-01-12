# NCC (네이버 포인트 스크래퍼) 아키텍처 다이어그램

## 전체 시스템 플로우

```mermaid
graph TD
    A[프로그램 시작] --> B[avoid_overlap - PID 락 체크]
    B --> C[setup_logging - 로깅 시스템 초기화]
    C --> D[NaverCoinScraper 인스턴스 생성]
    
    D --> E[초기화 과정]
    E --> E1[작업 디렉토리 설정]
    E --> E2[파일 경로 설정]
    E --> E3[config.py 설정 로드]
    E --> E4[휴면 파일 검사]
    E --> E5[방문 기록 로드]
    
    E --> F[post_scrap 메인 실행]
    
    F --> G[게시판 스크래핑]
    G --> G1[다모앙]
    G --> G2[클리앙]
    G --> G3[뽐뿌]
    G --> G4[루리웹]
    
    G1 --> H[게시글 수집]
    G2 --> H
    G3 --> H
    G4 --> H
    
    H --> I[캠페인 URL 추출]
    I --> J{캠페인 링크 발견?}
    
    J -->|Yes| K[Firefox 자동화 시작]
    J -->|No| P[방문 기록 저장]
    
    K --> L[네이버 계정별 처리]
    L --> M[Firefox 드라이버 생성]
    M --> N[네이버 로그인]
    N --> O[캠페인 링크 방문]
    O --> O1[포인트 받기 클릭]
    O --> O2[자연스러운 스크롤]
    O --> O3[체류 시간 대기]
    
    O --> P[방문 기록 저장]
    P --> Q[프로그램 종료]
```

## 클래스 구조 다이어그램

```mermaid
classDiagram
    class NaverCoinScraper {
        -logger: Logger
        -work_dir: Path
        -visited_urls_file: Path
        -break_point_file: Path
        -gecko_path: str
        -delay_hours: int
        -min_dwell_time: int
        -request_ua: str
        -firefox_ua: str
        -visited_urls: Set[str]
        
        +__init__()
        +post_scrap()
        +get_coin(campaign_links)
        +campaign_scrap(posts)
        +dwell_and_scroll(driver, min_seconds)
        -_get_naver_accounts()
        -_check_break_point()
        -_load_visited_urls()
        -_save_visited_urls()
        -_create_break_point(reason)
        -_collect_posts_from_sites()
        -_collect_posts_from_site(site_url, site_config)
        -_extract_url_candidates(html_content, base_url)
        -_filter_campaign_urls(url_candidates)
        -_create_firefox_driver()
        -_login_naver(driver, account_id, password)
        -_visit_campaign_links(driver, campaign_links, account_id)
        -_handle_alert(driver)
        -_process_campaign_site(driver)
        -_cleanup_driver(driver)
        -_perform_natural_scrolling(driver, scrollable_height, viewport_height)
        -_extract_post_url(element, base_url, hostname)
        -_is_naver_related_post(element)
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
    
    NaverCoinScraper --> Config : uses
```

## 데이터 플로우 다이어그램

```mermaid
flowchart LR
    A[커뮤니티 사이트들] --> B[게시글 수집]
    B --> C[네이버 관련 게시글 필터링]
    C --> D[게시글 내용 분석]
    D --> E[캠페인 URL 추출]
    E --> F[네이버/Adison URL 필터링]
    F --> G[Firefox 자동화]
    G --> H[네이버 로그인]
    H --> I[캠페인 사이트 방문]
    I --> J[포인트 적립]
    J --> K[방문 기록 저장]
    
    subgraph "파일 시스템"
        L[visited_urls.txt]
        M[scraper.log]
        N[break-point.html]
        O[config.py]
    end
    
    K --> L
    G --> M
    F --> N
    B --> O
```

## 사이트별 처리 플로우

```mermaid
graph TD
    A[캠페인 링크 방문] --> B{사이트 유형 판별}
    
    B -->|campaign2.naver.com| C[네이버 포인트 캠페인]
    B -->|ofw.adison.co| D[Adison 광고]
    B -->|기타| E[일반 사이트]
    
    C --> C1[포인트 받기 버튼 클릭]
    C1 --> C2[페이지 이동 대기]
    C2 --> F[자연스러운 체류]
    
    D --> F
    E --> F
    
    F --> F1[페이지 스크롤]
    F1 --> F2[키보드 입력 시뮬레이션]
    F2 --> F3[최소 체류 시간 보장]
    F3 --> G[다음 링크로 이동]
```

## 에러 처리 및 보안 플로우

```mermaid
graph TD
    A[프로그램 시작] --> B{PID 락 체크}
    B -->|이미 실행 중| C[프로그램 종료]
    B -->|실행 가능| D{휴면 파일 존재?}
    
    D -->|Yes| E{휴면 시간 만료?}
    D -->|No| F[정상 실행]
    
    E -->|No| G[휴면 중 - 프로그램 종료]
    E -->|Yes| H[휴면 파일 삭제]
    H --> F
    
    F --> I[스크래핑 실행]
    I --> J{보안 감지?}
    J -->|Yes| K[휴면 파일 생성]
    J -->|No| L[정상 완료]
    
    K --> M[48시간 휴면]
```

이 다이어그램들은 코드의 전체적인 구조와 실행 흐름을 시각적으로 보여줍니다. 각 다이어그램은 다른 관점에서 시스템을 설명합니다:

1. **전체 시스템 플로우**: 프로그램의 전체 실행 순서
2. **클래스 구조**: 객체지향 설계 구조
3. **데이터 플로우**: 데이터가 어떻게 처리되는지
4. **사이트별 처리**: 각 캠페인 사이트별 처리 방식
5. **에러 처리**: 보안 및 예외 상황 대응

필요하시면 특정 부분을 더 자세히 설명하거나 다른 관점의 다이어그램도 만들어드릴 수 있습니다!

## 시퀀스 다이어그램

### 1. 전체 실행 시퀀스

```mermaid
sequenceDiagram
    participant Main as main()
    participant AO as avoid_overlap()
    participant SL as setup_logging()
    participant NCS as NaverCoinScraper
    participant Config as config.py
    participant FS as FileSystem
    participant Sites as 커뮤니티사이트들
    participant Firefox as Firefox Driver
    participant Naver as 네이버

    Main->>AO: PID 락 체크
    AO->>FS: PID 파일 생성/확인
    AO-->>Main: 실행 허가
    
    Main->>SL: 로깅 시스템 초기화
    SL->>FS: scraper.log 파일 생성
    SL-->>Main: Logger 반환
    
    Main->>NCS: 인스턴스 생성
    NCS->>Config: 설정 로드
    Config-->>NCS: 설정값 반환
    NCS->>FS: 휴면 파일 검사
    NCS->>FS: 방문 기록 로드
    FS-->>NCS: visited_urls.txt
    NCS-->>Main: 초기화 완료
    
    Main->>NCS: post_scrap() 실행
    NCS->>NCS: _collect_posts_from_sites()
    
    loop 각 커뮤니티 사이트
        NCS->>Sites: HTTP 요청
        Sites-->>NCS: HTML 응답
        NCS->>NCS: 네이버 관련 게시글 필터링
    end
    
    NCS->>NCS: campaign_scrap(posts)
    
    loop 각 게시글
        NCS->>Sites: 게시글 내용 요청
        Sites-->>NCS: 게시글 HTML
        NCS->>NCS: 캠페인 URL 추출
    end
    
    alt 캠페인 링크 발견됨
        NCS->>NCS: get_coin(campaign_links)
        NCS->>NCS: _get_naver_accounts()
        NCS->>Config: 계정 정보 요청
        Config-->>NCS: 네이버 계정들
        
        loop 각 네이버 계정
            NCS->>NCS: _create_firefox_driver()
            NCS->>Firefox: WebDriver 생성
            Firefox-->>NCS: Driver 인스턴스
            
            NCS->>Firefox: 네이버 로그인 페이지 이동
            NCS->>Firefox: 계정 정보 입력
            Firefox->>Naver: 로그인 요청
            Naver-->>Firefox: 로그인 성공
            
            loop 각 캠페인 링크
                NCS->>Firefox: 캠페인 페이지 이동
                Firefox->>Naver: 페이지 요청
                Naver-->>Firefox: 캠페인 페이지
                
                alt 네이버 포인트 캠페인
                    NCS->>Firefox: 포인트 받기 버튼 클릭
                    Firefox->>Naver: 포인트 적립 요청
                    Naver-->>Firefox: 적립 완료
                end
                
                NCS->>Firefox: 자연스러운 스크롤
                NCS->>NCS: 체류 시간 대기
            end
            
            NCS->>Firefox: 드라이버 종료
        end
    end
    
    NCS->>FS: 방문 기록 저장
    NCS-->>Main: 실행 완료
    Main->>AO: PID 파일 정리
```

### 2. 게시글 스크래핑 시퀀스

```mermaid
sequenceDiagram
    participant NCS as NaverCoinScraper
    participant Damoang as 다모앙
    participant Clien as 클리앙
    participant Ppomppu as 뽐뿌
    participant Ruliweb as 루리웹
    participant Parser as HTML Parser

    NCS->>NCS: _collect_posts_from_sites() 시작
    
    par 다모앙 스크래핑
        NCS->>Damoang: GET /economy
        Damoang-->>NCS: HTML 응답
        NCS->>Parser: BeautifulSoup 파싱
        Parser-->>NCS: div.flex-grow-1 요소들
        NCS->>NCS: 네이버 관련 게시글 필터링
    and 클리앙 스크래핑
        NCS->>Clien: GET /service/board/jirum
        Clien-->>NCS: HTML 응답
        NCS->>Parser: BeautifulSoup 파싱
        Parser-->>NCS: span.list_subject 요소들
        NCS->>NCS: 네이버 관련 게시글 필터링
    and 뽐뿌 스크래핑
        NCS->>Ppomppu: GET /zboard/zboard.php?id=coupon
        Ppomppu-->>NCS: HTML 응답
        NCS->>Parser: BeautifulSoup 파싱
        Parser-->>NCS: td.baseList-space 요소들
        NCS->>NCS: 네이버 관련 게시글 필터링
    and 루리웹 스크래핑
        NCS->>Ruliweb: GET /market/board/1020
        Ruliweb-->>NCS: HTML 응답
        NCS->>Parser: BeautifulSoup 파싱
        Parser-->>NCS: td.subject 요소들
        NCS->>NCS: 네이버 관련 게시글 필터링
    end
    
    NCS->>NCS: 모든 게시글 병합
    NCS->>NCS: campaign_scrap(posts) 호출
```

### 3. Firefox 자동화 시퀀스

```mermaid
sequenceDiagram
    participant NCS as NaverCoinScraper
    participant Firefox as Firefox Driver
    participant NaverLogin as 네이버 로그인
    participant Campaign as 캠페인 사이트
    participant Logger as Logger

    NCS->>Firefox: _create_firefox_driver()
    Firefox-->>NCS: WebDriver 인스턴스
    
    NCS->>Firefox: get(naver_login_url)
    Firefox->>NaverLogin: 로그인 페이지 요청
    NaverLogin-->>Firefox: 로그인 폼
    
    NCS->>Firefox: execute_script(아이디 입력)
    NCS->>Firefox: execute_script(비밀번호 입력)
    NCS->>Firefox: 로그인 버튼 클릭
    
    Firefox->>NaverLogin: 로그인 요청
    NaverLogin-->>Firefox: 로그인 성공/실패
    
    alt 로그인 성공
        NCS->>Logger: 로그인 성공 로그
        
        loop 각 캠페인 링크
            NCS->>Firefox: get(campaign_url)
            Firefox->>Campaign: 캠페인 페이지 요청
            Campaign-->>Firefox: 캠페인 페이지
            
            NCS->>Firefox: _handle_alert() - Alert 처리
            
            alt campaign2.naver.com
                NCS->>Firefox: 포인트 받기 버튼 찾기
                Firefox-->>NCS: 버튼 요소
                NCS->>Firefox: 버튼 클릭
                Firefox->>Campaign: 포인트 적립 요청
                Campaign-->>Firefox: 적립 결과
                NCS->>Firefox: URL 변경 대기
            else ofw.adison.co
                Note over NCS: Adison은 체류만으로 충분
            end
            
            NCS->>Firefox: dwell_and_scroll() 실행
            
            loop 자연스러운 스크롤
                NCS->>Firefox: execute_script(스크롤)
                NCS->>NCS: random 대기시간
                NCS->>Firefox: send_keys(PAGE_DOWN/UP)
            end
            
            NCS->>Logger: 방문 완료 로그
        end
        
    else 로그인 실패
        NCS->>Logger: 로그인 실패 로그
    end
    
    NCS->>Firefox: quit() - 드라이버 종료
```

### 4. 에러 처리 및 보안 시퀀스

```mermaid
sequenceDiagram
    participant Main as main()
    participant NCS as NaverCoinScraper
    participant FS as FileSystem
    participant Logger as Logger
    participant System as System

    Main->>NCS: 프로그램 시작
    
    NCS->>FS: break-point.html 존재 확인
    
    alt 휴면 파일 존재
        FS-->>NCS: 파일 존재
        NCS->>FS: 파일 수정 시간 확인
        FS-->>NCS: 수정 시간
        
        alt 휴면 시간 만료
            NCS->>FS: 휴면 파일 삭제
            NCS->>Logger: 휴면 해제 로그
            NCS->>NCS: 정상 실행 계속
        else 휴면 시간 미만료
            NCS->>Logger: 휴면 중 에러 로그
            NCS->>System: sys.exit(1)
        end
    else 휴면 파일 없음
        NCS->>NCS: 정상 실행
    end
    
    NCS->>NCS: 스크래핑 실행
    
    alt 보안 감지 (예: CAPTCHA)
        NCS->>FS: break-point.html 생성
        NCS->>Logger: 보안 감지 로그
        NCS->>System: 48시간 휴면 시작
    else 정상 실행
        NCS->>Logger: 정상 완료 로그
    end
    
    alt 예외 발생
        NCS->>Logger: 예외 로그 (exc_info=True)
        NCS->>System: sys.exit(1)
    else KeyboardInterrupt
        NCS->>Logger: 사용자 중단 로그
    end
    
    Main->>Logger: 프로그램 종료 로그
```

이제 총 4개의 시퀀스 다이어그램이 추가되었습니다:

1. **전체 실행 시퀀스** - 프로그램 전체 실행 흐름
2. **게시글 스크래핑 시퀀스** - 다중 사이트 병렬 스크래핑
3. **Firefox 자동화 시퀀스** - 브라우저 자동화 상세 과정
4. **에러 처리 및 보안 시퀀스** - 예외 상황 처리 흐름

각 시퀀스는 시간 순서대로 객체 간의 상호작용을 보여주어 코드의 동작 방식을 더 명확하게 이해할 수 있습니다! 🎯