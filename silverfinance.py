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
            "Repairs and maintenance
