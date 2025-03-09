import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import re
from pypdf import PdfReader  # For PDF parsing
from github import Github  # For GitHub API integration

# Set page configuration as the first Streamlit command to avoid errors
st.set_page_config(page_title="Silver Finance", layout="wide")

# Configuration
DATA_FILE = "financial_data.csv"
CURRENCY_FORMAT = "R{:,.2f}"  # South African Rand currency format for display

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

# Aliases for category variations (to handle typos or formatting differences)
aliases = {
    "Nett turnover": ["net turnover"],
    "Credit card commission Paid": ["credit card comission paid"],
    "Printing, stationery and menus": ["printing stationery and menus"]
}

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False
if 'data' not in st.session_state:
    st.session_state.data = None

# Security functions
def authenticate(username: str, password: str) -> bool:
    """Authenticate user against credentials stored in st.secrets."""
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
                st.rerun()  # Refresh app after login
            else:
                st.error("Invalid credentials")

def logout():
    """Log out the user and refresh the app."""
    st.session_state.logged_in = False
    st.rerun()

# Data handling functions
@st.cache_data
def load_data():
    """Load financial data from CSV file."""
    try:
        df = pd.read_csv(DATA_FILE)
        df["month"] = df["month"].astype(str)
        for field in fields_list:
            df[field] = pd.to_numeric(df[field], errors='coerce')
        return df
    except FileNotFoundError:
        st.warning(f"{DATA_FILE} not found. Starting with an empty dataset.")
        return pd.DataFrame(columns=["month"] + fields_list)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(columns=["month"] + fields_list)

def save_data(df):
    """Save DataFrame to CSV and push to GitHub using SSH secret."""
    try:
        df.to_csv(DATA_FILE, index=False)
        st.session_state.data = df
        
        # GitHub API integration with SSH secret (replace with your repo details)
        g = Github(st.secrets["github"]["ssh_key"])
        repo = g.get_repo("yourusername/yourrepo")  # Update with your GitHub repo
        with open(DATA_FILE, "r") as file:
            content = file.read()
        # Update file in repo (requires existing file SHA)
        contents = repo.get_contents(DATA_FILE)
        repo.update_file(DATA_FILE, "Update financial_data.csv", content, contents.sha)
        return True
    except Exception as e:
        st.error(f"Error saving data to GitHub: {e}")
        return False

def append_row(month, data, df):
    """Append a new row to DataFrame if month doesn't exist."""
    if month in df["month"].values:
        st.error(f"Data for {month} already exists!")
        return df
    new_row = pd.DataFrame([[month] + [data[field] for field in fields_list]], 
                          columns=["month"] + fields_list)
    return pd.concat([df, new_row], ignore_index=True)

def clear_data(df):
    """Clear all data, returning an empty DataFrame."""
    return pd.DataFrame(columns=["month"] + fields_list)

def parse_pdf_data(pdf_bytes):
    """
    Parse financial data from PDF bytes, ensuring all categories are extracted.
    Reads all pages, uses regex for extraction, and maps categories with aliases.
    """
    # Read all pages of the PDF and combine text
    pdf_reader = PdfReader(pdf_bytes)
    full_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
    lines = full_text.split("\n")
    
    # Create field mapping with normalized field names and aliases
    field_mapping = {}
    for field in fields_list:
        normalized_field = " ".join(field.split()).strip().lower()
        field_mapping[normalized_field] = field
        for alias in aliases.get(field, []):
            normalized_alias = " ".join(alias.split()).strip().lower()
            field_mapping[normalized_alias] = field
    
    extracted_data = {}
    # Regex pattern to match category name followed by "R" and value (e.g., "R 16,371.24")
    pattern = r"^(.*?)\s+R\s+([\d,]+\.\d{2})"
    
    for line in lines:
        match = re.search(pattern, line)
        if match:
            # Extract and normalize category name
            category = match.group(1).strip()
            normalized_category = " ".join(category.split()).lower()
            # Extract and convert value to float
            value_str = match.group(2).replace(",", "").strip()
            try:
                value = float(value_str)
                # Map normalized category to original field name
                if normalized_category in field_mapping:
                    original_field = field_mapping[normalized_category]
                    extracted_data[original_field] = value
                else:
                    st.warning(f"Category '{category}' not found in fields_list or aliases")
            except ValueError:
                continue  # Skip if value can't be converted to float
    
    # Optional: Log extracted and missing fields for debugging
    missing_fields = [field for field in fields_list if field not in extracted_data]
    if missing_fields:
        st.info(f"Extracted {len(extracted_data)} fields. Missing: {', '.join(missing_fields)}")
    else:
        st.success("All fields extracted successfully!")
    
    return extracted_data

def manual_entry_form(df):
    """Form for manual data entry, split into income and expenses."""
    with st.expander("📝 Manual Data Entry", expanded=True):
        with st.form("manual_form", clear_on_submit=True):
            month = st.date_input("Report Month", value=datetime.today().replace(day=1)).strftime("%Y-%m")
            manual_data = {}

            st.subheader("Income Section")
            cols = st.columns(3)
            for i, field in enumerate(fields_list[:15]):  # Adjust split based on your fields
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
    """Main app with sidebar and tabs for data entry, analysis, and management."""
    st.title("💰 Silver Finance Management")
    # Load data if not already in session state
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
                    st.error("No data extracted from PDF. Check file format.")
                else:
                    month_str = pdf_month.strftime("%Y-%m")
                    full_data = {field: parsed_data.get(field, 0.0) for field in fields_list}
                    df = append_row(month_str, full_data, df)
                    if save_data(df):
                        st.success(f"PDF processed and data for {month_str} saved!")

    tab1, tab2, tab3 = st.tabs(["Data Entry", "Analysis", "Management"])

    with tab1:
        df = manual_entry_form(df)
        st.session_state.data = df

    with tab2:
        if not df.empty:
            selected_metrics = st.multiselect("Metrics for Trend Analysis", 
                                            fields_list, default=["Nett Profit /(Loss)"])
            fig = px.line(df.sort_values("month"), x=pd.to_datetime(df["month"] + '-01'), 
                         y=selected_metrics, title="Financial Trends")
            fig.update_layout(xaxis_title="Month", yaxis_title="Amount (R)")
            st.plotly_chart(fig)

            unique_months = sorted(df["month"].unique())
            selected_month = st.selectbox("Select Month to View", ["All"] + unique_months)
            display_df = df if selected_month == "All" else df[df["month"] == selected_month]
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
        format_dict = {field: CURRENCY_FORMAT for field in fields_list}
        st.dataframe(df.style.format(format_dict))

def main():
    """Entry point for the Streamlit app."""
    if not st.session_state.logged_in:
        login_form()
    else:
        main_app()

if __name__ == "__main__":
    main()
