#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefox에 저장된 네이버 쿠키를 Selenium에서 사용할 JSON 형식으로 추출합니다.

예시:
  python extract_cookies.py --account my-account
  python extract_cookies.py --account my-account --output-dir ./naver_cookies
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import browser_cookie3
except ImportError:
    browser_cookie3 = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Firefox에서 네이버 쿠키를 추출해 naver_cookies/<account>.json 파일로 저장합니다."
    )
    parser.add_argument(
        "--account",
        required=True,
        help="저장할 쿠키 파일명에 사용할 계정 식별자입니다. 예: my-account",
    )
    parser.add_argument(
        "--output-dir",
        default="naver_cookies",
        help="쿠키 JSON을 저장할 디렉토리입니다. 기본값: naver_cookies",
    )
    parser.add_argument(
        "--domain",
        default="naver.com",
        help="추출할 쿠키 도메인입니다. 기본값: naver.com",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Firefox 프로필 경로입니다. 생략하면 browser-cookie3 기본 탐색을 사용합니다.",
    )
    return parser.parse_args()


def validate_account_name(account: str) -> None:
    if not account or account in {".", ".."}:
        raise ValueError("계정 식별자가 올바르지 않습니다.")
    if any(separator in account for separator in ("/", "\\")):
        raise ValueError("계정 식별자에는 경로 구분자를 사용할 수 없습니다.")


def cookie_to_dict(cookie) -> dict:
    cookie_dict = {
        "name": cookie.name,
        "value": cookie.value,
        "domain": cookie.domain,
        "path": cookie.path or "/",
        "secure": bool(cookie.secure),
    }
    if cookie.expires:
        cookie_dict["expiry"] = int(cookie.expires)
    if getattr(cookie, "discard", None) is not None:
        cookie_dict["discard"] = bool(cookie.discard)
    if getattr(cookie, "rest", None):
        rest = cookie._rest
        if "HttpOnly" in rest:
            cookie_dict["httpOnly"] = True
    return cookie_dict


def extract_firefox_cookies(domain: str, profile: str = None) -> list:
    if browser_cookie3 is None:
        raise RuntimeError("browser-cookie3가 설치되어 있지 않습니다. requirements.txt를 설치하세요.")

    kwargs = {"domain_name": domain}
    if profile:
        kwargs["cookie_file"] = str(Path(profile).expanduser() / "cookies.sqlite")

    cookie_jar = browser_cookie3.firefox(**kwargs)
    return [cookie_to_dict(cookie) for cookie in cookie_jar]


def save_cookies(cookies: list, output_dir: Path, account: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{account}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return output_file


def main() -> int:
    args = parse_args()
    try:
        validate_account_name(args.account)
        cookies = extract_firefox_cookies(args.domain, args.profile)
        if not cookies:
            print(f"추출된 쿠키가 없습니다. Firefox에서 {args.domain} 로그인 상태를 확인하세요.")
            return 1

        output_file = save_cookies(cookies, Path(args.output_dir), args.account)
        print(f"쿠키 추출 완료: {len(cookies)}개")
        print(f"저장 위치: {output_file.resolve()}")
        print("서버에서 사용할 때는 이 파일을 프로젝트의 naver_cookies/ 디렉토리에 두세요.")
        return 0
    except Exception as e:
        print(f"쿠키 추출 실패: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
