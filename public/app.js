// State Management
let currentScreen = 'screen-1';
let ws = null;
let charts = {};
let dashboardState = null;
let activeSymbol = 'KRW-BTC';
let dbTotalTicks = 0;

// Strategy Library list (50+ available strategies)
const STRATEGY_LIBRARY = [
    "AI", "SENTIMENT", "BOLLINGER", "RSI", "MACD", "EMA_CROSS", "SMA_CROSS", "VWAP", "ADX", "STOCH",
    "CCI", "ATR", "MFI", "CHAIKIN", "EOM", "KVO", "OBV", "ROC", "TRIX", "WILLIAMS_R",
    "SAR", "ICHIMOKU", "HEIKIN_ASHI", "PIVOT_POINTS", "FIBONACCI", "DEMA", "TEMA", "KDJ",
    "HULL_MA", "ALMA", "SINE_WAVE", "FRACTAL", "ZIGZAG", "DONCHIAN", "KELTNER", "SUPER_TREND",
    "PARABOLIC_SAR", "CHANDELIER_EXIT", "ARROON", "CHOPPINESS", "COPPMOCK", "KST", "MASS_INDEX",
    "SAFE_ZONE", "TDFI", "VORTEX", "ULTIMATE_OSC", "TRIPLE_EMA", "T3_MA", "KAMA", "FRAMA"
];

// Document Ready
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initWebSocket();
    initCharts();
    initSettingsControls();
    initMixerControls();
    initModalControls();
    initSentimentControls();
    
    // Initial fetch
    fetchDashboardState();
    fetchTradeHistory();
    fetchAiActivities();
    fetchSystemLogs();
    fetchSentimentState();
    
    // Load historical candles
    setTimeout(() => {
        loadHistoricalCandles(activeSymbol);
    }, 500);
    
    // Start regular polling
    setInterval(() => {
        fetchDashboardState();
        fetchTradeHistory();
        fetchAiActivities();
        fetchSystemLogs();
        fetchSentimentState();
    }, 3000);
});


// Navigation Handling
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");
            
            const target = item.getAttribute("data-target");
            switchScreen(target);
        });
    });
}

function switchScreen(screenId) {
    currentScreen = screenId;
    document.querySelectorAll(".screen-container").forEach(screen => {
        screen.classList.remove("active");
    });
    
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) targetScreen.classList.add("active");
    
    // Update Header Title
    const titleMap = {
        'screen-1': '종합 관제 대시보드',
        'screen-2': '가동 중인 전략',
        'screen-3': '상세 거래 내역',
        'screen-4': '시계열 DB 상태',
        'screen-5': '시스템 로그 콘솔',
        'screen-6': '수동 및 조건 설정',
        'screen-7': '통합 트레이딩 데스크',
        'screen-8': '종목별 전략 믹서'
    };
    
    document.getElementById("current-screen-title").innerText = titleMap[screenId] || '대시보드';
}

// WebSocket Connection
function initWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log("WebSocket connected to backend.");
        appendLog("INFO", "System", "웹소켓 실시간 데이터 링크 연결 완료.");
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'tick') {
                handleIncomingTick(data);
            }
        } catch (e) {
            console.error("Error parsing WS message:", e);
        }
    };
    
    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
    };
    
    ws.onclose = () => {
        console.warn("WebSocket closed. Attempting reconnect in 5s...");
        setTimeout(initWebSocket, 5000);
    };
}

// Handling Tick Events
function handleIncomingTick(tick) {
    // Increment DB tick count
    dbTotalTicks++;
    document.getElementById("db-total-ticks-count").innerText = dbTotalTicks.toLocaleString();

    // Update real-time price labels if BTC or ETH
    if (tick.symbol === activeSymbol) {
        // Update Chart
        pushChartData(tick.price, tick.timestamp);
    }
    
    // Render Tick in logs summary
    appendLog("INFO", "WebSocket", `Tick [${tick.symbol}] Price: ${tick.price.toLocaleString()} | Vol: ${tick.volume.toFixed(4)} | AI Score: ${tick.ai_score.toFixed(1)}`);
}

