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

# FIELDS based on your actual PDF columns
FIELDS = [
    "Sales", "Direct Costs", "Gross Profit", "Expenses", "Nett Profit /(Loss)",  # Main summary fields
    "Gross turnover", "Less VAT", "Nett turnover", "Total cost of sales",
    "Beverages", "Bread and rolls", "Butter and cheese", "Chicken", "Chips",
    "Dairy", "Delivery expenses", "Desserts", "Fish", "Fruit and veg",
    "Garnish", "Groceries", "Hot beverages", "Ice-cream", "Liquor - beer and cider",
    "Liquor - spirits", "Liquor - wine", "Meat", "Mushrooms", "Oil", "Ribs",
    "Premade Sauces", "Spur sauces", "Other income", "Breakages recovery",
    "Interest received", "Transport", "Refund on old oil", "Total variable overheads",
    "Accounting and audit fees", "Bank charges", "Breakages and replacements",
    "Cleaning and pest control", "Computer expenses", "Credit card commission Paid",
    "Donations", "Entertainment Costs", "General gas", "Interest paid",
    "Legal and Licence fees", "Printing, stationery and menus", "Repairs and maintenance",
    "Salaries and wages: -Management", "Salaries and wages: -Production staff (Incl Casuals)",
    "Salaries and wages: -Waitrons (Incl Casuals)", "Salaries and wages: -Director",
    "Salaries and wages: -Company portion UIF and SDL", "Staff transport",
    "Staff uniforms", "Staff meals", "Staff medical", "Staff welfare",
    "Telephone expenses", "Waste removal", "Total fixed overheads",
    "Electricity, water, refuse, sewerage and rates", "Insurance - HIC",
    "Insurance - Sanlam", "Rent paid", "Security expenses", "Marketing Fees",
    "Marketing general", "Spur Marketing fee", "Spur Franchise Fee"
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
        st.title("🍽 Silver Spur Analytics")
        st.subheader("🔒 Financial Portal")
        user = st.text_input("👤 Username")
        pwd = st.text_input("🔑 Password", type="password")
        if st.form_submit_button("🚪 Login"):
            if user == "Silver" and pwd == "Silver@123":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect username or password.")

# Enhanced PDF parsing with debug output
def parse_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        st.write("Debug: First 500 characters of PDF text:", text[:500])  # Show raw text
        
        amounts = {}
        patterns = {
            "Gross turnover": r"Gross turnover\s+([\d,]+\.\d{2})",
            "Less VAT": r"Less VAT\s+([\d,]+\.\d{2})",
            "Nett turnover": r"Nett turnover\s+([\d,]+\.\d{2})",
            "Total cost of sales": r"Total cost of sales\s+([\d,]+\.\d{2})",
            "Beverages": r"Beverages\s+([\d,]+\.\d{2})",
            "Bread and rolls": r"Bread and rolls\s+([\d,]+\.\d{2})",
            "Butter and cheese": r"Butter and cheese\s+([\d,]+\.\d{2})",
            "Chicken": r"Chicken\s+([\d,]+\.\d{2})",
            "Chips": r"Chips\s+([\d,]+\.\d{2})",
            "Dairy": r"Dairy\s+([\d,]+\.\d{2})",
            "Delivery expenses": r"Delivery expenses\s+([\d,]+\.\d{2})",
            "Desserts": r"Desserts\s+([\d,]+\.\d{2})",
            "Fish": r"Fish\s+([\d,]+\.\d{2})",
            "Fruit and veg": r"Fruit and veg\s+([\d,]+\.\d{2})",
            "Garnish": r"Garnish\s+([\d,]+\.\d{2})",
            "Groceries": r"Groceries\s+([\d,]+\.\d{2})",
            "Hot beverages": r"Hot beverages\s+([\d,]+\.\d{2})",
            "Ice-cream": r"Ice-cream\s+([\d,]+\.\d{2})",
            "Liquor - beer and cider": r"Liquor - beer and cider\s+([\d,]+\.\d{2})",
            "Liquor - spirits": r"Liquor - spirits\s+([\d,]+\.\d{2})",
            "Liquor - wine": r"Liquor - wine\s+([\d,]+\.\d{2})",
            "Meat": r"Meat\s+([\d,]+\.\d{2})",
            "Mushrooms": r"Mushrooms\s+([\d,]+\.\d{2})",
            "Oil": r"Oil\s+([\d,]+\.\d{2})",
            "Ribs": r"Ribs\s+([\d,]+\.\d{2})",
            "Premade Sauces": r"Premade Sauces\s+([\d,]+\.\d{2})",
            "Spur sauces": r"Spur sauces\s+([\d,]+\.\d{2})",
            "Gross Profit": r"Gross profit\s+([\d,]+\.\d{2})",
            "Other income": r"Other income\s+([\d,]+\.\d{2})",
            "Breakages recovery": r"Breakages recovery\s+([\d,]+\.\d{2})",
            "Interest received": r"Interest received\s+([\d,]+\.\d{2})",
            "Transport": r"Transport\s+([\d,]+\.\d{2})",
            "Refund on old oil": r"Refund on old oil\s+([\d,]+\.\d{2})",
            "Total variable overheads": r"Total variable overheads\s+([\d,]+\.\d{2})",
            "Accounting and audit fees": r"Accounting and audit fees\s+([\d,]+\.\d{2})",
            "Bank charges": r"Bank charges\s+([\d,]+\.\d{2})",
            "Breakages and replacements": r"Breakages and replacements\s+([\d,]+\.\d{2})",
            "Cleaning and pest control": r"Cleaning and pest control\s+([\d,]+\.\d{2})",
            "Computer expenses": r"Computer expenses\s+([\d,]+\.\d{2})",
            "Credit card commission Paid": r"Credit card commission Paid\s+([\d,]+\.\d{2})",
            "Donations": r"Donations\s+([\d,]+\.\d{2})",
            "Entertainment Costs": r"Entertainment Costs\s+([\d,]+\.\d{2})",
            "General gas": r"General gas\s+([\d,]+\.\d{2})",
            "Interest paid": r"Interest paid\s+([\d,]+\.\d{2})",
            "Legal and Licence fees": r"Legal and Licence fees\s+([\d,]+\.\d{2})",
            "Printing, stationery and menus": r"Printing, stationery and menus\s+([\d,]+\.\d{2})",
            "Repairs and maintenance": r"Repairs and maintenance\s+([\d,]+\.\d{2})",
            "Salaries and wages: -Management": r"Salaries and wages: -Management\s+([\d,]+\.\d{2})",
            "Salaries and wages: -Production staff (Incl Casuals)": r"Salaries and wages: -Production staff \(Incl Casuals\)\s+([\d,]+\.\d{2})",
            "Salaries and wages: -Waitrons (Incl Casuals)": r"Salaries and wages: -Waitrons \(Incl Casuals\)\s+([\d,]+\.\d{2})",
            "Salaries and wages: -Director": r"Salaries and wages: -Director\s+([\d,]+\.\d{2})",
            "Salaries and wages: -Company portion UIF and SDL": r"Salaries and wages: -Company portion UIF and SDL\s+([\d,]+\.\d{2})",
            "Staff transport": r"Staff transport\s+([\d,]+\.\d{2})",
            "Staff uniforms": r"Staff uniforms\s+([\d,]+\.\d{2})",
            "Staff meals": r"Staff meals\s+([\d,]+\.\d{2})",
            "Staff medical": r"Staff medical\s+([\d,]+\.\d{2})",
            "Staff welfare": r"Staff welfare\s+([\d,]+\.\d{2})",
            "Telephone expenses": r"Telephone expenses\s+([\d,]+\.\d{2})",
            "Waste removal": r"Waste removal\s+([\d,]+\.\d{2})",
            "Total fixed overheads": r"Total fixed overheads\s+([\d,]+\.\d{2})",
            "Electricity, water, refuse, sewerage and rates": r"Electricity, water, refuse, sewerage and rates\s+([\d,]+\.\d{2})",
            "Insurance - HIC": r"Insurance - HIC\s+([\d,]+\.\d{2})",
            "Insurance - Sanlam": r"Insurance - Sanlam\s+([\d,]+\.\d{2})",
            "Rent paid": r"Rent paid\s+([\d,]+\.\d{2})",
            "Security expenses": r"Security expenses\s+([\d,]+\.\d{2})",
            "Marketing Fees": r"Marketing Fees\s+([\d,]+\.\d{2})",
            "Marketing general": r"Marketing general\s+([\d,]+\.\d{2})",
            "Spur Marketing fee": r"Spur Marketing fee\s+([\d,]+\.\d{2})",
            "Spur Franchise Fee": r"Spur Franchise Fee\s+([\d,]+\.\d{2})",
            "Sales": r"Sales\s+([\d,]+\.\d{2})",
            "Direct Costs": r"Direct Costs\s+([\d,]+\.\d{2})",
            "Gross Profit": r"Gross Profit\s+([\d,]+\.\d{2})",
            "Expenses": r"Expenses\s+([\d,]+\.\d{2})",
            "Nett Profit /(Loss)": r"Nett Profit /\(Loss\)\s+(-?[\d,]+\.\d{2})"
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                value = match.group(1).replace(',', '')
                amounts[field] = float(value)
        
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
    threshold = st.number_input("Nett Profit Threshold", value=0.0, step=1000.0)
    if not df.empty:
        if "Nett Profit /(Loss)" in df.columns:
            low_profit = df[df["Nett Profit /(Loss)"] < threshold]
            for _, row in low_profit.iterrows():
                alert = f"⚠️ Low Nett Profit in {row['Month'].strftime('%Y-%m')}: {row['Nett Profit /(Loss)']:.2f}"
                if alert not in st.session_state.alerts:
                    st.session_state.alerts.append(alert)
        else:
            st.warning("Nett Profit /(Loss) column not found in data. Upload a PDF or enter data manually.")
    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            st.error(alert)
    else:
        st.success("No alerts.")

# Main app
def main_app():
    st.title("💰 Silver Spur Financial Dashboard")

    # Load data
    try:
        df = pd.read_csv(DATA_FILE)
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
        df = df[["Month"] + [col for col in FIELDS if col in df.columns]]
        st.write("Debug: Loaded DataFrame columns:", df.columns.tolist())
        st.write("Debug: First few rows:", df.head())
        st.write("Debug: Month column type:", str(df["Month"].dtype))
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Month"] + FIELDS)
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
        st.write("Debug: Initialized empty DataFrame with columns:", df.columns.tolist())
    except pd.errors.ParserError as e:
        st.error(f"CSV Error: {e}")
        df = pd.DataFrame(columns=["Month"] + FIELDS)
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
        st.write("Debug: Initialized empty DataFrame due to CSV error with columns:", df.columns.tolist())

    # Sidebar
    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
        st.header("📤 Import Data")
        uploaded_pdf = st.file_uploader("Upload Income Statement PDF", type=["pdf"])
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
                    df = df[["Month"] + [col for col in FIELDS if col in df.columns]]
                    df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ Processed!")
                    st.write("Debug: Updated DataFrame columns after upload:", df.columns.tolist())
                    st.write("Debug: Month column type after upload:", str(df["Month"].dtype))
        
        st.header("🗑️ Clear Data")
        if st.button("Clear All Data"):
            df = pd.DataFrame(columns=["Month"] + FIELDS)
            df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
            df.to_csv(DATA_FILE, index=False)
            st.success("✅ All data cleared from CSV!")
            st.write("Debug: DataFrame columns after clearing:", df.columns.tolist())
            st.rerun()

    # Alerts
    send_alerts(df)

    # Tabs
    tabs = st.tabs(["📈 Trends", "📊 Bars", "📅 Compare", "📋 Costs", "💹 Ratios", "🔗 Correlations", "📝 Entry", "📄 Data"])

    # Trends with enhanced validation
    with tabs[0]:
        if not df.empty and len(df) > 0:  # Check for rows
            st.subheader("Trends")
            metrics = st.multiselect("Metrics", FIELDS, default=["Sales", "Expenses", "Nett Profit /(Loss)"], key="trends_metrics")
            if metrics and all(metric in df.columns for metric in metrics):
                # Ensure numeric data
                plot_df = df[["Month"] + metrics].dropna(subset=metrics)
                if not plot_df.empty:
                    fig = px.line(plot_df, x="Month", y=metrics, title="Over Time")
                    st.plotly_chart(fig)
                else:
                    st.warning("No valid data available for selected metrics.")
            else:
                st.warning("Please select valid metrics that exist in the data.")
        else:
            st.warning("No data available. Upload a PDF or enter data manually.")

    # Bars
    with tabs[1]:
        if not df.empty and len(df) > 0:
            st.subheader("Monthly Breakdown")
            metrics = st.multiselect("Metrics", FIELDS, default=["Sales", "Expenses", "Nett Profit /(Loss)"], key="bars_metrics")
            if metrics and all(metric in df.columns for metric in metrics):
                plot_df = df[["Month"] + metrics].dropna(subset=metrics)
                if not plot_df.empty:
                    fig = px.bar(plot_df, x="Month", y=metrics, barmode="group", title="By Month")
                    st.plotly_chart(fig)
                else:
                    st.warning("No valid data available for selected metrics.")
            else:
                st.warning("Please select valid metrics that exist in the data.")
    
    # Compare
    with tabs[2]:
        if not df.empty and len(df) > 0:
            st.subheader("Compare Months")
            if df["Month"].dtype != "datetime64[ns]":
                st.warning("Month column is not in datetime format. Converting...")
                df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
            months = df["Month"].dt.strftime("%Y-%m").dropna().unique()
            if len(months) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    month1 = pd.to_datetime(st.selectbox("Month 1", months) + "-01")
                with col2:
                    month2 = pd.to_datetime(st.selectbox("Month 2", months, index=1 if len(months) > 1 else 0) + "-01")
                fields = st.multiselect("Fields", FIELDS, default=["Sales", "Expenses", "Nett Profit /(Loss)"])
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
            else:
                st.warning("No valid months available for comparison.")
    
    # Costs
    with tabs[3]:
        if not df.empty and len(df) > 0:
            st.subheader("Cost Breakdown")
            cost_fields = [f for f in FIELDS if f not in ["Sales", "Gross Profit", "Nett Profit /(Loss)"]]
            month = pd.to_datetime(st.selectbox("Month", df["Month"].dt.strftime("%Y-%m").dropna()) + "-01")
            month_data = df[df["Month"] == month][cost_fields].T
            if not month_data.empty:
                month_data.columns = ["Value"]
                fig = px.pie(month_data, values="Value", names=month_data.index, title=f"Costs for {month.strftime('%Y-%m')}")
                st.plotly_chart(fig)
    
    # Ratios
    with tabs[4]:
        if not df.empty and len(df) > 0:
            st.subheader("Ratios")
            df["Gross Margin"] = (df["Gross Profit"] / df["Sales"] * 100).fillna(0)
            df["Net Margin"] = (df["Nett Profit /(Loss)"] / df["Sales"] * 100).fillna(0)
            df["Labor to Turnover"] = ((df["Salaries and wages: -Management"].fillna(0) + 
                                        df["Salaries and wages: -Production staff (Incl Casuals)"].fillna(0) + 
                                        df["Salaries and wages: -Waitrons (Incl Casuals)"].fillna(0)) / df["Sales"] * 100).fillna(0)
            fig = px.line(df, x="Month", y=["Gross Margin", "Net Margin", "Labor to Turnover"], title="Ratios Over Time")
            st.plotly_chart(fig)
    
    # Correlations
    with tabs[5]:
        if not df.empty and len(df) > 0:
            st.subheader("Correlations with Sales")
            corr_fields = st.multiselect("Select fields to correlate with Sales", [f for f in FIELDS if f != "Sales"], default=["General gas", "Salaries and wages: -Management"])
            if corr_fields:
                corr_matrix = df[["Sales"] + corr_fields].corr()
                fig = px.imshow(corr_matrix, text_auto=True, title="Correlation Heatmap")
                st.plotly_chart(fig)
                for field in corr_fields:
                    fig_scatter = px.scatter(df, x=field, y="Sales", trendline="ols", title=f"{field} vs Sales")
                    st.plotly_chart(fig_scatter)
    
    # Manual Entry
    with tabs[6]:
        st.subheader("Manual Entry")
        month_str = select_statement_month("Entry Month")
        month = pd.to_datetime(month_str + "-01")
        with st.form("manual_entry"):
            data = {}
            for field in FIELDS:
                data[field] = st.number_input(field, min_value=-1000000.0 if field == "Nett Profit /(Loss)" else 0.0, value=0.0)
            if st.form_submit_button("Save"):
                if month in df["Month"].values:
                    overwrite = st.radio(f"Data for {month_str} exists. Overwrite?", ("No", "Yes"))
                    if overwrite == "No":
                        st.warning("Skipping save.")
                    else:
                        df = df[df["Month"] != month]
                        new_row = {"Month": month, **data}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
                        df.to_csv(DATA_FILE, index=False)
                        st.success("Saved!")
                else:
                    new_row = {"Month": month, **data}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
                    df.to_csv(DATA_FILE, index=False)
                    st.success("Saved!")
    
    # Data
    with tabs[7]:
        st.subheader("Raw Data")
        st.dataframe(df)
        st.download_button("Download CSV", df.to_csv(index=False), "financial_data.csv", "text/csv")

if __name__ == "__main__":
    st.set_page_config(page_title="Silver Spur Analytics", layout="wide")
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()
