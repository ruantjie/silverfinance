# 🚀 app.py - Restaurant Financial Analytics
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from pypdf import PdfReader

# 🔒 Authentication (Use Streamlit Secrets in production)
AUTHENTICATION = {
    "username": "Silver",
    "password": "Silver@123"
}

# 📁 Data Configuration
DATA_FILE = "restaurant_finances.csv"
CURRENCY = "R{:,.2f}"
CATEGORIES = [
    "Gross turnover", "Less VAT", "Nett turnover", "Total cost of sales",
    "Beverages", "Staff wages", "Utilities", "Marketing", "Gross profit",
    "Net profit/(loss)"
]

# 🏁 Session State Initialization
if "auth" not in st.session_state:
    st.session_state.auth = False
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Month"] + CATEGORIES)

# 🔐 Authentication Functions
def login_section():
    """Secure login form with emojis"""
    with st.form("auth"):
        st.title("🍽 Restaurant Financial Hub")
        st.subheader("🔒 Authenticate to Continue")
        user = st.text_input("👤 Username")
        pwd = st.text_input("🔑 Password", type="password")
        
        if st.form_submit_button("🚪 Login"):
            if user == AUTHENTICATION["username"] and pwd == AUTHENTICATION["password"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

# 📊 Data Handling
@st.cache_data
def load_financials():
    """Load data from GitHub repository"""
    try:
        return pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except:
        return pd.DataFrame(columns=["Month"] + CATEGORIES)

def save_financials(df):
    """Save data to GitHub repository"""
    try:
        df.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"💾 Save Error: {str(e)}")
        return False

def parse_statement(pdf_file):
    """Advanced PDF parser for restaurant financials"""
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join([page.extract_text() for page in reader.pages])
        
        # 🧹 Text cleaning and normalization
        text = re.sub(r"\s+", " ", text)  # Remove extra whitespace
        text = re.sub(r"(%|\$|ZAR)", "", text)  # Remove currency symbols
        
        # 🕵️ Field-value extraction
        financials = {}
        for field in CATEGORIES:
            # Match field name followed by amount (handles multi-line)
            pattern = re.compile(
                rf"{re.escape(field)}.*?(R?\s*[\d,]+\.\d{{2}})", 
                re.IGNORECASE | re.DOTALL
            )
            match = pattern.search(text)
            if match:
                try:
                    value = float(match.group(1).replace("R", "").replace(",", "").strip())
                    financials[field] = value
                except:
                    continue
        
        return financials
    except Exception as e:
        st.error(f"📄 PDF Error: {str(e)}")
        return {}

# 📈 Visualization Components
def profit_loss_dashboard(df):
    """Interactive financial dashboard"""
    st.header("📅 Monthly Financial Overview")
    
    # 🎚️ Timeframe Selector
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("📌 Start Date", df["Month"].min())
    with col2:
        end = st.date_input("📌 End Date", df["Month"].max())
    
    filtered = df[(df["Month"] >= pd.to_datetime(start)) & 
                (df["Month"] <= pd.to_datetime(end))]
    
    # 📊 Main Financial Metrics
    metric_cols = st.columns(3)
    with metric_cols[0]:
        st.metric("💰 Total Income", filtered["Nett turnover"].sum())
    with metric_cols[1]:
        st.metric("💸 Total Expenses", filtered["Total cost of sales"].sum())
    with metric_cols[2]:
        st.metric("📈 Net Profit", filtered["Net profit/(loss)"].sum())
    
    # 📉 Interactive Trend Chart
    fig = px.line(filtered, x="Month", y=CATEGORIES,
                 title="Financial Trends Over Time",
                 labels={"value": "Amount (R)"})
    st.plotly_chart(fig, use_container_width=True)

# 🖥 Main Application Interface
def main_interface():
    st.title("🍴 Silver Spur Financial Management")
    
    # 💾 Load Data
    df = load_financials()
    
    # 🎛️ Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Operations")
        if st.button("🚪 Logout"):
            st.session_state.auth = False
            st.rerun()
        
        # 📄 PDF Processing
        st.subheader("📤 Import Statement")
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_pdf and st.button("✨ Process PDF"):
            parsed_data = parse_statement(uploaded_pdf)
            if parsed_data:
                month = st.date_input("🗓️ Statement Month")
                new_row = {"Month": month, **parsed_data}
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                if save_financials(updated_df):
                    st.success("✅ PDF processed successfully!")
                    df = updated_df
    
    # 📝 Data Entry & Analysis Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Manual Entry", "📊 Analysis", "⚙️ Management"])
    
    with tab1:
        with st.form("manual_entry"):
            st.subheader("✍️ Manual Data Entry")
            month = st.date_input("🗓️ Month")
            income = st.number_input("💰 Gross Income", min_value=0.0)
            expenses = st.number_input("💸 Total Expenses", min_value=0.0)
            profit = st.number_input("📈 Net Profit", value=income - expenses)
            
            if st.form_submit_button("💾 Save Entry"):
                new_row = {
                    "Month": month,
                    "Gross turnover": income,
                    "Total cost of sales": expenses,
                    "Net profit/(loss)": profit
                }
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                if save_financials(updated_df):
                    st.success("✅ Entry saved successfully!")
                    df = updated_df
    
    with tab2:
        profit_loss_dashboard(df)
        
        # 🔍 Detailed Analysis
        st.subheader("🔍 Detailed Breakdown")
        selected = st.multiselect("Choose Categories", CATEGORIES, default=CATEGORIES[:3])
        if selected:
            fig = px.bar(df.melt(id_vars="Month", value_vars=selected),
                        x="Month", y="value", color="variable",
                        title="Category Comparison")
            st.plotly_chart(fig)
    
    with tab3:
        st.subheader("🗄️ Data Management")
        st.dataframe(df.sort_values("Month", ascending=False))
        
        if st.button("🧹 Clear All Data"):
            df = pd.DataFrame(columns=["Month"] + CATEGORIES)
            save_financials(df)
            st.rerun()
        
        st.download_button("⬇️ Export CSV", df.to_csv(), "financial_data.csv")

# 🚀 Launch Application
if __name__ == "__main__":
    st.set_page_config(page_title="Restaurant Finance", layout="wide")
    if st.session_state.auth:
        main_interface()
    else:
        login_section()