// Charts Initialization
function initCharts() {
    // 1. Dashboard Chart
    const ctx1 = document.getElementById('dashboard-chart').getContext('2d');
    charts.dashboard = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'BTC/KRW 실시간 체결가',
                data: [],
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.05)',
                borderWidth: 2,
                tension: 0.2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } },
                y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } }
            },
            plugins: { legend: { display: false } }
        }
    });

    // 2. Pro Desk Chart
    const ctx2 = document.getElementById('pro-desk-chart').getContext('2d');
    charts.proDesk = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '실시간 가상자산 시세',
                data: [],
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.05)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } },
                y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } }
            },
            plugins: { legend: { display: false } }
        }
    });

    // 3. Strategy Cumulative Performance Chart
    const ctx3 = document.getElementById('strategy-perf-chart').getContext('2d');
    charts.strategyPerf = new Chart(ctx3, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'FreqAI 하이브리드 전략',
                    data: [],
                    borderColor: '#10B981',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'Buy & Hold (단순 보유)',
                    data: [],
                    borderColor: '#EF4444',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } },
                y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } }
            }
        }
    });

    // 4. DB Disk usage chart
    const ctx4 = document.getElementById('db-disk-chart').getContext('2d');
    charts.dbDisk = new Chart(ctx4, {
        type: 'bar',
        data: {
            labels: ['tick_data', 'ai_activity_log', 'trade_history', 'continuous_views'],
            datasets: [{
                label: '디스크 사용량 (MB)',
                data: [0, 0, 0, 0],
                backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#A78BFA'],
                borderWidth: 0,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { display: false }, ticks: { color: '#9CA3AF' } },
                y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } }
            }
        }
    });

    // 5. Strategy Mixer Donut Chart
    const ctx5 = document.getElementById('mixer-donut-chart').getContext('2d');
    charts.mixerDonut = new Chart(ctx5, {
        type: 'doughnut',
        data: {
            labels: ['AI 예측', '볼린저 밴드', 'RSI 지표'],
            datasets: [{
                data: [50, 30, 20],
                backgroundColor: ['#10B981', '#F59E0B', '#3B82F6'],
                borderColor: '#121824',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            cutout: '70%'
        }
    });

    // 6. Mixer Preview Chart
    const ctx6 = document.getElementById('mixer-preview-chart').getContext('2d');
    charts.mixerPreview = new Chart(ctx6, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '예상 누적 수익률(%)',
                data: [],
                borderColor: '#10B981',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: false },
                y: { grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#9CA3AF' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function pushChartData(price, timeStr) {
    const formattedTime = timeStr.split('T')[1]?.substring(0, 8) || timeStr;
    
    // Dashboard Chart Update
    charts.dashboard.data.labels.push(formattedTime);
    charts.dashboard.data.datasets[0].data.push(price);
    
    if (charts.dashboard.data.labels.length > 20) {
        charts.dashboard.data.labels.shift();
        charts.dashboard.data.datasets[0].data.shift();
    }
    charts.dashboard.update('none');

    // Pro Desk Chart Update
    charts.proDesk.data.labels.push(formattedTime);
    charts.proDesk.data.datasets[0].data.push(price);
    
    if (charts.proDesk.data.labels.length > 20) {
        charts.proDesk.data.labels.shift();
        charts.proDesk.data.datasets[0].data.shift();
    }
    charts.proDesk.update('none');
}

// Fetch REST API Functions
async function fetchDashboardState() {
    try {
        const response = await fetch('/api/dashboard_state');
        const state = await response.json();
        dashboardState = state;
        updateDashboardUI(state);
    } catch (e) {
        console.error("Error fetching dashboard state:", e);
    }
}

async function fetchTradeHistory() {
    try {
        const response = await fetch('/api/trade_history');
        const trades = await response.json();
        renderTradeHistory(trades);
    } catch (e) {
        console.error("Error fetching trades:", e);
    }
}

async function fetchAiActivities() {
    try {
        const response = await fetch('/api/ai_activities');
        const logs = await response.json();
        renderAiActivities(logs);
    } catch (e) {
        console.error("Error fetching AI activities:", e);
    }
}

async function fetchSystemLogs() {
    try {
        const response = await fetch('/api/system_logs');
        const logs = await response.json();
        renderSystemLogsConsole(logs);
    } catch (e) {
        console.error("Error fetching system logs:", e);
    }
}

// UI Updating functions
function updateDashboardUI(state) {
    document.getElementById("val-total-assets").innerText = state.equity.toLocaleString() + " KRW";
    document.getElementById("val-cash").innerText = state.cash.toLocaleString() + " KRW";
    document.getElementById("val-risk").innerText = `${(state.current_risk * 100).toFixed(2)}% / ${(state.risk_limit * 100).toFixed(1)}%`;
    document.getElementById("val-today-pnl").innerText = (state.daily_pnl >= 0 ? "+" : "") + state.daily_pnl.toLocaleString() + " KRW";
    
    // Render positions table
    const tableBody = document.getElementById("active-positions-table");
    tableBody.innerHTML = "";
    if (state.positions.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">보유 중인 포지션이 없습니다.</td></tr>`;
    } else {
        state.positions.forEach(pos => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight: 600;">${pos.symbol}</td>
                <td>${pos.entry_price.toLocaleString()} KRW</td>
                <td>${pos.current_price.toLocaleString()} KRW</td>
                <td>${pos.volume} ${pos.symbol.split('-')[1]}</td>
                <td class="${pos.pnl_amount >= 0 ? 'change-up' : 'change-down'}" style="font-weight: 600;">
                    ${pos.pnl_amount >= 0 ? '+' : ''}${pos.pnl_amount.toLocaleString()} KRW (${pos.pnl_pct.toFixed(2)}%)
                </td>
            `;
            tableBody.innerHTML += tr.outerHTML;
        });
    }

    // Update bot status
    const statusTextEl = document.getElementById("bot-status-text");
    const statusDotEl = document.querySelector(".status-dot");
    if (statusTextEl && statusDotEl) {
        if (state.status === "PANIC") {
            statusTextEl.innerText = "비상 정지됨 (PANIC)";
            statusTextEl.style.color = "var(--color-panic)";
            statusDotEl.style.backgroundColor = "var(--color-panic)";
            statusDotEl.style.boxShadow = "0 0 8px var(--color-panic)";
        } else if (state.status === "RUNNING") {
            statusTextEl.innerText = "가동 중";
            statusTextEl.style.color = "var(--color-success)";
            statusDotEl.style.backgroundColor = "var(--color-success)";
            statusDotEl.style.boxShadow = "0 0 8px var(--color-success)";
        } else if (state.status === "STOPPED") {
            statusTextEl.innerText = "정지됨";
            statusTextEl.style.color = "var(--text-secondary)";
            statusDotEl.style.backgroundColor = "var(--text-secondary)";
            statusDotEl.style.boxShadow = "0 0 8px var(--text-secondary)";
        }
    }
}

function renderTradeHistory(trades) {
    const tableBody = document.getElementById("trade-history-table-body");
    tableBody.innerHTML = "";
    
    if (trades.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">거래 체결 이력이 없습니다.</td></tr>`;
        return;
    }
    
    trades.forEach(t => {
        const dateStr = t.timestamp.split('T')[0] + " " + t.timestamp.split('T')[1].substring(0, 8);
        const tr = document.createElement("tr");
        tr.className = "trade-row";
        tr.innerHTML = `
            <td>${dateStr}</td>
            <td style="font-weight: 600;">${t.symbol}</td>
            <td><span class="${t.side.toUpperCase() === 'BUY' ? 'badge-ai' : 'badge-manual'}" style="background-color: ${t.side.toUpperCase() === 'BUY' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${t.side.toUpperCase() === 'BUY' ? 'var(--color-success)' : 'var(--color-panic)'}; font-size:11px; padding: 2px 6px; border-radius: 4px;">${t.side.toUpperCase()}</span></td>
            <td>${t.price.toLocaleString()} KRW</td>
            <td>${t.volume} ${t.symbol.split('-')[1]}</td>
            <td>${t.fee.toLocaleString()} KRW</td>
            <td class="${t.pnl >= 0 ? 'change-up' : 'change-down'}" style="font-weight: 700;">
                ${t.pnl > 0 ? '+' : ''}${t.pnl.toLocaleString()} KRW
            </td>
        `;
        
        tr.addEventListener("click", () => {
            showReceiptModal(t);
        });
        
        tableBody.innerHTML += tr.outerHTML;
    });

    // Update overall history metrics
    document.getElementById("history-total-trades").innerText = trades.length + "회";
    const profitable = trades.filter(t => t.pnl > 0).length;
    const winRate = trades.length > 0 ? ((profitable / trades.length) * 100).toFixed(1) : "0.0";
    document.getElementById("history-win-rate").innerText = winRate + "%";
}

function renderAiActivities(logs) {
    const container = document.getElementById("mixer-activity-timeline");
    container.innerHTML = "";
    if (logs.length === 0) {
        container.innerHTML = `<div class="log-entry-mini" style="text-align: center;">기록된 활동이 없습니다.</div>`;
        return;
    }
    
    logs.forEach(l => {
        const dateStr = l.timestamp.split('T')[0] + " " + l.timestamp.split('T')[1].substring(0, 8);
        const entry = document.createElement("div");
        entry.className = "log-entry-mini";
        entry.innerHTML = `
            <div style="display:flex; justify-content:space-between; margin-bottom: 2px;">
                <span class="log-time">${dateStr}</span>
                <span style="color: var(--color-success); font-weight:600;">[${l.symbol}]</span>
            </div>
            <div style="color: var(--text-primary); font-weight:500;">${l.action}</div>
            <div style="font-size: 11px; color: var(--text-secondary); margin-top:2px;">사유: ${l.reason}</div>
        `;
        container.appendChild(entry);
    });
}

function renderSystemLogsConsole(logs, filterLevel = "ALL") {
    const container = document.getElementById("console-logs-container");
    container.innerHTML = "";
    
    const filtered = logs.filter(l => {
        if (filterLevel === "ALL") return true;
        if (filterLevel === "RISK") return l.message.includes("RISK") || l.level === "WARNING";
        return l.level === filterLevel;
    });
    
    filtered.forEach(l => {
        const div = document.createElement("div");
        div.style.lineHeight = "1.5";
        div.style.borderBottom = "1px solid rgba(255,255,255,0.01)";
        div.style.paddingBottom = "4px";
        
        const dateStr = l.timestamp.split('T')[0] + " " + l.timestamp.split('T')[1].substring(0, 8);
        let lvlClass = "log-lvl-info";
        if (l.level === "WARNING" || l.level === "WARN") lvlClass = "log-lvl-warn";
        if (l.level === "ERROR") lvlClass = "log-lvl-error";
        
        div.innerHTML = `
            <span class="log-time">${dateStr}</span>
            [<span class="${lvlClass}">${l.level}</span>]
            <span style="color: #60A5FA;">${l.name}</span>:
            <span style="color: var(--text-primary);">${l.message}</span>
        `;
        container.appendChild(div);
    });
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function appendLog(level, name, message) {
    const log = {
        timestamp: new Date().toISOString(),
        level: level,
        name: name,
        message: message
    };
    
    // Put at end of mini console
    const miniConsole = document.getElementById("mini-log-console");
    const dateStr = log.timestamp.split('T')[1].substring(0, 8);
    let lvlClass = "log-lvl-info";
    if (level === "WARNING") lvlClass = "log-lvl-warn";
    if (level === "ERROR") lvlClass = "log-lvl-error";
    
    const entry = document.createElement("div");
    entry.className = "log-entry-mini";
    entry.innerHTML = `<span class="log-time">${dateStr}</span>[<span class="${lvlClass}">${level}</span>] ${message}`;
    miniConsole.appendChild(entry);
    
    // Limit log size
    if (miniConsole.children.length > 50) {
        miniConsole.removeChild(miniConsole.firstChild);
    }
    miniConsole.scrollTop = miniConsole.scrollHeight;
}

// Log Filters in Screen 5
function initSettingsControls() {
    const filters = document.querySelectorAll(".btn-filter");
    filters.forEach(btn => {
        btn.addEventListener("click", () => {
            filters.forEach(f => f.classList.remove("active"));
            btn.classList.add("active");
            const lvl = btn.getAttribute("data-level");
            fetchSystemLogs().then(() => {
                // Fetch state again to render with new level filter
                renderSystemLogsConsole(document.getElementById("console-logs-container").getAttribute("data-logs-raw") ? JSON.parse(document.getElementById("console-logs-container").getAttribute("data-logs-raw")) : [], lvl);
            });
        });
    });
}

// Sliders and Mixer logic (Screen 8)
function initMixerControls() {
    // Monitored symbol selection on Screen 8 left list
    const coinCards = document.querySelectorAll(".coin-card-item");
    coinCards.forEach(card => {
        card.addEventListener("click", () => {
            coinCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            activeSymbol = card.getAttribute("data-symbol");
            
            // Update UI title
            document.getElementById("mixer-active-symbol-title").innerText = `전략 혼합 믹서 (${activeSymbol})`;
            
            // Reload weights for active symbol
            loadMixerSliders();
            // Reload historical candles for active symbol
            loadHistoricalCandles(activeSymbol);
        });
    });
    
    // Autopilot toggle
    const autoToggle = document.getElementById("mixer-autopilot-toggle");
    autoToggle.addEventListener("change", async (e) => {
        const enabled = e.target.checked;
        appendLog("INFO", "Autopilot", `${activeSymbol} 오토파일럿 설정이 ${enabled ? "가동" : "비활성화"}되었습니다.`);
        await fetch('/api/set_autopilot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: activeSymbol, enabled: enabled })
        });
    });

    // Add strategy to mixing desk button
    document.getElementById("mixer-add-strategy-btn").addEventListener("click", () => {
        // Simple random add strategy from library for demo
        const currentStrategies = Object.keys(getCurrentWeights());
        const available = STRATEGY_LIBRARY.filter(s => !currentStrategies.includes(s));
        if (available.length === 0) return;
        
        const nextStrategy = available[0];
        addStrategySlider(nextStrategy, 10);
        appendLog("INFO", "Mixer", `${activeSymbol}에 새로운 매매 기법 [${nextStrategy}]이/가 추가되었습니다.`);
    });
    
    // Apply recommended weights
    document.getElementById("mixer-apply-recommend-btn").addEventListener("click", () => {
        // Recommend values
        const recommended = {
            "AI": 60,
            "BOLLINGER": 25,
            "RSI": 15
        };
        updateMixerSliders(recommended);
        appendLog("INFO", "Autopilot", `${activeSymbol}에 AI 추천 가중치가 전량 핫스왑 조율되었습니다.`);
    });

    loadMixerSliders();
}

function getCurrentWeights() {
    const weights = {};
    document.querySelectorAll(".mixer-slider-item").forEach(item => {
        const name = item.getAttribute("data-name");
        const val = parseInt(item.querySelector(".custom-slider").value);
        weights[name] = val;
    });
    return weights;
}

function loadMixerSliders() {
    const defaultWeights = {
        "KRW-BTC": { "AI": 50, "BOLLINGER": 30, "RSI": 20 },
        "KRW-ETH": { "AI": 40, "BOLLINGER": 40, "RSI": 20 }
    };
    
    const weights = (dashboardState && dashboardState.weights && dashboardState.weights[activeSymbol]) 
        || defaultWeights[activeSymbol] 
        || { "AI": 50, "BOLLINGER": 30, "RSI": 20 };
        
    const container = document.getElementById("mixer-sliders-list-container");
    container.innerHTML = "";
    
    Object.entries(weights).forEach(([name, val]) => {
        addStrategySlider(name, val);
    });
    
    updateDonutChart();
}

function addStrategySlider(name, val) {
    const container = document.getElementById("mixer-sliders-list-container");
    const div = document.createElement("div");
    div.className = "slider-row mixer-slider-item";
    div.setAttribute("data-name", name);
    div.innerHTML = `
        <div class="slider-header">
            <div class="slider-label-group">
                <i class="fa-solid fa-times-circle slider-delete-btn" title="제척"></i>
                <span>${name}</span>
            </div>
            <span class="slider-val">${val}%</span>
        </div>
        <div class="slider-container-inner">
            <input type="range" class="custom-slider" min="0" max="100" value="${val}">
        </div>
    `;
    
    // Sliders drag event
    const slider = div.querySelector(".custom-slider");
    slider.addEventListener("input", (e) => {
        const currentVal = e.target.value;
        div.querySelector(".slider-val").innerText = `${currentVal}%`;
        
        // Normalize other sliders if sum > 100% or just update donut
        updateDonutChart();
        debouncedUpdateWeights();
    });
    
    // Delete strategy button
    div.querySelector(".slider-delete-btn").addEventListener("click", () => {
        div.remove();
        updateDonutChart();
        debouncedUpdateWeights();
        appendLog("INFO", "Mixer", `${activeSymbol}에서 매매 기법 [${name}]이/가 제척되었습니다.`);
    });
    
    container.appendChild(div);
}

function updateMixerSliders(weightsMap) {
    document.querySelectorAll(".mixer-slider-item").forEach(item => {
        const name = item.getAttribute("data-name");
        if (weightsMap[name] !== undefined) {
            const val = weightsMap[name];
            item.querySelector(".custom-slider").value = val;
            item.querySelector(".slider-val").innerText = `${val}%`;
        }
    });
    updateDonutChart();
    debouncedUpdateWeights();
}

function updateDonutChart() {
    const weights = getCurrentWeights();
    const labels = Object.keys(weights);
    const data = Object.values(weights);
    
    charts.mixerDonut.data.labels = labels;
    charts.mixerDonut.data.datasets[0].data = data;
    charts.mixerDonut.update();
}

let updateWeightsTimeout = null;
function debouncedUpdateWeights() {
    clearTimeout(updateWeightsTimeout);
    updateWeightsTimeout = setTimeout(async () => {
        const weights = getCurrentWeights();
        await fetch('/api/update_strategy_weights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: activeSymbol, weights: weights })
        });
    }, 1000);
}

// Modal dialog configurations (1-M ~ 8-M)
let activeOrderPayload = null;
function initModalControls() {
    // 1. PANIC button click
    const btnPanic = document.getElementById("panic-button");
    const modalPanic = document.getElementById("modal-panic");
    
    btnPanic.addEventListener("click", () => {
        modalPanic.classList.add("active");
    });
    
    document.getElementById("btn-panic-cancel").addEventListener("click", () => {
        modalPanic.classList.remove("active");
    });
    
    document.getElementById("btn-panic-confirm").addEventListener("click", async () => {
        modalPanic.classList.remove("active");
        appendLog("WARNING", "Panic", "🚨 비상 정지 최종 승인 감지! 모든 미체결 주문 취소 및 포지션 청산 집행.");
        await fetch('/api/panic', { method: 'POST' });
    });

    // 2. Receipt Close
    document.getElementById("btn-receipt-close").addEventListener("click", () => {
        document.getElementById("modal-receipt").classList.remove("active");
    });

    // 3. Manual Order confirm popup (Screen 6-M)
    const btnBuy = document.getElementById("manual-buy-submit-btn");
    const btnSell = document.getElementById("manual-sell-submit-btn");
    const modalOrderConfirm = document.getElementById("modal-order-confirm");
    
    const proBuyBtn = document.getElementById("pro-buy-btn");
    const proSellBtn = document.getElementById("pro-sell-btn");

    // Standard Buy
    btnBuy.addEventListener("click", () => triggerManualBuyFlow("manual-order-symbol", "manual-order-price", "manual-order-volume"));
    proBuyBtn.addEventListener("click", () => triggerManualBuyFlow("pro-order-symbol", "pro-order-price", "pro-order-volume"));

    // Standard Sell
    btnSell.addEventListener("click", () => triggerManualSellFlow("manual-order-symbol", "manual-order-price", "manual-order-volume"));
    proSellBtn.addEventListener("click", () => triggerManualSellFlow("pro-order-symbol", "pro-order-price", "pro-order-volume"));

    // Order confirm button actions
    document.getElementById("btn-order-cancel").addEventListener("click", () => {
        modalOrderConfirm.classList.remove("active");
    });
    
    document.getElementById("btn-order-confirm").addEventListener("click", async () => {
        modalOrderConfirm.classList.remove("active");
        if (!activeOrderPayload) return;
        
        appendLog("INFO", "OrderExecutor", `지정가 주문 전송 중... ${activeOrderPayload.side} ${activeOrderPayload.volume} ${activeOrderPayload.symbol}`);
        
        await fetch('/api/manual_trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activeOrderPayload)
        });
    });

    // AI Sell warnings force/cancel buttons (Screen 7-M)
    const modalSellWarning = document.getElementById("modal-sell-warning");
    document.getElementById("btn-sell-warn-cancel").addEventListener("click", () => {
        modalSellWarning.classList.remove("active");
        appendLog("INFO", "ManualVerifier", "AI 권고 수용: 즉시 매도 주문 취소됨.");
    });
    
    document.getElementById("btn-sell-warn-force").addEventListener("click", async () => {
        modalSellWarning.classList.remove("active");
        appendLog("WARNING", "ManualVerifier", "사용자 매도 강행 감지! 빗썸 거래소로 매도 전송.");
        await fetch('/api/manual_trade', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activeOrderPayload)
        });
    });

    // 5. Add Monitored Symbol (Screen 8-M)
    document.getElementById("mixer-add-coin-btn").addEventListener("click", () => {
        document.getElementById("modal-add-symbol").classList.add("active");
    });
    
    document.getElementById("btn-add-symbol-close").addEventListener("click", () => {
        document.getElementById("modal-add-symbol").classList.remove("active");
    });
    
    document.getElementById("btn-add-symbol-submit").addEventListener("click", async () => {
        document.getElementById("modal-add-symbol").classList.remove("active");
        const symbol = document.getElementById("add-symbol-code").value;
        const threshold = document.getElementById("add-symbol-threshold").value;
        
        appendLog("INFO", "System", `신규 자산 감시 활성화: ${symbol} (자동 진입 임계점: ${threshold}%)`);
        await fetch('/api/add_symbol', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: symbol })
        });
    });
}

