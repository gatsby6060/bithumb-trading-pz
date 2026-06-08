"""
LangChain Phase 3 — ReAct 에이전트 (RoboAdvisorAgent)

[Phase 2와의 차이점]
  Phase 2: 개발자가 뉴스를 수집해서 LLM에 직접 전달
  Phase 3: AI 에이전트가 스스로 어떤 도구를 쓸지 결정하고 호출

[동작 흐름 — ReAct(Reason + Act) 패턴]
  사용자 질문
    → AI [Thought]: "BTC 분석을 위해 뉴스와 시세 정보가 필요해"
    → AI [Action]: get_market_summary("BTC") 호출
    → [Observation]: 뉴스 10건 + 현재 시세 수신
    → AI [Thought]: "충분한 정보를 얻었어, 이제 분석할게"
    → AI [Final Answer]: {"sentiment": ..., "score": ..., "summary": ...}

[설계 원칙]
  - RoboAdvisorStrategy는 수정하지 않음
  - BaseSentimentAnalyzer 인터페이스 준수하여 플러그인 교체 가능
  - 에이전트의 '생각 과정(Chain of Thought)' 로그를 터미널에 출력
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

from ai_engine.sentiment.base import BaseSentimentAnalyzer
from ai_engine.agent.tools import ALL_TOOLS


# ─────────────────────────────────────────────────────────
# ReAct 에이전트용 프롬프트 템플릿
# LangChain 표준 ReAct 형식: Thought / Action / Observation / Final Answer
# ─────────────────────────────────────────────────────────
REACT_PROMPT_TEMPLATE = """You are an expert cryptocurrency quantitative analyst and trading agent.

Your goal is to analyze the current market situation for {target_asset} and provide a structured sentiment assessment.

You have access to the following tools:
{tools}

Use the following format STRICTLY:

Question: the user's analysis request
Thought: your reasoning about what information you need and which tool to use
Action: the tool to use — must be exactly one of [{tool_names}]
Action Input: the input to the tool (a JSON object or plain string)
Observation: the result from the tool
... (you may repeat Thought/Action/Observation as needed)
Thought: I now have enough information to provide the final analysis
Final Answer: A JSON object with exactly these fields:
  - "sentiment": one of "Bullish", "Bearish", or "Neutral"
  - "score": a float from -1.0 (extremely bearish) to 1.0 (extremely bullish)
  - "summary": a single sentence explaining your reasoning

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class RoboAdvisorAgent(BaseSentimentAnalyzer):
    """
    LangChain ReAct 에이전트 기반 로보어드바이저.

    BaseSentimentAnalyzer를 상속하므로 RoboAdvisorStrategy에서
    GeminiSentimentAnalyzer나 LangChainSentimentAnalyzer와 동일하게 사용 가능합니다.

    차이점: 이 분석기는 AI가 스스로 필요한 정보(뉴스, 시세)를 도구를 통해 수집합니다.
    analyze()를 호출할 때 text 인자를 비워두어도 됩니다.
    """

    def __init__(
        self,
        api_key:    Optional[str] = None,
        model:      str = "gemini-3.1-flash-lite",
        verbose:    bool = True,
        max_iterations: int = 8,
    ):
        _api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not _api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        # LLM
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=_api_key,
            temperature=0.1,
            convert_system_message_to_human=True,
        )

        # ReAct 프롬프트
        prompt = PromptTemplate.from_template(REACT_PROMPT_TEMPLATE)

        # ReAct 에이전트 생성
        agent = create_react_agent(llm=llm, tools=ALL_TOOLS, prompt=prompt)

        # AgentExecutor — 도구 호출 루프를 관리
        self.executor = AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            verbose=verbose,           # Thought/Action/Observation 로그 출력
            max_iterations=max_iterations,
            handle_parsing_errors=True,  # LLM 파싱 오류 시 자동 재시도
            return_intermediate_steps=True,
        )

        self.target_asset = "BTC"
        print(f"✅ RoboAdvisorAgent 초기화 완료 (모델: {model}, 도구: {len(ALL_TOOLS)}개)")
        for t in ALL_TOOLS:
            print(f"   🔧 {t.name}: {t.description[:60]}...")

    async def analyze(self, text: str = "", target_asset: str = "BTC", current_price: float = 0.0) -> Dict[str, Any]:
        """
        에이전트를 실행합니다.
        text 인자가 없어도 에이전트가 스스로 도구를 호출해 정보를 수집합니다.

        Returns:
            {"sentiment": str, "score": float, "summary": str}
        """
        self.target_asset = target_asset

        # 에이전트에게 전달할 질문 (한국어로 지시하면 한국어 맥락에서 분석)
        question = (
            f"{target_asset} (비트코인)의 현재 시장 상황을 분석해줘. "
            f"최신 뉴스 헤드라인과 현재 시세를 직접 도구를 통해 확인하고, "
            f"단기 매매 관점에서의 감성(Bullish/Bearish/Neutral), "
            f"점수(-1.0~1.0), 요약을 JSON으로 반환해줘."
        )

        try:
            # 동기 executor를 비동기 스레드에서 실행 (이벤트 루프 블로킹 방지)
            result = await asyncio.to_thread(
                self.executor.invoke,
                {"input": question, "target_asset": target_asset}
            )

            raw_output = result.get("output", "")

            # Final Answer에서 JSON 파싱 시도
            parsed = self._parse_agent_output(raw_output)
            return parsed

        except Exception as e:
            print(f"❌ 에이전트 실행 오류: {e}")
            return {"sentiment": "Neutral", "score": 0.0, "summary": f"에이전트 오류: {e}"}

    def _parse_agent_output(self, output: str) -> Dict[str, Any]:
        """에이전트의 Final Answer에서 JSON을 추출합니다."""
        try:
            # JSON 블록 추출 시도
            start = output.find("{")
            end   = output.rfind("}") + 1
            if start != -1 and end > start:
                json_str = output[start:end]
                data = json.loads(json_str)
                return {
                    "sentiment": data.get("sentiment", "Neutral"),
                    "score":     float(data.get("score", 0.0)),
                    "summary":   data.get("summary", output[:200]),
                }
        except (json.JSONDecodeError, ValueError):
            pass

        # JSON 파싱 실패 시 텍스트 기반 감성 추론
        output_lower = output.lower()
        if "bullish" in output_lower:
            sentiment, score = "Bullish", 0.5
        elif "bearish" in output_lower:
            sentiment, score = "Bearish", -0.5
        else:
            sentiment, score = "Neutral", 0.0

        return {"sentiment": sentiment, "score": score, "summary": output[:300]}
