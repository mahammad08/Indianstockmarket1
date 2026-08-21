import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import feedparser
import streamlit.components.v1 as components
from datetime import datetime, date
from google import genai
import streamlit as st

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Indian Market & Metals Swing Radar",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background-color: #1e222d;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #2962ff;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization (Active + Sample Achieved)
# ---------------------------------------------------------
if "trades" not in st.session_state or len(st.session_state.trades) == 0:
    st.session_state.trades = [
        {
            "symbol": "BEL.NS",
            "name": "Bharat Electronics",
            "category": "Large Cap",
            "pattern": "20 EMA Bounce",
            "entry_price": 295.0,
            "stop_loss": 282.0,
            "target1": 321.0,
            "target2": 334.0,
            "entry_date": str(date.today()),
            "status": "Active",
            "notes": "Defense sector momentum, testing 20 EMA support."
        },
        {
            "symbol": "TRENT.NS",
            "name": "Trent Ltd",
            "category": "Large Cap",
            "pattern": "Macro Base Breakout",
            "entry_price": 6800.0,
            "stop_loss": 6550.0,
            "target1": 7300.0,
            "target2": 7550.0,
            "entry_date": str(date.today()),
            "status": "Active",
            "notes": "Stage 2 breakout above resistance with volume."
        },
        {
            "symbol": "HAL.NS",
            "name": "Hindustan Aeronautics",
            "category": "Large Cap",
            "pattern": "Cup & Handle",
            "entry_price": 4750.0,
            "stop_loss": 4550.0,
            "target1": 5150.0,
            "target2": 5350.0,
            "entry_date": "2026-08-10",
            "status": "Target 2 Hit",
            "notes": "Target 2 achieved at 5350."
        },
        {
            "symbol": "SBIN.NS",
            "name": "State Bank of India",
            "category": "PSU Banks",
            "pattern": "50 EMA Support",
            "entry_price": 845.0,
            "stop_loss": 820.0,
            "target1": 895.0,
            "target2": 920.0,
            "entry_date": "2026-08-08",
            "status": "Stop Loss Hit",
            "notes": "Banking index pullback broke stop loss."
        }
    ]

# ---------------------------------------------------------
# Universe & Stock Mappings
# ---------------------------------------------------------
LARGE_CAPS = {
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Infosys": "INFY.NS",
    "State Bank of India": "SBIN.NS",
    "Larsen & Toubro": "LT.NS",
    "ITC Ltd": "ITC.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Bharat Electronics": "BEL.NS",
    "Trent Ltd": "TRENT.NS",
    "Hindustan Aeronautics": "HAL.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Sun Pharma": "SUNPHARMA.NS",
}

MID_CAPS = {
    "Polycab India": "POLYCAB.NS",
    "Persistent Systems": "PERSISTENT.NS",
    "Tata Communications": "TATACOMM.NS",
    "Dixon Technologies": "DIXON.NS",
    "Federal Bank": "FEDERALBNK.NS",
    "Ashok Leyland": "ASHOKLEY.NS",
    "Cummins India": "CUMMINSIND.NS",
    "APL Apollo Tubes": "APLAPOLLO.NS",
}

SMALL_CAPS = {
    "KPIT Technologies": "KPITTECH.NS",
    "CDSL": "CDSL.NS",
    "Birlasoft": "BSOFT.NS",
    "Kaynes Technology": "KAYNES.NS",
    "Radico Khaitan": "RADICO.NS",
    "Zen Technologies": "ZENTEC.NS",
}

PSU_BANKS = {
    "State Bank of India": "SBIN.NS",
    "Bank of Baroda": "BANKBARODA.NS",
    "Punjab National Bank": "PNB.NS",
    "Canara Bank": "CANBK.NS",
    "Union Bank of India": "UNIONBANK.NS",
    "Indian Bank": "INDIANB.NS",
}

METALS_ETFS = {
    "Nippon India Gold BEES": "GOLDBEES.NS",
    "Nippon India Silver BEES": "SILVERBEES.NS",
    "Tata Steel": "TATASTEEL.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Hindalco Industries": "HINDALCO.NS",
    "Vedanta": "VEDL.NS",
}

ALL_STOCKS = {**LARGE_CAPS, **MID_CAPS, **SMALL_CAPS, **PSU_BANKS, **METALS_ETFS}