function triggerManualBuyFlow(symbolId, priceId, volumeId) {
    const symbol = document.getElementById(symbolId).value;
    const price = parseFloat(document.getElementById(priceId).value);
    const volume = parseFloat(document.getElementById(volumeId).value);
    
    activeOrderPayload = { symbol, side: "BUY", price, volume };
    
    document.getElementById("order-confirm-body-text").innerHTML = 
        `<strong>${symbol} ${volume}개</strong>를 <strong>${price.toLocaleString()} KRW</strong>에 지정가 매수 전송하시겠습니까?`;
    document.getElementById("modal-order-confirm").classList.add("active");
}

async function triggerManualSellFlow(symbolId, priceId, volumeId) {
    const symbol = document.getElementById(symbolId).value;
    const price = parseFloat(document.getElementById(priceId).value);
    const volume = parseFloat(document.getElementById(volumeId).value);
    
    activeOrderPayload = { symbol, side: "SELL", price, volume };
    
    appendLog("INFO", "ManualVerifier", `매도 주문 1.5초 실시간 후보고(AI Assist) 검증 구동 시작...`);
    
    try {
        const response = await fetch('/api/manual_sell_verifier', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(activeOrderPayload)
        });
        const data = await response.json();
        if (data.verdict === "WARN") {
            document.getElementById("modal-sell-warning").classList.add("active");
        } else {
            appendLog("INFO", "ManualVerifier", "AI 검증 통과. 매도 집행 완료.");
            fetchTradeHistory();
        }
    } catch (e) {
        console.error("Verifier request failed:", e);
    }
}

