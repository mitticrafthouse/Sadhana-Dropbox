import streamlit as st
import pandas as pd
import numpy as np
import requests

# ==============================
# CONFIG
# ==============================
MIN_BALANCE = 500

INDICES = {
    "NIFTY": {"lot": 75, "step": 50},
    "BANKNIFTY": {"lot": 15, "step": 100},
    "FINNIFTY": {"lot": 40, "step": 50},
    "SENSEX": {"lot": 10, "step": 100}
}

# ==============================
# LOGIN SYSTEM
# ==============================
USERS = {"admin": "admin123"}

def login():
    st.sidebar.title("🔐 Login")
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if USERS.get(user) == pwd:
            st.session_state.logged_in = True
        else:
            st.error("Invalid login")

    return st.session_state.get("logged_in", False)


# ==============================
# DHAN WALLET (Mock / Replace API)
# ==============================
def get_wallet_balance():
    try:
        # ✅ Replace with real Dhan API
        # Example:
        # from dhanhq import dhanhq
        # client = dhanhq("CLIENT_ID","ACCESS_TOKEN")
        # funds = client.get_fund_limits()
        # return funds['data']['availabelBalance']

        return 12000  # mock value (for deploy)
    except:
        return 0


# ==============================
# AUTO MODE CHECK
# ==============================
def check_auto_mode():
    bal = get_wallet_balance()
    if bal < MIN_BALANCE:
        return False, bal
    return True, bal


# ==============================
# INDICATORS
# ==============================
def calculate_indicators(df):
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
    return df


# ==============================
# SIGNAL LOGIC
# ==============================
def generate_signal(df):
    df = calculate_indicators(df)

    latest = df.iloc[-1]

    if latest['ema9'] > latest['ema21'] and latest['close'] > latest['vwap']:
        return "BUY CE"
    elif latest['ema9'] < latest['ema21'] and latest['close'] < latest['vwap']:
        return "BUY PE"

    return None


# ==============================
# RISK MANAGEMENT
# ==============================
def position_size(index, sl_points):
    capital = get_wallet_balance()
    risk_amt = capital * 0.01

    lot_size = INDICES[index]["lot"]

    qty = int(risk_amt / sl_points)
    lots = max(1, qty // lot_size)

    return lots * lot_size


def trade_levels(entry):
    return entry + 45, entry - 12


# ==============================
# BACKTEST ENGINE
# ==============================
def run_backtest(df):
    df = calculate_indicators(df)

    trades = []

    for i in range(21, len(df)):
        row = df.iloc[i]

        if row['ema9'] > row['ema21'] and row['close'] > row['vwap']:
            entry = row['close']
            target = entry + 45
            sl = entry - 12

            for j in range(i+1, len(df)):
                price = df.iloc[j]['close']

                if price >= target:
                    trades.append(45)
                    break
                elif price <= sl:
                    trades.append(-12)
                    break

    return trades


# ==============================
# UI START
# ==============================
st.set_page_config(page_title="Options Algo", layout="wide")

if not login():
    st.stop()

st.title("📈 Options Algo Trading Dashboard")

# ==============================
# WALLET DISPLAY
# ==============================
auto_mode, balance = check_auto_mode()

st.sidebar.subheader("💰 Wallet Balance")
st.sidebar.write(f"₹{balance}")

if not auto_mode:
    st.warning("⚠️ Low Balance! Auto Mode Disabled")

    st.markdown("""
    <div style='background-color:#ff4b4b;padding:15px;border-radius:10px;color:white'>
        ❌ AUTO MODE DISABLED<br>
        Balance below ₹500<br>
        Please add funds
    </div>
    """, unsafe_allow_html=True)

else:
    st.success("✅ AUTO MODE ACTIVE")


# ==============================
# INDEX SELECT
# ==============================
index = st.selectbox(
    "Select Index",
    ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX"]
)

# ==============================
# FILE UPLOAD
# ==============================
file = st.file_uploader("Upload OHLC CSV")

if file:
    df = pd.read_csv(file)

    st.subheader("📊 Market Data")
    st.dataframe(df.tail())

    signal = generate_signal(df)

    st.subheader("📡 LIVE SIGNAL")

    if signal:
        entry = df.iloc[-1]['close']
        target, sl = trade_levels(entry)
        qty = position_size(index, 12)

        st.success(f"{signal} @ {entry}")
        st.write(f"🎯 Target: {target}")
        st.write(f"🛑 SL: {sl}")
        st.write(f"📦 Quantity: {qty}")

        # AUTO / MANUAL info
        if auto_mode:
            st.info("🤖 Executing in AUTO mode (Dhan API)")
        else:
            st.info("👁 Manual Trade Mode")

    else:
        st.info("No Signal")

# ==============================
# BACKTEST
# ==============================
st.subheader("📊 Backtesting")

if file and st.button("Run Backtest"):
    trades = run_backtest(df)

    if trades:
        pnl = sum(trades)
        win_rate = len([t for t in trades if t > 0]) / len(trades)

        st.write(f"Total Trades: {len(trades)}")
        st.write(f"Win Rate: {round(win_rate*100,2)}%")
        st.write(f"Net P&L (points): {pnl}")

    else:
        st.warning("No trades found")

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.caption("🚀 EMA + VWAP Options Scalper (Auto + Risk Managed)")