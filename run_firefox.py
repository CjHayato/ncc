#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import fcntl
import config
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoAlertPresentException

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
        self.gecko = '/usr/local/bin/geckodriver'
        #########################################################
        self.visited_urls_file='visited_urls.txt'
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
        try:                                                       # 방문 기록을 파일에서 읽어 온다
            with open(self.visited_urls_file, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    def get_coin(self, campaign_links):
        print("starting firefox then login naver site.")
        f_opts = webdriver.FirefoxOptions()                        # firefox 드라이버 옵션 설정
        f_opts.add_argument('--headless')                          # firefox - headless mode
        f_opts.add_argument("--window-size=1920,1080")             # 창 크기 설정
        f_opts.add_argument("--disable-gpu")                       # GPU 가속 비활성화
        f_opts.add_argument("--no-sandbox")                        # 샌드박스 모드 비활성화
        f_opts.add_argument("--disable-blink-features=AutomationControlled")
        f_opts.set_preference("general.useragent.override", self.ua)
        for nid, npw in config.naver_login_info.items():           # config에서 선언된 더미 아이디는 건너 뛴다
            if nid is None or nid == "" or nid == "naver_ID1" or nid == "naver_ID2" or nid == "naver_ID3":
                continue
            else:
                if sys.version_info.major == 3:                    # python 버전에 따라 selenium 버전이 바뀌고 사용법이 다르다
                    if sys.version_info.minor >= 10:
                        driver = webdriver.Firefox(service=Service(executable_path=self.gecko, log_output=os.devnull), options=f_opts)
                    elif 9 >= sys.version_info.minor >= 7:
                        driver = webdriver.Firefox(service=Service(executable_path=self.gecko), log_path=os.devnull, options=f_opts)
                    elif 6 >= sys.version_info.minor:
                        driver = webdriver.Firefox(executable_path=self.gecko, service_log_path=os.devnull, options=f_opts)
                try:
                    driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/')
                    driver.implicitly_wait(10)                     # 로그인 페이지 로딩 완료를 기다린다
                    driver.execute_script("document.getElementsByName('id')[0].value=\'" + nid + "\'")
                    driver.execute_script("document.getElementsByName('pw')[0].value=\'" + npw + "\'")
                    driver.find_element(By.CLASS_NAME, "btn_login").click()
                    driver.implicitly_wait(10)                     # 로그인후 로딩이 완료되길 기다린다
                    with open("scrap-link.logs", "a") as f:
                        f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' naver login success.\n')
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    for link in campaign_links:
                        driver.get(link)                           # 네이버 캠페인 접속
                        with open("scrap-link.logs", "a") as f:
                            f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + link + '\n')
                        try:                                       # 얼럿창의 내용을 기록하고 accept 버튼을 누른다.
                            result = driver.switch_to.alert
                            with open("scrap-link.logs", "a") as f:
                                f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + result.text + '\n')
                            result.accept()
                        except (NameError, NoAlertPresentException): # 레이어 팝업 내용을 기록 한다.
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            if "div" in str(soup.find('div', class_="dim")):
                                DIM = soup.find('div', class_="dim")
                                with open("scrap-link.logs", "a") as f:
                                    f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + str(DIM.get_text().strip()) + '\n')
                        time.sleep(5)
                except Exception as e:
                    with open("scrap-link.logs", "a") as f:
                        f.write(str(time.strftime('%Y-%m-%d %H:%M:%S')) + ' ' + e + '\n')
                finally:
                    driver.quit()                                  # firefox 종료 한다
        print("모든 링크를 방문했습니다.")

    def campaign_scrap(self, posts, base_url, campaign_links):
        if len(posts) != 0:
            for link in posts:
                if link in self.visited_urls:                      # 기록에 따라 방문 했던 곳은 넘어 간다
                    continue
                res = requests.get(link, headers={"User-Agent": self.ua})
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):  # 아티클에서 링크 주소(a href)를 가져 온다
                    cl = a_tag.get_text().strip()
                    if ('campaign2-api.naver.com' in cl or 'ofw.adison.co' in cl) and cl not in campaign_links:
                        campaign_links.add(cl)                     # 캠페인 주소일 경우 목록에 추가 한다
        return campaign_links

    def post_scrap(self):
        campaign_links, posts = set(), set()
        post_check_urls = [ "https://damoang.net/economy",
                            "https://www.clien.net/service/board/jirum",
                            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon" ]
        for base_url in post_check_urls:
            response = requests.get(base_url, headers={"User-Agent": self.ua})
            soup = BeautifulSoup(response.text, 'html.parser')
            post = set()
            if 'damoang.net' in base_url:                          # damoang: list-group-item - li
                row_tag, row_class = 'li', 'list-group-item'
            elif 'ppomppu.co.kr' in base_url:                      # ppomppu: baseList-space - td # list_vspace - td
                row_tag, row_class, url_split = 'td', 'baseList-space', 'zboard.php'
            elif 'clien.net' in base_url:                          # clien  : list_subject - span
                row_tag, row_class, url_split = 'span', 'list_subject', '/service'
            list_subject_links = soup.find_all(row_tag, class_=row_class)
            if len(list_subject_links) != 0:
                for span in list_subject_links:
                    a_tag = span.find('a', href=True)
                    if a_tag and '네이버' in a_tag.text:
                        try:                                       # baseurl과 링크URL 을 조합해 캠페인에 추가 한다
                            post.add(str(base_url.split(url_split)[0]) + str(a_tag['href']))
                        except UnboundLocalError:
                            post.add(str(a_tag['href']))           # damoang은 링크URL이 풀URL으로 나온다
                try:
                    del url_split
                except NameError:
                    pass
            posts |= post                                          # set() + set()
            print("searched new article", len(post), "from: " + base_url)
        campaign_links = naver_coin_scraper.campaign_scrap(self, posts, base_url, campaign_links)
        print("searched naver campaign:", len(campaign_links))
        if len(campaign_links) >= 1:
            naver_coin_scraper.get_coin(self, campaign_links)      # firefox를 통한 캠페인 접속 시작
            self.visited_urls = posts
            with open(self.visited_urls_file, 'w') as file:        # 방문했던 아티클 링크를 저장한다
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