function showReceiptModal(trade) {
    document.getElementById("receipt-id").innerText = `#TRD-${trade.id || Math.randint(1000, 9999)}`;
    
    let dateStr = trade.timestamp;
    if (trade.timestamp.includes('T')) {
        dateStr = trade.timestamp.split('T')[0] + " " + trade.timestamp.split('T')[1].substring(0, 8);
    }
    document.getElementById("receipt-time").innerText = dateStr;
    document.getElementById("receipt-symbol").innerText = trade.symbol;
    
    const sideBadge = document.getElementById("receipt-side");
    sideBadge.innerText = trade.side.toUpperCase();
    if (trade.side.toUpperCase() === 'BUY') {
        sideBadge.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
        sideBadge.style.color = 'var(--color-success)';
    } else {
        sideBadge.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
        sideBadge.style.color = 'var(--color-panic)';
    }
    
    document.getElementById("receipt-price").innerText = trade.price.toLocaleString() + " KRW";
    document.getElementById("receipt-volume").innerText = `${trade.volume} ${trade.symbol.split('-')[1]}`;
    document.getElementById("receipt-fee").innerText = trade.fee.toLocaleString() + " KRW";
    
    const pnlText = document.getElementById("receipt-pnl");
    pnlText.innerText = (trade.pnl > 0 ? "+" : "") + trade.pnl.toLocaleString() + " KRW";
    pnlText.className = trade.pnl >= 0 ? "change-up" : "change-down";
    
    document.getElementById("modal-receipt").classList.add("active");
}

