import pandas as pd
import requests
import io
import streamlit as st


@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_all_indian_stocks_by_category():
    """
    Fetches official constituent CSVs directly from NiftyIndices / NSE archives.
    Returns clean lists of NSE ticker symbols for each cap and sector.
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
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                df = pd.read_csv(io.StringIO(resp.text))
                # The symbol column in official files is 'Symbol'
                if "Symbol" in df.columns:
                    universes[category] = df["Symbol"].dropna().str.strip().tolist()
                else:
                    universes[category] = []
            else:
                universes[category] = []
        except Exception:
            universes[category] = []

    # Add ETFs & Commodities manually
    universes["Gold & Silver ETFs"] = [
        "GOLDBEES", "SILVERBEES", "HDFCGOLD", "SETFGOLD", "AXISGOLD", "ICICIGOLD", "KOTAKGOLD"
    ]

    # Fallback lists if offline or blocked
    fallbacks = {
        "Large Cap": ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "INFY", "ITC", "LT", "TRENT", "M&M"],
        "Mid Cap": ["DIXON", "POLYCAB", "PERSISTENT", "COFORGE", "FEDERALBNK", "VOLTAS", "CUMMINSIND", "ASTRAL"],
        "Small Cap": ["KAYNES", "CDSL", "BSOFT", "KPITTECH", "ANGELONE", "CYIENT", "CAMS", "RADICO"],
        "PSU Banks": ["SBIN", "CANBK", "BANKBARODA", "PNB", "UNIONBANK", "INDIANB"]
    }

    for k, v in fallbacks.items():
        if not universes.get(k):
            universes[k] = v

    return universes