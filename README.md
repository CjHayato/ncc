![header](https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=130&section=header&text=CjHayato/ncc&fontSize=30&fontColor=ffffff&fontAlign=80&fontAlignY=40)

[![CodeQL](https://github.com/CjHayato/ncc/actions/workflows/codeql.yml/badge.svg)](https://github.com/CjHayato/ncc/actions/workflows/codeql.yml)
[![Ruff](https://github.com/CjHayato/ncc/actions/workflows/ruff-action.yml/badge.svg)](https://github.com/CjHayato/ncc/actions/workflows/ruff-action.yml)
> @stateofai 님께서 배포한 소스를 기반으로 수정하였습니다:)  
> `aarch64` 아키텍처 대응을 위해 Browser가 [![Static Badge](https://img.shields.io/badge/chrome-_-4285F4?style=plastic&logo=googlechrome)](#)에서 [![Static Badge](https://img.shields.io/badge/firefox-_-FF7139?style=plastic&logo=firefoxbrowser)](#)로 교체되었습니다.  
> `geckodriver` 설치 하시고 코드를 실행해주세요.
>
> <details>
> <summary>Fork 후 원본(stateofai/naver-paper) 대비 변경점</summary>
>
> - **chatGTPv3.5** 님이 Browser 교체 수정 했습니다.
> - 네이버 아이디, 패스워드를 `config.py` 에 지정해서 동작 하도록 수정했습니다.
> - 캠페인(네이버 링크) 수집 -> 네이버 로그인 -> 캠페인 방문 순으로 변경하여 불필요한 네이버 로그인을 하지 않도록 했습니다.
> - 다모앙, 클리앙, 뽐뿌, 루리웹의 최신 게시물을 수집 해서 네이버 이벤트 URL 을 타켓팅 하도록 수정 했습니다.
> - 프로그램이 중복 실행을 방지 하도록 했습니다.
> - 다중 아이디를 지원하도록 수정했습니다.
> - 방문한 네이버 캠페인의 로그를 scrap-link.log 파일로 생성합니다.
> - 캠페인 수집(PC), 캠페인 참여(네이버) 의 브라우져 User-Agent를 분리 했습니다.
> - 네이버 CAPTCHA 발생을 최소화 하도록 수정 되었고, 이에 걸렸을 경우 48시간 동안 수집을 정지 합니다.
> - Selenium 버전 인식을 통해 Python 3.6 ~ 3.12 버전을 지원 하도록 수정 했습니다.
> - AI코딩(kiro.dev)을 이용 하여 로그 표준화, 코드 품질, 함수 구조가 개선 또는 최적화 되었습니다.
> - 네이버 보안 강화 대응: `pyautogui`를 이용한 OS 레벨 실제 키보드 입력 방식으로 변경하여 자동화 감지 우회.
> - 쿠키 기반 세션 로그인 지원: 최초 로그인 성공 후 `naver_cookies/`에 세션 쿠키를 저장하여 이후 실행 시 비밀번호 입력 없이 로그인 복원.
> - 계정별 Firefox 프로필 지원: `FIREFOX_PROFILE_ROOT` 환경변수로 계정별 전용 프로필 경로 지정 가능.
> - 캡차 감지 및 로그인 실패 시 스크린샷 자동 저장 (`login_screenshots/`).
> - HTTP 요청 재시도 로직 추가 (최대 3회, 지수 백오프), 타임아웃 30초로 증가.
> - `xvfb-run`을 통한 가상 디스플레이 환경에서 실행 지원 (pyautogui 요구사항).
> </details>
>
> **개발 환경**
> 
> [![Static Badge](https://img.shields.io/badge/Oracle_Cloud_Infrastructure-A1_instance-F80000?style=plastic&logo=oracle)](#)
> [![Static Badge](https://img.shields.io/badge/ORACLE_linux-8_aarch64-F80000?style=plastic&logo=oracle)](#)
>
> **테스트 완료 Python 버전**
> 
> [![Static Badge](https://img.shields.io/badge/Python-3.6-3776AB?style=plastic&logo=python&labelColor=silver)](#)
> [![Static Badge](https://img.shields.io/badge/Python-3.8-3776AB?style=plastic&logo=python&labelColor=silver)](#)
> [![Static Badge](https://img.shields.io/badge/Python-3.9-3776AB?style=plastic&logo=python&labelColor=silver)](#)
> [![Static Badge](https://img.shields.io/badge/(pyenv)Python-3.10-3776AB?style=plastic&logo=python&labelColor=silver)](#)
> [![Static Badge](https://img.shields.io/badge/Python-3.11-3776AB?style=plastic&logo=python&labelColor=silver)](#)
> [![Static Badge](https://img.shields.io/badge/Python-3.12-3776AB?style=plastic&logo=python&labelColor=silver)](#)

# 설치 방법
### Mozilla Firefox 설치
> ```as3
> ~]$ sudo dnf -y install firefox
> ```
### GeckoDriver 설치
- GeckoDriver 배포 URL: [https://github.com/mozilla/geckodriver/releases]<br>
  *아래 예제문은 aarch64(arm64)으로 되어 있습니다. 자신의 서버에 맞추어 변경해서 사용하기 바랍니다.*
> ```as3
> ~]$ cd /usr/local/bin
> ~]$ sudo curl -LO https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux-aarch64.tar.gz
> ~]$ sudo tar xfzp geckodriver-v0.35.0-linux-aarch64.tar.gz
> ~]$ sudo chmod +x geckodriver
> ~]$ sudo chown root: geckodriver
> ```

### 소스 설치 방법
> ```as3
> ~]$ cd /opt
> ~]$ sudo git clone https://github.com/CjHayato/ncc.git
> ~]$ cd ncc
> ~]$ sudo pip install -r requirements.txt
> ```

### xvfb 및 VNC 설치 (서버 GUI 환경)
> GUI 없는 서버에서 Firefox를 실행하려면 xvfb가 필요하고, 최초 로그인용 화면 접속에는 VNC가 필요합니다.
> ```as3
> ~]$ sudo dnf -y install xorg-x11-server-Xvfb tigervnc-server firefox
> ```

### Firefox 프로필 생성 (계정별)
> 최초 1회 VNC 환경에서 계정별 Firefox 프로필을 생성하고 네이버에 직접 로그인해야 합니다.  
> 프로필 디렉토리 이름은 `config.py`의 `naver_login_info` 계정명과 동일해야 합니다.
> ```as3
> # 계정별 프로필 디렉토리 생성
> ~]$ mkdir -p /free/home/naver/firefox-profiles/account-1
> ~]$ mkdir -p /free/home/naver/firefox-profiles/account-2
>
> # VNC 접속 비밀번호 설정 (최초 1회)
> ~]$ vncpasswd
>
> # VNC 서버 실행
> ~]$ vncserver :1 -geometry 1280x900 -depth 24
>
> # 첫 번째 계정 프로필로 Firefox 실행 후 VNC 화면에서 네이버 로그인
> ~]$ DISPLAY=:1 MOZ_DISABLE_CONTENT_SANDBOX=1 firefox --no-remote \
>      --profile /free/home/naver/firefox-profiles/account-1 \
>      https://www.naver.com
>
> # Firefox를 정상 종료한 뒤 두 번째 계정도 같은 방식으로 로그인
> ~]$ DISPLAY=:1 MOZ_DISABLE_CONTENT_SANDBOX=1 firefox --no-remote \
>      --profile /free/home/naver/firefox-profiles/account-2 \
>      https://www.naver.com
>
> # 설정 완료 후 VNC 종료
> ~]$ vncserver -kill :1
> ```
> 로그인 후 Firefox를 메뉴에서 정상 종료해야 세션이 프로필에 저장됩니다.  
> 위 `account-1`, `account-2`는 예시이며 실제로는 `config.py`의 계정 키와 같은 이름을 사용하세요.  
> Cron 실행 시간에는 VNC에서 같은 프로필을 열어두지 마세요.

### Firefox 프로필 캐시 정리
> Firefox 프로필의 `cache2` 디렉토리는 디스크 캐시이므로 주기적으로 삭제해도 로그인 세션에는 보통 영향이 없습니다.  
> 단, Firefox가 실행 중일 때는 삭제하지 마세요.
> ```as3
> # 캐시 용량 확인
> ~]$ du -sh /free/home/naver/firefox-profiles/*/cache2
>
> # Firefox가 종료된 상태에서 캐시 삭제
> ~]$ find /free/home/naver/firefox-profiles -mindepth 2 -maxdepth 2 -type d -name cache2 -exec rm -rf {} +
>
> # 프로필 전체 용량 확인
> ~]$ du -sh /free/home/naver/firefox-profiles/*
> ```
> 하루 1회 새벽에 자동 정리하는 crontab 예시:
>> ```as3
>> 30 4 * * * find /free/home/naver/firefox-profiles -mindepth 2 -maxdepth 2 -type d -name cache2 -exec rm -rf {} +
>> ```

# 사용 방법
### config.py 수정
> config.py 파일을 사용하시는 에디터로 열어 네이버 로그인 전용 아이디/비밀번호를 입력해주세요.  
[References 전용아이디 소개 및 설정](https://help.naver.com/service/5640/contents/10219?lang=ko) 참조
>> ```as3
>> naver_login_info = {
>>    'your_naver_id_1': 'your_password_1',
>>    'your_naver_id_2': 'your_password_2',
>>    'your_naver_id_3': 'your_password_3',
>> }
>> ```

### 프로그램 실행
> ```as3
> ~]$ python run_firefox.py
> ```
> xvfb 가상 디스플레이 환경에서 실행 (서버 환경 권장):
> ```as3
> ~]$ FIREFOX_PROFILE_ROOT=/free/home/naver/firefox-profiles \
>     MOZ_DISABLE_CONTENT_SANDBOX=1 \
>     xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
> ```

### 스케쥴링 설정 (Crontab)
> `crontab -e` 매 시간 15분마다 실행하는 예시입니다.
>> ```as3
>> 15 */1 * * * cd /free/home/naver/ncc && FIREFOX_PROFILE_ROOT=/free/home/naver/firefox-profiles MOZ_DISABLE_CONTENT_SANDBOX=1 /usr/bin/xvfb-run -a /usr/local/pyenv/versions/3.12.1/bin/python run_firefox.py
>> ```
> pyenv를 사용하지 않을 경우:
>> ```as3
>> 15 */1 * * * cd /opt/ncc && FIREFOX_PROFILE_ROOT=/path/to/firefox-profiles MOZ_DISABLE_CONTENT_SANDBOX=1 /usr/bin/xvfb-run -a python run_firefox.py
>> ```

### 환경변수 설정
> | 환경변수 | 설명 | 기본값 |
> |---|---|---|
> | `FIREFOX_PROFILE_ROOT` | 계정별 Firefox 프로필 루트 디렉토리 | 없음 (임시 프로필 사용) |
> | `FIREFOX_PROFILE_PATH` | 단일 Firefox 프로필 경로 | 없음 |
> | `MOZ_DISABLE_CONTENT_SANDBOX` | 서버/VNC 환경에서 Firefox 콘텐츠 샌드박스 비활성화 | 없음 |
> | `GECKODRIVER_PATH` | GeckoDriver 실행 파일 경로 | `/usr/local/bin/geckodriver` |
> | `DELAY_HOURS` | 보안 감지 시 휴면 시간 (시간) | `48` |
> | `MIN_DWELL_TIME` | 페이지 최소 체류 시간 (초) | `6` |
> | `ALLOW_PASSWORD_LOGIN` | 쿠키 로그인 실패 시 비밀번호 로그인 허용 | `0` (비활성) |

# References
> | 설명 | URL |
> |---|---|
> | 네이버 로그인 전용 아이디 소개 및 설정 | https://help.naver.com/service/5640/contents/10219?lang=ko |
> | 네이버 애플리케이션 비밀번호 사용 방법 | https://help.naver.com/service/5640/contents/8584?lang=ko |
> | @stateofai 님 레포 | https://github.com/stateofai/naver-paper |
> | @20eung 뽐뿌 기반 코인 줍기 레포 | https://github.com/20eung/naverpaper |
> | ruff-action - python 코드 자동 리뷰 | https://github.com/astral-sh/ruff-action |

![footer](https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=70&section=footer)
