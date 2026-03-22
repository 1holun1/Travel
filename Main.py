import streamlit as st
import uuid
import json

# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Travel Expense Splitter",
    page_icon="🧳",
    layout="wide"
)

st.title("🧳 Travel Expense Splitter")
st.caption("Record expenses, borrowings & auto-calculate who owes whom • Default RM, HKD supported")

# ====================== SIDEBAR ======================
st.sidebar.header("Settings")

# Currency
currency = st.sidebar.selectbox(
    "Currency",
    options=["RM", "HKD"],
    key="currency"
)
symbol = "RM" if currency == "RM" else "HK$"

# Data Management
st.sidebar.subheader("Data Management")

if st.sidebar.button("🔄 Reset All Data"):
    st.session_state.participants = ["Rachel", "Cady", "Justin", "Plastic", "Jovan", "Evan", "Clayton"]
    st.session_state.expenses = []
    st.session_state.transfers = []
    st.rerun()

if st.sidebar.button("🛠️ Repair Invalid Data"):
    # Remove any corrupted expenses
    st.session_state.expenses = [
        e for e in st.session_state.expenses
        if isinstance(e, dict) and all(k in e for k in ["id", "payer", "amount", "description", "split_with"])
    ]
    # Remove any corrupted transfers
    st.session_state.transfers = [
        t for t in st.session_state.transfers
        if isinstance(t, dict) and all(k in t for k in ["id", "from_person", "to_person", "amount", "description"])
    ]
    st.success("✅ Data repaired! All bad records removed.")
    st.rerun()

# Download backup
if "participants" in st.session_state:
    backup_data = {
        "participants": st.session_state.participants,
        "expenses": st.session_state.expenses,
        "transfers": st.session_state.transfers,
        "currency": currency
    }
    st.sidebar.download_button(
        label="📥 Download Backup (JSON)",
        data=json.dumps(backup_data, indent=2),
        file_name="trip_expenses_backup.json",
        mime="application/json"
    )

# Upload backup
uploaded = st.sidebar.file_uploader("📤 Upload Backup", type=["json"])
if uploaded:
    try:
        data = json.load(uploaded)
        st.session_state.participants = data.get("participants", ["Rachel", "Cady", "Justin", "Plastic", "Jovan", "Evan", "Clayton"])
        st.session_state.expenses = data.get("expenses", [])
        st.session_state.transfers = data.get("transfers", [])
        st.session_state.currency = data.get("currency", "RM")
        st.success("✅ Backup loaded!")
        st.rerun()
    except Exception as e:
        st.error(f"Invalid backup file: {e}")

# ====================== INITIALISE SESSION STATE ======================
if "participants" not in st.session_state:
    st.session_state.participants = ["Rachel", "Cady", "Justin", "Plastic", "Jovan", "Evan", "Clayton"]
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "transfers" not in st.session_state:
    st.session_state.transfers = []

participants = st.session_state.participants

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 Participants",
    "💰 Add Expense",
    "🔄 Add Transfer",
    "📋 View All",
    "📊 Results & Settlements"
])

# ====================== TAB 1: PARTICIPANTS ======================
with tab1:
    st.header("Participants")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_name = st.text_input("Add new friend", placeholder="e.g. Alex")
    with col2:
        if st.button("Add", type="primary") and new_name.strip():
            new_name = new_name.strip()
            if new_name not in participants:
                st.session_state.participants.append(new_name)
                st.rerun()
            else:
                st.warning("Already exists")

    st.subheader("Current participants")
    to_remove = st.multiselect("Select to remove", participants)
    if st.button("Remove Selected") and to_remove:
        for name in to_remove:
            if name in st.session_state.participants:
                st.session_state.participants.remove(name)
        st.rerun()

    st.write(", ".join(participants))

# ====================== TAB 2: ADD EXPENSE ======================
with tab2:
    st.header("Add New Expense")
    payer = st.selectbox("Who paid?", participants)
    amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
    description = st.text_input("Description", placeholder="e.g. Dinner at KLCC")

    split_type = st.radio("Split with", ["All participants", "Select specific people"])
    if split_type == "All participants":
        split_with = participants[:]
    else:
        split_with = st.multiselect("Who shares this expense?", participants, default=[payer])

    if st.button("✅ Add Expense", type="primary"):
        if amount > 0 and description.strip() and split_with:
            expense = {
                "id": str(uuid.uuid4()),
                "payer": payer,
                "amount": round(amount, 2),
                "description": description.strip(),
                "split_with": split_with
            }
            st.session_state.expenses.append(expense)
            st.success(f"Added: {description}")
            st.rerun()
        else:
            st.error("Please fill all fields")

