import datetime

import altair as alt
import pandas as pd
import streamlit as st

# Default expense/income categories — user can add more
DEFAULT_CATEGORIES = [
    "Electric Bills",
    "Groceries",
    "Rent / Mortgage",
    "Transport",
    "Entertainment",
    "Dining Out",
    "Subscriptions",
    "Healthcare",
    "Shopping",
    "Utilities",
    "Income (Salary)",
    "Income (Other)",
]

# Page config and title
st.set_page_config(page_title="Personal Finance Tracker", page_icon="💰")
st.title("💰 Personal Finance Tracker")
st.write(
    "Track your income and expenses by category. Add new categories (e.g. Electric Bills, Rent) and log transactions below."
)

# Initialize session state: empty transactions and custom categories
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(
        columns=["Date", "Category", "Description", "Amount", "Type"]
    )

if "categories" not in st.session_state:
    st.session_state.categories = list(DEFAULT_CATEGORIES)

categories = st.session_state.categories

# ——— Add new category (section) ———
st.header("➕ Manage categories")
with st.expander("Add a new expense/income section (e.g. Electric Bills, Gym)"):
    new_cat = st.text_input("New category name", placeholder="e.g. Electric Bills, Gym, Pet Care")
    if st.button("Add category") and new_cat and new_cat.strip():
        name = new_cat.strip()
        if name not in categories:
            categories.append(name)
            st.session_state.categories = categories
            st.success(f"Added category: **{name}**")
            st.rerun()
        else:
            st.warning("That category already exists.")

# ——— Add a transaction ———
st.header("Add a transaction")

with st.form("add_transaction_form"):
    trans_date = st.date_input("Date", value=datetime.date.today())
    trans_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    trans_category = st.selectbox("Category", options=categories)
    trans_description = st.text_input("Description", placeholder="e.g. Monthly electric bill")
    trans_amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
    submitted = st.form_submit_button("Add transaction")

if submitted:
    amount = trans_amount if trans_type == "Income" else -abs(trans_amount)
    df_new = pd.DataFrame(
        [
            {
                "Date": trans_date,
                "Category": trans_category,
                "Description": trans_description or "-",
                "Amount": amount,
                "Type": trans_type,
            }
        ]
    )
    st.session_state.df = pd.concat([df_new, st.session_state.df], axis=0)
    st.success("Transaction added.")
    st.rerun()

# ——— Transactions table ———
st.header("Transactions")
st.write(f"Total entries: **{len(st.session_state.df)}**")

st.info(
    "Edit cells by double-clicking. Category must be one of your saved categories. Amount: negative = expense, positive = income.",
    icon="✍️",
)

edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=categories,
            required=True,
        ),
        "Description": st.column_config.TextColumn("Description"),
        "Amount": st.column_config.NumberColumn("Amount", format="%.2f"),
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=["Expense", "Income"],
            required=True,
        ),
    },
    disabled=[],
)

# Persist edits back to session state
st.session_state.df = edited_df

# ——— Statistics ———
st.header("Statistics")

df = st.session_state.df
total_income = df[df["Type"] == "Income"]["Amount"].sum()
total_expense = abs(df[df["Type"] == "Expense"]["Amount"].sum())
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"${total_income:,.2f}")
col2.metric("Total Expenses", f"${total_expense:,.2f}")
col3.metric("Balance", f"${balance:,.2f}", delta=f"${balance:,.2f}" if balance != 0 else None)

# Spending by category (expenses only)
st.write("")
st.write("##### Spending by category")
expenses = df[df["Type"] == "Expense"].copy()
expenses["Amount"] = expenses["Amount"].abs()
if not expenses.empty:
    by_cat = expenses.groupby("Category", as_index=False)["Amount"].sum()
    cat_plot = (
        alt.Chart(by_cat)
        .mark_bar()
        .encode(x=alt.X("Category:N", sort="-y"), y=alt.Y("Amount:Q", title="Amount ($)"))
        .properties(height=320)
    )
    st.altair_chart(cat_plot, use_container_width=True, theme="streamlit")
else:
    st.caption("No expenses to show yet.")

# Income vs Expense pie
st.write("##### Income vs Expense")
totals = pd.DataFrame(
    {"Type": ["Income", "Expense"], "Amount": [total_income, total_expense]}
)
if totals["Amount"].sum() > 0:
    pie = (
        alt.Chart(totals)
        .mark_arc()
        .encode(theta="Amount:Q", color="Type:N")
        .properties(height=300)
        .configure_legend(orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5)
    )
    st.altair_chart(pie, use_container_width=True, theme="streamlit")
else:
    st.caption("Add some transactions to see the chart.")
