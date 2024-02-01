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
        self.visited_urls_file='visited_urls.txt'
        try:                                                            # Read visited URLs from file
            with open(self.visited_urls_file, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    def from_clien_page(self, posts, base_url):
        campaign_links = set()
        if len(posts) != 0:
            for link in posts:                                          # Check each Naver link
                #full_link = urljoin(base_url, link)
                if link in self.visited_urls:
                    continue                                            # Skip already visited links
                res = requests.get(full_link)
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):       # Find all links that start with the campaign URL
                    if a_tag['href'].startswith("https://campaign2-api.naver.com"):
                        campaign_links.add(a_tag['href'])
                        self.visited_urls.add(full_link)                # Add the visited link to the set
        return campaign_links

    def from_ppomppu_page(self, posts, base_url):
        campaign_links = set()
        if len(posts) != 0:
            for link in posts:                                          # Check each Naver link
                if link in self.visited_urls:
                    continue                                            # Skip already visited links
                res = requests.get(link)
                inner_soup = BeautifulSoup(res.text, 'html.parser')
                for a_tag in inner_soup.find_all('a', href=True):       # Find all links that start with the campaign URL
                    campaign_link = a_tag.get_text().strip()
                    if ('campaign2-api.naver.com' in campaign_link or 'ofw.adison.co' in campaign_link) and campaign_link not in campaign_links:
                        campaign_links.add(campaign_link)
        return campaign_links

    def prep_firefox():
        print("starting firefox then login naver site.")
        firefox_options = webdriver.FirefoxOptions()                    # firefox 드라이버 옵션 설정
        firefox_options.add_argument('--headless')                      # headless mode
        service = Service(executable_path='/usr/local/bin/geckodriver') # 켁코드라이버 경로
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.get('https://naver.com')
        current_window_handle = driver.current_window_handle            # 현재 열려 있는 창 가져오기
        # <a href class='MyView-module__link_login___HpHMW'> 일때 해당 링크 클릭
        driver.find_element(By.XPATH, "//a[@class='MyView-module__link_login___HpHMW']").click()
        new_window_handle = None                                        # 새롭게 생성된 탭의 핸들을 찾습니다 # 만일 새로운 탭이 없을경우 기존 탭을 사용합니다.
        for handle in driver.window_handles:
            if handle != current_window_handle:
                new_window_handle = handle
                break
            else:
                new_window_handle = handle
        driver.switch_to.window(new_window_handle)
        driver2 = driver
        username = driver2.find_element(By.NAME, 'id')
        pw = driver2.find_element(By.NAME, 'pw')
        username.click()
        driver2.execute_script("arguments[0].value = arguments[1]", username, config.input_id)
        time.sleep(1)
        pw.click()
        driver2.execute_script("arguments[0].value = arguments[1]", pw, config.input_pw)
        time.sleep(1)
        driver2.find_element(By.CLASS_NAME, "btn_login").click()
        time.sleep(1)
        return driver2

    def get_coin(campaign_links):
        d2 = naver_coin_scraper.prep_firefox()
        for link in campaign_links:
            d2.get(link)
            try:
                result = d2.switch_to.alert
                print(result.text)
                result.accept()
            except:
                print("no alert")
                pageSource = d2.page_source
#               print(pageSource)
            time.sleep(5)
        d2.quit()
        print("모든 링크를 방문했습니다.")

    def post_scrap(self):
        campaign_links = set()
        post_check_urls = [ "https://www.clien.net/service/board/jirum",
                            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon" ]
        for base_url in post_check_urls:
            posts = set()
            response = requests.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')          # Send a request to the base URL
            if 'ppomppu.co.kr' in base_url:
                list_subject_links = soup.find_all('td', class_='list_vspace')
                if len(list_subject_links) != 0:
                    for span in list_subject_links:                     # Find all span elements with class 'list_subject' and get 'a' tags
                        a_tag = span.find('a', href=True)
                        if a_tag and '네이버' in a_tag.text:
                            posts.add(str(base_url.split('zboard.php')[0]) + str(a_tag['href']))
                    campaign_links |= naver_coin_scraper.from_ppomppu_page(self, posts, base_url)
                print("searched campaign", len(campaign_links), "from: " + base_url)
            elif 'clien.net' in base_url:
                list_subject_links = soup.find_all('span', class_='list_subject')
                if len(list_subject_links) != 0:
                    for span in list_subject_links:
                        a_tag = span.find('a', href=True)
                        if a_tag and '네이버' in a_tag.text:
                            posts.add(str(base_url.split('/service')[0]) + a_tag['href'])
                    campaign_links |= naver_coin_scraper.from_clien_page(self, posts, base_url)
                print("searched campaign", len(campaign_links), "from: " + base_url)
        if len(campaign_links) >= 1:
            naver_coin_scraper.get_coin(campaign_links)
            self.visited_urls |= posts
            with open(self.visited_urls_file, 'w') as file:                 # Save the updated visited URLs to the file
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
