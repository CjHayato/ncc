#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import fcntl
import config
import random
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoAlertPresentException
from urllib.parse import urlparse, urljoin

def avoid_overlab():
    sys.argv[0]
    pid_lock_file = sys.argv[0] + '.pid'
    try:
        fcntl.lockf(open(pid_lock_file, 'w'), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print('이미 실행 중입니다')
        sys.exit(1)
    finally:
        os.remove(pid_lock_file)

class naver_coin_scraper:
    def __init__(self):
        ####### 여기 있는 정보 OS 에따라 수정 될 수 있다. #######
        self.gecko = '/usr/local/bin/geckodriver'                  # geckodriver 경로
        delay_hour = 48                                            # naver security 에 노출되었을때 쉬는 시간 정의
        #########################################################
        self.pwd = os.path.abspath(os.path.join(__file__,  ".."))
        os.chdir(self.pwd)
        self.tdb = self.pwd + '/visited_urls.txt'
        self.log = self.pwd + '/scrap-link.log'
        self.bp  = self.pwd + '/break-point.html'
        self.rqua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
        self.ffua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1"
        if os.path.isfile(self.bp):                                # 딜레이 파일이 있다면...
            if delay_hour*60*60 <= int(time.time()-os.path.getmtime(self.bp)):
                os.remove(self.bp)                                 # 쉬는 시간 초과시딜레이 파일 삭제
            else:
                print(f"it's need yo delay for {delay_hour} hour. coz naver security.")
                exit(1)                                            # 쉰다.
        try:                                                       # 방문 기록을 파일에서 읽어 온다
            with open(self.tdb, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    def get_coin(self, campaign_links):
        print("starting firefox then login naver site.")
        f_opts = webdriver.FirefoxOptions()                        # firefox 드라이버 옵션 설정
        f_opts.add_argument('--headless')                          # firefox - headless mode
        f_opts.add_argument("--window-size=402,874")               # 창 크기 설정(iPhone 16 pro)
        f_opts.add_argument("--disable-gpu")                       # GPU 가속 비활성화
        f_opts.add_argument("--no-sandbox")                        # 샌드박스 모드 비활성화
        f_opts.add_argument("--disable-blink-features=AutomationControlled")
        f_opts.set_preference("network.cookie.cookieBehavior", 1)  # 쿠키 모두 허용으로 변경
        f_opts.set_preference("general.useragent.override", self.ffua)
        f_opts.set_preference("intl.accept_languages", "ko")
        for nid, npw in config.naver_login_info.items():           # config에서 선언된 더미 아이디는 건너 뛴다
            if nid is None or nid == "" or nid == "naver_ID1" or nid == "naver_ID2" or nid == "naver_ID3":
                continue
            else:
                if sys.version_info.major == 3:                    # python 및 selenium 버전에 따라 사용법이 다름.
                    if sys.version_info.minor >= 10:
                        driver = webdriver.Firefox(service=Service(executable_path=self.gecko, log_output=os.devnull),
                                                   options=f_opts)
                    elif 9 >= sys.version_info.minor >= 7:
                        driver = webdriver.Firefox(service=Service(executable_path=self.gecko),
                                                   log_path=os.devnull, options=f_opts)
                    elif 6 >= sys.version_info.minor:
                        driver = webdriver.Firefox(executable_path=self.gecko,
                                                   log_path=os.devnull, options=f_opts)
                try:
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/')
                    driver.implicitly_wait(10)                     # 로그인 페이지 로딩 완료를 기다린다
                    spot = driver.find_element(By.XPATH, '//*[@id="id"]')
                    driver.execute_script("document.getElementsByName('id')[0].value=\'" + nid + "\'")
                    spot.send_keys(Keys.TAB)                       # bot 탐지 방지를 위한 키보드 입력
                    spot = driver.find_element(By.XPATH, '//*[@id="pw"]')
                    driver.execute_script("document.getElementsByName('pw')[0].value=\'" + npw + "\'")
                    time.sleep(random.uniform(1, 3))
                    spot.send_keys(Keys.ENTER)                     # bot 탐지 방지를 위한 키보드 입력
                    driver.implicitly_wait(30)                     # 로딩이 완료되길 기다린다
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    if soup.find('div', class_="captcha_img"):     # captcha 제한이 걸렸는지 확인한다.
                        print("It's traped naver anti-bot security.(CAPTCHA)")
                        with open(self.bp, "w") as f:              # 딜레이 파일을 생성 한다.(break-point.html)
                            f.write(str(soup.prettify()))
                        break
                    with open(self.log, "a") as f:
                        f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' naver login for try to scrap ' +
                                str(len(campaign_links)) + ' times\n')
                    for link in campaign_links:
                        driver.get(link)                           # 네이버 캠페인 접속
                        driver.implicitly_wait(10)                 # 로딩이 완료되길 기다린다
                        with open(self.log, "a") as f:
                            f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + link + '\n')
                        try:                                       # 얼럿창의 내용을 기록하고 accept 버튼을 누른다.
                            result = driver.switch_to.alert
                            with open(self.log, "a") as f:
                                f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + result.text + '\n')
                            time.sleep(random.uniform(1, 2))
                            result.accept()
                            time.sleep(random.uniform(4, 6))
                        except (NameError, NoAlertPresentException): # 레이어 팝업 내용을 기록 한다.
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            if "div" in str(soup.find('div', class_="dim")):
                                DIM = soup.find('div', class_="dim")
                                with open(self.log, "a") as f:
                                    f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' +
                                            str(DIM.get_text().strip()) + '\n')
                            time.sleep(random.uniform(4, 6))
                except Exception as e:
                    with open(self.log, "a") as f:
                        f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + e + '\n')
                finally:
                    driver.quit()                                  # firefox 종료 한다
        print("모든 링크를 방문했습니다.")

    def campaign_scrap(self, posts, campaign_links):
        if len(posts) != 0:
            for link in posts:
                baseurl = urlparse(link).hostname
                if link in self.visited_urls:                      # 기록에 따라 방문 했던 곳은 넘어 간다
                    continue
                res = requests.get(link, headers={"User-Agent": self.rqua})
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):  # 아티클에서 링크 주소(a href)를 가져 온다
                    if baseurl.endswith(".ppomppu.co.kr"):
                        inlink = a_tag.get_text().strip()          # 뽐뿌는 링크가 a href 로 되어 있지 않다.
                    else:
                        inlink = a_tag['href']
                    host = urlparse(inlink)
                    if host and host not in campaign_links:
                        if host.netloc == "campaign2-api.naver.com" or host.netloc == "ofw.adison.co":
                            campaign_links.add(inlink)             # 캠페인 주소일 경우 목록에 추가 한다
        return campaign_links

    def post_scrap(self):
        campaign_links, posts = set(), set()
        post_check_urls = [ "https://damoang.net/economy",
                            "https://www.clien.net/service/board/jirum",
                            "https://bbs.ruliweb.com/market/board/1020",
                            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon" ]
        for base_url in post_check_urls:
            response = requests.get(base_url, headers={"User-Agent": self.rqua})
            soup = BeautifulSoup(response.text, 'html.parser')
            post = set()
            host = urlparse(base_url).hostname
            if host and host == "damoang.net":                     # damoang: list-group-item - li
                row_tag, row_class = 'li', 'list-group-item'
            elif host and host.endswith(".ruliweb.com"):           # ruliweb : subject - td
                row_tag, row_class = 'td', 'subject'
            elif host and host.endswith(".ppomppu.co.kr"):         # ppomppu: baseList-space - td
                row_tag, row_class = 'td', 'baseList-space'
            elif host and host.endswith(".clien.net"):             # clien  : list_subject - span
                row_tag, row_class = 'span', 'list_subject'
            list_subject_links = soup.find_all(row_tag, class_=row_class)
            if len(list_subject_links) != 0:
                for span in list_subject_links:
                    a_tag = span.find('a', href=True)
                    if a_tag and '네이버' in a_tag.text:
                        post.add(urljoin(base_url, a_tag['href'])) # baseurl과a href 을 조합해 캠페인에 추가 한다
            posts |= post                                          # set() + set()
            print(len(post), "of article from: " + base_url)
        campaign_links = naver_coin_scraper.campaign_scrap(self, posts, campaign_links)
        print("Discovered glean URLs:", len(campaign_links))
        if len(campaign_links) >= 1:
            naver_coin_scraper.get_coin(self, campaign_links)      # firefox를 통한 캠페인 접속 시작
            self.visited_urls = posts
            with open(self.tdb, 'w') as file:                      # 방문했던 아티클 링크를 저장한다
                for url in self.visited_urls:
                    file.write(url + '\n')

def config_check(config_dict):
    cr, cg, c0= '\033[31;1m', '\033[32;1m', '\033[0m'
    if not isinstance(config_dict, dict):
        print(cg + 'change ' + cr + 'config.py' + cg + ' file to new.' + c0)
        exit(1)
    for nid, npw in config_dict.items():
        if nid is None or nid == "" or nid == "naver_ID1":
            print(cg + 'make sure edit to ' + cr + 'config.py' + cg + ' first.' + c0)
            exit(1)
        break

def main():
    avoid_overlab()
    config_check(config.naver_login_info)
    ncc = naver_coin_scraper()
    naver_coin_scraper.post_scrap(ncc)

if __name__ == "__main__":
    main()

exit(0)
