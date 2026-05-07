#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 포인트 자동 적립 스크래퍼
  주요 기능:
    - 여러 커뮤니티 사이트에서 네이버 포인트 캠페인 링크 수집
    - 자동 로그인 및 포인트 적립
    - 중복 방문 방지 및 보안 대응
"""
import os
import re
import sys
import time
import fcntl
import shutil
import config
import random
import atexit
import logging
import requests
import tempfile
from pathlib import Path
from typing import Set, Dict, List
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException, 
    TimeoutException, 
    NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, urljoin, parse_qs

def setup_logging() -> logging.Logger:
    """로깅 시스템 설정"""
    logger = logging.getLogger('ncc')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        # 스크립트 파일이 있는 디렉토리에 로그 파일 생성
        script_dir = Path(__file__).parent.absolute()
        log_file = script_dir / 'scraper.log'
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

def avoid_overlap():
    """단일 인스턴스 실행 보장 (PID 파일 사용)"""
    pid_lock_file = Path(sys.argv[0]).with_suffix('.pid')
    try:
        f = open(pid_lock_file, 'w')
        fcntl.lockf(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(os.getpid()))
        f.flush()
    except (IOError, OSError):
        logging.getLogger('ncc').error('이미 실행 중입니다')
        sys.exit(1)
    # 프로그램 종료 시 정리 작업 등록
    atexit.register(_cleanup_pid_file, f, pid_lock_file)
    return f

def _cleanup_pid_file(f, pid_lock_file):
    """PID 파일 정리 작업"""
    try:
        f.close()
        if pid_lock_file.exists():
            pid_lock_file.unlink()
    except Exception as e:
        logging.getLogger('ncc').warning(f'정리 작업 중 오류: {e}')

class NaverCoinScraper:
    """네이버 포인트 자동 적립 스크래퍼"""
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("스크래퍼 초기화 시작")
        # 경로 설정
        self.work_dir = Path(__file__).parent.absolute()
        os.chdir(self.work_dir)
        # 파일 경로
        self.visited_urls_file = self.work_dir / 'visited_urls.txt'
        self.break_point_file = self.work_dir / 'break-point.html'
        self.cookies_dir = self.work_dir / 'naver_cookies'
        self.cookies_dir.mkdir(exist_ok=True)
        self.temp_profile_dirs: List[Path] = []
        # 설정값 (config.py에서 이미 환경변수 처리됨)
        self.gecko_path = config.GECKODRIVER_PATH
        self.delay_hours = config.DELAY_HOURS
        self.min_dwell_time = config.MIN_DWELL_TIME
        self.request_timeout = (10, 30)
        self.request_max_retries = 3
        self.allow_password_login = os.getenv("ALLOW_PASSWORD_LOGIN", "0") == "1"
        # User Agent 설정
        self.request_ua = config.REQUEST_USER_AGENT
        self.firefox_ua = config.FIREFOX_USER_AGENT
        # 휴면 파일 검사
        self._check_break_point()
        # 방문 기록 로드
        self.visited_urls = self._load_visited_urls()
        self.logger.info(f"초기화 완료 - 방문 기록: {len(self.visited_urls)}개")
    
    def _get_naver_accounts(self) -> Dict[str, str]:
        """네이버 계정 정보 가져오기 (config.py에서 로드)"""
        accounts = {}
        # config.py에서 계정 정보 가져오기
        for naver_id, naver_pw in config.naver_login_info.items():
            if (naver_id and naver_pw and 
                not naver_id.startswith('your_naver_id') and 
                not naver_pw.startswith('your_password')):
                accounts[naver_id] = naver_pw
        return accounts
    
    def _check_break_point(self) -> None:
        """보안 휴면 파일 검사"""
        if not self.break_point_file.exists():
            return
        file_age = time.time() - self.break_point_file.stat().st_mtime
        delay_seconds = self.delay_hours * 3600
        if file_age >= delay_seconds:
            self.break_point_file.unlink()
            self.logger.info("휴면 기간 만료, 정상 실행")
        else:
            remaining_hours = (delay_seconds - file_age) / 3600
            self.logger.error(f"네이버 보안으로 인한 휴면 중 (남은 시간: {remaining_hours:.1f}시간)")
            sys.exit(1)
    
    def _load_visited_urls(self) -> Set[str]:
        """방문 기록 로드"""
        try:
            if self.visited_urls_file.exists():
                with open(self.visited_urls_file, 'r', encoding='utf-8') as f:
                    return set(line.strip() for line in f if line.strip())
        except Exception as e:
            self.logger.warning(f"방문 기록 로드 실패: {e}")
        return set()
    
    def _save_visited_urls(self) -> None:
        """방문 기록 저장"""
        try:
            with open(self.visited_urls_file, 'w', encoding='utf-8') as f:
                for url in sorted(self.visited_urls):
                    f.write(f"{url}\n")
            self.logger.info(f"방문 기록 저장 완료: {len(self.visited_urls)}개")
        except Exception as e:
            self.logger.error(f"방문 기록 저장 실패: {e}")

    def _get_with_retries(self, url: str, purpose: str) -> requests.Response:
        """일시적인 네트워크 실패를 흡수하기 위한 HTTP GET 재시도"""
        last_error = None
        for attempt in range(1, self.request_max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": self.request_ua},
                    timeout=self.request_timeout
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_error = e
                if attempt >= self.request_max_retries:
                    break

                wait_time = min(2 ** attempt, 8) + random.uniform(0.2, 0.8)
                self.logger.warning(
                    f"{purpose} 재시도 예정 ({attempt}/{self.request_max_retries}): "
                    f"{url} - {e}"
                )
                time.sleep(wait_time)

        raise last_error
    
    def _save_cookies(self, driver: webdriver.Firefox, account_id: str) -> None:
        """쿠키 저장"""
        try:
            cookies = self._collect_naver_cookies(driver)
            if not self._has_required_auth_cookies(cookies):
                self.logger.warning(
                    f"인증 쿠키가 부족하여 쿠키 저장 건너뜀: {account_id} ({len(cookies)}개)"
                )
                return

            cookie_file = self.cookies_dir / f"{account_id}.json"
            with open(cookie_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            self.logger.info(f"쿠키 저장 완료: {account_id} ({len(cookies)}개)")
        except Exception as e:
            self.logger.error(f"쿠키 저장 실패 ({account_id}): {e}")

    def _collect_naver_cookies(self, driver: webdriver.Firefox) -> list:
        """네이버 관련 도메인의 쿠키를 수집"""
        cookie_map = {}
        for url in ("https://www.naver.com", "https://nid.naver.com"):
            try:
                driver.get(url)
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                for cookie in driver.get_cookies():
                    key = (
                        cookie.get("domain", ""),
                        cookie.get("path", "/"),
                        cookie.get("name", ""),
                    )
                    cookie_map[key] = cookie
            except Exception as e:
                self.logger.debug(f"쿠키 수집용 페이지 접근 실패 ({url}): {e}")
        return list(cookie_map.values())

    def _has_required_auth_cookies(self, cookies: list) -> bool:
        """로그인 복원에 필요한 핵심 쿠키가 있는지 확인"""
        cookie_names = {cookie.get("name") for cookie in cookies}
        return {"NID_AUT", "NID_SES"}.issubset(cookie_names)
    
    def _load_cookies(self, account_id: str) -> list:
        """쿠키 로드"""
        try:
            cookie_file = self.cookies_dir / f"{account_id}.json"
            if cookie_file.exists():
                import json
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                # 쿠키 만료 확인 (24시간)
                if cookies:
                    self.logger.info(f"저장된 쿠키 로드: {account_id} ({len(cookies)}개)")
                    return cookies
        except Exception as e:
            self.logger.warning(f"쿠키 로드 실패 ({account_id}): {e}")
        return []

    def _normalize_cookie(self, cookie: dict) -> dict:
        """Selenium add_cookie 형식으로 쿠키 정규화"""
        normalized = {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain"),
            "path": cookie.get("path", "/"),
            "secure": bool(cookie.get("secure", False)),
        }

        if "httpOnly" in cookie:
            normalized["httpOnly"] = bool(cookie["httpOnly"])

        expiry = cookie.get("expiry")
        if expiry:
            try:
                expiry = int(expiry)
                # browser_cookie3로 추출한 값은 밀리초일 수 있다.
                if expiry > 10**12:
                    expiry //= 1000
                if expiry > int(time.time()):
                    normalized["expiry"] = expiry
            except (TypeError, ValueError):
                pass

        same_site = cookie.get("sameSite")
        if same_site in {"Strict", "Lax", "None"}:
            normalized["sameSite"] = same_site

        return normalized

    def _cookie_seed_url(self, domain: str) -> str:
        """쿠키를 주입하기 위해 먼저 방문할 URL 생성"""
        normalized_domain = (domain or "").lstrip(".")
        if not normalized_domain:
            return "https://www.naver.com"
        if normalized_domain == "naver.com":
            return "https://www.naver.com"
        return f"https://{normalized_domain}"

    def _is_logged_in(self, driver: webdriver.Firefox) -> bool:
        """네이버 로그인 상태 확인"""
        try:
            driver.get("https://www.naver.com")
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            current_url = driver.current_url
            if "nidlogin" in current_url:
                return False

            logout_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='nidlogin.logout']")
            if logout_links:
                return True

            page_text = driver.find_element(By.TAG_NAME, "body").text
            return "로그아웃" in page_text and "NAVER 로그인" not in page_text
        except Exception as e:
            self.logger.warning(f"로그인 상태 확인 실패: {e}")
            return False

    def _seed_cookies(self, driver: webdriver.Firefox, cookies: List[dict]) -> int:
        """도메인별로 페이지를 연 뒤 쿠키 주입"""
        applied_count = 0
        cookies_by_domain: Dict[str, List[dict]] = {}
        for cookie in cookies:
            domain = cookie.get("domain")
            if not domain or not cookie.get("name"):
                continue
            cookies_by_domain.setdefault(domain, []).append(cookie)

        for domain, domain_cookies in cookies_by_domain.items():
            seed_url = self._cookie_seed_url(domain)
            try:
                driver.get(seed_url)
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except Exception as e:
                self.logger.debug(f"쿠키 주입용 페이지 로드 실패 ({seed_url}): {e}")
                continue

            for cookie in domain_cookies:
                normalized = self._normalize_cookie(cookie)
                try:
                    driver.add_cookie(normalized)
                    applied_count += 1
                except Exception as e:
                    self.logger.debug(
                        f"쿠키 적용 실패 ({normalized.get('name')} @ {domain}): {e}"
                    )

        return applied_count
    
    def _apply_cookies(self, driver: webdriver.Firefox, account_id: str) -> bool:
        """쿠키 적용하여 로그인 우회"""
        cookies = self._load_cookies(account_id)
        if not cookies:
            return False
        
        try:
            applied_count = self._seed_cookies(driver, cookies)
            if applied_count == 0:
                self.logger.warning(f"적용 가능한 쿠키가 없음: {account_id}")
                return False

            if self._is_logged_in(driver):
                self.logger.info(f"쿠키로 로그인 성공: {account_id}")
                return True

            self.logger.warning(
                f"쿠키 로그인 실패 (주입 {applied_count}개, 만료 또는 인증 불가): {account_id}"
            )
            return False
        except Exception as e:
            self.logger.error(f"쿠키 적용 실패 ({account_id}): {e}")
            return False
    
    def _create_break_point(self, reason: str = "보안 감지") -> None:
        """휴면 파일 생성"""
        try:
            with open(self.break_point_file, 'w', encoding='utf-8') as f:
                f.write(f"Break point created: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Reason: {reason}\n")
            self.logger.warning(f"휴면 파일 생성: {reason}")
        except Exception as e:
            self.logger.error(f"휴면 파일 생성 실패: {e}")

    def _prepare_firefox_profile(self, account_id: str = None) -> Path:
        """Firefox 프로필 준비

        FIREFOX_PROFILE_ROOT가 지정되면 계정명 하위 프로필을 우선 사용한다.
        FIREFOX_PROFILE_PATH가 지정되면 해당 프로필을 지속 사용한다.
        지정되지 않은 경우 실사용 프로필 잠금 충돌을 피하기 위해 복제본을 사용한다.
        """
        import glob

        profile_root = os.getenv("FIREFOX_PROFILE_ROOT")
        if profile_root and account_id:
            account_profile = Path(profile_root).expanduser() / account_id
            if account_profile.exists():
                self.logger.info(f"계정별 Firefox 프로필 사용: {account_id} -> {account_profile}")
                return account_profile
            self.logger.warning(f"계정별 Firefox 프로필을 찾을 수 없음: {account_profile}")

        configured_profile = os.getenv("FIREFOX_PROFILE_PATH")
        if configured_profile:
            profile_path = Path(configured_profile).expanduser()
            if profile_path.exists():
                self.logger.info(f"지정된 Firefox 프로필 사용: {profile_path}")
                return profile_path
            self.logger.warning(f"지정된 Firefox 프로필을 찾을 수 없음: {profile_path}")

        profile_patterns = [
            "~/Library/Application Support/Firefox/Profiles/*.default*",
            "~/.mozilla/firefox/*.default*",
        ]
        profile_paths = []
        for pattern in profile_patterns:
            profile_paths.extend(glob.glob(os.path.expanduser(pattern)))
        if not profile_paths:
            self.logger.warning("기존 Firefox 프로필을 찾을 수 없음, Selenium 기본 프로필 사용")
            return None

        source_profile = Path(sorted(profile_paths)[-1])
        temp_profile_root = Path(tempfile.mkdtemp(prefix="ncc-firefox-profile-"))
        temp_profile = temp_profile_root / source_profile.name

        def _ignore_profile_files(_, names):
            ignored = {
                ".parentlock",
                "parent.lock",
                "lock",
                "MarionetteActivePort",
                "WebDriverBiDiServer.json",
                "geckodriver.log",
            }
            return [name for name in names if name in ignored]

        try:
            shutil.copytree(source_profile, temp_profile, ignore=_ignore_profile_files)
            self.temp_profile_dirs.append(temp_profile_root)
            self.logger.info(f"Firefox 프로필 복제본 사용: {temp_profile}")
            return temp_profile
        except Exception as e:
            self.logger.warning(f"Firefox 프로필 복제 실패, 기본 프로필로 진행: {e}")
            shutil.rmtree(temp_profile_root, ignore_errors=True)
            return None

    def dwell_and_scroll(self, driver: webdriver.Firefox, min_seconds: int = None) -> None:
        """페이지에서 자연스러운 체류 및 스크롤 동작 수행"""
        if min_seconds is None:
            min_seconds = self.min_dwell_time
        start_time = time.time()
        try:
            # 페이지 로딩 완료 대기
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            self.logger.warning("페이지 로딩 완료 대기 시간 초과")
        except Exception as e:
            self.logger.warning(f"페이지 로딩 상태 확인 실패: {e}")
        try:
            # 페이지 크기 정보 수집
            total_height = driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
            ) or 0
            viewport_height = driver.execute_script("return window.innerHeight;") or 800
            # 스크롤 가능한 높이 계산
            scrollable_height = max(0, total_height - viewport_height)
            if scrollable_height > 0:
                self._perform_natural_scrolling(driver, scrollable_height, viewport_height)
            else:
                self.logger.debug("스크롤할 내용이 없음")
        except Exception as e:
            self.logger.warning(f"스크롤 동작 중 오류: {e}")
        # 최소 체류 시간 보장
        elapsed = time.time() - start_time
        remaining = min_seconds - elapsed
        if remaining > 0:
            sleep_time = remaining + random.uniform(0.3, 0.8)
            self.logger.debug(f"추가 대기: {sleep_time:.1f}초")
            time.sleep(sleep_time)
    
    def _perform_natural_scrolling(self, driver: webdriver.Firefox, 
                                 scrollable_height: int, viewport_height: int) -> None:
        """자연스러운 스크롤 패턴 수행"""
        current_position = 0
        scroll_steps = random.randint(3, 6)
        # 아래로 스크롤
        for i in range(scroll_steps):
            step_size = random.randint(
                int(viewport_height * 0.3), 
                int(viewport_height * 0.8)
            )
            current_position = min(scrollable_height, current_position + step_size)
            driver.execute_script(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}});")
            time.sleep(random.uniform(0.8, 1.6))
        # 위로 약간 스크롤 (자연스러운 읽기 패턴)
        for _ in range(random.randint(1, 3)):
            step_size = random.randint(
                int(viewport_height * 0.1), 
                int(viewport_height * 0.4)
            )
            current_position = max(0, current_position - step_size)
            driver.execute_script(f"window.scrollTo({{top: {current_position}, behavior: 'smooth'}});")
            time.sleep(random.uniform(0.6, 1.2))
        # 키보드 입력으로 자연스러움 추가
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(random.randint(1, 3)):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(random.uniform(0.2, 0.4))
            if random.choice([True, False]):
                body.send_keys(Keys.PAGE_UP)
                time.sleep(random.uniform(0.2, 0.4))
        except NoSuchElementException:
            self.logger.debug("body 요소를 찾을 수 없음")

    def click_point_and_dwell(self, driver: webdriver.Firefox, dwell_seconds: int = None) -> bool:
        """포인트 받기 버튼 클릭 후 체류"""
        if dwell_seconds is None:
            dwell_seconds = self.min_dwell_time
        success = False
        # 포인트 받기 버튼 클릭 시도
        selectors = [
            ".type_no_points .popup_link",
            ".point_btn",
            "[class*='point'] button",
            "button[onclick*='point']"
        ]
        
        for selector in selectors:
            try:
                btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                old_url = driver.current_url
                btn.click()
                self.logger.debug(f"포인트 버튼 클릭 성공: {selector}")
                success = True
                # URL 변경 대기
                try:
                    WebDriverWait(driver, 8).until(
                        lambda d: d.current_url != old_url
                    )
                    self.logger.debug("페이지 이동 확인됨")
                except TimeoutException:
                    self.logger.debug("페이지 이동 없음 (동일 페이지 처리)")
                break
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                self.logger.warning(f"포인트 버튼 클릭 실패 ({selector}): {e}")
                continue
        if not success:
            self.logger.info("포인트 버튼을 찾을 수 없음 (이미 적립되었거나 기간 만료)")
        # 체류 및 스크롤
        self.dwell_and_scroll(driver, dwell_seconds)
        return success

    def get_coin(self, campaign_links: Set[str]) -> None:
        """Firefox를 사용하여 캠페인 링크 방문 및 포인트 적립 (쿠키 기반 로그인)"""
        if not campaign_links:
            self.logger.info("방문할 캠페인 링크가 없습니다")
            return
        accounts = self._get_naver_accounts()
        if not accounts:
            self.logger.error("네이버 계정 정보가 없습니다. config.py 또는 환경변수를 확인하세요")
            return
        self.logger.info(f"Firefox 시작 - 계정 {len(accounts)}개, 링크 {len(campaign_links)}개")
        for account_id, password in accounts.items():
            if not account_id or not password:
                continue
            driver = None
            max_retries = 2
            login_success = False
            
            for attempt in range(1, max_retries + 1):
                try:
                    self.logger.info(f"계정 {account_id} 로그인 시도 ({attempt}/{max_retries})")
                    driver = self._create_firefox_driver(account_id)
                    
                    # 1차: 저장된 쿠키로 로그인 시도
                    if self._apply_cookies(driver, account_id):
                        self.logger.info(f"쿠키 로그인 성공: {account_id}")
                        self._save_cookies(driver, account_id)
                        login_success = True
                        break
                    
                    if not self.allow_password_login:
                        self.logger.error(
                            f"쿠키 로그인 실패, 직접 로그인 비활성화됨: {account_id}"
                        )
                        break

                    # 2차: 쿠키가 없거나 만료되었으면 직접 로그인
                    self.logger.info(f"쿠키 로그인 실패, 직접 로그인 시도: {account_id}")
                    if self._login_naver(driver, account_id, password):
                        # 로그인 성공 시 쿠키 저장
                        self._save_cookies(driver, account_id)
                        login_success = True
                        break
                    else:
                        self.logger.warning(f"로그인 실패 ({attempt}/{max_retries}): {account_id}")
                        if attempt < max_retries:
                            if driver:
                                self._cleanup_driver(driver)
                                driver = None
                            wait_time = random.uniform(3.0, 5.0)
                            self.logger.info(f"{wait_time:.1f}초 후 재시도...")
                            time.sleep(wait_time)
                        else:
                            self.logger.error(f"로그인 최종 실패: {account_id} ({max_retries}회 시도)")
                except Exception as e:
                    self.logger.error(f"계정 {account_id} 처리 중 오류 ({attempt}/{max_retries}): {e}")
                    if driver:
                        self._cleanup_driver(driver)
                        driver = None
                    if attempt < max_retries:
                        wait_time = random.uniform(3.0, 5.0)
                        self.logger.info(f"{wait_time:.1f}초 후 재시도...")
                        time.sleep(wait_time)
            
            # 로그인 성공 시 캠페인 링크 방문
            if login_success and driver:
                self._visit_campaign_links(driver, campaign_links, account_id)
                self._save_cookies(driver, account_id)
            
            # 드라이버 정리
            if driver:
                self._cleanup_driver(driver)
        self.logger.info("모든 링크 방문 완료")
    
    def _create_firefox_driver(self, account_id: str = None) -> webdriver.Firefox:
        """Firefox WebDriver 생성"""
        options = webdriver.FirefoxOptions()
        # headless 모드 제거 (네이버가 headless 감지)
        # options.add_argument('--headless')
        options.add_argument("--window-size=402,874")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        profile_path = self._prepare_firefox_profile(account_id)
        if profile_path:
            options.add_argument("-profile")
            options.add_argument(str(profile_path))
        
        # 자동화 탐지 우회를 위한 설정
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference("general.useragent.override", self.firefox_ua)
        options.set_preference("intl.accept_languages", "ko-KR,ko")
        options.set_preference("network.cookie.cookieBehavior", 0)  # 모든 쿠키 허용
        options.set_preference("javascript.enabled", True)
        options.set_preference("dom.disable_window_open", True)
        options.set_preference("privacy.trackingprotection.enabled", False)
        options.set_preference("permissions.default.image", 1)  # 이미지 로드 허용
        options.set_preference("media.navigator.enabled", True)
        options.set_preference("dom.webnotifications.enabled", False)
        
        try:
            service = Service(executable_path=self.gecko_path)
            driver = webdriver.Firefox(service=service, options=options)
            
            # WebDriver 흔적 제거 (더 강력한 방법)
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            self.logger.info("Firefox 드라이버 생성 완료")
            return driver
        except Exception as e:
            self.logger.error(f"Firefox 드라이버 생성 실패: {e}")
            raise
    
    def _login_naver(self, driver: webdriver.Firefox, account_id: str, password: str) -> bool:
        """네이버 로그인 수행 (PyAutoGUI + 윈도우 포커스)"""
        try:
            import pyautogui
            
            login_url = 'https://nid.naver.com/nidlogin.login'
            driver.get(login_url)
            # 페이지 로딩 대기
            time.sleep(random.uniform(3.0, 5.0))
            
            # 캡차 감지
            if self._check_captcha(driver):
                self.logger.error(f"캡차 감지됨: {account_id}")
                self._save_login_screenshot(driver, account_id, "captcha_detected")
                return False
            
            # 아이디 필드 클릭 및 포커스
            id_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "id"))
            )
            driver.execute_script("arguments[0].focus();", id_field)
            id_field.click()
            time.sleep(1.5)
            
            # PyAutoGUI로 실제 키보드 입력
            pyautogui.typewrite(account_id, interval=0.15)
            time.sleep(random.uniform(2.0, 3.0))
            
            # 비밀번호 필드 클릭 및 포커스
            pw_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.NAME, "pw"))
            )
            driver.execute_script("arguments[0].focus();", pw_field)
            pw_field.click()
            time.sleep(1.5)
            
            # PyAutoGUI로 실제 키보드 입력
            pyautogui.typewrite(password, interval=0.15)
            time.sleep(random.uniform(2.0, 3.0))
            
            # 로그인 버튼 클릭
            login_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "log.login"))
            )
            time.sleep(random.uniform(1.0, 2.0))
            login_btn.click()
            
            # 로그인 완료 대기
            self.logger.info(f"로그인 처리 대기 중: {account_id}")
            try:
                WebDriverWait(driver, 40).until(
                    lambda d: "naver.com" in d.current_url and "nidlogin" not in d.current_url
                )
                self.logger.info(f"로그인 성공 (메인 페이지 이동): {account_id}")
                return True
            except TimeoutException:
                current_url = driver.current_url
                self.logger.info(f"현재 URL: {current_url}")
                if "nid.naver.com" not in current_url or "login" not in current_url:
                    self.logger.info(f"로그인 성공 (로그인 페이지 이탈): {account_id}")
                    return True
                
                # 캡차 재감지
                if self._check_captcha(driver):
                    self.logger.error(f"로그인 후 캡차 감지: {account_id}")
                    self._save_login_screenshot(driver, account_id, "captcha_after_login")
                    return False
                
                # 에러 메시지 확인
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error']")
                    for elem in error_elements:
                        if elem.is_displayed() and elem.text.strip():
                            self.logger.error(f"로그인 에러 메시지: {elem.text.strip()}")
                            break
                except Exception:
                    pass
                
                self._save_login_screenshot(driver, account_id, "timeout")
                self.logger.error(f"로그인 시간 초과: {account_id}")
                return False
        except Exception as e:
            self.logger.error(f"로그인 실패 ({account_id}): {e}")
            try:
                self._save_login_screenshot(driver, account_id, "exception")
            except Exception:
                pass
            return False
    
    def _check_captcha(self, driver: webdriver.Firefox) -> bool:
        """캡차 존재 여부 확인"""
        try:
            # 캡차 관련 키워드 확인
            captcha_indicators = [
                "자동입력방지문자",
                "captcha",
                "CAPTCHA",
                "보안문자",
                "security code"
            ]
            
            page_text = driver.find_element(By.TAG_NAME, "body").text
            for indicator in captcha_indicators:
                if indicator in page_text:
                    self.logger.warning(f"캡차 지표 발견: {indicator}")
                    return True
            
            # 캡차 이미지 요소 확인
            captcha_elements = driver.find_elements(By.CSS_SELECTOR, 
                "img[src*='captcha'], img[src*='security'], .captcha, #captcha")
            if captcha_elements:
                self.logger.warning("캡차 이미지 요소 발견")
                return True
            
            return False
        except Exception as e:
            self.logger.debug(f"캡차 확인 중 오류: {e}")
            return False

    def _save_login_screenshot(self, driver: webdriver.Firefox, account_id: str, reason: str) -> None:
        """로그인 실패 시 스크린샷 저장"""
        try:
            screenshot_dir = self.work_dir / 'login_screenshots'
            screenshot_dir.mkdir(exist_ok=True)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"login_fail_{account_id}_{timestamp}_{reason}.png"
            filepath = screenshot_dir / filename
            driver.save_screenshot(str(filepath))
            self.logger.info(f"스크린샷 저장: {filepath}")
        except Exception as e:
            self.logger.warning(f"스크린샷 저장 실패: {e}")
    
    def _visit_campaign_links(self, driver: webdriver.Firefox, 
                            campaign_links: Set[str], account_id: str) -> None:
        """캠페인 링크들을 순차적으로 방문"""
        success_count = 0
        for i, link in enumerate(campaign_links, 1):
            try:
                self.logger.info(f"[{account_id}] 방문 중 ({i}/{len(campaign_links)}): {link}")
                driver.get(link)
                time.sleep(random.uniform(1.0, 2.0))
                # Alert 처리
                self._handle_alert(driver)
                # 사이트별 처리
                if self._process_campaign_site(driver):
                    success_count += 1
                # 링크 간 대기
                time.sleep(random.uniform(0.8, 1.5))
            except Exception as e:
                self.logger.warning(f"링크 방문 실패 ({link}): {e}")
                continue
        self.logger.info(f"[{account_id}] 방문 완료: {success_count}/{len(campaign_links)}")
    
    def _handle_alert(self, driver: webdriver.Firefox) -> None:
        """Alert 팝업 처리"""
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            self.logger.info(f"Alert 감지: {alert_text}")
            time.sleep(random.uniform(0.5, 1.0))
            alert.accept()
            time.sleep(random.uniform(0.3, 0.6))
        except NoAlertPresentException:
            pass
        except Exception as e:
            self.logger.warning(f"Alert 처리 실패: {e}")
    
    def _process_campaign_site(self, driver: webdriver.Firefox) -> bool:
        """캠페인 사이트별 처리 로직"""
        try:
            current_url = driver.current_url
            parsed_url = urlparse(current_url)
            if parsed_url.netloc == "campaign2.naver.com" and "/npay/v2/click-point/" in parsed_url.path:
                # 네이버 포인트 캠페인
                return self.click_point_and_dwell(driver)
            elif parsed_url.netloc == "ofw.adison.co" and "/u/naverpay/ads/" in parsed_url.path:
                # Adison 광고
                self.dwell_and_scroll(driver)
                return True
            else:
                # 기타 사이트
                self.dwell_and_scroll(driver)
                return True
        except Exception as e:
            self.logger.warning(f"사이트 처리 중 오류: {e}")
            return False
    
    def _cleanup_driver(self, driver: webdriver.Firefox) -> None:
        """WebDriver 정리"""
        try:
            driver.quit()
            time.sleep(0.5)  # 완전 종료 대기
        except Exception as e:
            self.logger.warning(f"드라이버 정리 실패: {e}")
        finally:
            while self.temp_profile_dirs:
                profile_dir = self.temp_profile_dirs.pop()
                shutil.rmtree(profile_dir, ignore_errors=True)

    def campaign_scrap(self, posts: Set[str]) -> Set[str]:
        """게시글에서 캠페인 URL 추출"""
        campaign_links = set()
        if not posts:
            return campaign_links
        self.logger.info(f"캠페인 URL 추출 시작: {len(posts)}개 게시글")
        for i, post_url in enumerate(posts, 1):
            if post_url in self.visited_urls:
                self.logger.debug(f"이미 처리된 게시글 건너뜀: {post_url}")
                continue
            try:
                self.logger.debug(f"게시글 분석 중 ({i}/{len(posts)}): {post_url}")
                # 게시글 내용 가져오기
                response = self._get_with_retries(post_url, "게시글 가져오기")
                # URL 후보 추출
                candidates = self._extract_url_candidates(response.text, post_url)
                # 캠페인 URL 필터링
                new_campaigns = self._filter_campaign_urls(candidates)
                campaign_links.update(new_campaigns)
                if new_campaigns:
                    self.logger.info(f"새 캠페인 발견 ({len(new_campaigns)}개): {post_url}")
                # 요청 간 대기
                time.sleep(random.uniform(0.3, 0.8))
            except requests.RequestException as e:
                self.logger.warning(f"게시글 가져오기 실패 ({post_url}): {e}")
                continue
            except Exception as e:
                self.logger.error(f"게시글 처리 중 오류 ({post_url}): {e}")
                continue
        self.logger.info(f"캠페인 URL 추출 완료: {len(campaign_links)}개")
        return campaign_links
    
    def _extract_url_candidates(self, html_content: str, base_url: str) -> Set[str]:
        """HTML에서 URL 후보들 추출"""
        soup = BeautifulSoup(html_content, 'html.parser')
        candidates = set()
        # 1. a 태그의 href, data-href 속성
        for a_tag in soup.find_all('a'):
            for attr in ('href', 'data-href'):
                href = a_tag.get(attr)
                if href:
                    candidates.add(href.strip())
            # 2. onclick 속성에서 URL 추출
            onclick = a_tag.get('onclick')
            if onclick:
                url_matches = re.findall(r"['\"](https?://[^'\"]+)['\"]", onclick)
                candidates.update(url_matches)
        # 3. 본문 텍스트에서 URL 추출
        text_content = soup.get_text(" ", strip=True)
        text_urls = re.findall(r'https?://[^\s\'"<>()]+', text_content)
        candidates.update(text_urls)
        # 4. URL 정규화
        normalized_urls = set()
        base_parsed = urlparse(base_url)
        base_netloc = f"{base_parsed.scheme}://{base_parsed.netloc}"
        for url in candidates:
            try:
                # 스킴 없는 URL 처리
                if url.startswith("//"):
                    url = "https:" + url
                # 상대 경로 처리
                elif not urlparse(url).scheme:
                    url = urljoin(base_netloc + "/", url)
                # 유효한 URL인지 확인
                parsed = urlparse(url)
                if parsed.scheme in ('http', 'https') and parsed.netloc:
                    normalized_urls.add(url)
            except Exception:
                continue
        return normalized_urls
    
    def _filter_campaign_urls(self, url_candidates: Set[str]) -> Set[str]:
        """캠페인 URL 필터링"""
        campaign_urls = set()
        for url in url_candidates:
            try:
                parsed = urlparse(url)
                # 네이버 포인트 캠페인
                if (parsed.netloc == "campaign2.naver.com" and 
                    "/npay/v2/click-point/" in parsed.path):
                    query_params = parse_qs(parsed.query)
                    if "eventId" in query_params:
                        campaign_urls.add(url)
                        continue
                # Adison 광고
                if (parsed.netloc == "ofw.adison.co" and 
                    "/u/naverpay/ads/" in parsed.path):
                    campaign_urls.add(url)
                    continue
                # 기타 네이버 관련 캠페인 (확장 가능)
                if "naver" in parsed.netloc and any(keyword in parsed.path.lower() 
                    for keyword in ["point", "campaign", "event"]):
                    campaign_urls.add(url)
            except Exception as e:
                self.logger.debug(f"URL 필터링 중 오류 ({url}): {e}")
                continue
        return campaign_urls

    def post_scrap(self) -> None:
        """게시판에서 포스트 수집 및 캠페인 실행"""
        self.logger.info("게시판 스크래핑 시작")
        # 게시글 수집
        posts = self._collect_posts_from_sites()
        if not posts:
            self.logger.warning("수집된 게시글이 없습니다")
            return
        # 캠페인 URL 추출
        campaign_links = self.campaign_scrap(posts)
        if not campaign_links:
            self.logger.info("발견된 캠페인 링크가 없습니다")
        else:
            # 캠페인 실행
            self.get_coin(campaign_links)
        # 방문 기록 교체 (새로운 게시글로 덮어쓰기)
        self.visited_urls = posts
        self._save_visited_urls()
        self.logger.info("게시판 스크래핑 완료")
    
    def _collect_posts_from_sites(self) -> Set[str]:
        """여러 사이트에서 게시글 수집"""
        all_posts = set()
        for site_url, site_config in config.SCRAPING_SITES.items():
            try:
                posts = self._collect_posts_from_site(site_url, site_config)
                all_posts.update(posts)
                self.logger.info(f"{len(posts)}개 게시글 수집: {site_url}")
                # 사이트 간 대기
                time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                self.logger.error(f"사이트 스크래핑 실패 ({site_url}): {e}")
                continue
        self.logger.info(f"총 {len(all_posts)}개 게시글 수집 완료")
        return all_posts
    
    def _collect_posts_from_site(self, site_url: str, site_config: Dict[str, str]) -> Set[str]:
        """단일 사이트에서 게시글 수집"""
        posts = set()
        try:
            response = self._get_with_retries(site_url, "사이트 접근")
            soup = BeautifulSoup(response.text, 'html.parser')
            hostname = urlparse(site_url).hostname
            # 게시글 링크 추출
            elements = soup.find_all(site_config["tag"], class_=site_config["class"])
            for element in elements:
                try:
                    post_url = self._extract_post_url(element, site_url, hostname)
                    if post_url and self._is_naver_related_post(element):
                        posts.add(post_url)
                except Exception as e:
                    self.logger.debug(f"게시글 URL 추출 실패: {e}")
                    continue
        except requests.RequestException as e:
            self.logger.warning(
                f"사이트 접근 최종 실패 ({site_url}, {self.request_max_retries}회 시도): {e}"
            )
        except Exception as e:
            self.logger.error(f"사이트 파싱 실패 ({site_url}): {e}")
        return posts
    
    def _extract_post_url(self, element, base_url: str, hostname: str) -> str:
        """요소에서 게시글 URL 추출"""
        a_tag = element.find('a', href=True)
        # 다모앙의 경우 두 번째 a 태그 사용
        if hostname == "damoang.net" and a_tag:
            next_a = a_tag.find_next('a', href=True)
            if next_a:
                a_tag = next_a
        if a_tag and a_tag.get('href'):
            return urljoin(base_url, a_tag['href'])
        return ""
    
    def _is_naver_related_post(self, element) -> bool:
        """네이버 관련 게시글인지 확인"""
        text_content = element.get_text(strip=True).lower()
        naver_keywords = ['네이버', 'naver', '포인트', 'point', '적립']
        return any(keyword in text_content for keyword in naver_keywords)

def main():
    """메인 실행 함수"""
    # 단일 인스턴스 보장
    avoid_overlap()
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("네이버 포인트 스크래퍼 시작")
    logger.info("=" * 50)
    try:
        # 스크래퍼 실행
        scraper = NaverCoinScraper()
        scraper.post_scrap()
        logger.info("스크래퍼 정상 종료")
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("=" * 50)

if __name__ == "__main__":
    main()