async function loadHistoricalCandles(symbol) {
    try {
        const response = await fetch(`/api/candles?symbol=${symbol}&limit=100`);
        const candles = await response.json();
        
        // Clear current charts data
        charts.dashboard.data.labels = [];
        charts.dashboard.data.datasets[0].data = [];
        charts.proDesk.data.labels = [];
        charts.proDesk.data.datasets[0].data = [];
        
        candles.forEach(c => {
            const formattedTime = c.time.split('T')[1]?.substring(0, 5) || c.time; // HH:MM
            const price = c.close;
            
            charts.dashboard.data.labels.push(formattedTime);
            charts.dashboard.data.datasets[0].data.push(price);
            
            charts.proDesk.data.labels.push(formattedTime);
            charts.proDesk.data.datasets[0].data.push(price);
        });
        
        charts.dashboard.update();
        charts.proDesk.update();
        
        console.log(`Loaded ${candles.length} historical candles for ${symbol}`);
    } catch (e) {
        console.error("Error loading historical candles:", e);
    }
}

function initSentimentControls() {
    const selectEl = document.getElementById("sentiment-engine-select");
    if (selectEl) {
        selectEl.addEventListener("change", async () => {
            const mode = selectEl.value;
            appendLog("INFO", "Sentiment", `AI 감성 분석 모드를 ${mode.toUpperCase()}(으)로 변경 요청 중...`);
            try {
                const response = await fetch('/api/set_sentiment_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode })
                });
                const data = await response.json();
                if (data.status === "success") {
                    appendLog("INFO", "Sentiment", `AI 감성 분석 모드가 ${mode.toUpperCase()}(으)로 변경되었습니다.`);
                    fetchSentimentState();
                } else {
                    appendLog("ERROR", "Sentiment", `모드 변경 실패: ${data.message}`);
                }
            } catch (err) {
                console.error("Failed to change sentiment mode:", err);
            }
        });
    }

    const btnTrigger = document.getElementById("btn-trigger-sentiment");
    if (btnTrigger) {
        btnTrigger.addEventListener("click", async () => {
            appendLog("INFO", "Sentiment", `${activeSymbol} 즉시 뉴스 수집 및 감성 분석 구동 시작...`);
            try {
                const response = await fetch('/api/trigger_sentiment_update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol: activeSymbol })
                });
                const data = await response.json();
                if (data.status === "success") {
                    appendLog("INFO", "Sentiment", `분석 요청 전송 완료. 백그라운드 연산 진행 중...`);
                    // Delay slightly to allow AI to respond, then fetch state
                    setTimeout(fetchSentimentState, 3000);
                } else {
                    appendLog("ERROR", "Sentiment", `분석 요청 실패: ${data.message}`);
                }
            } catch (err) {
                console.error("Failed to trigger sentiment update:", err);
            }
        });
    }
}

