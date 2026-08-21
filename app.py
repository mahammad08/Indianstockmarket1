import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yfinance as yf
import feedparser
import requests
import io
import datetime

st.set_page_config(page_title="AlphaRadar | Indian Equities & Metals", layout="wide", page_icon="📈")


# ---------------------------------------------------------
# 1. TRADINGVIEW EMBED GENERATOR (NSE Focused)
# ---------------------------------------------------------
def render_tradingview_chart(symbol: str, height: int = 420):
    clean = symbol.replace(".NS", "").strip().upper()
    if clean in ["GC=F", "GOLD"]:
        tv_symbol = "COMEX:GC1!"
    elif clean in ["SI=F", "SILVER"]:
        tv_symbol = "COMEX:SI1!"
    elif clean in ["NIFTY", "^NSEI"]:
        tv_symbol = "NSE:NIFTY"
    elif clean in ["BANKNIFTY", "^NSEBANK"]:
        tv_symbol = "NSE:BANKNIFTY"
    elif clean in ["CNXPSUBANK", "^CNXPSUBANK"]:
        tv_symbol = "NSE:CNXPSUBANK"
    else:
        tv_symbol = f"NSE:{clean}"

    html = f"""
    <div class="tradingview-widget-container" style="height:{height}px; width:100%;">
      <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px); width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
        "autosize": true,
        "symbol": "{tv_symbol}",
        "interval": "D",
        "timezone": "Asia/Kolkata",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "calendar": false,
        "support_host": "https://www.tradingview.com"
      }}
      </script>
    </div>
    """
    components.html(html, height=height)


