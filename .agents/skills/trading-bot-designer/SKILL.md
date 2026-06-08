---
name: trading-bot-designer
description: Assists in generating and validating the Bithumb auto-trading bot codebase based on the system architecture design and screen specifications.
---

# Trading Bot Designer Skill

This skill guides the agent in developing, code-generating, and verifying the **Bithumb Automated Crypto Trading Bot** in strict compliance with the system architecture and UI/UX screen specifications.

---

## 1. Core Architecture Guidelines

All generated code must adhere to the modular, decoupled async flow defined in the reference documents:

### 1.1 Data & Event Flow
* **Raw Ticks**: WebSocket ticks (`bithumb_ws.py`) must push standardized event dictionaries into an `asyncio.Queue` non-blockingly.
* **Database**: `TimescaleDBManager` must handle fast inserts into `tick_data` and query continuous aggregates (e.g., `ohlcv_1m`).
* **ML Inference**: Machine learning routines (`FreqaiModel`) must execute in executor thread pools to prevent event loop lag.

### 1.2 Dynamic Strategy Mixer (10-Mixer & 50-Library)
* **Strategy Interface**: Every trading technique must inherit a base strategy interface.
* **Composition**: The `StrategyEngine` must dynamically load a list of up to 10 strategies with respective weight variables stored as JSON in SQLite `symbol_settings`.
* **Hot-swapping**: Weight updates (manual slider changes or AI autopilot optimization updates) must swap variables in memory instantly without restarting the trading loop.

### 1.3 Safe Sell Assistance (AI Assist Modal Validation)
* **Manual Sell Hold**: Manual sell triggers must invoke `ManualSellVerifier.verify()` and await FreqAI short-term predictions with a strict **1.5s timeout**.
* **Confirmation Loop**:
  * If the verifier flags a high-probability bounce, emit `SHOW_SELL_WARNING` to trigger the confirmation modal in the UI.
  * If the 1.5s timeout is reached without a response from the verifier, bypass the warning immediately and dispatch the sell order to Bithumb via REST to preserve responsiveness.

---

## 2. File Verification Checklist

Before finalizing any code changes, verify:
1. **Per-Coin Customization**: Strategy mixer weights are saved dynamically per symbol, not globally.
2. **AI Action Logging**: All AI Autopilot modifications are logged into the SQLite table `ai_activity_log` with detailed reasons.
3. **Panic Routine**: SIGINT or shutdown calls cancellation of all open orders and flattens all active positions immediately.

---

## 3. Reference Documents

* [System Architecture Design](file:///c:/260606coin/.agents/skills/trading-bot-designer/references/system_architecture_design.md): Detailed system architecture design and SQL schemas.
* [UI/UX Screen Specification](file:///c:/260606coin/.agents/skills/trading-bot-designer/references/ui_ux_screen_specification.md): Screen layouts (1~8), layout measurements, and interactive popup modal states.

