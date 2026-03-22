# app.py
# Streamlit version of Travel Expense Tracker
# For group trip with friends - equal split + transfers/borrows

import streamlit as st
import pandas as pd
import json
from io import StringIO, BytesIO

# ────────────────────────────────────────────────
# DATA & PARTICIPANTS (fixed as requested)
# ────────────────────────────────────────────────
PARTICIPANTS = ["Rachel", "Cady", "Justin", "Plastic", "Jovan", "Evan", "Clayton"]

if "expenses" not in st.session_state:
    st.session_state.expenses = []          # [{"payer": str, "amount": float, "desc": str}]
if "transfers" not in st.session_state:
    st.session_state.transfers = []         # [{"lender": str, "borrower": str, "amount": float, "desc": str}]
if "currency" not in st.session_state:
    st.session_state.currency = "RM"

# ────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────
def get_symbol():
    return st.session_state.currency + " "

def total_expenses():
    return sum(e["amount"] for e in st.session_state.expenses)

def get_paid_dict():
    paid = {p: 0.0 for p in PARTICIPANTS}
    for e in st.session_state.expenses:
        amt = e["amount"]
        if e["payer"] == "All":
            share = amt / len(PARTICIPANTS)
            for p in PARTICIPANTS:
                paid[p] += share
        else:
            paid[e["payer"]] += amt
    return paid

def get_adjustment_dict():
    adj = {p: 0.0 for p in PARTICIPANTS}
    for t in st.session_state.transfers:
        adj[t["lender"]]   += t["amount"]
        adj[t["borrower"]] -= t["amount"]
    return adj

def get_balances():
    total = total_expenses()
    share = total / len(PARTICIPANTS) if PARTICIPANTS else 0.0
    paid = get_paid_dict()
    adj  = get_adjustment_dict()
    return {p: paid.get(p, 0.0) + adj.get(p, 0.0) - share for p in PARTICIPANTS}

def calculate_minimal_transfers():
    balances = get_balances()
    # Positive = owed money (creditor), Negative = owes money (debtor)
    creditors = [(name, amt) for name, amt in balances.items() if amt > 0.01]
    debtors   = [(name, -amt) for name, amt in balances.items() if amt < -0.01]
    
    creditors.sort(key=lambda x: x[1], reverse=True)  # largest creditor first
    debtors.sort(key=lambda x: x[1], reverse=True)     # largest debtor first
    
    transactions = []
    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        c_name, c_amt = creditors[ci]
        d_name, d_amt = debtors[di]
        if c_amt <= 0 or d_amt <= 0:
            break
        pay = min(c_amt, d_amt)
        transactions.append(f"{d_name} → {c_name}   {get_symbol()}{pay:,.2f}")
        creditors[ci] = (c_name, c_amt - pay)
        debtors[di]   = (d_name, d_amt - pay)
        if creditors[ci][1] < 0.01: ci += 1
        if debtors[di][1]   < 0.01: di += 1
    
    return transactions

# ────────────────────────────────────────────────
# SAVE / LOAD
# ────────────────────────────────────────────────
def get_data_json():
    data = {
        "expenses": st.session_state.expenses,
        "transfers": st.session_state.transfers,
        "currency": st.session_state.currency
    }
    return json.dumps(data, indent=2)

def load_from_json(json_str):
    try:
        data = json.loads(json_str)
        st.session_state.expenses = data.get("expenses", [])
        st.session_state.transfers = data.get("transfers", [])
        st.session_state.currency = data.get("currency", "RM")
        st.success("Data loaded successfully!")
    except Exception as e:
        st.error(f"Failed to load: {e}")

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="Travel Expense Tracker", layout="wide")

st.title("✈️ Travel Expense Tracker")
st.caption("Group trip splitting – equal shares + borrows/transfers")

# Currency selector (top right)
col_currency = st.columns([6,1])[1]
with col_currency:
    curr = st.selectbox("Currency", ["RM", "HKD"], index=0 if st.session_state.currency == "RM" else 1,
                        label_visibility="collapsed")
    if curr != st.session_state.currency:
        st.session_state.currency = curr
        st.rerun()

tab_exp, tab_trans, tab_sum, tab_settle, tab_data = st.tabs([
    "Add Expense", "Add Transfer", "Summary", "Settle Up", "Data"
])

