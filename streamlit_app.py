import datetime

import altair as alt
import pandas as pd
import streamlit as st

# Default categories — expense and income separate so the form shows the right list
DEFAULT_EXPENSE_CATEGORIES = [
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
]
DEFAULT_INCOME_CATEGORIES = [
    "Salary",
    "Other",
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

if "expense_categories" not in st.session_state:
    st.session_state.expense_categories = list(DEFAULT_EXPENSE_CATEGORIES)
if "income_categories" not in st.session_state:
    st.session_state.income_categories = list(DEFAULT_INCOME_CATEGORIES)

expense_categories = st.session_state.expense_categories
income_categories = st.session_state.income_categories
all_categories = expense_categories + income_categories

# ——— Add new category (section) ———
st.header("➕ Manage categories")
with st.expander("Add a new expense or income category (e.g. Electric Bills, Gym)"):
    cat_type = st.radio("Category for", ["Expense", "Income"], horizontal=True)
    new_cat = st.text_input("New category name", placeholder="e.g. Electric Bills, Gym, Pet Care")
    if st.button("Add category") and new_cat and new_cat.strip():
        name = new_cat.strip()
        target = st.session_state.expense_categories if cat_type == "Expense" else st.session_state.income_categories
        if name not in target:
            target.append(name)
            if cat_type == "Expense":
                st.session_state.expense_categories = target
            else:
                st.session_state.income_categories = target
            st.success(f"Added **{name}** to {cat_type} categories.")
            st.rerun()
        else:
            st.warning("That category already exists.")

# ——— Add a transaction ———
st.header("Add a transaction")

# Type and Category outside the form so changing Type updates Category options (form doesn't rerun until submit)
trans_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
trans_category = st.selectbox(
    "Category",
    options=expense_categories if trans_type == "Expense" else income_categories,
    key="add_trans_category",
)

with st.form("add_transaction_form"):
    trans_date = st.date_input("Date", value=datetime.date.today())
    trans_description = st.text_input("Description", placeholder="e.g. Monthly electric bill" if trans_type == "Expense" else "e.g. Monthly salary")
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
    "Edit cells by double-clicking. Use the section below to delete a transaction.",
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
            options=all_categories,
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
st.session_state.df = edited_df

# ——— Delete a transaction (button, not checkbox) ———
st.subheader("Delete a transaction")
df = st.session_state.df
if len(df) > 0:
    def format_transaction(i):
        row = df.iloc[i]
        desc = str(row["Description"])[:40] if pd.notna(row["Description"]) else ""
        return f"{row['Date']} | {row['Category']} | {desc} | ₱{row['Amount']:,.2f}"

    delete_index = st.selectbox(
        "Select transaction to delete",
        options=range(len(df)),
        format_func=format_transaction,
        key="delete_select",
    )
    if st.button("Delete", type="primary"):
        st.session_state.df = df.drop(df.index[delete_index]).reset_index(drop=True)
        st.success("Transaction deleted.")
        st.rerun()
else:
    st.caption("No transactions to delete.")

# ——— Statistics ———
st.header("Statistics")

df = st.session_state.df
total_income = df[df["Type"] == "Income"]["Amount"].sum()
total_expense = abs(df[df["Type"] == "Expense"]["Amount"].sum())
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₱{total_income:,.2f}")
col2.metric("Total Expenses", f"₱{total_expense:,.2f}")
col3.metric("Balance", f"₱{balance:,.2f}", delta=f"₱{balance:,.2f}" if balance != 0 else None)

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
        .encode(x=alt.X("Category:N", sort="-y"), y=alt.Y("Amount:Q", title="Amount (₱)"))
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

