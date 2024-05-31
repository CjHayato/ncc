![header](https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=130&section=header&text=CjHayato/ncc&fontSize=30&fontColor=ffffff&fontAlign=80&fontAlignY=40)

> @stateofai 님께서 배포한 소스를 기반으로 수정하였습니다:)
> 
> aarch64 아키텍처 대응을 위해 브라우저가 **Chrome**에서 **Firefox**로 교체되었습니다.
> 
> geckodriver 설치 하시고 코드를 실행해주세요.
>
>> 1. **chatGTPv3.5** 님이 브라우져 교체 코드를 수정 했습니다.
>> 2. 네이버 아이디, 패스워드를 config.py 에 지정해서 동작 하도록 수정했습니다.
>> 3. 캠페인(네이버링크) 수집 -> 네이버 로그인 -> 캠페인 방문 순으로 변경하여 불필요한 네이버 로그인을 없앴습니다.
>> 4. @20eung 님의 코드를 참조 하여 다모앙, 클리앙, 뽐뿌 등 게시물을 수집 해서 네이버 이벤트 URL 을 타켓팅 하도록 수정 했습니다.
>> 5. 프로그램이 중복 실행이 되지 않도록 구현했습니다.
>> 6. 다중 아이디를 지원하도록 수정했습니다.
>> 7. 성공 또는 실패 후 firefox 프로세스가 종료 되도록 수정했습니다.
>> 8. 방문한 네이버 캠페인의 로그를 scrap-link.logs 파일로 생성합니다.
>
> **개발 환경**
> 
> ![js](https://img.shields.io/badge/Oracle_Cloud_Infrastructure-A1-F80000?logo=oracle)
> ![js](https://img.shields.io/badge/ORACLE_linux-8(aarch64)-F80000?logo=oracle)
> 
> ![js](https://img.shields.io/badge/Python-3.6-3776AB?logo=python)
> ![js](https://img.shields.io/badge/Python-3.9-3776AB?logo=python)
> ![js](https://img.shields.io/badge/(pyenv)Python-3.10-3776AB?logo=python)
> ![js](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)

# 설치 방법
### Mozilla Firefox 설치
> ```
> $ sudo dnf -y install firefox
> ```
### GeckoDriver 설치
- Go to [https://github.com/mozilla/geckodriver/releases]

> ```
> $ cd /usr/local/bin
> $ wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz
> $ tar -xvf geckodriver-v0.34.0-linux-aarch64.tar.gz
> $ chmod +x geckodriver
> ```

### 소스 설치 방법
> ```
> $ cd /opt
> $ git clone https://github.com/CjHayato/ncc.git
> $ cd ncc
> $ pip install -r requirements.txt
> ```

# 사용법
### config.py 수정
> config.py 파일을 사용하시는 에디터로 열어 네이버 로그인 전용 아이디/비밀번호를 입력해주세요. (References 전용아이디 소개 및 설정 방법 참조)

### 프로그램 실행
> ```
> $ python run_firefox.py
> ```

### 스케쥴링 설정 (Crontab)
> 3시간 기준으로 작동하는 예시 입니다.
>> ```
>> 00 */3 * * * /usr/local/pyenv/shims/python /opt/ncc/run_firefox.py
>> ```
> pyenv 를 사용 하지 않을 경우 아래와 같이 사용이 가능 합니다.
>> ```
>> 00 */3 * * *  python /opt/ncc/run_firefox.py
>> ```

# References
> * **네이버 로그인 전용 아이디 소개 및 설정 방법**: [https://help.naver.com/service/5640/contents/10219?lang=ko]
> * 애플리케이션 비밀번호 사용 방법: [https://help.naver.com/service/5640/contents/8584?lang=ko]
> * @stateofai 님 레포: [https://github.com/stateofai/naver-paper]
> * 뽐뿌 기반 네이버 코인 줍기: [https://github.com/20eung/naverpaper]

![footer](https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=70&section=footer)
