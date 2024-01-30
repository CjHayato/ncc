> @stateofai 님께서 배보한 소스를 기반으로 ChatGTP v3.5님이 수정하였습니다:)
> 
> aarch64 아키텍터 대응을 위해 브라우저가 Chrome에서 Firefox로 교체되었습니다.
> 
> geckodriver 설치 하시고 코드를 실행해주세요.
> 
> Python 3.10.12에서 제작 하였습니다.

## Prerequisites
### Install Mozilla Firefox
```bash
$ sudo dnf -y install firefox
```
> Install GeckoDriver
- Go to [https://github.com/mozilla/geckodriver/releases]

```bash
$ cd /usr/local/bin
$ curl -O https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux-aarch64.tar.gz
$ tar -xvf geckodriver-v0.34.0-linux-aarch64.tar.gz
$ chmod +x geckodriver
```
## Usage
```
$ git clone https://github.com/CjHayato/ncc.git
$ cd ncc
$ pip install -r requirements.txt
$ python run_firefox.py 
```

## References
* https://github.com/stateofai/naver-paper
* https://help.naver.com/service/5640/contents/10219?lang=ko
* https://help.naver.com/service/5640/contents/8584?lang=ko
