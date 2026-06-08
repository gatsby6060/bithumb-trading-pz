from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSentimentAnalyzer(ABC):
    """
    뉴스 기사 및 텍스트 데이터를 분석하여 거래 엔진에서 사용할 
    감성 점수(Sentiment Score) 및 호재/악재 판독 결과를 반환하는 추상 클래스입니다.

    추후 OpenAI API 경량 구현체나 LangChain 기반 고도화 구현체로 언제든 
    교체할 수 있도록 공통 인터페이스를 정의합니다.
    """

    @abstractmethod
    async def analyze(self, text: str, target_asset: str = "BTC", current_price: float = 0.0) -> Dict[str, Any]:
        """
        주어진 텍스트(뉴스 등)를 분석하여 감성 점수를 도출합니다.
        
        Args:
            text (str): 분석할 뉴스 제목, 본문 등의 텍스트
            target_asset (str): 분석 대상 가상자산 심볼 (예: "BTC", "ETH")
            current_price (float): (Phase 4) 분석 당시의 시세. 메모리 기록용.
            
        Returns:
            Dict[str, Any]: 
                - sentiment (str): "Bullish", "Bearish", "Neutral"
                - score (float): 0.0 ~ 1.0 (혹은 -1.0 ~ 1.0) 감성 점수
                - summary (str): 근거 및 요약
        """
        pass
