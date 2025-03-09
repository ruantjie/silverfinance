import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
from pypdf import PdfReader  # For PDF parsing

# Configuration
CSV_FILE_PATH = "financial_data.csv"  # Path to the CSV in the GitHub repo
CURRENCY_FORMAT = "R{:,.2f}"  # Currency format (South African Rand)

# Financial fields list
fields_list = [
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
    "Hire of Equipment", "Interest paid", "Kids Entertainment", "Legal and Licence fees",
    "Printing, stationery and menus", "Packaging cost", "Repairs and maintenance",
    "Salaries and wages: -Management", "Salaries and wages: -Production staff (Incl Casuals)",
    "Salaries and wages: -Waitrons (Incl Casuals)", "Salaries and wages: -Director",
    "Salaries and wages: -Company portion UIF and SDL", "Staff transport", "Staff uniforms",
    "Staff meals", "Staff medical", "Telephone expenses", "Waste removal",
    "Total fixed overheads", "Electricity, water, refuse, sewerage and rates",
    "Insurance - HIC", "Insurance - Sanlam", "Rent paid", "Security expenses",
    "Marketing Fees", "Marketing general", "Spur Marketing fee", "Spur Franchise Fee",
    "Expenses grand total", "Nett Profit /(Loss)"
]

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False
if 'data' not in st.session_state:
    st.session_state.data = None

# Security functions
def authenticate(username: str, password: str) -> bool:
    """Authenticate user against credentials from st.secrets."""
    return (username == st.secrets["credentials"]["username"] and
            password == st.secrets["credentials"]["password"])

def login_form():
    """Display login form and handle authentication."""
    with st.form("Login"):
        st.subheader("Silver Finance Login 🔒")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

def logout():
    """Log out the user and refresh the app."""
    st.session_state.logged_in = False
    st.rerun()

# Data handling functions
@st.cache_data
def load_data():
    """Load financial data from the CSV file in the repo."""
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        df["month"] = df["month"].astype(str)
        for field in fields_list:
            df[field] = pd.to_numeric(df[field], errors='coerce')
        return df
    except FileNotFoundError:
        st.warning(f"{CSV_FILE_PATH} not found. Starting with an empty dataset.")
        return pd.DataFrame(columns=["month"] + fields_list)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=["month"] + fields_list)

def save_data(df):
    """Save the updated DataFrame to a temporary file."""
    try:
        df.to_csv(CSV_FILE_PATH, index=False)
        st.session_state.data = df  # Update session state
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def append_row(month, data, df):
    """Append a new row to the DataFrame if the month doesn’t exist."""
    if month in df["month"].values:
        st.error(f"Data for {month} already exists!")
        return df
    new_row = pd.DataFrame([[month] + [data[field] for field in fields_list]], columns=["month"] + fields_list)
    df = pd.concat([df, new_row], ignore_index=True)
    return df

def clear_data(df):
    """Clear all data, returning an empty DataFrame with the correct columns."""
    return pd.DataFrame(columns=["month"] + fields_list)

def parse_pdf_data(pdf_bytes) -> dict:
    """Parse financial data from PDF bytes using regex."""
    extracted_data = {}
    pdf_reader = PdfReader(pdf_bytes)
    full_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
    
    amount_pattern = r"R?\s*(-?\s*\d{1,3}(?:,\d{3})*\.\d{2})"
    for field in fields_list:
        search_terms = [field.lower()] + [
            alias.lower() for alias in {
                "nett turnover": ["net turnover"],
                "credit card commission paid": ["credit card comission paid"],
                "printing, stationery and menus": ["printing stationery and menus"]
            }.get(field, [])
        ]
        pattern = re.compile(rf"({'|'.join(search_terms)}).*?{amount_pattern}", re.IGNORECASE|re.DOTALL)
        match = pattern.search(full_text)
        if match:
            try:
                amount = float(match.group(2).replace(" ", "").replace(",", ""))
                extracted_data[field] = amount
            except:
                continue
    return extracted_data

