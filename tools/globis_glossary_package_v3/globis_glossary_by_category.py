import argparse
import hashlib
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_SEARCH_URL = "https://mba.globis.ac.jp/about_mba/glossary/search.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GLOBIS-GlossaryFetcher/3.0; +https://mba.globis.ac.jp)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


@dataclass(frozen=True)
class Category:
    name: str
    category_id: int


CATEGORIES: Sequence[Category] = (
    Category("テクノベート(テクノロジー×イノベーション)", 32),
    Category("アカウンティング", 21),
    Category("ファイナンス", 20),
    Category("マーケティング", 15),
    Category("経営戦略", 16),
    Category("交渉術・ゲーム理論", 31),
    Category("人材マネジメント", 18),
    Category("組織行動学・リーダーシップ", 19),
    Category("論理思考・問題解決", 17),
)


def _uniq_keep_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _page_fingerprint(terms: Sequence[str], hrefs: Sequence[str]) -> str:
    payload = "\n".join([*hrefs, "---", *terms]).encode("utf-8", errors="replace")
    return hashlib.sha256(payload).hexdigest()


def _build_session(*, verify_tls: bool, no_env_proxy: bool) -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = verify_tls
    if no_env_proxy:
        session.trust_env = False

    retry = Retry(
        total=6,
        connect=3,
        read=3,
        status=6,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _configure_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("globis_glossary")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8-sig")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(fh)
    return logger


def _extract_terms_from_results(soup: BeautifulSoup) -> Tuple[List[str], List[str]]:
    terms: List[str] = []
    hrefs: List[str] = []

    # 検索結果の用語リンクは href="detail-xxxxx.html" になる(アクセストップ10等は /about_mba/... なので除外できる)
    candidates = soup.select("a.no_underline.border[href^='detail-']")
    if not candidates:
        candidates = soup.select("a[href^='detail-']")

    for a in candidates:
        href = (a.get("href") or "").strip()
        if not href:
            continue
        h3 = a.select_one("h3")
        text = h3.get_text(" ", strip=True) if h3 else a.get_text(" ", strip=True)
        if "カテゴリー：" in text:
            text = text.split("カテゴリー：", 1)[0].strip()
        if not text:
            continue
        terms.append(text)
        hrefs.append(href)

    return _uniq_keep_order(terms), _uniq_keep_order(hrefs)


def _fetch_page(
    session: requests.Session,
    url: str,
    *,
    timeout_sec: float,
    logger: logging.Logger,
    context: str,
) -> str:
    try:
        r = session.get(url, timeout=timeout_sec)
        status = r.status_code
        if status >= 400:
            logger.warning("%s status=%s url=%s", context, status, url)
        r.raise_for_status()
        r.encoding = r.encoding or "utf-8"
        return r.text
    except requests.exceptions.SSLError as e:
        logger.error("%s SSL error url=%s error=%s", context, url, repr(e))
        raise
    except requests.RequestException as e:
        logger.error("%s request failed url=%s error=%s", context, url, repr(e))
        raise


def _crawl_category(
    session: requests.Session,
    category: Category,
    *,
    timeout_sec: float,
    sleep_sec: float,
    max_pages: int,
    logger: logging.Logger,
) -> List[str]:
    all_terms: List[str] = []
    prev_fp: Optional[str] = None

    page = 0
    while page < max_pages:
        params: Dict[str, str] = {"category": str(category.category_id)}
        if page > 0:
            params["page"] = str(page)
        url = f"{BASE_SEARCH_URL}?{urlencode(params)}"
        context = f"category={category.category_id} page={page}"

        html = _fetch_page(session, url, timeout_sec=timeout_sec, logger=logger, context=context)
        soup = BeautifulSoup(html, "lxml")
        terms, hrefs = _extract_terms_from_results(soup)

        logger.info("%s url=%s terms=%d", context, url, len(terms))

        if not terms:
            logger.info("%s stop=empty", context)
            break

        fp = _page_fingerprint(terms, hrefs)
        if prev_fp is not None and fp == prev_fp:
            logger.warning("%s stop=duplicate_page", context)
            break
        prev_fp = fp

        all_terms.extend(terms)
        page += 1
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    if page >= max_pages:
        logger.warning("category=%s stop=max_pages max_pages=%d", category.category_id, max_pages)

    return _uniq_keep_order(all_terms)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description="GLOBIS MBA 用語集: カテゴリ×ページネーションで用語名のみ抽出")
    p.add_argument("--output", default=os.path.join(base_dir, "glossary_terms.txt"), help="用語名(1行1語)の出力先")
    p.add_argument("--log", default=os.path.join(base_dir, "run.log"), help="ログ出力先")
    p.add_argument("--sleep", type=float, default=0.4, help="ページ間スリープ秒")
    p.add_argument("--timeout", type=float, default=60.0, help="HTTPタイムアウト秒")
    p.add_argument("--max-pages", type=int, default=300, help="カテゴリあたりの最大ページ数(暴走防止)")
    p.add_argument(
        "--insecure",
        action="store_true",
        help="TLS検証を無効化(社内SSL等で止まる場合の最終手段; 推奨はREQUESTS_CA_BUNDLE設定)",
    )
    p.add_argument("--no-env-proxy", action="store_true", help="環境変数プロキシ(HTTP(S)_PROXY)を無視")
    return p.parse_args(list(argv))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    logger = _configure_logger(args.log)

    verify_tls = not args.insecure
    session = _build_session(verify_tls=verify_tls, no_env_proxy=args.no_env_proxy)

    logger.info(
        "start output=%s log=%s insecure=%s no_env_proxy=%s", args.output, args.log, args.insecure, args.no_env_proxy
    )
    all_terms: List[str] = []

    for category in CATEGORIES:
        logger.info("category_start id=%s name=%s", category.category_id, category.name)
        try:
            terms = _crawl_category(
                session,
                category,
                timeout_sec=args.timeout,
                sleep_sec=args.sleep,
                max_pages=args.max_pages,
                logger=logger,
            )
            logger.info("category_done id=%s terms=%d", category.category_id, len(terms))
            all_terms.extend(terms)
        except Exception as e:
            logger.exception("category_failed id=%s name=%s error=%s", category.category_id, category.name, repr(e))
            continue

    uniq_all = _uniq_keep_order(all_terms)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8-sig", newline="\n") as f:
        for t in uniq_all:
            f.write(t)
            f.write("\n")

    logger.info("done categories=%d terms_total=%d terms_unique=%d", len(CATEGORIES), len(all_terms), len(uniq_all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
