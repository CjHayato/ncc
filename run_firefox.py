#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import fcntl
import config
import random
import atexit
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, urljoin, parse_qs

def avoid_overlab():
    """Single-instance guard with PID file that is cleaned up on exit."""
    pid_lock_file = sys.argv[0] + '.pid'
    f = open(pid_lock_file, 'w')
    try:
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print('이미 실행 중입니다')
        sys.exit(1)

    def _cleanup():
        try:
            try:
                f.close()
            except Exception:
                pass
            if os.path.exists(pid_lock_file):
                os.remove(pid_lock_file)
        except Exception:
            pass
    atexit.register(_cleanup)

class naver_coin_scraper:
    def __init__(self):
        # ---- 환경 설정 ----
        self.gecko = '/usr/local/bin/geckodriver'                  # geckodriver 경로
        delay_hour = 48                                            # naver security 노출 시 휴면 시간
        self.pwd = os.path.abspath(os.path.join(__file__,  ".."))
        os.chdir(self.pwd)
        self.tdb = self.pwd + '/visited_urls.txt'
        self.log = self.pwd + '/scrap-link.log'
        self.bp  = self.pwd + '/break-point.html'
        self.rqua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"
        self.ffua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Mobile/15E148 Safari/604.1"

        # ---- 휴면 파일 검사 ----
        if os.path.isfile(self.bp):
            if delay_hour*60*60 <= int(time.time()-os.path.getmtime(self.bp)):
                os.remove(self.bp)
            else:
                print(f"it's need yo delay for {delay_hour} hour. coz naver security.")
                sys.exit(1)

        # ---- 방문 기록 로드 ----
        try:
            with open(self.tdb, 'r') as file:
                self.visited_urls = set(file.read().splitlines())
        except FileNotFoundError:
            self.visited_urls = set()

    # -------------------- 유틸: 체류 + 스크롤 --------------------
    def dwell_and_scroll(self, driver, min_seconds=6):
        start = time.time()
        # readyState complete 대기 (실패해도 진행)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            pass

        # 페이지 높이/뷰포트 확인
        try:
            total_h = driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
            ) or 0
            viewport = driver.execute_script("return window.innerHeight;") or 800
        except Exception:
            total_h, viewport = 0, 800

        # 아래로 여러 번 스크롤
        pos = 0
        down_steps = max(3, int(min_seconds // 1))
        for _ in range(down_steps):
            step = random.randint(int(viewport * 0.4), int(viewport * 0.9))
            pos = min(max(total_h - viewport, 0), pos + step)
            driver.execute_script("window.scrollTo({top: arguments[0]});", pos)
            time.sleep(random.uniform(0.8, 1.6))

        # 위로 약간 스크롤
        for _ in range(2):
            step = random.randint(int(viewport * 0.2), int(viewport * 0.5))
            pos = max(0, pos - step)
            driver.execute_script("window.scrollTo({top: arguments[0]});", pos)
            time.sleep(random.uniform(0.6, 1.2))

        # 키 입력으로 액션 보강
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(2):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.25)
            body.send_keys(Keys.PAGE_UP)
            time.sleep(0.25)
        except Exception:
            pass

        # 최소 체류시간 보장
        remain = min_seconds - (time.time() - start)
        if remain > 0:
            time.sleep(remain + random.uniform(0.3, 0.8))

    # -------------------- 유틸: '포인트 받기' → 리다이렉트 → 체류 --------------------
    def click_point_and_dwell(self, driver, dwell_seconds=6):
        # 팝업 버튼 클릭
        try:
            btn = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".type_no_points .popup_link"))
            )
            btn.click()
        except Exception:
            # 팝업이 없거나 이미 적립/기간외 등일 수 있음
            pass
            #with open(self.log, "a") as f:
            #    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' popup not found/click failed\n')

        # URL 변경 대기 (replace 또는 SPA 반영)
        try:
            old_url = driver.current_url
            WebDriverWait(driver, 12).until(lambda d: d.current_url != old_url)
        except Exception:
            pass

        # 다음 페이지에서 체류 + 스크롤
        self.dwell_and_scroll(driver, min_seconds=dwell_seconds)

    # -------------------- Firefox로 로그인 → 각 링크 방문 --------------------
    def get_coin(self, campaign_links):
        print("starting firefox and try to login naver site.")
        f_opts = webdriver.FirefoxOptions()
        f_opts.add_argument('--headless')
        f_opts.add_argument("--window-size=402,874")
        f_opts.add_argument("--disable-gpu")
        f_opts.set_preference("network.cookie.cookieBehavior", 1)
        f_opts.set_preference("general.useragent.override", self.ffua)
        f_opts.set_preference("intl.accept_languages", "ko")

        for nid, npw in config.naver_login_info.items():
            if nid is None or nid == "" or nid.startswith("naver_ID"):  # 더미 아이디 skip
                continue

            driver = webdriver.Firefox(service=Service(executable_path=self.gecko), options=f_opts)
            try:
                # webdriver 흔적 최소화
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                # 로그인
                driver.get('https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/')
                driver.implicitly_wait(10)
                driver.execute_script("document.getElementsByName('id')[0].value='" + nid + "'")
                driver.find_element(By.XPATH, '//*[@id="id"]').send_keys(Keys.TAB)
                driver.execute_script("document.getElementsByName('pw')[0].value='" + npw + "'")
                time.sleep(random.uniform(1, 3))
                driver.find_element(By.XPATH, '//*[@id="pw"]').send_keys(Keys.ENTER)
                driver.implicitly_wait(30)

                with open(self.log, "a") as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S') + f' naver login ok, {len(campaign_links)} links\n')

                # 각 캠페인 링크 방문
                for link in campaign_links:
                    driver.get(link)
                    driver.implicitly_wait(10)

                    # 즉시 뜨는 alert 처리 (있으면 닫고 진행)
                    try:
                        result = driver.switch_to.alert
                        with open(self.log, "a") as f:
                            f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + result.text + '\n')
                        time.sleep(random.uniform(0.8, 1.4))
                        result.accept()
                        time.sleep(random.uniform(0.4, 0.8))
                    except (NameError, NoAlertPresentException):
                        pass

                    # URL 기준 분기
                    pu = urlparse(driver.current_url)
                    if pu.netloc == "campaign2.naver.com" and "/npay/v2/click-point/" in pu.path:
                        # '포인트 받기' 누르고 다음 페이지 체류
                        self.click_point_and_dwell(driver, dwell_seconds=6)
                    elif pu.netloc == "ofw.adison.co" and "/u/naverpay/ads/" in pu.path:
                        # Adison는 내부 흐름상 체류만으로 충분한 케이스가 대부분
                        self.dwell_and_scroll(driver, min_seconds=6)
                    else:
                        # 기타 케이스도 최소 체류
                        self.dwell_and_scroll(driver, min_seconds=6)

                    with open(self.log, "a") as f:
                        f.write(time.strftime('%Y-%m-%d %H:%M:%S') + ' visited ' + link + '\n')

                    time.sleep(random.uniform(0.6, 1.2))

            finally:
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(0.5)  # WebDriver 완전 종료 여유

        print("모든 링크를 방문했습니다.")
        return  # ✅ 명시적으로 함수 종료

    # -------------------- 게시글에서 캠페인 URL 추출 --------------------
    def campaign_scrap(self, posts, campaign_links):
        if len(posts) != 0:
            for link in posts:
                if link in self.visited_urls:                      # 이미 처리한 게시글은 건너뜀
                    continue
                try:
                    res = requests.get(link, headers={"User-Agent": self.rqua}, timeout=10)
                except Exception as e:
                    with open(self.log, "a") as f:
                        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} fetch-error {link} {e}\n")
                    continue

                inner_soup = BeautifulSoup(res.text, 'html.parser')
                candidates = set()

                # 1) 표준 a[href], data-href
                for a_tag in inner_soup.find_all('a'):
                    for attr in ('href', 'data-href'):
                        href = a_tag.get(attr)
                        if href:
                            candidates.add(href)

                    # 2) onclick 속성에서 URL 추출 (window.open / location 등)
                    onclick = a_tag.get('onclick')
                    if onclick:
                        m = re.search(r"['\"](https?://[^'\"]+)['\"]", onclick)
                        if m:
                            candidates.add(m.group(1))

                # 3) 본문 텍스트에서 URL-like 문자열 추가 추출 (뽐뿌 등)
                text_urls = re.findall(r'https?://[^\s\'"<>]+', inner_soup.get_text(" ", strip=True))
                candidates.update(text_urls)

                # 4) //domain/path (스킴 없는 링크) 정규화 + 상대경로 보정
                normed = set()
                base = urlparse(link)
                baseurl = f"{base.scheme}://{base.netloc}"
                for u in candidates:
                    if u.startswith("//"):
                        u = "https:" + u
                    if not urlparse(u).scheme:
                        u = urljoin(baseurl + "/", u)
                    normed.add(u)

                # 5) 캠페인 URL 필터링 (네이버 & Adison)
                for inlink in normed:
                    try:
                        pu = urlparse(inlink)
                        is_naver_clickpoint = (
                            pu.netloc == "campaign2.naver.com"
                            and "/npay/v2/click-point/" in pu.path
                            and "eventId" in parse_qs(pu.query)
                        )
                        is_adison_clickpoint = (
                            pu.netloc == "ofw.adison.co"
                            and "/u/naverpay/ads/" in pu.path
                        )
                        if (is_naver_clickpoint or is_adison_clickpoint) and inlink not in campaign_links:
                            campaign_links.add(inlink)
                    except Exception:
                        continue

        return campaign_links

    # -------------------- 게시판 순회 진입점 --------------------
    def post_scrap(self):
        campaign_links, posts = set(), set()
        post_check_urls = [
            "https://damoang.net/economy",
            "https://www.clien.net/service/board/jirum",
            "https://bbs.ruliweb.com/market/board/1020",
            "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon",
        ]

        # 게시판별 목록 파싱 (간략: 각 보드 페이지 자체를 posts에 넣고 campaign_scrap에서 URL 추출)
        for base_url in post_check_urls:
            try:
                response = requests.get(base_url, headers={"User-Agent": self.rqua})
                soup = BeautifulSoup(response.text, 'html.parser')
                post = set()
                host = urlparse(base_url).hostname
                if host and host == "damoang.net":                     # damoang: list-group-item - li
                    row_tag, row_class = 'div', 'flex-grow-1 overflow-hidden'
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
                        if host == "damoang.net":                      # damoang 은 두번째 a href가 진짜임
                            a_tag = a_tag.find_next('a', href=True)
                        if a_tag and '네이버' in a_tag.text.strip():
                            post.add(urljoin(base_url, a_tag['href'])) # baseurl과a href 을 조합해 캠페인에 추가 한다
            except Exception:
                continue
            posts |= post                                              # set() + set()
            print(len(post), "of article from: " + base_url)

        # 캠페인 URL 추출
        campaign_links = self.campaign_scrap(posts, campaign_links)
        print("Discovered glean URLs:", len(campaign_links))
        # 캠페인 방문
        if len(campaign_links) >= 1:
            self.get_coin(campaign_links)
            # 방문 기록 저장 (원래 동작 유지: 게시판 URL 기준 저장)
            self.visited_urls = posts
            with open(self.tdb, 'w') as file:
                for url in sorted(self.visited_urls):
                    file.write(url + '\n')

def main():
    avoid_overlab()
    ncc = naver_coin_scraper()
    with open(ncc.log, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} START\n")
    ncc.post_scrap()
    with open(ncc.log, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} END\n")

if __name__ == "__main__":
    main()

exit(0)
