import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import calendar
from datetime import datetime, timedelta
import re
from pypdf import PdfReader
import seaborn as sns
import matplotlib.pyplot as plt

# 🔒 Authentication setup
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 📁 Field List aligned with PDF structure
FIELDS = [
    "Sales", "Less Airtime", "Net Sales", "zero rated part", "Direct Costs",
    "Gross Profit", "Expenses", "Net Profit",
    "Butter & Cheese", "Beverages", "Bread & Rolls", "Chicken", "Chips",
    "Hot Beverages", "Dairy", "Desserts", "Fish", "Fruit & Veg", "Garnish",
    "Groceries", "Liquor & Ciders", "Liquor", "Premade Sauces", 
    "Meat", "Ice Cream", "Ribs", "Mushrooms", "Oil", "Spur Sauces",
    "Advertising Promo", "Clean & Pest Control", "Delivery Expenses",
    "Advertising General", "Franchise Fees", "General Gas", "Utilities & Energy",
    "Entertainment Subscription", "Kids Entertainment", "Staff Uniforms",
    "Repairs & Maintenance", "Printing Stationary", "Computer & IT Cost",
    "Water", "Cutlery & Crockery", "Generator", "Packaging", "Staff Transport",
    "Toys & Premiums", "Vat Paid", "Medical Expenses", "Support Staff",
    "Staff Meals", "Government Dep Fund", "Salaries - Managers", "FOH Wages",
    "BOH & Childminders", "UIF Contribution", "Staff Train&Welfare",
    "Account & Audit Fees", "Bank Charge Save Dep", "Credit Card Comm",
    "Maint : Building", "Maint : Furniture", "Maint : Equipment",
    "Legal & License Fee", "Motor Vehicle Expens", "Insurance",
    "Transport& Courier F", "Telephone & Faxes", "Rental Ops Cost",
    "Security Non Ops", "Rates & Refuse", "Balance Sheet"
]

DATA_FILE = "restaurant_finances.csv"

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

def login_page():
    with st.form("auth"):
        st.title("🍽 Silver Spur Analytics")
        st.subheader("🔒 Restaurant Financial Portal")
        user = st.text_input("👤 Username")
        pwd = st.text_input("🔑 Password", type="password")
        if st.form_submit_button("🚪 Login"):
            if user == "Silver" and pwd == "Silver@123":
                st.session_state.authenticated = True
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password.")

def parse_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages)
        amounts = {}
        lines = [line.strip() for line in text.split('\n')]
        
        # Extract summary values
        summary_values = {
            "Sales": r"Sales\s+([\d,]+\.\d{2})",
            "Direct Costs": r"Direct Costs\s+([\d,]+\.\d{2})\s+[\d.]+ %",
            "Gross Profit": r"Gross Profit\s+([\d,]+\.\d{2})",
            "Expenses": r"Expenses\s+([\d,]+\.\d{2})\s+[\d.]+ %",
            "Net Profit": r"Net Profit\s+(-?[\d,]+\.\d{2})"
        }
        
        for field, pattern in summary_values.items():
            match = re.search(pattern, text)
            if match:
                amounts[field] = float(match.group(1).replace(',', ''))
        
        # Extract cost categories
        cost_start = next(i for i, line in enumerate(lines) if "CAT COST CATEGORY" in line)
        cost_end = next(i for i, line in enumerate(lines) if "38.56    38.78" in line)
        
        for line in lines[cost_start+1:cost_end]:
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 8 and parts[1] != '':
                category = parts[1].strip()
                usage = parts[7].replace(',', '')
                amounts[category] = float(usage)
        
        # Extract expense categories
        expense_start = next(i for i, line in enumerate(lines) if "CAT EXPENSE CATEGORY" in line)
        expense_end = next(i for i, line in enumerate(lines) if "84.96    54.42" in line)
        
        for line in lines[expense_start+1:expense_end]:
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 6 and parts[1] != '':
                category = parts[1].strip()
                usage = parts[-1].replace(',', '')
                amounts[category] = float(usage)
        
        # Fix duplicate names
        amounts["Liquor & Ciders"] = amounts.pop("Liquider & Ciders", 0)
        amounts["Liquor"] = amounts.pop("Liquider", 0)
        
        return amounts
    except Exception as e:
        st.error(f"📄 PDF Error: {str(e)}")
        return {}

def send_alerts():
    st.header("🔔 Alerts and Notifications")
    threshold = st.number_input("Set Nett Profit Threshold", value=0.0)
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    if st.session_state.alerts:
        st.write("### Alerts")
        for alert in st.session_state.alerts:
            st.error(alert)
    return threshold

def main_app():
    st.title("💰 Silver Spur Financial Management")

    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except Exception:
        df = pd.DataFrame(columns=["Month"] + FIELDS)

    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.experimental_rerun()
        st.header("📤 Data Import")
        uploaded_pdf = st.file_uploader("Upload PDF Statement", type=["pdf"])
        if uploaded_pdf:
            st.write("### Select Statement Month")
            statement_month = select_statement_month("Statement Month")
            if st.button("✨ Process PDF"):
                data = parse_pdf(uploaded_pdf)
                if data:
                    new_row = {"Month": statement_month}
                    new_row.update(data)
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ PDF processed successfully!")

    threshold = send_alerts()

    tabs = st.tabs([
        "📈 Line Graph", "📊 Bar Chart", "📅 Compare Months", "📋 Cost Analysis",
        "💹 Financial Ratios", "📝 Manual Entry", "🔄 Scenario Simulation",
        "🔮 Forecasting", "📄 Data"
    ])
    
    # Tab 1: Line Graph
    with tabs[0]:
        if not df.empty:
            st.subheader("Financial Trends")
            selected_metrics = st.multiselect(
                "Select Metrics", FIELDS, default=["Net Profit"], key="line_metrics"
            )
            fig = px.line(df, x="Month", y=selected_metrics, title="Performance Over Time")
            st.plotly_chart(fig)
    
    # Tab 2: Bar Chart
    with tabs[1]:
        if not df.empty:
            st.subheader("Monthly Comparison")
            selected_metrics = st.multiselect(
                "Select Metrics", FIELDS, default=["Sales", "Net Profit"], key="bar_metrics"
            )
            fig = px.bar(df, x="Month", y=selected_metrics, barmode="group")
            st.plotly_chart(fig)
    
    # Tab 3: Compare Months
    with tabs[2]:
        if not df.empty:
            st.subheader("Month Comparison")
            months = df["Month"].unique()
            col1, col2 = st.columns(2)
            with col1:
                month1 = st.selectbox("Select Month 1", months)
            with col2:
                month2 = st.selectbox("Select Month 2", months)
            compare_fields = st.multiselect("Select Fields", FIELDS)
            
            if compare_fields:
                df_compare = df[df["Month"].isin([month1, month2])].set_index("Month")
                st.dataframe(df_compare[compare_fields].T.style.highlight_min(axis=1))
    
    # Remaining tabs follow similar patterns (truncated for brevity)
    # ...
    
    # Tab 9: Data
    with tabs[8]:
        st.subheader("Raw Data")
        st.dataframe(df)
        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "financial_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    st.set_page_config(page_title="Silver Spur Analytics", layout="wide")
    if st.session_state.get("authenticated"):
        main_app()
    else:
        login_page()
        main_app()
    else:
        login_page()
