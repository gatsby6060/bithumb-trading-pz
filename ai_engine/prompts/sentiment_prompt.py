"""
감성 분석을 위한 LangChain PromptTemplate을 정의합니다.
프롬프트를 코드와 분리하여 독립적으로 수정·버전관리할 수 있습니다.
"""
from langchain_core.prompts import ChatPromptTemplate

# ─────────────────────────────────────────────
# 시스템 역할 프롬프트
# 분석가의 전문성, 출력 형식, 분석 관점을 명확히 지정합니다.
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert crypto quantitative analyst specializing in sentiment analysis.

Your task is to analyze the given cryptocurrency news and determine its short-term market impact.

Guidelines:
- Focus on recency and urgency of the news
- Consider regulatory, technological, and macroeconomic factors
- Be concise but precise in your reasoning
- Score range: -1.0 (extremely bearish) to +1.0 (extremely bullish), 0.0 is neutral

You MUST respond with valid JSON matching the exact schema provided."""

# ─────────────────────────────────────────────
# 사용자 요청 프롬프트 (변수 포함)
# {asset}     : 분석 대상 코인 심볼 (예: BTC, ETH)
# {news_text} : 분석할 뉴스 제목/내용
# {format_instructions} : Pydantic 파서가 주입하는 출력 형식 명세
# ─────────────────────────────────────────────
HUMAN_PROMPT = """Analyze the following news for {asset} and provide your sentiment assessment.

## Past Predictions & Market Reactions (Memory Reflection):
{past_memory}
*Review your previous predictions above. If the price moved against your prediction, reflect on what macroeconomic or sentiment factors you missed, and adjust your current analysis accordingly. Do NOT just repeat past reasoning if it was wrong.*

## News to Analyze:
{news_text}

## Required Output Format:
{format_instructions}

Provide your analysis now:"""



def get_sentiment_prompt() -> ChatPromptTemplate:
    """
    감성 분석용 ChatPromptTemplate을 생성하여 반환합니다.
    LangChainSentimentAnalyzer에서 LCEL 체인에 조립됩니다.
    """
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human",  HUMAN_PROMPT),
    ])
