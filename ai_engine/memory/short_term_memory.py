import os
import json
from datetime import datetime
from typing import List, Dict, Any

class AgentMemory:
    """
    로보어드바이저의 단기 기억을 저장하고 불러오는 모듈 (Phase 4).
    로컬 JSON 파일을 일종의 경량 데이터베이스(버퍼)로 활용합니다.
    """
    def __init__(self, filename: str = "agent_memory.json"):
        # 최상위 경로(bithumb-quantitative-trading)의 data 디렉토리 지정
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(base_dir, "data")
        self.filepath = os.path.join(self.data_dir, filename)
        
        self._ensure_file()

    def _ensure_file(self):
        """저장할 파일과 디렉토리가 없으면 기본 배열 구조로 생성합니다."""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_memory(
        self, 
        target_asset: str, 
        current_price: float, 
        sentiment: str, 
        score: float, 
        summary: str
    ):
        """
        AI의 예측 결과와 그 당시의 시세(기준점)를 파일에 기록합니다.
        
        Args:
            target_asset: 코인 심볼 (예: 'BTC')
            current_price: 분석 당시의 코인 시세
            sentiment: AI 판단 라벨 ('Bullish', 'Bearish', 'Neutral')
            score: -1.0 ~ 1.0 점수
            summary: 판단 사유 요약
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except Exception:
            memories = []

        new_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_asset": target_asset,
            "price_at_time": current_price,
            "predicted_sentiment": sentiment,
            "predicted_score": score,
            "reason": summary
        }
        
        memories.append(new_entry)
        
        # 파일이 비대해지지 않도록 최근 100개만 관리
        memories = memories[-100:]
        
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

    def load_recent_memories(self, target_asset: str, limit: int = 5) -> str:
        """
        프롬프트 주입용으로, 과거 분석 기록 M개를 텍스트 포맷으로 반환합니다.
        
        Args:
            target_asset: 대상 코인 심볼
            limit: 가져올 최근 기억의 개수
            
        Returns:
            가독성 좋게 포맷팅된 문자열 (이력 없음 시 빈 문자열 반환)
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                all_memories = json.load(f)
        except Exception:
            return "과거 기록 없음"

        # 해당 코인(target_asset)의 기록만 필터링
        filtered = [m for m in all_memories if m.get("target_asset") == target_asset]
        recent = filtered[-limit:]

        if not recent:
            return "이 코인에 대한 과거 예측 기록이 없습니다; 새로운 관점에서 분석하세요."

        lines = ["[과거 당신의 예측 및 시장 반응 기록들]"]
        
        for i, m in enumerate(recent):
            lines.append(f"({i+1}) 기록 시점: {m['timestamp']}")
            lines.append(f"    - 당시 실제 가격 : {m.get('price_at_time', 0):,} KRW")
            lines.append(f"    - 나의 AI 판단   : {m['predicted_sentiment']} (Score: {m['predicted_score']})")
            lines.append(f"    - 판단의 근거    : {m['reason']}")
            lines.append("") # 띄어쓰기

        return "\n".join(lines)