def manual_entry_form(df):
    """Form for manual data entry with income and expenses sections."""
    with st.expander("📝 Manual Data Entry", expanded=True):
        with st.form("manual_form", clear_on_submit=True):
            month = st.date_input("Report Month", value=datetime.today().replace(day=1)).strftime("%Y-%m")
            manual_data = {}

            st.subheader("Income Section")
            cols = st.columns(3)
            for i, field in enumerate(fields_list[:15]):
                with cols[i % 3]:
                    manual_data[field] = st.number_input(field, value=0.0, step=1000.0)

            st.subheader("Expenses Section")
            exp_cols = st.columns(3)
            for i, field in enumerate(fields_list[15:]):
                with exp_cols[i % 3]:
                    manual_data[field] = st.number_input(field, value=0.0, step=1000.0)

            if st.form_submit_button("💾 Save Entry"):
                df = append_row(month, manual_data, df)
                if save_data(df):
                    st.success(f"Entry for {month} saved!")
    return df

def main_app():
    """Main application with sidebar and tabs."""
    st.title("💰 Silver Finance Management")
    # Load data into session state if not already loaded
    if st.session_state.data is None:
        st.session_state.data = load_data()
    df = st.session_state.data

    with st.sidebar:
        if st.button("🚪 Logout"):
            logout()
        
        st.header("Data Import")
        with st.expander("📄 Upload PDF"):
            uploaded_pdf = st.file_uploader("PDF File", type=["pdf"])
            pdf_month = st.date_input("Statement Month", value=datetime.today().replace(day=1))
            if uploaded_pdf and st.button("Process PDF"):
                parsed_data = parse_pdf_data(uploaded_pdf)
                if not parsed_data:
                    st.error("No data extracted from the PDF. Please check the file format.")
                else:
                    month_str = pdf_month.strftime("%Y-%m")
                    full_data = {field: parsed_data.get(field, 0.0) for field in fields_list}
                    df = append_row(month_str, full_data, df)
                    if save_data(df):
                        st.success(f"PDF processed and data for {month_str} saved!")

    tab1, tab2, tab3 = st.tabs(["Data Entry", "Analysis", "Management"])

    with tab1:
        df = manual_entry_form(df)
        st.session_state.data = df  # Update session state

    with tab2:
        if not df.empty:
            selected_metrics = st.multiselect("Metrics for Trend Analysis", fields_list, default=["Nett Profit /(Loss)"])
            # Plot trends over all months
            fig = px.line(df.sort_values("month"), x=pd.to_datetime(df["month"] + '-01'), y=selected_metrics, title="Financial Trends")
            fig.update_layout(xaxis_title="Month", yaxis_title="Amount (R)")
            st.plotly_chart(fig)

            # Month selector for detailed view
            unique_months = sorted(df["month"].unique())
            selected_month = st.selectbox("Select Month to View", ["All"] + unique_months)
            if selected_month == "All":
                display_df = df
            else:
                display_df = df[df["month"] == selected_month]
            # Format numbers with currency
            format_dict = {field: CURRENCY_FORMAT for field in fields_list}
            st.dataframe(display_df.style.format(format_dict))

            st.download_button("Download Data as CSV", df.to_csv(index=False), "financial_data.csv")
        else:
            st.info("No data available")

    with tab3:
        if st.button("Clear All Data"):
            st.session_state.confirm_clear = True
        
        if st.session_state.confirm_clear:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Deletion"):
                    df = clear_data(df)
                    save_data(df)
                    st.session_state.confirm_clear = False
                    st.success("All data cleared!")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_clear = False
        # Display entire dataset
        format_dict = {field: CURRENCY_FORMAT for field in fields_list}
        st.dataframe(df.style.format(format_dict))

def main():
    """Entry point for the Streamlit app."""
    st.set_page_config(page_title="Silver Finance", layout="wide")
    if not st.session_state.logged_in:
        login_form()
    else:
        main_app()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
