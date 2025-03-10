import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import calendar
from datetime import datetime
import re
from pypdf import PdfReader

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# Financial fields
FIELDS = [
    "Sales", "Direct Costs", "Gross Profit", "Expenses", "Net Profit",
    "Butter & Cheese", "Beverages", "Bread & Rolls", "Chicken", "Chips",
    "Hot Beverages", "Dairy", "Desserts", "Fish", "Fruit & Veg",
    "Meat", "Ice Cream", "Ribs", "Mushrooms", "Oil", "Advertising Promo",
    "Clean & Pest Control", "Delivery Expenses", "Franchise Fees", "Utilities & Energy",
    "Staff Uniforms", "Repairs & Maintenance", "Water", "Packaging", "Staff Transport",
    "Salaries - Managers", "FOH Wages", "BOH & Childminders"
]

DATA_FILE = "restaurant_finances.csv"

# Month selection helper
def select_statement_month(label="Select Statement Month"):
    current_year = datetime.today().year
    years = list(range(2000, current_year + 1))
    month_names = list(calendar.month_name)[1:]
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox(f"{label} - Year", years, index=years.index(current_year))
    with col2:
        month_name = st.selectbox(f"{label} - Month", month_names, index=datetime.today().month - 1)
    month_index = month_names.index(month_name) + 1
    return f"{year}-{month_index:02d}"

# Login page
def login_page():
    with st.form("auth"):
        st.title("🍽 Restaurant Analytics")
        st.subheader("🔒 Financial Portal")
        user = st.text_input("👤 Username")
        pwd = st.text_input("🔑 Password", type="password")
        if st.form_submit_button("🚪 Login"):
            if user == "Silver" and pwd == "Silver@123":
                st.session_state.authenticated = True
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password.")