async function fetchSentimentState() {
    try {
        const response = await fetch(`/api/sentiment_state?symbol=${activeSymbol}`);
        const data = await response.json();
        
        // Update selector value if it exists but not focused
        const selectEl = document.getElementById("sentiment-engine-select");
        if (selectEl && document.activeElement !== selectEl) {
            selectEl.value = data.mode;
        }
        
        const sentimentInfo = data.latest_sentiment[activeSymbol] || { sentiment: "Neutral", score: 0.0, summary: "분석 이력 없음" };
        
        // Update Badge and Score
        const badgeEl = document.getElementById("sentiment-badge");
        const scoreEl = document.getElementById("sentiment-score-text");
        const summaryEl = document.getElementById("sentiment-summary-text");
        
        if (badgeEl) {
            badgeEl.innerText = sentimentInfo.sentiment;
            if (sentimentInfo.sentiment.toUpperCase() === "BULLISH") {
                badgeEl.style.backgroundColor = "rgba(16, 185, 129, 0.15)";
                badgeEl.style.color = "var(--color-success)";
            } else if (sentimentInfo.sentiment.toUpperCase() === "BEARISH") {
                badgeEl.style.backgroundColor = "rgba(239, 68, 68, 0.15)";
                badgeEl.style.color = "var(--color-panic)";
            } else {
                badgeEl.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                badgeEl.style.color = "var(--text-secondary)";
            }
        }
        
        if (scoreEl) {
            scoreEl.innerText = (sentimentInfo.score >= 0 ? "+" : "") + sentimentInfo.score.toFixed(2);
            scoreEl.style.color = sentimentInfo.score > 0 ? "var(--color-success)" : (sentimentInfo.score < 0 ? "var(--color-panic)" : "var(--text-primary)");
        }
        
        if (summaryEl) {
            summaryEl.innerText = sentimentInfo.summary;
        }
        
        // Render News feed
        const newsFeedEl = document.getElementById("sentiment-news-feed");
        if (newsFeedEl) {
            newsFeedEl.innerHTML = "";
            if (!data.news_list || data.news_list.length === 0) {
                newsFeedEl.innerHTML = `<div style="text-align: center; color: var(--text-secondary); padding: 20px;">수집된 뉴스가 없습니다.</div>`;
            } else {
                data.news_list.forEach(n => {
                    const div = document.createElement("div");
                    div.style.borderBottom = "1px solid rgba(255, 255, 255, 0.02)";
                    div.style.paddingBottom = "6px";
                    
                    const timeStr = n.published || "";
                    div.innerHTML = `
                        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">
                            <a href="${n.link}" target="_blank" style="color: var(--text-primary); text-decoration: none; hover: underline;">${n.title}</a>
                        </div>
                        <div style="font-size: 10px; color: var(--text-secondary);">${timeStr}</div>
                    `;
                    newsFeedEl.appendChild(div);
                });
            }
        }
        
        // Render memory reflection
        const reflectionEl = document.getElementById("sentiment-reflection-log");
        if (reflectionEl) {
            reflectionEl.innerText = data.past_memory || "과거 성찰 내역이 없습니다.";
        }
    } catch (e) {
        console.error("Error fetching sentiment state:", e);
    }
}


