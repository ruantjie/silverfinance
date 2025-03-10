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

# Updated PDF parsing
def parse_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        st.write("Debug: First 2000 characters of PDF text:", text[:2000])
        
        amounts = {}
        
        # Summary fields
        summary_patterns = {
            "Sales": r"Sales\s+([\d,]+\.\d{2})",
            "Direct Costs": r"Direct Costs\s+([\d,]+\.\d{2})",
            "Gross Profit": r"Gross Profit\s+([\d,]+\.\d{2})",
            "Expenses": r"Expenses\s+([\d,]+\.\d{2})",
            "Nett Profit /(Loss)": r"(-?[\d,]+\.\d{2})Nett Profit",
            "Nett turnover": r"Nett Sales\s+[\d,]+\.\d{2}\s+([\d,]+\.\d{2})"
        }
        
        for field, pattern in summary_patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).replace(',', '')
                amounts[field] = float(value)
        
        # Improved food categories regex
        category_lines = re.findall(r"[a-z]{2}\s+(.+?)\s+(-?[\d,]+\.\d{2})\s+(-?[\d,]+\.\d{2})\s+(-?[\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})", text)
        field_map = {f.lower().replace('and', '&'): f for f in FIELDS}  # Reverse normalization for matching PDF
        for line in category_lines:
            category = line[0].strip()
            usage = line[7]  # CAT USAGE is the 8th group (index 7)
            category_key = category.lower().replace('&', 'and')
            if category_key in field_map:
                amounts[field_map[category_key]] = float(usage.replace(',', ''))
            else:
                st.warning(f"Category '{category}' not mapped to FIELDS.")
        
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
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
        df = df[["Month"] + [col for col in FIELDS if col in df.columns]]
        st.write("Debug: Loaded DataFrame columns:", df.columns.tolist())
        st.write("Debug: First few rows:", df.head())
        st.write("Debug: Month column type:", str(df["Month"].dtype))
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Month"] + FIELDS)
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
        st.write("Debug: Initialized empty DataFrame with columns:", df.columns.tolist())
    except pd.errors.ParserError as e:
        st.error(f"CSV Error: {e}")
        df = pd.DataFrame(columns=["Month"] + FIELDS)
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
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
            month = pd.to_datetime(month_str + "-01").normalize()
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
                    df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ Processed!")
                    st.write("Debug: Updated DataFrame columns after upload:", df.columns.tolist())
                    st.write("Debug: Month column type after upload:", str(df["Month"].dtype))
        
        st.header("🗑️ Clear Data")
        if st.button("Clear All Data"):
            df = pd.DataFrame(columns=["Month"] + FIELDS)
            df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
            df.to_csv(DATA_FILE, index=False)
            st.success("✅ All data cleared from CSV!")
            st.write("Debug: DataFrame columns after clearing:", df.columns.tolist())
            st.rerun()

    # Alerts
    send_alerts(df)

    # Tabs
    tabs = st.tabs(["📈 Trends", "📊 Bars", "📅 Compare", "📋 Costs", "💹 Ratios", "🔗 Correlations", "📝 Entry", "📄 Data"])

    # Trends
    with tabs[0]:
        if not df.empty and len(df) > 0:
            st.subheader("Trends")
            metrics = st.multiselect("Metrics", FIELDS, default=["Sales", "Expenses", "Nett Profit /(Loss)"], key="trends_metrics")
            if metrics and all(metric in df.columns for metric in metrics):
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
                df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
            months = df["Month"].dt.strftime("%Y-%m").dropna().unique()
            if len(months) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    month1_str = st.selectbox("Month 1", months)
                    month1 = pd.to_datetime(month1_str + "-01").normalize()
                with col2:
                    default_idx = 1 if len(months) > 1 else 0
                    month2_str = st.selectbox("Month 2", months, index=default_idx)
                    month2 = pd.to_datetime(month2_str + "-01").normalize()
                fields = st.multiselect("Fields", FIELDS, default=["Sales", "Expenses", "Nett Profit /(Loss)"])
                if fields and month1 != month2:
                    df["Month"] = df["Month"].dt.normalize()
                    df_compare = df[df["Month"].isin([month1, month2])].set_index("Month")[fields]
                    if not df_compare.empty and len(df_compare) == 2:
                        df_compare.index = df_compare.index.strftime("%Y-%m")
                        diff = df_compare.diff().iloc[1]
                        pct_change = (df_compare.pct_change().iloc[1] * 100).replace([np.inf, -np.inf], np.nan)
                        comparison_df = pd.concat([df_compare.T, diff.rename("Diff"), pct_change.rename("% Change")], axis=1)
                        st.dataframe(comparison_df.style.format("{:.2f}", subset=df_compare.columns)
                                     .format("{:.2f}", subset=["Diff"])
                                     .format("{:.2f}%", subset=["% Change"]))
                    else:
                        st.warning("Selected months not found in data or insufficient data for comparison.")
            else:
                st.warning("No valid months available for comparison.")
        else:
            st.warning("No data available. Upload a PDF or enter data manually.")
    
    # Costs
    with tabs[3]:
        if not df.empty and len(df) > 0:
            st.subheader("Cost Breakdown")
            cost_fields = [f for f in FIELDS if f not in ["Sales", "Gross Profit", "Nett Profit /(Loss)"]]
            month = pd.to_datetime(st.selectbox("Month", df["Month"].dt.strftime("%Y-%m").dropna()) + "-01").normalize()
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
        month = pd.to_datetime(month_str + "-01").normalize()
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
                        df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
                        df.to_csv(DATA_FILE, index=False)
                        st.success("Saved!")
                else:
                    new_row = {"Month": month, **data}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df["Month"] = pd.to_datetime(df["Month"], errors="coerce").dt.normalize()
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
