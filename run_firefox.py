#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import config
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service

class naver_coin_scraper:
    def __init__(self):
        ####### 여기 있는 정보 OS 에따라 수정 될 수 있다. #######
        self.gecko = '/usr/local/bin/geckodriver'                       # geckodriver 경로
        #########################################################
        self.visited_urls_file='visited_urls.txt'
        try:                                                            # 방문 기록을 파일에서 읽어 온다
            with open(self.visited_urls_file, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    def get_coin(self, campaign_links):
        print("starting firefox then login naver site.")
        firefox_options = webdriver.FirefoxOptions()                    # firefox 드라이버 옵션 설정
        firefox_options.add_argument('--headless')                      # firefox - headless mode
        try:
            driver = webdriver.Firefox(service=Service(executable_path=self.gecko), options=firefox_options)
        except:
            driver = webdriver.Firefox(executable_path=self.gecko, options=firefox_options)
        driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/')
        driver.execute_script("document.getElementsByName('id')[0].value=\'" + config.input_id + "\'")
        driver.execute_script("document.getElementsByName('pw')[0].value=\'" + config.input_pw + "\'")
        driver.find_element(By.CLASS_NAME, "btn_login").click()         # login 한다
        time.sleep(1)
        for link in campaign_links:
            driver.get(link)                                            # 네이버 캠페인 접속
            try:
                result = driver.switch_to.alert
                print(result.text)
                result.accept()
            except:
                pass
            time.sleep(5)
        try:
            driver.quit()                                               # firefox 종료
        except:
            pass
        print("모든 링크를 방문했습니다.")

    def campaign_scrap(self, posts, base_url):
        campaign_links = set()
        if len(posts) != 0:
            for link in posts:
                if link in self.visited_urls:                           # 기록에 따라 방문 했던 곳은 넘어 간다.
                    continue
                res = requests.get(link)
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):       # 아티클에서 링크 주소(a href)를 가져 온다.
                    cl = a_tag.get_text().strip()
                    if ('campaign2-api.naver.com' in cl or 'ofw.adison.co' in cl) and cl not in campaign_links:
                        campaign_links.add(cl)                          # 캠페인 주소일 경우 목록에 추가 한다.
        return campaign_links

    def post_scrap(self):
        campaign_links, posts = set(), set()
        post_check_urls = [ "https://www.clien.net/service/board/jirum",
                            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon" ]
        for base_url in post_check_urls:
            response = requests.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            post = set()
            if 'ppomppu.co.kr' in base_url:
                list_subject_links = soup.find_all('td', class_='list_vspace')    # ppomppu - list_vspace - td
            elif 'clien.net' in base_url:
                list_subject_links = soup.find_all('span', class_='list_subject') # clien - list_subject - span
            if len(list_subject_links) != 0:
                for span in list_subject_links:
                    a_tag = span.find('a', href=True)
                    if a_tag and '네이버' in a_tag.text:
                        if 'ppomppu.co.kr' in base_url:                 # ppomppu url assemble
                            post.add(str(base_url.split('zboard.php')[0]) + str(a_tag['href']))
                        elif 'clien.net' in base_url:                   # clien url assemble
                            post.add(str(base_url.split('/service')[0]) + a_tag['href'])
            posts |= post
            print("searched article", len(post), "from: " + base_url)
        campaign_links = naver_coin_scraper.campaign_scrap(self, posts, base_url)
        print("searched naver campaign:", len(campaign_links))
        if len(campaign_links) >= 1:
            naver_coin_scraper.get_coin(self, campaign_links)           # firefox를 통한 네이버 접속 시작
            self.visited_urls = posts
            with open(self.visited_urls_file, 'w') as file:
                for url in self.visited_urls:
                    file.write(url + '\n')

def config_check(id, pw):
    if id is None or id == "" or pw is None or pw == "":
        cr, cg, c0= '\033[31;1m', '\033[32;1m', '\033[0m'
        print(cg + 'make sure edit to ' + cr + 'config.py' + cg + ' first.' + c0)
        exit(1)

def main():
    config_check(config.input_id, config.input_pw)
    ncc = naver_coin_scraper()
    naver_coin_scraper.post_scrap(ncc)

if __name__ == "__main__":
    main()

exit(0)
