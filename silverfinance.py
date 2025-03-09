import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
from typing import Dict

# Constants
DATA_FILE = "financial_data.csv"
CURRENCY_FORMAT = "R{:,.2f}"

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# Field configuration matching your PDF structure
fields_list = [
    # ... (keep the full fields list from previous example)
]

alias_mapping = {
    # ... (keep the alias mapping from previous example)
}

@st.cache_data
def load_data():
    """Load historical data from CSV"""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["month"])
    else:
        df = pd.DataFrame(columns=["month"] + fields_list)
    return df

def save_data(df):
    """Save DataFrame to CSV"""
    df.to_csv(DATA_FILE, index=False)

def parse_pdf_data(pdf_bytes):
    """PDF parser for income statements"""
    extracted_data = {}
    pdf_reader = PdfReader(pdf_bytes)
    full_text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

    amount_pattern = r"R?\s*(-?\s*\d{1,3}(?:,\d{3})*\.\d{2})"
    
    for field in fields_list:
        search_terms = [field.lower()] + alias_mapping.get(field.lower(), [])
        pattern = re.compile(rf"({'|'.join(re.escape(term) for term in search_terms)}).*?{amount_pattern}", re.IGNORECASE | re.DOTALL)
        
        match = pattern.search(full_text)
        if match:
            try:
                amount = float(match.group(2).replace(" ", "").replace(",", ""))
                extracted_data[field] = amount
            except (ValueError, IndexError):
                continue

    return extracted_data

def manual_entry_form(df):
    """Manual data entry form with sections"""
    with st.expander("📝 Manual Data Entry", expanded=True):
        with st.form("manual_form", clear_on_submit=True):
            month = st.date_input("Report Month", value=datetime.today().replace(day=1)).strftime("%Y-%m")
            manual_data = {}

            # Income Section
            st.subheader("Income Details")
            income_cols = st.columns(3)
            for i, field in enumerate(fields_list[:15]):  # First 15 fields as income-related
                with income_cols[i % 3]:
                    manual_data[field] = st.number_input(field, value=0.0, step=1000.0)

            # Expenses Section
            st.subheader("Expenses Details")
            with st.expander("Operating Expenses"):
                expense_cols = st.columns(3)
                for i, field in enumerate(fields_list[15:]):
                    with expense_cols[i % 3]:
                        manual_data[field] = st.number_input(field, value=0.0, step=1000.0)

            if st.form_submit_button("💾 Save Manual Entry"):
                if month in df["month"].astype(str).values:
                    st.error(f"Data for {month} already exists!")
                else:
                    new_row = pd.DataFrame([{**{"month": month}, **manual_data}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("Manual entry saved successfully!")
    return df

def main():
    st.set_page_config(page_title="Silver Finance Dashboard", page_icon="💼", layout="wide")
    st.title("💰 Silver Finance Management System")
    
    df = load_data()
    
    with st.sidebar:
        st.header("Data Import")
        
        # PDF Upload Section
        with st.expander("📄 Upload PDF Statement"):
            uploaded_pdf = st.file_uploader("Select PDF file", type=["pdf"])
            pdf_month = st.date_input("Statement Month", value=datetime.today().replace(day=1))
            
            if uploaded_pdf and PdfReader and st.button("Process PDF"):
                parsed_data = parse_pdf_data(uploaded_pdf)
                if parsed_data:
                    month_str = pdf_month.strftime("%Y-%m")
                    
                    if month_str in df["month"].astype(str).values:
                        st.error(f"Data for {month_str} already exists!")
                    else:
                        new_row = pd.DataFrame([{**{"month": month_str}, **parsed_data}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        st.success("PDF data imported successfully!")
                else:
                    st.warning("No valid data found in PDF")

        # Additional Data Upload
        with st.expander("📤 Upload Other Data"):
            additional_data = st.file_uploader("Select CSV/Excel file", type=["csv", "xlsx"])
            if additional_data:
                try:
                    if additional_data.name.endswith(".csv"):
                        new_df = pd.read_csv(additional_data)
                    else:
                        new_df = pd.read_excel(additional_data)
                    
                    # Merge with existing data
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df)
                    st.success("Additional data uploaded successfully!")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

    # Main Content Area
    tab1, tab2, tab3 = st.tabs(["Data Entry", "Financial Analysis", "Data Management"])

    with tab1:
        df = manual_entry_form(df)

    with tab2:
        st.header("Financial Analysis")
        if not df.empty:
            # Time Series Analysis
            st.subheader("Trend Analysis")
            selected_metrics = st.multiselect("Select metrics", fields_list, default=["Gross turnover", "Nett Profit /(Loss)"])
            
            fig = px.line(
                df.sort_values("month"),
                x="month",
                y=selected_metrics,
                title="Financial Metrics Over Time",
                labels={"value": "Amount (R)", "month": "Month"},
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Month Comparison
            st.subheader("Month Comparison")
            compare_months = st.multiselect("Select months to compare", df["month"].unique())
            if compare_months:
                compare_df = df[df["month"].isin(compare_months)].set_index("month").T
                st.dataframe(compare_df.style.format(CURRENCY_FORMAT))

    with tab3:
        st.header("Data Management")
        if not df.empty:
            st.subheader("Current Data")
            st.dataframe(df.sort_values("month", ascending=False).style.format({
                **{field: CURRENCY_FORMAT for field in fields_list},
                "month": lambda x: x.strftime("%Y-%m")
            }))
            
            if st.button("Clear All Data"):
                df = pd.DataFrame(columns=["month"] + fields_list)
                save_data(df)
                st.experimental_rerun()
        else:
            st.info("No financial data available")

if __name__ == "__main__":
    main()