# ====================== TAB 3: ADD TRANSFER ======================
with tab3:
    st.header("Add Money Transfer / Borrowing")
    st.caption("Example: You borrowed RM500 from Jovan → From: Jovan, To: Clayton")

    col_from, col_to = st.columns(2)
    with col_from:
        from_person = st.selectbox("From (lender / giver)", participants, key="from_trans")
    with col_to:
        to_person = st.selectbox("To (borrower / receiver)", participants, key="to_trans")

    trans_amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key="trans_amt")
    trans_desc = st.text_input("Description", placeholder="e.g. Borrowed for taxi", key="trans_desc")

    if st.button("✅ Add Transfer", type="primary"):
        if from_person != to_person and trans_amount > 0 and trans_desc.strip():
            transfer = {
                "id": str(uuid.uuid4()),
                "from_person": from_person,
                "to_person": to_person,
                "amount": round(trans_amount, 2),
                "description": trans_desc.strip()
            }
            st.session_state.transfers.append(transfer)
            st.success(f"Transfer recorded: {from_person} → {to_person}")
            st.rerun()
        else:
            st.error("From and To must be different")

# ====================== TAB 4: VIEW ALL ======================
with tab4:
    st.header("All Transactions")

    st.subheader("Expenses")
    if not st.session_state.expenses:
        st.info("No expenses yet")
    else:
        for exp in st.session_state.expenses:
            col_a, col_b, col_c = st.columns([5, 1, 1])
            with col_a:
                st.write(f"**{exp.get('description', 'No description')}**")
                st.write(f"Paid by **{exp.get('payer', 'Unknown')}** • {symbol} {exp.get('amount', 0):.2f}")
                st.write(f"Split with: {', '.join(exp.get('split_with', []))}")
            with col_b:
                st.caption(exp.get('id', '')[:8])
            with col_c:
                if st.button("🗑️", key=f"del_exp_{exp.get('id', '')}"):
                    st.session_state.expenses = [e for e in st.session_state.expenses if e.get('id') != exp.get('id')]
                    st.rerun()

    st.divider()

    st.subheader("Transfers / Loans")
    if not st.session_state.transfers:
        st.info("No transfers yet")
    else:
        for trans in st.session_state.transfers:
            col_a, col_b, col_c = st.columns([5, 1, 1])
            with col_a:
                st.write(f"**{trans.get('from_person', 'Unknown')}** → **{trans.get('to_person', 'Unknown')}**")
                st.write(f"{symbol} {trans.get('amount', 0):.2f} • {trans.get('description', 'No description')}")
            with col_b:
                st.caption(trans.get('id', '')[:8])
            with col_c:
                if st.button("🗑️", key=f"del_trans_{trans.get('id', '')}"):
                    st.session_state.transfers = [t for t in st.session_state.transfers if t.get('id') != trans.get('id')]
                    st.rerun()

# ====================== TAB 5: RESULTS & SETTLEMENTS ======================
with tab5:
    st.header("Results & Final Settlements")

    if len(participants) < 2:
        st.error("Add at least 2 participants")
        st.stop()

    # === CALCULATIONS (safe version) ===
    paid = {p: 0.0 for p in participants}
    owed = {p: 0.0 for p in participants}

    for exp in st.session_state.expenses:
        if isinstance(exp, dict):
            payer = exp.get("payer")
            amount = exp.get("amount", 0)
            split_with = exp.get("split_with", [])
            if payer and amount > 0:
                paid[payer] += amount
                if split_with:
                    share = amount / len(split_with)
                    for person in split_with:
                        if person in owed:
                            owed[person] += share

    net = {p: round(paid[p] - owed[p], 2) for p in participants}

    # Apply transfers
    for trans in st.session_state.transfers:
        if isinstance(trans, dict):
            frm = trans.get("from_person")
            to = trans.get("to_person")
            amt = trans.get("amount", 0)
            if frm in net:
                net[frm] = round(net[frm] + amt, 2)
            if to in net:
                net[to] = round(net[to] - amt, 2)

    st.metric("Total Trip Expenses", f"{symbol} {sum(e.get('amount', 0) for e in st.session_state.expenses):.2f}")

    st.subheader("Individual Balances")
    for p in participants:
        bal = net[p]
        if bal > 0:
            st.success(f"**{p}** should **receive** {symbol} {bal:.2f}")
        elif bal < 0:
            st.error(f"**{p}** should **pay** {symbol} {-bal:.2f}")
        else:
            st.info(f"**{p}** is settled")

    # ====================== MINIMAL SETTLEMENTS ======================
    st.subheader("💸 Suggested Minimal Transfers")
    creditors = [p for p in participants if net[p] > 0.01]
    debtors = [p for p in participants if net[p] < -0.01]

    creditors.sort(key=lambda p: net[p], reverse=True)
    debtors.sort(key=lambda p: net[p])

    balances = net.copy()
    settlements = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        deb = debtors[i]
        cred = creditors[j]
        amt = min(-balances[deb], balances[cred])
        if amt > 0.01:
            settlements.append((deb, cred, round(amt, 2)))
            balances[deb] += amt
            balances[cred] -= amt
        if abs(balances[deb]) < 0.01:
            i += 1
        if abs(balances[cred]) < 0.01:
            j += 1

    if settlements:
        for deb, cred, amt in settlements:
            st.write(f"🔹 **{deb}** pays **{cred}** → {symbol} {amt:.2f}")
        st.caption("This is the smallest number of transfers needed")
    else:
        st.success("🎉 Everyone is already settled! No transfers required.")

    st.caption("All calculations include expenses + borrowings. Currency: " + currency)
