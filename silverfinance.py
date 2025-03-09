import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from pypdf import PdfReader

# 🔒 Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# 📁 Complete Field List from PDF
FIELDS = [
    "Gross turnover", "Less VAT", "Nett turnover", "Total cost of sales",
    "Beverages", "Bread and rolls", "Butter and cheese", "Chicken", "Chips",
    "Dairy", "Delivery expenses", "Desserts", "Fish", "Fruit and veg", "Garnish",
    "Groceries", "Hot beverages", "Ice-cream", "Liquor - beer and cider",
    "Liquor - spirits", "Liquor - wine", "Meat", "Mushrooms", "Oil", "Ribs",
    "Premade Sauces", "Spur sauces", "Gross profit", "Other income",
    "Breakages recovery", "Interest received", "Transport", "Refund on old oil",
    "Total variable overheads", "Accounting and audit fees", "Bank charges",
    "Breakages and replacements", "Cleaning and pest control", "Computer expenses",
    "Credit card commission Paid", "Donations", "Entertainment Costs", "General gas",
    "Interest paid", "Legal and Licence fees", "Printing, stationery and menus",
    "Repairs and maintenance", "Salaries and wages: -Management",
    "Salaries and wages: -Production staff (Incl Casuals)",
    "Salaries and wages: -Waitrons (Incl Casuals)", "Salaries and wages: -Director",
    "Salaries and wages: -Company portion UIF and SDL", "Staff transport",
    "Staff uniforms", "Staff meals", "Staff medical", "Staff welfare",
    "Telephone expenses", "Waste removal", "Total fixed overheads",
    "Electricity, water, refuse, sewerage and rates", "Insurance - HIC",
    "Insurance - Sanlam", "Rent paid", "Security expenses", "Marketing Fees",
    "Marketing general", "Spur Marketing fee", "Spur Franchise Fee",
    "Expenses grand total", "Nett Profit /(Loss)"
]

DATA_FILE = "restaurant_finances.csv"

def login_page():
    with st.form("auth"):
        st.title("🍽 Silver Spur Analytics")
        st.subheader("🔒 Restaurant Financial Portal")
        user = st.text_input("👤 Username")
        pwd = st.text_input("🔑 Password", type="password")
        if st.form_submit_button("🚪 Login"):
            if user == "Silver" and pwd == "Silver@123":
                st.session_state.authenticated = True
                st.rerun()

def parse_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "\n".join(page.extract_text() for page in reader.pages)
        
        # Enhanced parsing with multi-line handling
        amounts = {}
        lines = re.split(r'\n\s*', text)
        
        for i, line in enumerate(lines):
            line = re.sub(r'\s+', ' ', line).strip()
            for field in FIELDS:
                pattern = re.compile(
                    rf"{re.escape(field)}\s*(?:R|%|:)?\s*([\d,]+\.\d{{2}})", 
                    re.IGNORECASE
                )
                match = pattern.search(line)
                if match and field not in amounts:
                    try:
                        value = float(match.group(1).replace(',', ''))
                        amounts[field] = value
                    except:
                        continue
                # Check next line for amount if field match found
                elif field.lower() in line.lower() and i+1 < len(lines):
                    next_line = lines[i+1]
                    amount_match = re.search(r'R?\s*([\d,]+\.\d{2})', next_line)
                    if amount_match and field not in amounts:
                        try:
                            value = float(amount_match.group(1).replace(',', ''))
                            amounts[field] = value
                        except:
                            continue
        return amounts
    except Exception as e:
        st.error(f"📄 PDF Error: {str(e)}")
        return {}

def main_app():
    st.title("💰 Silver Spur Financial Management")
    
    # Load data
    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except:
        df = pd.DataFrame(columns=["Month"] + FIELDS)

    # Sidebar controls
    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.rerun()
            
        st.header("📤 Data Import")
        uploaded_pdf = st.file_uploader("Upload PDF Statement", type=["pdf"])
        if uploaded_pdf and st.button("✨ Process PDF"):
            data = parse_pdf(uploaded_pdf)
            if data:
                month = st.date_input("🗓 Statement Month")
                new_row = {"Month": month.strftime("%Y-%m")}
                new_row.update(data)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("✅ PDF processed successfully!")

    # Main interface
    tab1, tab2, tab3 = st.tabs(["📈 Analysis", "📝 Manual Entry", "📋 Data"])

    with tab1:
        if not df.empty:
            st.subheader("Financial Trends")
            selected = st.multiselect("Select Metrics", FIELDS, default=["Nett Profit /(Loss)"])
            fig = px.line(df, x="Month", y=selected, title="Performance Over Time")
            st.plotly_chart(fig)
            
            st.subheader("Category Breakdown")
            selected_month = st.selectbox("Select Month", df["Month"].unique())
            month_data = df[df["Month"] == selected_month].iloc[0]
            cols = st.columns(2)
            with cols[0]:
                st.metric("Total Income", f"R{month_data['Nett turnover']:,.2f}")
                st.write("### Income Details")
                st.write(f"Gross Turnover: R{month_data['Gross turnover']:,.2f}")
                st.write(f"Other Income: R{month_data['Other income']:,.2f}")
            with cols[1]:
                st.metric("Net Profit", f"R{month_data['Nett Profit /(Loss)']:,.2f}")
                st.write("### Expense Highlights")
                st.write(f"Total Costs: R{month_data['Total cost of sales']:,.2f}")
                st.write(f"Staff Costs: R{month_data['Salaries and wages: -Management'] + month_data['Salaries and wages: -Production staff (Incl Casuals)']:,.2f}")

    with tab2:
        with st.form("manual_entry"):
            st.subheader("✍️ Manual Data Entry")
            month = st.date_input("Month")
            entries = {}
            
            st.write("### Income Section")
            cols = st.columns(3)
            for i, field in enumerate(FIELDS[:10]):
                with cols[i%3]:
                    entries[field] = st.number_input(field, value=0.0)
            
            st.write("### Expense Section")
            cols = st.columns(3)
            for i, field in enumerate(FIELDS[10:]):
                with cols[i%3]:
                    entries[field] = st.number_input(field, value=0.0)
            
            if st.form_submit_button("💾 Save Entry"):
                new_row = {"Month": month.strftime("%Y-%m")}
                new_row.update(entries)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Entry saved!")

    with tab3:
        st.subheader("📄 Financial Records")
        st.dataframe(df.sort_values("Month", ascending=False))
        st.download_button("⬇️ Download CSV", df.to_csv(), "financial_data.csv")

if __name__ == "__main__":
    st.set_page_config(page_title="Silver Spur Analytics", layout="wide")
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()
        main_interface()
    else:
        login_section()
