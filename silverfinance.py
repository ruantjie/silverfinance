import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
from typing import Dict

# Constants
DATA_FILE = "income_statement_data.csv"
CURRENCY_FORMAT = "R{:,.2f}"

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# Field configuration
fields_list = [
    "Gross turnover",
    "Less VAT",
    "Nett turnover",
    "Total cost of sales",
    "Beverages",
    "Bread and rolls",
    # ... (rest of your fields)
    "Nett Profit /(Loss)"
]

alias_mapping = {
    # ... (your alias mappings)
}

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and cache financial data."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["month"])
    else:
        df = pd.DataFrame(columns=["month"] + fields_list)
    return df

def save_data(df: pd.DataFrame) -> None:
    """Save data to CSV."""
    df.to_csv(DATA_FILE, index=False)

def month_selector(label: str) -> str:
    """Date input that returns YYYY-MM format."""
    selected_date = st.date_input(
        label,
        value=datetime.today().replace(day=1),
        format="YYYY-MM-DD",
        help="Select any day in the target month"
    )
    return selected_date.strftime("%Y-%m")

def manual_entry_form(df: pd.DataFrame) -> pd.DataFrame:
    """Manual data entry form."""
    with st.expander("📝 Manual Data Entry", expanded=True):
        form = st.form(key="manual_form", clear_on_submit=True)
        
        # Month selector
        month = month_selector("Report Month")
        
        # Initialize data dict
        manual_data = {}

        # Income Section
        form.subheader("Income Section")
        income_cols = form.columns(3)
        for i, field in enumerate(fields_list[:7]):
            with income_cols[i % 3]:
                manual_data[field] = st.number_input(
                    field, 
                    value=0.0, 
                    step=1000.0,
                    key=f"income_{field}"
                )

        # Expenses Section
        form.subheader("Expenses Section")
        with form.container():
            expense_cols = st.columns(3)
            for i, field in enumerate(fields_list[7:]):
                with expense_cols[i % 3]:
                    manual_data[field] = st.number_input(
                        field, 
                        value=0.0, 
                        step=1000.0,
                        key=f"expense_{field}"
                    )

        # Submit button
        if form.form_submit_button("💾 Save Entry"):
            return handle_data_submission(manual_data, month, df)
    
    return df

def handle_data_submission(data: Dict, month: str, df: pd.DataFrame) -> pd.DataFrame:
    """Process and validate data submission."""
    # Convert to datetime for comparison
    month_dt = pd.to_datetime(month)
    
    # Check for existing entries
    if not df.empty and (df["month"].dt.strftime("%Y-%m") == month_dt.strftime("%Y-%m")).any():
        st.error(f"Data for {month} already exists!")
        return df
    
    # Auto-calculate Gross Profit
    if data.get("Gross profit", 0) == 0:
        data["Gross profit"] = data.get("Nett turnover", 0) - data.get("Total cost of sales", 0)
    
    # Create new row
    new_row = pd.DataFrame([{**{"month": month_dt}, **data}])
    updated_df = pd.concat([df, new_row], ignore_index=True).sort_values("month")
    save_data(updated_df)
    st.success(f"Data for {month} saved successfully!")
    return updated_df

def analysis_section(df: pd.DataFrame) -> None:
    """Financial analysis visualizations."""
    st.header("📈 Financial Analysis")
    
    if not df.empty:
        # Convert month to string for display
        display_df = df.copy()
        display_df["month"] = display_df["month"].dt.strftime("%Y-%m")
        
        selected_fields = st.multiselect("Select Metrics", fields_list, default=["Nett turnover"])
        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Area"])
        
        fig = px.line(display_df, x="month", y=selected_fields) if chart_type == "Line" else \
              px.bar(display_df, x="month", y=selected_fields) if chart_type == "Bar" else \
              px.area(display_df, x="month", y=selected_fields)
        
        fig.update_layout(
            title=f"{chart_type} Chart of Selected Metrics",
            xaxis_title="Month",
            yaxis_title="Amount (R)",
            hovermode="x unified",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Data Table
        st.subheader("📄 Financial Records")
        styled_df = display_df.style.format({
            **{field: CURRENCY_FORMAT for field in fields_list},
            "month": lambda x: x
        })
        st.dataframe(styled_df, use_container_width=True)
        
        # Data Export
        st.download_button(
            "⬇️ Download Full Data",
            df.to_csv(index=False),
            file_name="financial_records.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available for analysis")

def data_management_section(df: pd.DataFrame) -> pd.DataFrame:
    """Data maintenance functions."""
    st.header("🔧 Data Management")
    
    if not df.empty:
        st.metric("Total Records", len(df))
        date_range = f"{df['month'].min().strftime('%Y-%m')} to {df['month'].max().strftime('%Y-%m')}"
        st.metric("Date Range", date_range)
        
        if st.button("❌ Clear All Data"):
            df = pd.DataFrame(columns=["month"] + fields_list)
            save_data(df)
            st.success("All data cleared successfully!")
            return df
    else:
        st.warning("No data available in the system")
    
    return df

def main():
    st.set_page_config(
        page_title="Silver Finance Dashboard",
        page_icon="💼",
        layout="wide"
    )
    
    st.title("💰 Silver Finance Management System")
    df = load_data()
    
    with st.sidebar:
        st.header("💰 Silver Finance")
        st.header("Navigation")
        section = st.radio("Go to", ["Data Entry", "Financial Analysis", "Data Management"])
    
    if section == "Data Entry":
        df = manual_entry_form(df)
    elif section == "Financial Analysis":
        analysis_section(df)
    elif section == "Data Management":
        df = data_management_section(df)

if __name__ == "__main__":
    main()