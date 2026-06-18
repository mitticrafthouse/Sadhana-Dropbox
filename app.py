import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# =====================
# CONFIG
# =====================
MIN_BALANCE = 500

INDICES = {
    "NIFTY": {"lot": 75, "step": 50},
    "BANKNIFTY": {"lot": 15, "step": 100},
    "FINNIFTY": {"lot": 40, "step": 50},
    "SENSEX": {"lot": 10, "step": 100}
}

# =====================
# LOGIN
# =====================
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


# =====================
# WALLET (Replace with Dhan API)
# =====================
def get_wallet_balance():
    return 12000  # Replace with real Dhan API


def check_auto_mode():
    bal = get_wallet_balance()
    return (bal >= MIN_BALANCE), bal


# =====================
# TELEGRAM
# =====================
BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass


# =====================
# MOCK LIVE DATA (Replace with NSE API)
# =====================
def get_live_data():
    return pd.DataFrame({
        "close": np.random.randint(100, 200, 200),
        "volume": np.random.randint(1000, 5000, 200)
    })


# =====================
# INDICATORS
# =====================
def add_indicators(df):
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
    return df


# =====================
# SIGNAL
# =====================
def get_signal(df):
    df = add_indicators(df)
    row = df.iloc[-1]

    if row['ema9'] > row['ema21'] and row['close'] > row['vwap']:
        return "BUY CE"
    elif row['ema9'] < row['ema21'] and row['close'] < row['vwap']:
        return "BUY PE"

    return None


# =====================
# RISK + POSITION SIZE
# =====================
def position_size(index, sl_points=12):
    capital = get_wallet_balance()
    risk = capital * 0.01

    lot = INDICES[index]["lot"]
    qty = int(risk / sl_points)

    return max(lot, (qty // lot) * lot)


def levels(entry):
    return entry + 45, entry - 12


# =====================
# TRAILING SL
# =====================
def trailing_sl(entry, price, sl):
    if price - entry >= 15:
        return entry
    if price - entry >= 25:
        return entry + 10
    if price - entry >= 35:
        return entry + 20
    return sl


# =====================
# BACKTEST
# =====================
def backtest(df):
    df = add_indicators(df)
    trades = []

    for i in range(20, len(df)):
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


# =====================
# UI START
# =====================
st.set_page_config(layout="wide")

if not login():
    st.stop()

st.title("📈 Options Algo Dashboard")

# =====================
# WALLET STATUS
# =====================
auto_mode, balance = check_auto_mode()

st.sidebar.subheader("💰 Wallet")
st.sidebar.write(f"₹{balance}")

mode = st.sidebar.radio("Mode", ["AUTO", "MANUAL"])

if not auto_mode:
    st.error("⚠️ Balance < ₹500 → AUTO DISABLED")
    mode = "MANUAL"

# =====================
# INDEX
# =====================
index = st.selectbox("Select Index", list(INDICES.keys()))

# =====================
# DATA
# =====================
data_mode = st.radio("Data Mode", ["Live", "Upload CSV"])

if data_mode == "Live":
    df = get_live_data()
else:
    file = st.file_uploader("Upload CSV")
    if file:
        df = pd.read_csv(file)
    else:
        df = None

# =====================
# SIGNAL
# =====================
if df is not None:

    st.subheader("📊 Market Snapshot")
    st.dataframe(df.tail())

    signal = get_signal(df)

    if signal:
        entry = df.iloc[-1]['close']
        target, sl = levels(entry)
        qty = position_size(index)

        st.markdown(f"""
        <div style='background:#111;padding:20px;border-radius:10px;color:white'>
        <h2>⚡ {signal} - {index}</h2>
        Entry: ₹{entry} <br>
        Target: ₹{target} <br>
        SL: ₹{sl} <br>
        Qty: {qty}
        </div>
        """, unsafe_allow_html=True)

        # Telegram
        send_telegram(f"{index} {signal} @ {entry} | T:{target} SL:{sl}")

        # AUTO EXECUTION
        if mode == "AUTO" and auto_mode:
            st.success("✅ Order sent to Dhan (Simulated)")
        else:
            st.info("👁 Manual Mode")

        # Trailing SL Demo
        current = entry + np.random.randint(-5, 50)
        new_sl = trailing_sl(entry, current, sl)
        st.write(f"📉 Trailing SL: {new_sl}")

    else:
        st.info("No Signal")

# =====================
# BACKTEST
# =====================
st.subheader("📊 Backtesting")

if df is not None and st.button("Run Backtest"):
    trades = backtest(df)

    if trades:
        pnl = sum(trades)
        win = len([t for t in trades if t > 0]) / len(trades)

        st.write(f"Trades: {len(trades)}")
        st.write(f"Win Rate: {round(win*100,2)}%")
        st.write(f"P&L: {pnl}")

        cum = np.cumsum(trades)
        fig, ax = plt.subplots()
        ax.plot(cum)
        ax.set_title("Equity Curve")
        st.pyplot(fig)
