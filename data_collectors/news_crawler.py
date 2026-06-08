import asyncio
import feedparser
import time
import json
import os
from typing import List, Dict

class NewsCrawler:
    """
    여러 RSS 채널(Google News, 인베스팅닷컴 등)을 주기적으로 크롤링하여 
    코인 관련 최신 뉴스를 가져오는 모듈입니다.
    가져온 뉴스를 JSON 파일로 저장하여 프로그램 재시작 시에도 중복 처리를 완벽하게 방지합니다.
    """
    def __init__(self, keyword: str = "비트코인"):
        self.keyword = keyword
        # 크롤링할 RSS 피드 목록
        self.rss_urls = [
            f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko", # 구글 뉴스
            "https://kr.investing.com/rss/news_301.rss"                               # 인베스팅닷컴 (암호화폐 탭)
        ]
        
        # 프로젝트 루트 디렉토리의 data 폴더에 히스토리 파일 저장
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, "data")
        self.history_file = os.path.join(self.data_dir, "news_history.json")
        
        self.seen_links = set()
        self._load_history()

    def _load_history(self):
        """기존 저장된 뉴스 기록을 불러와 seen_links 세트를 초기화합니다."""
        os.makedirs(self.data_dir, exist_ok=True)
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for item in history:
                        self.seen_links.add(item.get("link"))
            except json.JSONDecodeError:
                pass  # 파일이 비어 있거나 손상된 경우 무시

    def _save_new_articles(self, new_articles: List[Dict]):
        """새로 수집된 뉴스를 기존 JSON 히스토리에 병합하여 저장합니다."""
        if not new_articles:
            return
            
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                pass

        history.extend(new_articles)
        
        # 무한정 커지는 것을 방지하기 위해 최근 2000개 기사만 유지
        history = history[-2000:]
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def fetch_latest_news(self) -> List[Dict[str, str]]:
        """
        등록된 다수의 RSS 피드를 파싱하여 이전에 본 적 없는 최신 뉴스를 반환하고 파일에 기록합니다.
        가져온 뉴스는 채널과 상관없이 통합되어 최신 시간순(내림차순)으로 정렬되어 반환됩니다.
        """
        new_articles = []
        
        for rss_url in self.rss_urls:
            # 타임아웃 방지 및 안정성을 위해 각 피드 파싱 시도 (feedparser 내부적으로 urllib 활용됨)
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                link = entry.link
                if link not in self.seen_links:
                    self.seen_links.add(link)
                    
                    # 피드의 시간 문자열을 파이썬이 이해할 수 있는 숫자로 변환
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_ts = time.mktime(entry.published_parsed)
                    else:
                        published_ts = time.time() # 시간 정보가 없을 경우 현재 시간
                        
                    article_data = {
                        "title": entry.title,
                        "link": link,
                        "published": getattr(entry, 'published', str(time.time())),
                        "timestamp": published_ts
                    }
                    new_articles.append(article_data)
                
        # 시간에 따른 정렬 (Timestamp 값이 가장 큰 최신 기사가 0번 인덱스에 오도록 내림차순 정렬)
        new_articles.sort(key=lambda x: x["timestamp"], reverse=True)
                
        # 새 기사가 발견되면 영구 저장소(JSON)에 동기화
        if new_articles:
            self._save_new_articles(new_articles)
                
        return new_articles

if __name__ == "__main__":
    crawler = NewsCrawler("비트코인 가상자산")
    print(f"Fetching news from {len(crawler.rss_urls)} sources... (현재까지 기억하는 뉴스 개수: {len(crawler.seen_links)}개)")
    news = crawler.fetch_latest_news()
    
    if news:
        print(f"새로운 뉴스 {len(news)}개 발견 및 저장 완료!")
        for n in news[:5]:
            # 어디 피드에서 가져왔는지 직관적으로 보기 위해 출력
            print(f">> {n['title']} ({n['published']})")
    else:
        print("새로운 뉴스가 없습니다. (모든 뉴스가 이미 파일에 저장됨)")
