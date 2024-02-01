> @stateofai 님께서 배포한 소스를 기반으로 ChatGTP v3.5 님이 수정하였습니다:)
> 
> aarch64 아키텍처 대응을 위해 브라우저가 Chrome에서 Firefox로 교체되었습니다.
> 
> geckodriver 설치 하시고 코드를 실행해주세요.
>
>> https://github.com/20eung/naverpaper 의 코드를 참조 하여 클리앙 및 뽐뿌 모두 가져오도록 수정했습니다.

> 개발 및 사용 추천 환경
> 
> OCI 인스턴스 (x86_64, aarch64) - OlacleLinux(RHEL) 8.7 - Python 3.10.12

## Prerequisites
### Install Mozilla Firefox
```
$ sudo dnf -y install firefox
```
> Install GeckoDriver
- Go to [https://github.com/mozilla/geckodriver/releases]

```
$ cd /usr/local/bin
$ wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz
$ tar -xvf geckodriver-v0.34.0-linux-aarch64.tar.gz
$ chmod +x geckodriver
```

## Usage
```
$ cd /opt
$ git clone https://github.com/CjHayato/ncc.git
$ cd ncc
$ pip install -r requirements.txt
```

## Edit config.py
> config.py 파일을 사용하시는 에디터로 열어 네이버 전용 아이디/비밀번호를 입력해주세요.

## 실행
```
$ python run_firefox.py
```

## 부록 - Crontab 설정
> 3시간 기준으로 작동하는 예시 입니다.
>
> `* */3 * * * /usr/local/pyenv/shims/python /opt/ncc/run_firefox.py; /usr/bin/killall -9 firefox`
>
> Firefox 브라우저가 자동으로 닫히지 않기 때문에 프로세스 실행 후 꺼지는 스크립트를 같이 실행합니다.

실행시 firefox가 꺼지지 않는 문제를 해결하기 위해 아래 스크립트로 종료하는것을 자동화 할 수 있습니다.

## 또는 firefox 자동 종료까지 하기 위해 bash-shell 실행
```
$ python ncc.sh
```
crontab 에 `* */3 * * * /usr/local/pyenv/shims/python /opt/ncc/ncc.sh` 와 같이 등록하세요.

## References
* @stateofai 님 레포: [https://github.com/stateofai/naver-paper]
* 네이버 로그인 전용 아이디 소개 및 설정 방법: [https://help.naver.com/service/5640/contents/10219?lang=ko]
* 애플리케이션 비밀번호 사용 방법: [https://help.naver.com/service/5640/contents/8584?lang=ko]