# PDF parsing
def parse_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages)
        amounts = {}
        
        patterns = {
            "Sales": r"Sales\s+([\d,]+\.\d{2})",
            "Direct Costs": r"Direct Costs\s+([\d,]+\.\d{2})",
            "Gross Profit": r"Gross Profit\s+([\d,]+\.\d{2})",
            "Expenses": r"Expenses\s+([\d,]+\.\d{2})",
            "Net Profit": r"Net Profit\s+(-?[\d,]+\.\d{2})"
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                amounts[field] = float(match.group(1).replace(',', ''))
        
        # Feedback
        extracted = len(amounts)
        total = len(FIELDS)
        st.info(f"Extracted {extracted}/{total} fields.")
        missing = [f for f in FIELDS if f not in amounts]
        if missing:
            st.warning(f"Missing: {', '.join(missing[:5])}" + ("..." if len(missing) > 5 else ""))
        
        return amounts
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return {}

# Alerts
def send_alerts(df):
    st.header("🔔 Alerts")
    threshold = st.number_input("Net Profit Threshold", value=0.0, step=1000.0)
    st.session_state.alerts = []
    if not df.empty:
        low_profit = df[df["Net Profit"] < threshold]
        for _, row in low_profit.iterrows():
            st.session_state.alerts.append(f"⚠️ Low Net Profit in {row['Month'].strftime('%Y-%m')}: {row['Net Profit']:.2f}")
    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            st.error(alert)
    else:
        st.success("No alerts.")

# Main app
def main_app():
    st.title("💰 Restaurant Financial Dashboard")

    # Load data
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Month"] + FIELDS)

    # Sidebar
    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.experimental_rerun()
        st.header("📤 Import Data")
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_pdf:
            month_str = select_statement_month("Statement Month")
            month = pd.to_datetime(month_str + "-01")
            if st.button("✨ Process PDF"):
                data = parse_pdf(uploaded_pdf)
                if data:
                    if month in df["Month"].values:
                        overwrite = st.radio(f"Data for {month_str} exists. Overwrite?", ("No", "Yes"))
                        if overwrite == "No":
                            st.warning("Skipping upload.")
                            return
                        df = df[df["Month"] != month]
                    new_row = {"Month": month, **data}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ Processed!")

    # Alerts
    send_alerts(df)

    # Tabs
    tabs = st.tabs(["📈 Trends", "📊 Bars", "📅 Compare", "📋 Costs", "💹 Ratios", "📝 Entry", "📄 Data"])
    
    # Trends
    with tabs[0]:
        if not df.empty:
            st.subheader("Trends")
            metrics = st.multiselect("Metrics", FIELDS, default=["Sales", "Expenses", "Net Profit"], key="line")
            fig = px.line(df, x="Month", y=metrics, title="Over Time")
            st.plotly_chart(fig)
    
    # Bars
    with tabs[1]:
        if not df.empty:
            st.subheader("Monthly Breakdown")
            metrics = st.multiselect("Metrics", FIELDS, default=["Sales", "Expenses", "Net Profit"], key="bar")
            fig = px.bar(df, x="Month", y=metrics, barmode="group", title="By Month")
            st.plotly_chart(fig)
    
    # Compare
    with tabs[2]:
        if not df.empty:
            st.subheader("Compare Months")
            months = df["Month"].dt.strftime("%Y-%m").unique()
            col1, col2 = st.columns(2)
            with col1:
                month1 = pd.to_datetime(st.selectbox("Month 1", months) + "-01")
            with col2:
                month2 = pd.to_datetime(st.selectbox("Month 2", months, index=1 if len(months) > 1 else 0) + "-01")
            fields = st.multiselect("Fields", FIELDS, default=["Sales", "Expenses", "Net Profit"])
            if fields and month1 != month2:
                df_compare = df[df["Month"].isin([month1, month2])].set_index("Month")[fields]
                df_compare.index = df_compare.index.strftime("%Y-%m")
                if len(df_compare) == 2:
                    diff = df_compare.diff().iloc[1]
                    pct_change = (df_compare.pct_change().iloc[1] * 100).replace([np.inf, -np.inf], np.nan)
                    comparison_df = pd.concat([df_compare.T, diff.rename("Diff"), pct_change.rename("% Change")], axis=1)
                    st.dataframe(comparison_df.style.format("{:.2f}", subset=df_compare.columns)
                                 .format("{:.2f}", subset=["Diff"])
                                 .format("{:.2f}%", subset=["% Change"]))
    
    # Costs
    with tabs[3]:
        if not df.empty:
            st.subheader("Cost Breakdown")
            cost_fields = [f for f in FIELDS if f not in ["Sales", "Gross Profit", "Net Profit"]]
            month = pd.to_datetime(st.selectbox("Month", df["Month"].dt.strftime("%Y-%m")) + "-01")
            month_data = df[df["Month"] == month][cost_fields].T
            if not month_data.empty:
                month_data.columns = ["Value"]
                fig = px.pie(month_data, values="Value", names=month_data.index, title=f"Costs for {month.strftime('%Y-%m')}")
                st.plotly_chart(fig)
    
    # Ratios
    with tabs[4]:
        if not df.empty:
            st.subheader("Ratios")
            df["Gross Margin"] = (df["Gross Profit"] / df["Sales"] * 100).fillna(0)
            df["Net Margin"] = (df["Net Profit"] / df["Sales"] * 100).fillna(0)
            fig = px.line(df, x="Month", y=["Gross Margin", "Net Margin"], title="Profit Margins")
            st.plotly_chart(fig)
    
    # Manual Entry
    with tabs[5]:
        st.subheader("Manual Entry")
        month_str = select_statement_month("Entry Month")
        month = pd.to_datetime(month_str + "-01")
        with st.form("manual_entry"):
            data = {}
            for field in ["Sales", "Direct Costs", "Expenses", "Net Profit"]:
                data[field] = st.number_input(field, min_value=-1000000.0 if field == "Net Profit" else 0.0, value=0.0)
            if st.form_submit_button("Save"):
                if month in df["Month"].values:
                    overwrite = st.radio(f"Data for {month_str} exists. Overwrite?", ("No", "Yes"))
                    if overwrite == "Yes":
                        df = df[df["Month"] != month]
                new_row = {"Month": month, **data}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Saved!")
    
    # Data
    with tabs[6]:
        st.subheader("Raw Data")
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "financial_data.csv", "text/csv")

if __name__ == "__main__":
    st.set_page_config(page_title="Restaurant Analytics", layout="wide")
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()