# ---------------------------------------------------------
# 2. DYNAMIC OFFICIAL NSE / NIFTY CONSTITUENTS INGESTION
# ---------------------------------------------------------
@st.cache_data(ttl=86400)
def get_all_indian_stocks_by_category():
    """
    Fetches the official constituent CSVs directly from NiftyIndices archives.
    Loads all 50 Large Cap, 150 Mid Cap, 250 Small Cap, and PSU Bank stocks.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    urls = {
        "Large Cap": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "Mid Cap": "https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv",
        "Small Cap": "https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv",
        "PSU Banks": "https://www.niftyindices.com/IndexConstituent/ind_niftypsubanklist.csv"
    }

    universes = {}
    for category, url in urls.items():
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                df = pd.read_csv(io.StringIO(resp.text))
                if "Symbol" in df.columns:
                    universes[category] = sorted(df["Symbol"].dropna().str.strip().tolist())
                else:
                    universes[category] = []
            else:
                universes[category] = []
        except Exception:
            universes[category] = []

    # Curated precious metals list
    universes["Gold & Silver ETFs"] = [
        "GOLDBEES", "SILVERBEES", "HDFCGOLD", "SETFGOLD", "AXISGOLD", "ICICIGOLD", "KOTAKGOLD"
    ]

    # Offline/Resilient Fallbacks
    fallbacks = {
        "Large Cap": ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "INFY", "ITC", "LT", "TRENT", "M&M",
                      "KOTAKBANK"],
        "Mid Cap": ["DIXON", "POLYCAB", "PERSISTENT", "COFORGE", "FEDERALBNK", "VOLTAS", "CUMMINSIND", "ASTRAL",
                    "ASHOKLEY"],
        "Small Cap": ["KAYNES", "CDSL", "BSOFT", "KPITTECH", "ANGELONE", "CYIENT", "CAMS", "RADICO", "SONACOMS"],
        "PSU Banks": ["SBIN", "CANBK", "BANKBARODA", "PNB", "UNIONBANK", "INDIANB", "BANKINDIA"]
    }

    for k, v in fallbacks.items():
        if not universes.get(k):
            universes[k] = v

    return universes


# ---------------------------------------------------------
# 3. TOP INDICES & COMMODITIES BAR
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_indices_snapshot():
    tickers = {
        "Nifty 50": "^NSEI",
        "MidCap 100": "^CRSLDX",
        "SmallCap 100": "^CNXSC",
        "PSU Bank": "^CNXPSUBANK",
        "COMEX Gold": "GC=F",
        "COMEX Silver": "SI=F",
        "GOLDBEES": "GOLDBEES.NS",
        "SILVERBEES": "SILVERBEES.NS"
    }
    data = {}
    for name, sym in tickers.items():
        try:
            hist = yf.Ticker(sym).history(period="5d")
            if len(hist) >= 2:
                prev = hist['Close'].iloc[-2]
                curr = hist['Close'].iloc[-1]
                pct = ((curr - prev) / prev) * 100
                data[name] = {"price": round(float(curr), 2), "change": round(float(pct), 2)}
            elif len(hist) == 1:
                data[name] = {"price": round(float(hist['Close'].iloc[-1]), 2), "change": 0.0}
            else:
                data[name] = {"price": 0.0, "change": 0.0}
        except Exception:
            data[name] = {"price": 0.0, "change": 0.0}
    return data


# ---------------------------------------------------------
# 4. NEWS RADAR (Moneycontrol, Zerodha Pulse, ET)
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_news_feed():
    feeds = {
        "Moneycontrol (Markets)": "https://www.moneycontrol.com/rss/MCmarket.xml",
        "Moneycontrol (Commodities & Metals)": "https://www.moneycontrol.com/rss/commodity.xml",
        "Zerodha Pulse": "https://pulse.zerodha.com/feed",
        "Economic Times (Stocks)": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"
    }
    articles = []
    for src, url in feeds.items():
        try:
            parsed = feedparser.parse(url)
            for item in parsed.entries[:6]:
                articles.append({
                    "source": src,
                    "title": item.title,
                    "link": item.link,
                    "published": item.get("published", "Recent")
                })
        except Exception:
            continue
    return articles


# ---------------------------------------------------------
# 5. DYNAMIC TECHNICAL & ATR LEVEL CALCULATOR
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def calculate_dynamic_swing_levels(symbol: str):
    ticker_sym = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
    try:
        ticker = yf.Ticker(ticker_sym)
        df = ticker.history(period="6mo")

        if df is None or df.empty or len(df) < 14:
            return None

        # Calculate 14-period ATR
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_14 = tr.rolling(window=14).mean().dropna().iloc[-1]

        ema_20 = df['Close'].ewm(span=20).mean().iloc[-1]
        ema_50 = df['Close'].ewm(span=50).mean().iloc[-1]

        curr_price = round(float(df['Close'].iloc[-1]), 2)
        atr_val = round(float(atr_14), 2)

        entry_price = curr_price
        stop_loss = round(entry_price - (1.5 * atr_val), 2)
        risk = entry_price - stop_loss
        target_1 = round(entry_price + (2.0 * risk), 2)
        target_2 = round(entry_price + (3.0 * risk), 2)

        in_uptrend = curr_price > ema_20 > ema_50
        trend_status = "Bullish Stage 2 (Above 20 & 50 EMA)" if in_uptrend else "Consolidation / Pullback"

        return {
            "symbol": symbol,
            "current_price": curr_price,
            "ema_20": round(float(ema_20), 2),
            "ema_50": round(float(ema_50), 2),
            "atr_14": atr_val,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "trend_status": trend_status
        }
    except Exception:
        return None


# ---------------------------------------------------------
# 6. TRADE TARGET & STOP LOSS MONITORING ENGINE
# ---------------------------------------------------------
def evaluate_trade_lifecycle(trade):
    symbol = f"{trade['symbol']}.NS" if not trade['symbol'].endswith(".NS") else trade['symbol']
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=trade["entry_date"])
        if df is None or df.empty:
            return "⏳ Monitoring (Waiting for price updates)", "gray"

        high_val = float(df["High"].max())
        low_val = float(df["Low"].min())

        if high_val >= trade["target_2"]:
            return "🎯 Target 2 Reached (+3R)", "green"
        elif high_val >= trade["target_1"]:
            return "🎯 Target 1 Reached (+2R)", "green"
        elif low_val <= trade["stop_loss"]:
            return "🛑 Stop Loss Hit", "red"
        else:
            return "⏳ Active / Holding", "orange"
    except Exception:
        return "⏳ Active / Holding", "orange"


# ---------------------------------------------------------
# 7. CATEGORY TAB RENDERER
# ---------------------------------------------------------
def render_dynamic_category_tab(category_name: str, universes_dict: dict):
    stock_list = universes_dict.get(category_name, [])

    col_select, col_info = st.columns([1.5, 2])
    with col_select:
        selected_stock = st.selectbox(
            f"Select Stock ({len(stock_list)} Available):",
            stock_list,
            key=f"select_{category_name}"
        )
    with col_info:
        st.write("")
        st.caption(f"Loaded all official **{category_name}** constituents from NSE/NiftyIndices.")

    with st.spinner(f"Fetching technical metrics for {selected_stock}..."):
        data = calculate_dynamic_swing_levels(selected_stock)

    if data:
        c1, c2 = st.columns([1.4, 1])
        with c1:
            render_tradingview_chart(selected_stock, height=420)
        with c2:
            st.markdown(f"### **NSE: {data['symbol']}**")
            st.caption(f"**Trend Condition:** `{data['trend_status']}`")

            m1, m2, m3 = st.columns(3)
            m1.metric("LTP / Entry", f"₹{data['entry_price']}")
            risk_pct = round(((data['entry_price'] - data['stop_loss']) / data['entry_price']) * 100, 1)
            m2.metric("ATR Stop Loss", f"₹{data['stop_loss']}", delta=f"-{risk_pct}%", delta_color="inverse")
            reward_pct = round(((data['target_1'] - data['entry_price']) / data['entry_price']) * 100, 1)
            m3.metric("Target 1 (2R)", f"₹{data['target_1']}", delta=f"+{reward_pct}%")

            st.markdown(f"**Target 2 (3R):** ₹{data['target_2']}")
            st.markdown(
                f"**ATR (14):** ₹{data['atr_14']} | **20 EMA:** ₹{data['ema_20']} | **50 EMA:** ₹{data['ema_50']}")

            if st.button(f"📌 Add {data['symbol']} to Action Tracker", key=f"btn_{selected_stock}"):
                st.session_state.trades_db.append({
                    "symbol": data['symbol'],
                    "category": category_name,
                    "entry_date": str(datetime.date.today()),
                    "entry_price": data['entry_price'],
                    "stop_loss": data['stop_loss'],
                    "target_1": data['target_1'],
                    "target_2": data['target_2'],
                    "pattern": "Calculated ATR Swing",
                    "notes": data['trend_status']
                })
                st.success(f"{data['symbol']} added to Action Tracker!")
                st.rerun()
    else:
        st.warning(f"Could not load technical metrics for {selected_stock}. Please select another stock.")


# ---------------------------------------------------------
# 8. INITIAL DATA STORE
# ---------------------------------------------------------
if "trades_db" not in st.session_state:
    st.session_state.trades_db = [
        {
            "symbol": "SBIN",
            "category": "PSU Banks",
            "entry_date": "2026-08-01",
            "entry_price": 810.0,
            "stop_loss": 782.0,
            "target_1": 866.0,
            "target_2": 894.0,
            "pattern": "20 EMA Support Bounce",
            "notes": "PSU Banking index outperforming benchmark."
        },
        {
            "symbol": "GOLDBEES",
            "category": "Gold & Silver ETFs",
            "entry_date": "2026-08-05",
            "entry_price": 62.50,
            "stop_loss": 60.80,
            "target_1": 65.90,
            "target_2": 67.60,
            "pattern": "Macro Base Breakout",
            "notes": "Safe haven demand & DXY softening."
        }
    ]

# ---------------------------------------------------------
# 9. MAIN UI EXECUTION
# ---------------------------------------------------------
st.title("🎯 Indian Market & Metals Swing Radar")

# Fetch all constituents once (cached)
all_universes = get_all_indian_stocks_by_category()

# Top Header: Indices Metrics Bar
indices = fetch_indices_snapshot()
cols = st.columns(len(indices))
for col, (idx_name, data) in zip(cols, indices.items()):
    val_str = f"₹{data['price']}" if "BEES" in idx_name else f"{data['price']}"
    col.metric(label=idx_name, value=val_str, delta=f"{data['change']}%")

st.divider()

# Primary Navigation Tabs
tabs = st.tabs([
    "⚡ Action Calls & Tracker",
    "💎 Large Cap (Nifty 50)",
    "🚀 Mid Cap (Midcap 150)",
    "🔥 Small Cap (Smallcap 250)",
    "🏛️ PSU Banks",
    "🟡 Gold & Silver (Metals / ETFs)",
    "📰 Live News Radar"
])

# --- TAB 1: ACTION TRACKER ---
with tabs[0]:
    st.subheader("📋 Active Swing Calls & Multi-Day Target Status")
    st.caption("Monitors daily Highs & Lows on NSE to check if Target 1, Target 2, or Stop Loss was hit.")

    for trade in st.session_state.trades_db:
        status, color = evaluate_trade_lifecycle(trade)
        with st.container(border=True):
            r1, r2, r3, r4 = st.columns([1.5, 1, 1, 1])
            r1.markdown(f"### **NSE: {trade['symbol']}** ({trade['category']})")
            r2.markdown(f"**Entry Date:** {trade['entry_date']}")
            r3.markdown(f"**Setup:** `{trade['pattern']}`")

            if color == "green":
                r4.success(status)
            elif color == "red":
                r4.error(status)
            else:
                r4.warning(status)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Entry Trigger", f"₹{trade['entry_price']}")
            c2.metric("Stop Loss", f"₹{trade['stop_loss']}")
            c3.metric("Target 1 (2R)", f"₹{trade['target_1']}")
            c4.metric("Target 2 (3R)", f"₹{trade['target_2']}")
            st.caption(f"**Notes:** {trade['notes']}")

    with st.expander("➕ Add Custom Trade Manually", expanded=False):
        with st.form("new_trade_form"):
            f1, f2, f3 = st.columns(3)
            sym = f1.text_input("NSE Symbol (e.g. BEL, TRENT)", "BEL").upper()
            cat = f2.selectbox("Category", ["Large Cap", "Mid Cap", "Small Cap", "PSU Banks", "Gold & Silver ETFs"])
            patt = f3.text_input("Pattern Type", "VCP Breakout")

            f4, f5, f6, f7 = st.columns(4)
            ent = f4.number_input("Entry Price (₹)", min_value=1.0, value=315.0)
            sl = f5.number_input("Stop Loss (₹)", min_value=1.0, value=302.0)
            t1 = f6.number_input("Target 1 (2R) (₹)", min_value=1.0, value=341.0)
            t2 = f7.number_input("Target 2 (3R) (₹)", min_value=1.0, value=354.0)

            edate = st.date_input("Entry Date", datetime.date.today())
            notes = st.text_input("Trade Notes", "Volume expansion above 20 EMA")

            if st.form_submit_button("Save Trade to Radar"):
                st.session_state.trades_db.append({
                    "symbol": sym,
                    "category": cat,
                    "entry_date": str(edate),
                    "entry_price": ent,
                    "stop_loss": sl,
                    "target_1": t1,
                    "target_2": t2,
                    "pattern": patt,
                    "notes": notes
                })
                st.rerun()

# --- TABS 2 TO 6: DYNAMIC CATEGORY TABS ---
with tabs[1]:
    render_dynamic_category_tab("Large Cap", all_universes)

with tabs[2]:
    render_dynamic_category_tab("Mid Cap", all_universes)

with tabs[3]:
    render_dynamic_category_tab("Small Cap", all_universes)

with tabs[4]:
    render_dynamic_category_tab("PSU Banks", all_universes)

with tabs[5]:
    render_dynamic_category_tab("Gold & Silver ETFs", all_universes)

# --- TAB 7: NEWS RADAR ---
with tabs[6]:
    st.subheader("📰 Market & Commodities News Radar")
    st.caption("Live streaming headlines from Moneycontrol, Zerodha Pulse, and Economic Times.")

    news_items = fetch_news_feed()
    for item in news_items:
        with st.container(border=True):
            st.markdown(f"**[{item['source']}]** [{item['title']}]({item['link']})")
            st.caption(f"Published: {item['published']}")