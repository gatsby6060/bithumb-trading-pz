"""
LangChain Phase 3 — @tool 등록 모음

여기에 등록된 함수들은 LangChain 에이전트가 "도구 목록"으로 인식합니다.
AI는 사용자의 질문을 받으면 스스로 어떤 도구를 호출할지 판단합니다.

현재 등록된 도구:
  - fetch_crypto_news   : Google + Investing.com RSS에서 최신 뉴스 수집
  - get_current_price   : 빗썸 REST API로 실시간 시세 조회
  - get_market_summary  : 위 두 도구를 종합한 시장 요약 제공
"""
import json
import asyncio
import requests
from typing import Optional
from langchain_core.tools import tool

from data_collectors.news_crawler import NewsCrawler


# ─────────────────────────────────────────────────────────
# Tool 1: 최신 암호화폐 뉴스 수집
# ─────────────────────────────────────────────────────────
@tool
def fetch_crypto_news(keyword: str = "비트코인") -> str:
    """
    Google News와 Investing.com RSS에서 최신 암호화폐 뉴스 헤드라인을 가져옵니다.
    keyword: 검색할 코인 이름 (예: '비트코인', '이더리움', '리플')
    새로운 뉴스가 없으면 이력에서 최근 10개를 반환합니다.
    """
    # 에이전트가 인자를 JSON dict나 JSON 문자열로 넘길 경우를 처리
    if isinstance(keyword, dict):
        keyword = keyword.get("keyword", "비트코인")
    elif isinstance(keyword, str):
        keyword = keyword.strip()
        if keyword.startswith("{"):
            try:
                parsed = json.loads(keyword)
                keyword = parsed.get("keyword", "비트코인")
            except json.JSONDecodeError:
                pass
    keyword = str(keyword).replace('\n', '').strip()

    try:
        crawler = NewsCrawler(keyword)
        news_list = crawler.fetch_latest_news()

        if not news_list:
            # 새 뉴스가 없을 경우 히스토리에서 최신 10개 반환
            import os, json as _json
            history_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "news_history.json"
            )
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    history = _json.load(f)
                # 타임스탬프 기준 내림차순 정렬 후 10개
                history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
                news_list = history[:10]

        if not news_list:
            return "현재 수집된 뉴스가 없습니다."

        lines = [f"[{i+1}] {n['title']} ({n.get('published', '')})"
                 for i, n in enumerate(news_list[:10])]
        return f"📰 '{keyword}' 최신 뉴스 {len(lines)}건:\n" + "\n".join(lines)

    except Exception as e:
        return f"뉴스 수집 오류: {e}"


# ─────────────────────────────────────────────────────────
# Tool 2: 빗썸 실시간 시세 조회
# ─────────────────────────────────────────────────────────
@tool
def get_current_price(symbol: str = "BTC") -> str:
    """
    빗썸 거래소에서 특정 코인의 현재 시세(원화 기준)를 실시간으로 조회합니다.
    symbol: 코인 심볼 (예: 'BTC', 'ETH', 'XRP', 'SOL')
    """
    # 에이전트가 인자를 JSON dict나 JSON 문자열로 넘길 경우를 처리
    if isinstance(symbol, dict):
        symbol = symbol.get("symbol", "BTC")
    elif isinstance(symbol, str):
        symbol = symbol.strip()
        if symbol.startswith("{"):
            try:
                parsed = json.loads(symbol)
                symbol = parsed.get("symbol", "BTC")
            except json.JSONDecodeError:
                pass
    symbol = str(symbol).replace('\n', '').strip()

    try:
        url = f"https://api.bithumb.com/public/ticker/{symbol.upper()}_KRW"
        headers = {"accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "0000":
                d = data["data"]
                price      = int(float(d.get("closing_price", 0)))
                high       = int(float(d.get("max_price", 0)))
                low        = int(float(d.get("min_price", 0)))
                change_rate = float(d.get("fluctate_rate_24H", 0))
                volume     = float(d.get("units_traded_24H", 0))

                sign = "▲" if change_rate >= 0 else "▼"
                return (
                    f"📊 빗썸 {symbol.upper()}/KRW 실시간 시세\n"
                    f"  현재가  : {price:,}원\n"
                    f"  등락률  : {sign} {abs(change_rate):.2f}% (24H)\n"
                    f"  24H 고가: {high:,}원\n"
                    f"  24H 저가: {low:,}원\n"
                    f"  24H 거래량: {volume:,.2f} {symbol.upper()}"
                )
        return f"{symbol} 시세 조회 실패 (HTTP {res.status_code})"

    except Exception as e:
        return f"시세 조회 오류: {e}"


# ─────────────────────────────────────────────────────────
# Tool 3: 시장 종합 요약 (뉴스 + 시세 one-shot)
# ─────────────────────────────────────────────────────────
@tool
def get_market_summary(symbol: str = "BTC") -> str:
    """
    특정 코인의 현재 시세와 최신 뉴스를 함께 조회하여 종합 시장 상황을 반환합니다.
    에이전트가 단 한 번의 호출로 뉴스+가격 정보를 모두 얻을 때 사용합니다.
    symbol: 코인 심볼 (예: 'BTC', 'ETH')
    """
    # 에이전트가 인자를 JSON dict나 JSON 문자열로 넘길 경우를 처리
    if isinstance(symbol, dict):
        symbol = symbol.get("symbol", "BTC")
    elif isinstance(symbol, str):
        symbol = symbol.strip()
        if symbol.startswith("{"):
            try:
                parsed = json.loads(symbol)
                symbol = parsed.get("symbol", "BTC")
            except json.JSONDecodeError:
                pass
    symbol = str(symbol).replace('\n', '').strip()

    # 키워드 매핑 (심볼 → 한국어 검색어)
    keyword_map = {
        "BTC":  "비트코인",
        "ETH":  "이더리움",
        "XRP":  "리플",
        "SOL":  "솔라나",
        "DOGE": "도지코인",
    }
    keyword = keyword_map.get(symbol.upper(), symbol)

    price_info = get_current_price.invoke({"symbol": symbol})
    news_info  = fetch_crypto_news.invoke({"keyword": keyword})

    return (
        f"=== {symbol.upper()} 시장 종합 요약 ===\n\n"
        f"{price_info}\n\n"
        f"{news_info}"
    )


# 에이전트에게 노출할 도구 목록 (robo_agent.py에서 가져다 씀)
ALL_TOOLS = [fetch_crypto_news, get_current_price, get_market_summary]
