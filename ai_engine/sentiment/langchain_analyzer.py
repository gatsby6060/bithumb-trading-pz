"""
LangChain LCEL(LangChain Expression Language) 기반 감성 분석기.

기존 GeminiSentimentAnalyzer(google-genai 직접 호출)의 LangChain 버전입니다.
BaseSentimentAnalyzer 인터페이스를 동일하게 구현하므로
RoboAdvisorStrategy는 이 클래스로 analyzer를 교체해도 코드 변경이 없습니다.

[LCEL 체인 구조]
  sentiment_prompt  →  ChatGoogleGenerativeAI  →  PydanticOutputParser
       (프롬프트 조립)          (LLM 호출)               (구조화 파싱)
"""
import os
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough

from .base import BaseSentimentAnalyzer
from ai_engine.prompts.sentiment_prompt import get_sentiment_prompt
from ai_engine.memory.short_term_memory import AgentMemory


# ─────────────────────────────────────────────
# 출력 스키마 (Pydantic)
# GeminiSentimentAnalyzer의 SentimentResult와 동일한 구조를 유지하여
# 다운스트림 코드(RoboAdvisorStrategy)가 동일하게 동작합니다.
# ─────────────────────────────────────────────
class SentimentResult(BaseModel):
    sentiment: str = Field(
        description="Overall market sentiment. Must be one of: 'Bullish', 'Bearish', 'Neutral'"
    )
    score: float = Field(
        description="Sentiment score from -1.0 (extremely bearish) to +1.0 (extremely bullish). Neutral ≈ 0.0"
    )
    summary: str = Field(
        description="A single sentence explaining the key reason for this sentiment score."
    )


class LangChainSentimentAnalyzer(BaseSentimentAnalyzer):
    """
    LangChain LCEL 파이프라인을 활용한 뉴스 감성 분석기.
    
    Phase 2 목표:
    - 프롬프트를 코드에서 분리 (ai_engine/prompts/sentiment_prompt.py)
    - LCEL 파이프라인으로 선언적 체인 구성
    - Pydantic 파서로 구조화된 출력 보장
    - BaseSentimentAnalyzer 인터페이스 준수 (트레이딩 엔진 수정 없음)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite"):
        _api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not _api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

        # 1. LLM — LangChain의 ChatGoogleGenerativeAI 래퍼 사용
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=_api_key,
            temperature=0.1,       # 일관성 있는 분석을 위해 낮은 temperature
            convert_system_message_to_human=True,  # Gemini 호환성 설정
        )

        # 1-1. 메모리 모듈 생성
        self.memory = AgentMemory()

        # 2. 출력 파서 — Pydantic 스키마로 LLM 응답을 자동 파싱
        parser = PydanticOutputParser(pydantic_object=SentimentResult)

        # 3. 프롬프트 — 분리된 파일에서 가져옴
        prompt = get_sentiment_prompt()

        # ─────────────────────────────────────────
        # LCEL 체인 조립 (|  파이프 연산자로 선언적 연결)
        #
        # 입력 dict → 프롬프트 조립 → LLM 호출 → Pydantic 파싱 → SentimentResult
        # ─────────────────────────────────────────
        self.chain = (
            {
                "news_text": RunnablePassthrough() | (lambda x: x["news_text"]),
                "asset":     RunnablePassthrough() | (lambda x: x["asset"]),
                "past_memory": RunnablePassthrough() | (lambda x: x["past_memory"]),
                "format_instructions": lambda _: parser.get_format_instructions(),
            }
            | prompt
            | llm
            | parser
        )

        self.model_name = model
        print(f"✅ LangChainSentimentAnalyzer 초기화 완료 (모델: {self.model_name})")

    async def analyze(self, text: str, target_asset: str = "BTC", current_price: float = 0.0) -> Dict[str, Any]:
        """
        LCEL 체인을 비동기로 실행하여 뉴스 텍스트의 감성을 분석합니다.

        Args:
            text: 분석할 뉴스 텍스트 (여러 기사를 묶은 배치 텍스트 가능)
            target_asset: 분석 대상 심볼 (예: "BTC", "ETH")
            current_price: 분석 당시 현재 가격 (메모리 기록용)

        Returns:
            {"sentiment": str, "score": float, "summary": str}
        """
        try:
            # 1. 과거 기억 불러오기
            past_memories_str = self.memory.load_recent_memories(target_asset, limit=5)

            # 2. 체인 실행
            # ainvoke: LCEL 체인의 비동기 실행 메서드
            result: SentimentResult = await self.chain.ainvoke({
                "news_text": text,
                "asset": target_asset,
                "past_memory": past_memories_str,
            })

            # 3. 새로운 기억 저장
            self.memory.save_memory(
                target_asset=target_asset,
                current_price=current_price,
                sentiment=result.sentiment,
                score=result.score,
                summary=result.summary
            )

            return {
                "sentiment": result.sentiment,
                "score":     result.score,
                "summary":   result.summary,
            }

        except Exception as e:
            print(f"❌ LangChain 감성 분석 오류: {e} (Using Simulated Fallback)")
            # Generate simulated sentiment based on news text
            import random
            text_lower = text.lower()
            if any(k in text_lower for k in ["호재", "상승", "급등", "상회", "우호", "rally", "bull", "gain", "breakout", "positive"]):
                sentiment, score, summary = "Bullish", random.uniform(0.3, 0.8), f"최근 수집된 뉴스에서 긍정적인 단기 상승 모멘텀 키워드가 관측되었습니다. (시뮬레이션 분석)"
            elif any(k in text_lower for k in ["악재", "하락", "급락", "우려", "규제", "drop", "bear", "dump", "negative", "crash"]):
                sentiment, score, summary = "Bearish", random.uniform(-0.8, -0.3), f"최근 수집된 뉴스에서 하방 압력 및 규제/우려 요인이 다수 관측되었습니다. (시뮬레이션 분석)"
            else:
                sentiment, score, summary = "Neutral", random.uniform(-0.15, 0.15), f"뉴스가 관측되었으나 방향성이 혼재되어 있으며, 전반적으로 중립적인 추세를 보이고 있습니다. (시뮬레이션 분석)"
                
            # Try to save to memory
            try:
                self.memory.save_memory(
                    target_asset=target_asset,
                    current_price=current_price,
                    sentiment=sentiment,
                    score=score,
                    summary=summary
                )
            except Exception as me:
                print(f"❌ 메모리 저장 오류: {me}")
                
            return {"sentiment": sentiment, "score": score, "summary": summary}

