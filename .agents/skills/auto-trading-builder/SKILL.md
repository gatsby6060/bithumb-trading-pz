---
name: auto-trading-builder
description: 비트코인 및 주식 자동매매 시스템의 모듈형 아키텍처를 설계하고 구축하는 스킬입니다. 종목별 독립 스레드 처리, 동적 전략 로딩, 복합 전략 조합 및 리스크 관리 기능을 포함한 고성능 트레이딩 시스템 구축 시 사용합니다.
---

# Auto Trading Builder

이 스킬은 고성능 모듈형 자동매매 시스템을 구축하기 위한 가이드와 템플릿을 제공합니다.

## 핵심 아키텍처

본 스킬이 제안하는 아키텍처는 다음과 같은 계층으로 구성됩니다:

1.  **데이터 수집 계층**: `WebSocketListener`를 통한 실시간 데이터 수신.
2.  **데이터 분배 계층**: `DataDispatcher`를 사용하여 종목별 개별 큐로 데이터 라우팅.
3.  **전략 실행 계층**: 종목별 독립 `StockThread`에서 `CompositeStrategy` 및 `RiskManager` 실행.
4.  **주문 실행 계층**: `OrderExecutor`를 통한 비동기 주문 처리.

## 주요 기능 구현 가이드

### 1. 종목별 독립 스레드 처리
각 종목은 고유한 `StockThread`와 `queue.Queue`를 가져야 합니다. 이를 통해 한 종목의 계산 지연이 다른 종목에 영향을 주지 않는 독립성을 보장합니다.

### 2. 동적 전략 로딩 (Dynamic Loading)
`importlib`를 사용하여 `strategies/` 디렉토리의 파일을 런타임에 로드하십시오. 각 파일은 `BaseStrategy`를 상속받아야 합니다.

### 3. 복합 전략 조합 (Composite Pattern)
사용자가 여러 전략을 선택할 수 있도록 `CompositeStrategy`를 사용하십시오. AND/OR 또는 가중치 기반 투표 로직을 통해 개별 전략의 신호를 통합합니다.

### 4. 리스크 관리 (Risk Management)
매매 신호 발생 전후에 `RiskManager`를 거치도록 설계하십시오. 최대 손실 제한(Stop-loss), 일일 거래 횟수 제한 등을 독립 모듈로 구현합니다.

## 활용 가능한 리소스

-   **템플릿**: `/home/ubuntu/skills/auto-trading-builder/templates/base_trading_system.py` - 시스템 구축을 위한 핵심 클래스 구조.

## 주의 사항

-   **Thread Safety**: 계좌 잔고 등 공유 자원 접근 시 반드시 `threading.Lock`을 사용하십시오.
-   **Backpressure**: 큐가 가득 찰 경우에 대비한 데이터 드롭 또는 블로킹 정책을 수립하십시오.
-   **Graceful Shutdown**: `threading.Event`를 사용하여 모든 스레드가 안전하게 종료되도록 구현하십시오.
