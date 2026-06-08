import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from .base import BaseSentimentAnalyzer

class SentimentResult(BaseModel):
    sentiment: str = Field(description="One of: 'Bullish', 'Bearish', 'Neutral'")
    score: float = Field(description="A sentiment score from -1.0 (extremely bearish) to 1.0 (extremely bullish). Neutral is around 0.")
    summary: str = Field(description="A brief 1-sentence explanation of why this sentiment was chosen based on the news.")

class GeminiSentimentAnalyzer(BaseSentimentAnalyzer):
    """
    구글의 Gemini API와 Pydantic을 활용하여 가장 가볍고 빠르게 뉴스의 감성을 판별하는 구현체입니다.
    """
    def __init__(self, api_key: Optional[str] = None):
        # 환경변수 또는 인자로 전달된 API 키 사용
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please set it in .env or pass it directly.")
        
        # 최신 google-genai SDK 
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3.1-flash-lite" # 빠른 속도와 가성비를 위한 2.5 flash 모델

    async def analyze(self, text: str, target_asset: str = "BTC", current_price: float = 0.0) -> Dict[str, Any]:
        """
        Gemini의 Structured Outputs 기능을 통해 정형화된 JSON 파이썬 객체를 반환합니다.
        """
        prompt = f"""
        You are an expert crypto quantitative analyst.
        Analyze the following news text and determine its short-term impact on {target_asset} (Bitcoin/Cryptos).
        
        News Text: {text}
        
        Provide your assessment strictly following the schema.
        """

        try:
            # google-genai 비동기 클라이언트 활용
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SentimentResult,
                    temperature=0.1
                )
            )
            
            # Pydantic 객체로 파싱된 결과 접근
            result = response.parsed
            
            return {
                "sentiment": result.sentiment,
                "score": result.score,
                "summary": result.summary
            }
        except Exception as e:
            print(f"❌ Gemini Sentiment Analysis Error: {e} (Using Simulated Fallback)")
            # Generate simulated sentiment based on news text
            import random
            text_lower = text.lower()
            if any(k in text_lower for k in ["호재", "상승", "급등", "상회", "우호", "rally", "bull", "gain", "breakout", "positive"]):
                sentiment, score, summary = "Bullish", random.uniform(0.3, 0.8), f"최근 수집된 뉴스에서 긍정적인 단기 상승 모멘텀 키워드가 관측되었습니다. (시뮬레이션 분석)"
            elif any(k in text_lower for k in ["악재", "하락", "급락", "우려", "규제", "drop", "bear", "dump", "negative", "crash"]):
                sentiment, score, summary = "Bearish", random.uniform(-0.8, -0.3), f"최근 수집된 뉴스에서 하방 압력 및 규제/우려 요인이 다수 관측되었습니다. (시뮬레이션 분석)"
            else:
                sentiment, score, summary = "Neutral", random.uniform(-0.15, 0.15), f"뉴스가 관측되었으나 방향성이 혼재되어 있으며, 전반적으로 중립적인 추세를 보이고 있습니다. (시뮬레이션 분석)"
            return {"sentiment": sentiment, "score": score, "summary": summary}

