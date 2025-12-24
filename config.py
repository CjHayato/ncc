"""
네이버 포인트 스크래퍼 설정 파일
  네이버 로그인 전용 아이디 생성: https://help.naver.com/service/5640/contents/10219?lang=ko
"""
import os

# ==================== 네이버 계정 정보 ====================
# 여기에 네이버 로그인 전용 아이디와 비밀번호를 입력하세요
naver_login_info = {
    'your_naver_id_1': 'your_password_1',
    'your_naver_id_2': 'your_password_2',
    'your_naver_id_3': 'your_password_3',
}

# ==================== 기본 설정 ====================
# GeckoDriver 경로 (환경변수 GECKODRIVER_PATH로 오버라이드 가능)
GECKODRIVER_PATH = os.getenv('GECKODRIVER_PATH', '/usr/local/bin/geckodriver')
# 네이버 보안 감지 시 휴면 시간 (시간 단위, 환경변수 DELAY_HOURS로 오버라이드 가능)
DELAY_HOURS = int(os.getenv('DELAY_HOURS', '48'))
# 페이지 최소 체류 시간 (초 단위, 환경변수 MIN_DWELL_TIME으로 오버라이드 가능)
MIN_DWELL_TIME = int(os.getenv('MIN_DWELL_TIME', '6'))

# ==================== User Agent 설정 ====================
# 게시판 스크래핑용 User Agent (PC 브라우저)
REQUEST_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"
# Firefox 자동화용 User Agent (모바일 브라우저)
FIREFOX_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0.1 Mobile/15E148 Safari/604.1"

# ==================== 스크래핑 대상 사이트 설정 ====================
SCRAPING_SITES = {
    "https://damoang.net/economy": {
        "tag": "div",
        "class": "flex-grow-1 overflow-hidden",
        "domain": "damoang.net"
    },
    "https://www.clien.net/service/board/jirum": {
        "tag": "span",
        "class": "list_subject",
        "domain": "clien.net"
    },
    "https://bbs.ruliweb.com/market/board/1020": {
        "tag": "td",
        "class": "subject",
        "domain": "ruliweb.com"
    },
    "https://www.ppomppu.co.kr/zboard/zboard.php?id=coupon": {
        "tag": "td",
        "class": "baseList-space",
        "domain": "ppomppu.co.kr"
    },
}
