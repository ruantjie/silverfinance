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

# Field configuration matching your PDF structure
fields_list = [
    "Gross turnover",
    "Less VAT",
    "Nett turnover",
    "Total cost of sales",
    "Beverages",
    "Bread and rolls",
    "Butter and cheese",
    "Chicken",
    "Chips",
    "Dairy",
    "Delivery expenses",
    "Desserts",
    "Fish",
    "Fruit and veg",
    "Garnish",
    "Groceries",
    "Hot beverages",
    "Ice-cream",
    "Liquor - beer and cider",
    "Liquor - spirits",
    "Liquor - wine",
    "Meat",
    "Mushrooms",
    "Oil",
    "Ribs",
    "Premade Sauces",
    "Spur sauces",
    "Gross profit",
    "Other income",
    "Breakages recovery",
    "Interest received",
    "Transport",
    "Refund on old oil",
    "Total variable overheads",
    "Accounting and audit fees",
    "Bank charges",
    "Breakages and replacements",
    "Cleaning and pest control",
    "Computer expenses",
    "Credit card commission Paid",
    "Donations",
    "Entertainment Costs",
    "General gas",
    "Hire of Equipment",
    "Interest paid",
    "Kids Entertainment",
    "Legal and Licence fees",
    "Printing, stationery and menus",
    "Packaging cost",
    "Repairs and maintenance",
    "Salaries and wages: -Management",
    "Salaries and wages: -Production staff (Incl Casuals)",
    "Salaries and wages: -Waitrons (Incl Casuals)",
    "Salaries and wages: -Director",
    "Salaries and wages: -Company portion UIF and SDL",
    "Staff transport",
    "Staff uniforms",
    "Staff meals",
    "Staff medical",
    "Telephone expenses",
    "Waste removal",
    "Total fixed overheads",
    "Electricity, water, refuse, sewerage and rates",
    "Insurance - HIC",
    "Insurance - Sanlam",
    "Rent paid",
    "Security expenses",
    "Marketing Fees",
    "Marketing general",
    "Spur Marketing fee",
    "Spur Franchise Fee",
    "Expenses grand total",
    "Nett Profit /(Loss)"
]

alias_mapping = {
    "nett turnover": ["net turnover"],
    "credit card commission paid": ["credit card comission paid"],
    "printing, stationery and menus": ["printing stationery and menus"],
    "donations": ["donations"],
    "salaries and wages: -management": ["-management"],
    "nett profit /(loss)": ["net profit / loss", "nett profit/loss"]
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
    """Enhanced PDF parser for your income statement format"""
    extracted_data = {}
    pdf_reader = PdfReader(pdf_bytes)
    full_text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())

    # Improved pattern to match both positive and negative amounts
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

def main():
    st.set_page_config(page_title="Silver Finance Dashboard", page_icon="💼", layout="wide")
    st.title("💰 Silver Finance Management System")
    
    df = load_data()
    
    with st.sidebar:
        st.header("Navigation")
        menu_choice = st.radio("Go to", ["Data Entry", "Financial Analysis"])
        
        st.header("PDF Import")
        uploaded_pdf = st.file_uploader("Upload Income Statement", type=["pdf"])
        if uploaded_pdf and PdfReader:
            if st.button("Process PDF"):
                parsed_data = parse_pdf_data(uploaded_pdf)
                if parsed_data:
                    month = st.date_input("Select Month for PDF Data", value=datetime.today().replace(day=1))
                    month_str = month.strftime("%Y-%m")
                    
                    # Check for existing entries
                    if month_str in df["month"].astype(str).values:
                        st.error(f"Data for {month_str} already exists!")
                    else:
                        new_row = pd.DataFrame([{**{"month": month_str}, **parsed_data}])
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        st.success("PDF data imported successfully!")
                else:
                    st.warning("No valid data found in PDF")

    if menu_choice == "Data Entry":
        st.header("Manual Data Entry")
        # ... (keep your manual entry form code)

    elif menu_choice == "Financial Analysis":
        st.header("Financial Analysis")
        if not df.empty:
            st.subheader("Cost Comparison Over Time")
            selected_fields = st.multiselect("Select Costs to Compare", fields_list, default=["Total cost of sales", "Gross profit"])
            
            fig = px.line(
                df, 
                x="month", 
                y=selected_fields,
                title="Cost Trend Analysis",
                labels={"value": "Amount (R)", "month": "Month"},
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Detailed Comparison")
            selected_month = st.selectbox("Select Month", df["month"].unique())
            month_data = df[df["month"] == selected_month].iloc[0]
            
            cols = st.columns(2)
            with cols[0]:
                st.metric("Total Costs", f"R{month_data['Total cost of sales']:,.2f}")
                st.write("### Cost Breakdown")
                cost_fields = [f for f in fields_list if "cost" in f.lower() or "expense" in f.lower()]
                for field in cost_fields:
                    if field in month_data and pd.notnull(month_data[field]):
                        st.write(f"{field}: R{month_data[field]:,.2f}")
            
            with cols[1]:
                st.metric("Net Profit", f"R{month_data['Nett Profit /(Loss)']:,.2f}")
                st.write("### Income Breakdown")
                income_fields = [f for f in fields_list if "income" in f.lower() or "turnover" in f.lower()]
                for field in income_fields:
                    if field in month_data and pd.notnull(month_data[field]):
                        st.write(f"{field}: R{month_data[field]:,.2f}")
        else:
            st.info("No data available for analysis")

if __name__ == "__main__":
    main()