# ── TAB: Add Expense ────────────────────────────────────────
with tab_exp:
    st.subheader("Record a shared expense")
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        payer = st.selectbox("Who paid?", ["All"] + PARTICIPANTS)
    with col2:
        amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
    with col3:
        desc = st.text_input("Description (optional)")

    if st.button("Add Expense", type="primary"):
        if amount > 0 and payer:
            st.session_state.expenses.append({
                "payer": payer,
                "amount": amount,
                "desc": desc.strip() or "—"
            })
            st.success(f"Added {get_symbol()}{amount:,.2f}")
            st.rerun()
        else:
            st.error("Please enter amount > 0 and select payer")

    if st.session_state.expenses:
        df_exp = pd.DataFrame(st.session_state.expenses)
        df_exp["amount"] = df_exp["amount"].apply(lambda x: f"{get_symbol()}{x:,.2f}")
        st.dataframe(df_exp[["payer", "amount", "desc"]], use_container_width=True, hide_index=True)

# ── TAB: Add Transfer ───────────────────────────────────────
with tab_trans:
    st.subheader("Record borrow / lend / transfer")
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        lender = st.selectbox("Lender (who gave money)", PARTICIPANTS, key="lender")
    with col2:
        borrower = st.selectbox("Borrower (who received)", PARTICIPANTS, key="borrower")
    with col3:
        t_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="t_amt")
        t_desc = st.text_input("Note (optional)", key="t_desc")

    if st.button("Add Transfer", type="primary"):
        if t_amount > 0 and lender and borrower and lender != borrower:
            st.session_state.transfers.append({
                "lender": lender,
                "borrower": borrower,
                "amount": t_amount,
                "desc": t_desc.strip() or "—"
            })
            st.success(f"Recorded {get_symbol()}{t_amount:,.2f}")
            st.rerun()
        else:
            st.error("Invalid: amount > 0, lender ≠ borrower")

    if st.session_state.transfers:
        df_t = pd.DataFrame(st.session_state.transfers)
        df_t["amount"] = df_t["amount"].apply(lambda x: f"{get_symbol()}{x:,.2f}")
        st.dataframe(df_t[["lender", "borrower", "amount", "desc"]], use_container_width=True, hide_index=True)

# ── TAB: Summary ────────────────────────────────────────────
with tab_sum:
    st.subheader("Live Balances")
    if not st.session_state.expenses and not st.session_state.transfers:
        st.info("No data yet. Add expenses or transfers above.")
    else:
        balances = get_balances()
        total = total_expenses()
        share = total / len(PARTICIPANTS) if PARTICIPANTS else 0.0
        paid_d = get_paid_dict()
        adj_d = get_adjustment_dict()

        data = []
        for p in PARTICIPANTS:
            data.append({
                "Name": p,
                "Paid": paid_d.get(p, 0.0),
                "Adj": adj_d.get(p, 0.0),
                "Should Pay": share,
                "Balance": balances[p]
            })
        df = pd.DataFrame(data)
        df_styled = df.style.format({
            "Paid": f"{get_symbol()}{{:,.2f}}",
            "Adj": f"{get_symbol()}{{:,.2f}}",
            "Should Pay": f"{get_symbol()}{{:,.2f}}",
            "Balance": lambda x: f"**{get_symbol()}{x:,.2f}**" if x >= 0 else f"{get_symbol()}{x:,.2f}"
        }).apply(lambda row: ['background: #e6ffe6' if row["Balance"] > 0 else
                              'background: #ffe6e6' if row["Balance"] < 0 else '' for _ in row], axis=1)

        st.dataframe(df_styled, use_container_width=True, hide_index=True)

# ── TAB: Settle Up ──────────────────────────────────────────
with tab_settle:
    st.subheader("How to settle (minimal transfers)")
    trans = calculate_minimal_transfers()
    if not trans:
        st.success("Everyone is settled! ✓ No transfers needed.")
    else:
        for line in trans:
            st.markdown(f"**{line}**")

# ── TAB: Data ───────────────────────────────────────────────
with tab_data:
    st.subheader("Save / Load Data")
    st.download_button(
        label="Download current data (JSON)",
        data=get_data_json(),
        file_name="trip_expenses.json",
        mime="application/json"
    )

    st.write("Or upload saved JSON:")
    uploaded = st.file_uploader("Upload JSON file", type=["json"])
    if uploaded:
        try:
            json_str = uploaded.read().decode("utf-8")
            load_from_json(json_str)
            st.rerun()
        except:
            st.error("Invalid file format.")

    if st.button("Clear ALL data", type="primary"):
        if st.button("Really clear everything? (cannot undo)", type="primary"):
            st.session_state.expenses = []
            st.session_state.transfers = []
            st.session_state.currency = "RM"
            st.success("All data cleared.")
            st.rerun()

st.markdown("---")
st.caption("Made for your group trip • Equal split + manual transfers • RM / HKD")