# ---------------------------------------------------------
# Technical Indicators & Strategy Calculation
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

        high_low = df["High"] - df["Low"]
        high_close = np.abs(df["High"] - df["Close"].shift())
        low_close = np.abs(df["Low"] - df["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR14"] = tr.rolling(window=14).mean()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df["RSI14"] = 100 - (100 / (1 + rs))

        return df
    except Exception:
        return None


def calculate_swing_strategy(df):
    latest = df.iloc[-1]
    ltp = round(float(latest["Close"]), 2)
    ema20 = round(float(latest["EMA20"]), 2)
    ema50 = round(float(latest["EMA50"]), 2)
    atr = round(float(latest["ATR14"]), 2)
    rsi = round(float(latest["RSI14"]), 2)

    stop_loss = round(ltp - (1.5 * atr), 2)
    risk = round(ltp - stop_loss, 2)
    target1 = round(ltp + (2.0 * risk), 2)
    target2 = round(ltp + (3.0 * risk), 2)

    if ltp > ema20 > ema50:
        trend = "Bullish Stage 2 (Above 20 & 50 EMA)"
        badge = "🟢 Strong Uptrend"
    elif ltp > ema50 and abs(ltp - ema20) / ltp < 0.025:
        trend = "Consolidation / 20 EMA Pullback"
        badge = "🟡 Pullback Setup"
    else:
        trend = "Neutral / Below Key Averages"
        badge = "⚪ Sideways / Corrective"

    return {
        "ltp": ltp,
        "ema20": ema20,
        "ema50": ema50,
        "atr": atr,
        "rsi": rsi,
        "stop_loss": stop_loss,
        "risk": risk,
        "risk_pct": round((risk / ltp) * 100, 2),
        "target1": target1,
        "target2": target2,
        "trend": trend,
        "badge": badge
    }


@st.cache_data(ttl=600)
def scan_fresh_market_setups():
    candidates = []
    scan_universe = {
        "BEL": "BEL.NS", "TRENT": "TRENT.NS", "HAL": "HAL.NS",
        "TATAMOTORS": "TATAMOTORS.NS", "SBIN": "SBIN.NS", "POLYCAB": "POLYCAB.NS",
        "PERSISTENT": "PERSISTENT.NS", "DIXON": "DIXON.NS", "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS", "GOLDBEES": "GOLDBEES.NS"
    }

    for name, ticker in scan_universe.items():
        try:
            df = fetch_stock_data(ticker)
            if df is not None and len(df) >= 50:
                metrics = calculate_swing_strategy(df)
                if "Bullish" in metrics["trend"] or "Pullback" in metrics["trend"]:
                    candidates.append({
                        "Symbol": ticker,
                        "Name": name,
                        "LTP (₹)": metrics["ltp"],
                        "Setup": metrics["badge"],
                        "20 EMA (₹)": metrics["ema20"],
                        "Stop Loss (₹)": metrics["stop_loss"],
                        "Target 1 (2R) (₹)": metrics["target1"],
                        "Target 2 (3R) (₹)": metrics["target2"],
                        "Risk %": f"{metrics['risk_pct']}%",
                        "RSI (14)": metrics["rsi"]
                    })
        except Exception:
            continue

    return pd.DataFrame(candidates)


# ---------------------------------------------------------
# TradingView Chart Widget
# ---------------------------------------------------------
def render_tradingview_widget(symbol):
    clean_sym = symbol.replace(".NS", "").replace(".BO", "")
    tv_symbol = f"NSE:{clean_sym}"
    tv_html = f"""
    <div class="tradingview-widget-container" style="height:480px;width:100%">
      <div id="tradingview_chart" style="height:100%;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(tv_html, height=500)


# ---------------------------------------------------------
# Multi-Source News Aggregator
# ---------------------------------------------------------
NEWS_FEEDS = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "Livemint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "Economic Times": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
}


@st.cache_data(ttl=300)
def fetch_multi_source_news():
    all_articles = []
    for source, url in NEWS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                all_articles.append({
                    "source": source,
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.get("published", entry.get("updated", "Recent"))
                })
        except Exception:
            continue
    return all_articles


# ---------------------------------------------------------
# UI: Top Header & Market Ticker
# ---------------------------------------------------------
st.title("⚡ Indian Market & Metals Swing Radar")
st.caption("Real-Time Technical Swing Screener, Risk/Reward Engine & Strategy Performance Hub")


@st.cache_data(ttl=300)
def get_market_indices():
    indices = {
        "NIFTY 50": "^NSEI",
        "MIDCAP 100": "^NSEMDCP50",
        "GOLD (GOLDBEES)": "GOLDBEES.NS",
        "SILVER (SILVERBEES)": "SILVERBEES.NS"
    }
    data = {}
    for name, ticker in indices.items():
        try:
            df = yf.download(ticker, period="2d", progress=False)
            if not df.empty and len(df) >= 2:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                cur = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                chg = ((cur - prev) / prev) * 100
                data[name] = (cur, chg)
            elif not df.empty:
                cur = float(df["Close"].iloc[-1])
                data[name] = (cur, 0.0)
        except Exception:
            data[name] = (0.0, 0.0)
    return data


indices_data = get_market_indices()
t_cols = st.columns(len(indices_data))
for col, (idx_name, (price, change)) in zip(t_cols, indices_data.items()):
    col.metric(label=idx_name, value=f"₹{price:,.2f}" if price > 0 else "N/A", delta=f"{change:+.2f}%")

st.markdown("---")


# ---------------------------------------------------------
# Sidebar: Universal Search & Global AI Settings
# ---------------------------------------------------------
def reset_global_search():
    st.session_state["global_search_dropdown"] = "-- None (Use Tabs) --"
    st.session_state["custom_ticker_input"] = ""

st.sidebar.header("🔍 Global Stock Search")

search_query = st.sidebar.selectbox(
    "Search Master Universe (500+ Stocks):",
    options=["-- None (Use Tabs) --"] + [f"{name} ({sym})" for name, sym in sorted(ALL_STOCKS.items())],
    index=0,
    key="global_search_dropdown"
)

custom_ticker_input = st.sidebar.text_input(
    "Or Enter Any Custom NSE Ticker:",
    placeholder="e.g. INFY, ADANIPOWER, ZOMATO",
    key="custom_ticker_input"
).strip().upper()

if st.sidebar.button("🧹 Clear Search", on_click=reset_global_search):
    st.rerun()

# --- GLOBAL AI API KEY (Place here once) ---
st.sidebar.markdown("---")
st.sidebar.header("🤖 AI Settings")
gemini_key = st.sidebar.text_input(
    "🔑 Gemini API Key (Optional):",
    type="password",
    placeholder="AIzaSy...",
    key="gemini_api_key"
)


# ---------------------------------------------------------
# Stock Analyzer Render Function
# ---------------------------------------------------------
def display_stock_analysis(ticker, company_name, category="Custom"):
    st.subheader(f"📊 {company_name} (`{ticker}`)")

    df = fetch_stock_data(ticker)
    if df is None or len(df) < 50:
        st.error(f"Could not load data for {ticker}. Verify ticker symbol.")
        return

    metrics = calculate_swing_strategy(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("LTP (Entry)", f"₹{metrics['ltp']}")
    c2.metric("Stop Loss (1.5 ATR)", f"₹{metrics['stop_loss']}", delta=f"-{metrics['risk_pct']}%",
              delta_color="inverse")
    c3.metric("Target 1 (2R)", f"₹{metrics['target1']}", delta=f"+{round(metrics['risk_pct'] * 2, 1)}%")
    c4.metric("Target 2 (3R)", f"₹{metrics['target2']}", delta=f"+{round(metrics['risk_pct'] * 3, 1)}%")
    c5.metric("RSI (14)", f"{metrics['rsi']}")

    st.info(
        f"**Trend Evaluation:** {metrics['badge']} — {metrics['trend']} | **20 EMA:** ₹{metrics['ema20']} | **50 EMA:** ₹{metrics['ema50']} | **ATR:** ₹{metrics['atr']}")

    # AI Analysis Expander
    with st.expander("🤖 **AI Swing Strategy & Catalyst Analysis**"):
        if st.button("✨ Generate AI Trade Rationale", key=f"ai_btn_{ticker}"):
            current_key = st.session_state.get("gemini_api_key", "")
            with st.spinner("Analyzing technical metrics with Gemini..."):
                ai_report = generate_ai_analysis(ticker, company_name, metrics, current_key)
                st.markdown(ai_report)

    # Chart & Tracker Action
    col_chart, col_side = st.columns([3, 1])
    with col_chart:
        render_tradingview_widget(ticker)

    with col_side:
        st.markdown("### 🎯 Quick Trade Logger")
        pattern_type = st.selectbox("Setup Pattern",
                                    ["20 EMA Bounce", "Macro Base Breakout", "Cup & Handle", "50 EMA Support",
                                     "Pullback Reversal"], key=f"pat_{ticker}")
        notes = st.text_area("Trade Rationale / Notes", "Holding above key averages with volume confirmation.",
                             key=f"note_{ticker}")

        if st.button(f"📥 Add {ticker} to Tracker", key=f"btn_{ticker}", use_container_width=True):
            new_trade = {
                "symbol": ticker,
                "name": company_name,
                "category": category,
                "pattern": pattern_type,
                "entry_price": metrics["ltp"],
                "stop_loss": metrics["stop_loss"],
                "target1": metrics["target1"],
                "target2": metrics["target2"],
                "entry_date": str(date.today()),
                "status": "Active",
                "notes": notes
            }
            st.session_state.trades.append(new_trade)
            st.success(f"Added {ticker} to Active Radar!")

# --- INITIALIZE & PARSE SELECTED TICKER ---
selected_global_ticker = None
selected_global_name = None

if "global_search_dropdown" in st.session_state and st.session_state["global_search_dropdown"] != "-- None (Use Tabs) --":
    search_val = st.session_state["global_search_dropdown"]
    selected_global_ticker = search_val.split("(")[-1].replace(")", "").strip()
    selected_global_name = search_val.split(" (")[0]
elif "custom_ticker_input" in st.session_state and st.session_state["custom_ticker_input"].strip():
    raw_input = st.session_state["custom_ticker_input"].strip().upper().replace(" ", "")
    if not (raw_input.endswith(".NS") or raw_input.endswith(".BO")):
        raw_input = f"{raw_input}.NS"
    selected_global_ticker = raw_input
    selected_global_name = raw_input.replace(".NS", "").replace(".BO", "")

# Line 471 follows below:
if selected_global_ticker:
    st.markdown(f"### 🎯 Global Search Result for: `{selected_global_ticker}`")
    if st.button("⬅️ Back to Market Tabs", on_click=reset_global_search):
        st.rerun()
    display_stock_analysis(selected_global_ticker, selected_global_name, "Global Search")
    st.stop()

# ---------------------------------------------------------
# Main App Routing (Global Search Result)
# ---------------------------------------------------------
if selected_global_ticker:
    st.markdown(f"### 🎯 Global Search Result for: `{selected_global_ticker}`")
    if st.button("⬅️ Back to Market Tabs", on_click=reset_global_search):
        st.rerun()
    display_stock_analysis(selected_global_ticker, selected_global_name, "Global Search")
    st.stop()

# ---------------------------------------------------------
# Main Navigation Tabs
# ---------------------------------------------------------
tab_tracker, tab_large, tab_mid, tab_small, tab_psu, tab_metals, tab_news = st.tabs([
    "⚡ Action Calls & Analytics",
    "💎 Large Cap (Nifty 50)",
    "🚀 Mid Cap (150)",
    "🔥 Small Cap (250)",
    "🏛️ PSU Banks",
    "🟡 Gold & Metals",
    "📰 Live News Radar"
])

# ---------------------------------------------------------
# Tab 1: Action Calls Hub (Upcoming + Achieved)
# ---------------------------------------------------------
with tab_tracker:
    st.subheader("⚡ Action Calls & Strategy Performance Hub")

    sub_tab_upcoming, sub_tab_achieved = st.tabs([
        "🚀 Upcoming & Active Calls",
        "🏆 Achieved Targets & Analytics"
    ])

    # 1. UPCOMING & ACTIVE CALLS
    with sub_tab_upcoming:
        st.markdown("### 🔍 1. Today's Fresh Market Setups (Live Scanner)")
        st.caption("Stocks currently meeting **Bullish Stage 2** and **20 EMA Pullback** criteria across the universe.")

        scanner_df = scan_fresh_market_setups()
        if not scanner_df.empty:
            st.dataframe(scanner_df, use_container_width=True)
        else:
            st.info("Scanning universe... No fresh triggers at this exact moment.")

        st.markdown("---")
        st.markdown("### 🎯 2. Active Radar Positions (In Progress)")

        active_trades = [t for t in st.session_state.trades if t.get("status") == "Active"]

        if active_trades:
            for idx, trade in enumerate(active_trades):
                with st.container():
                    df_curr = fetch_stock_data(trade["symbol"])
                    cur_price = round(float(df_curr["Close"].iloc[-1]), 2) if df_curr is not None else trade[
                        "entry_price"]
                    pnl_pct = round(((cur_price - trade["entry_price"]) / trade["entry_price"]) * 100, 2)

                    c_info, c_levels, c_actions = st.columns([2, 3, 2])
                    with c_info:
                        st.markdown(f"#### **{trade['name']} (`{trade['symbol']}`)**")
                        st.caption(f"Setup: **{trade['pattern']}** | Logged: {trade['entry_date']}")
                        st.write(f"*{trade['notes']}*")

                    with c_levels:
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Entry", f"₹{trade['entry_price']}")
                        m2.metric("Live LTP", f"₹{cur_price}", delta=f"{pnl_pct:+}%")
                        m3.metric("Target 1 (2R)", f"₹{trade['target1']}")
                        m4.metric("Target 2 (3R)", f"₹{trade['target2']}")

                    with c_actions:
                        st.markdown(f"**Stop Loss:** `₹{trade['stop_loss']}`")
                        b1, b2 = st.columns(2)
                        if b1.button("🏆 Target Hit", key=f"win_{idx}", use_container_width=True):
                            trade["status"] = "Target 2 Hit"
                            trade["exit_date"] = str(date.today())
                            st.success(f"{trade['symbol']} marked as Achieved!")
                            st.rerun()
                        if b2.button("❌ Stop Loss", key=f"loss_{idx}", use_container_width=True):
                            trade["status"] = "Stop Loss Hit"
                            trade["exit_date"] = str(date.today())
                            st.warning(f"{trade['symbol']} marked as Stop Loss Hit.")
                            st.rerun()
                    st.divider()
        else:
            st.info("No active positions currently logged. Use the scanner above or the form below to add trades.")

        with st.expander("➕ Log New Upcoming Trade to Radar"):
            with st.form("add_trade_form"):
                f1, f2, f3 = st.columns(3)
                with f1:
                    t_sym = st.text_input("NSE Symbol (e.g. HAL.NS):").upper().strip()
                    t_name = st.text_input("Company Name:")
                with f2:
                    t_entry = st.number_input("Entry Price (₹):", min_value=0.0, step=1.0)
                    t_sl = st.number_input("Stop Loss (₹):", min_value=0.0, step=1.0)
                with f3:
                    t_t1 = st.number_input("Target 1 (2R) (₹):", min_value=0.0, step=1.0)
                    t_t2 = st.number_input("Target 2 (3R) (₹):", min_value=0.0, step=1.0)
                t_pat = st.selectbox("Setup Type:",
                                     ["20 EMA Bounce", "Macro Base Breakout", "50 EMA Support", "Cup & Handle"])
                t_note = st.text_input("Trade Catalyst / Notes:")

                if st.form_submit_button("Save to Active Radar"):
                    if t_sym and t_entry > 0:
                        st.session_state.trades.append({
                            "symbol": t_sym if t_sym.endswith(".NS") else f"{t_sym}.NS",
                            "name": t_name if t_name else t_sym,
                            "category": "Custom",
                            "pattern": t_pat,
                            "entry_price": t_entry,
                            "stop_loss": t_sl,
                            "target1": t_t1,
                            "target2": t_t2,
                            "entry_date": str(date.today()),
                            "status": "Active",
                            "notes": t_note
                        })
                        st.success(f"Added {t_sym} to Active Radar!")
                        st.rerun()

    # 2. ACHIEVED TARGETS & ANALYTICS
    with sub_tab_achieved:
        st.markdown("### 🏆 Achieved Targets & Closed Trade Analytics")

        achieved_trades = [t for t in st.session_state.trades if t.get("status") != "Active"]

        if achieved_trades:
            ach_df = pd.DataFrame(achieved_trades)

            total_closed = len(ach_df)
            t2_wins = len(ach_df[ach_df["status"] == "Target 2 Hit"])
            t1_wins = len(ach_df[ach_df["status"] == "Target 1 Hit"])
            sl_losses = len(ach_df[ach_df["status"] == "Stop Loss Hit"])
            win_rate = round(((t2_wins + t1_wins) / total_closed) * 100, 1) if total_closed > 0 else 0.0

            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            kpi1.metric("Total Closed Trades", total_closed)
            kpi2.metric("Win Rate", f"{win_rate}%")
            kpi3.metric("Target 2 Hits (3R)", t2_wins)
            kpi4.metric("Target 1 Hits (2R)", t1_wins)
            kpi5.metric("Stop Loss Exits", sl_losses, delta_color="inverse")

            st.markdown("---")

            g1, g2 = st.columns(2)
            with g1:
                fig_donut = px.pie(
                    ach_df,
                    names="status",
                    title="🎯 Target Achieved vs. Missed Ratio",
                    color="status",
                    color_discrete_map={
                        "Target 2 Hit": "#00C853",
                        "Target 1 Hit": "#76FF03",
                        "Stop Loss Hit": "#FF1744"
                    },
                    hole=0.45
                )
                fig_donut.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_donut, use_container_width=True)

            with g2:
                r_map = {"Target 2 Hit": 3.0, "Target 1 Hit": 2.0, "Stop Loss Hit": -1.0}
                ach_df["R_Return"] = ach_df["status"].map(r_map).fillna(0.0)
                ach_df["Cumulative_R"] = ach_df["R_Return"].cumsum()

                fig_line = px.line(
                    ach_df,
                    x="symbol",
                    y="Cumulative_R",
                    title="📈 Cumulative Strategy Performance (R-Multiples)",
                    markers=True
                )
                fig_line.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_line, use_container_width=True)

            st.markdown("### 📋 Historical Achieved & Closed Trades Ledger")
            st.dataframe(
                ach_df[["symbol", "name", "pattern", "entry_price", "target1", "target2", "stop_loss", "status",
                        "entry_date"]],
                use_container_width=True
            )
        else:
            st.info(
                "No trades have been marked as achieved yet. Mark active trades complete in the 'Upcoming & Active Calls' tab.")


# ---------------------------------------------------------
# Tabs 2-6: Market Cap & Sector Analyzers
# ---------------------------------------------------------
def render_sector_tab(stock_dict, category_name):
    selected_name = st.selectbox(f"Select {category_name} Stock:", list(stock_dict.keys()), key=f"sel_{category_name}")
    ticker = stock_dict[selected_name]
    display_stock_analysis(ticker, selected_name, category_name)


with tab_large:
    render_sector_tab(LARGE_CAPS, "Large Cap")

with tab_mid:
    render_sector_tab(MID_CAPS, "Mid Cap")

with tab_small:
    render_sector_tab(SMALL_CAPS, "Small Cap")

with tab_psu:
    render_sector_tab(PSU_BANKS, "PSU Banks")

with tab_metals:
    render_sector_tab(METALS_ETFS, "Gold & Metals")

# ---------------------------------------------------------
# Tab 7: Multi-Source Live News Radar
# ---------------------------------------------------------
with tab_news:
    st.subheader("📰 Multi-Source Financial News Radar")
    st.caption("Aggregated streaming financial news from Moneycontrol, Livemint, Business Standard, and Economic Times")

    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        source_filter = st.multiselect("Filter Source:", list(NEWS_FEEDS.keys()), default=list(NEWS_FEEDS.keys()))
    with col_filter2:
        search_kw = st.text_input("Search Headlines:", placeholder="e.g. RBI, Tata, Earnings, Defense")

    articles = fetch_multi_source_news()
    filtered_articles = [a for a in articles if a["source"] in source_filter]
    if search_kw:
        filtered_articles = [a for a in filtered_articles if search_kw.lower() in a["title"].lower()]

    if filtered_articles:
        for item in filtered_articles:
            with st.container():
                st.markdown(f"**[{item['source']}]** [{item['title']}]({item['link']})")
                st.caption(f"Published: {item['published']}")
                st.divider()
    else:
        st.info("No matching news articles found.")



def generate_ai_analysis(ticker, company_name, metrics, api_key):
    """Sends technical indicators and trend data to Gemini for automated trade thesis."""
    if not api_key:
        return "⚠️ Please enter your Gemini API Key in the sidebar to enable AI analysis."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
        You are a quantitative swing trading research assistant specializing in Indian Equities (NSE/BSE).

        Analyze the following technical setup:
        - Stock: {company_name} ({ticker})
        - Current Market Price (LTP): ₹{metrics['ltp']}
        - 20-day EMA: ₹{metrics['ema20']}
        - 50-day EMA: ₹{metrics['ema50']}
        - 14-period ATR (Volatility): ₹{metrics['atr']}
        - 14-period RSI: {metrics['rsi']}
        - Setup State: {metrics['trend']}
        - Calculated Stop Loss: ₹{metrics['stop_loss']} (1.5 ATR)
        - Target 1 (2R): ₹{metrics['target1']} | Target 2 (3R): ₹{metrics['target2']}

        Provide a concise analysis in 3 structured sections:
        1. **Technical Setup Rationale**: Evaluate the 20/50 EMA alignment and whether this represents a high-probability swing setup.
        2. **Risk & Invalidation Level**: Clarify where the thesis fails and how to manage the stop loss.
        3. **Sector Catalyst / Key Factor**: Key Indian market triggers or earnings factors to watch for this sector.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Error generating analysis: {str(e)}"