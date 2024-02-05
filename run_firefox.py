#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import requests
import config
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By

class naver_coin_scraper:
    def __init__(self):
        ####### 여기 있는 정보 OS 에따라 수정 될 수 있다. #######        # geckodriver 경로를 아래에 기입
        self.se = Service(executable_path='/usr/local/bin/geckodriver')
        #########################################################
        self.visited_urls_file='visited_urls.txt'
        try:                                                             # Read visited URLs from file
            with open(self.visited_urls_file, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    def get_coin(self, campaign_links):
        print("starting firefox then login naver site.")
        firefox_options = webdriver.FirefoxOptions()                     # firefox 드라이버 옵션 설정
        firefox_options.add_argument('--headless')                       # firefox - headless mode
        driver = webdriver.Firefox(service=self.se, options=firefox_options)
        driver.get('https://naver.com')
        current_window_handle = driver.current_window_handle             # 현재 열려 있는 창 가져오기
        # <a href class='MyView-module__link_login___HpHMW'> 을 네이버 로그인창으로 인식
        driver.find_element(By.XPATH, "//a[@class='MyView-module__link_login___HpHMW']").click()
        new_window_handle = None                                         # 새롭게 생성된 탭의 핸들을 찾습니다
        for handle in driver.window_handles:
            if handle != current_window_handle:
                new_window_handle = handle
                break
            else:
                new_window_handle = handle
        driver2 = driver.switch_to.window(new_window_handle)             # 새탭으로 변경.
        username = driver2.find_element(By.NAME, 'id')
        pw = driver2.find_element(By.NAME, 'pw')
        username.click()                                                 # 네이버 ID 입력
        driver2.execute_script("arguments[0].value = arguments[1]", username, config.input_id)
        time.sleep(1)
        pw.click()                                                       # 네이버 PW 입력
        driver2.execute_script("arguments[0].value = arguments[1]", pw, config.input_pw)
        time.sleep(1)
        driver2.find_element(By.CLASS_NAME, "btn_login").click()
        time.sleep(1)
        for link in campaign_links:
            driver.get(link)                                            # 네이버 캡페인 접속
            try:
                result = driver.switch_to.alert
                print(result.text)
                result.accept()
            except:
                pass
            time.sleep(5)
        try:                                                            # firefox 종료
            driver.quit()
        except:
            pass
        try:                                                            # firefox 종료
            driver2.quit()
        except:
            pass
        print("모든 링크를 방문했습니다.")

    def campaign_scrap(self, posts, base_url):
        campaign_links = set()
        if len(posts) != 0:
            for link in posts:
                if link in self.visited_urls:                           # 기록에 따라 방문 했던곳은 넘어간다.
                    continue
                res = requests.get(link)
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):       # 아이클에서 링크주소(a href)를 가져온다.
                    campaign_link = a_tag.get_text().strip()
                    if ('campaign2-api.naver.com' in campaign_link or 'ofw.adison.co' in campaign_link) and campaign_link not in campaign_links:
                        campaign_links.add(campaign_link)               # 캠페인주소일 경우 목록에 추가한다.
        return campaign_links

    def post_scrap(self):
        campaign_links, posts = set(), set()
        post_check_urls = [ "https://www.clien.net/service/board/jirum",
                            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon" ]
        for base_url in post_check_urls:
            response = requests.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            if 'ppomppu.co.kr' in base_url:
                ppomppu = set()
                list_subject_links = soup.find_all('td', class_='list_vspace') # ppomppu - list_vspace - td
                if len(list_subject_links) != 0:
                    for span in list_subject_links:
                        a_tag = span.find('a', href=True)
                        if a_tag and '네이버' in a_tag.text:
                            ppomppu.add(str(base_url.split('zboard.php')[0]) + str(a_tag['href']))
                print("searched article", len(ppomppu), "from: " + base_url)
                posts |= ppomppu
            elif 'clien.net' in base_url:
                clien = set()
                list_subject_links = soup.find_all('span', class_='list_subject') # clien - list_subject - span
                if len(list_subject_links) != 0:
                    for span in list_subject_links:
                        a_tag = span.find('a', href=True)
                        if a_tag and '네이버' in a_tag.text:
                            clien.add(str(base_url.split('/service')[0]) + a_tag['href'])
                print("searched article", len(clien), "from: " + base_url)
                posts |= clien
        campaign_links = naver_coin_scraper.campaign_scrap(self, posts, base_url)
        print("searched naver campaign:", len(campaign_links))
        if len(campaign_links) >= 1:
            naver_coin_scraper.get_coin(self, campaign_links)           # firefox를 통한 네이버 접속ㄱㄱ
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
