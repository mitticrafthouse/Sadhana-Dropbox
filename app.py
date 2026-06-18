import streamlit as st
import pandas as pd
import numpy as np
import requests

# =========================
# CONFIG
# =========================
MIN_BALANCE = 500

INDICES = {
    "NIFTY": {"lot": 65, "step": 50},
    "BANKNIFTY": {"lot": 15, "step": 100},
    "FINNIFTY": {"lot": 40, "step": 50},
    "SENSEX": {"lot": 20, "step": 100}
}

# =========================
# LOAD SECRETS (Dhan API)
# =========================
CLIENT_ID = st.secrets.get("CLIENT_ID", "")
ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN", "")

# =========================
# LOGIN
# =========================
USERS = {"admin": "admin123"}

def login():
    st.sidebar.title("🔐 Login")
    user = st.sidebar.text_input("Username")
    pwd = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if USERS.get(user) == pwd:
            st.session_state["logged"] = True
        else:
            st.error("Invalid login")

    return st.session_state.get("logged", False)


# =========================
# DHAN WALLET BALANCE
# =========================
def get_wallet_balance():
    try:
        from dhanhq import dhanhq
        client = dhanhq(CLIENT_ID, ACCESS_TOKEN)

        data = client.get_fund_limits()
        balance = data["data"].get("availabelBalance", 0)

        return balance

    except Exception:
        return 0


# =========================
# AUTO MODE CHECK
# =========================
def check_auto_mode():
    bal = get_wallet_balance()
    return bal >= MIN_BALANCE, bal


# =========================
# SAFE PRICE FETCH (Fallback)
# =========================
def get_spot_price(index):
    try:
