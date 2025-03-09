def main_app():
    st.title("💰 Silver Spur Financial Management")

    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except Exception:
        df = pd.DataFrame(columns=["Month"] + FIELDS)

    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.experimental_rerun()

        st.header("📤 Data Import")

        uploaded_pdf = st.file_uploader("Upload PDF Statement", type=["pdf"])
        if uploaded_pdf:
            st.write("### Select Statement Month")
            statement_month = select_statement_month("Statement Month")
            if st.button("✨ Process PDF"):
                data = parse_pdf(uploaded_pdf)
                if data:
                    new_row = {"Month": statement_month}
                    new_row.update(data)
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ PDF processed successfully!")

    threshold = send_alerts()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Line Graph", "📊 Bar Chart", "📅 Compare Months", "📋 Cost Analysis", "📝 Manual Entry", "📄 Data"])

    with tab1:
        if not df.empty:
            st.subheader("Financial Trends")
            selected_metrics = st.multiselect("Select Metrics", FIELDS, default=["Nett Profit /(Loss)"])
            fig = px.line(df, x="Month", y=selected_metrics, title="Performance Over Time")
            st.plotly_chart(fig)
            # Check for Alerts
            last_profit = df["Nett Profit /(Loss)"].iloc[-1]
            if last_profit < threshold:
                st.session_state.alerts.append(f"Nett Profit of R{last_profit:,.2f} is below the threshold!")
    
    with tab2:
        if not df.empty:
            st.subheader("Monthly Financials Bar Chart")
            selected_metrics = st.multiselect("Select Metrics", FIELDS, default=["Nett Profit /(Loss)"])
            fig = px.bar(df, x="Month", y=selected_metrics, title="Monthly Financials")
            st.plotly_chart(fig)

    with tab3:
        if not df.empty:
            st.subheader("Compare Months")
            months = sorted(df["Month"].unique())
            month1 = st.selectbox("Select First Month", months, index=0)
            month2 = st.selectbox("Select Second Month", months, index=1)
            selected_fields = st.multiselect("Select Fields to Compare", FIELDS, default=["Nett Profit /(Loss)"])
            data1 = df[df["Month"] == month1][selected_fields].iloc[0]
            data2 = df[df["Month"] == month2][selected_fields].iloc[0]
            comparison = pd.DataFrame({"Field": selected_fields, month1: data1.values, month2: data2.values})
            comparison["Difference"] = comparison[month2] - comparison[month1]
            fig = px.bar(comparison, x="Field", y="Difference", title="Comparison of Selected Fields")
            st.plotly_chart(fig)

    with tab4:
        if not df.empty:
            st.subheader("Cost Analysis")
            st.write("### Expense Breakdown")
            expenses = df[FIELDS[3:]]  # Exclude non-expense fields
            expense_totals = expenses.sum()
            fig = px.pie(names=expense_totals.index, values=expense_totals.values, title="Expense Breakdown")
            st.plotly_chart(fig)

            st.write("### Cost Correlations")
            corr = df[FIELDS].corr()
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)

    with tab5:
        with st.form("manual_entry"):
            st.subheader("✍️ Manual Data Entry")
            statement_month = select_statement_month("Entry Month")
            entries = {}

            st.write("### Income Section")
            income_fields = FIELDS[:10]
            inc_cols = st.columns(3)
            for i, field in enumerate(income_fields):
                with inc_cols[i % 3]:
                    entries[field] = st.number_input(field, value=0.0)

            st.write("### Expense Section")
            expense_fields = FIELDS[10:]
            exp_cols = st.columns(3)
            for i, field in enumerate(expense_fields):
                with exp_cols[i % 3]:
                    entries[field] = st.number_input(field, value=0.0)

            if st.form_submit_button("💾 Save Entry"):
                new_row = {"Month": statement_month}
                new_row.update(entries)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Entry saved!")

    with tab6:
        st.subheader("📄 Financial Records")
        st.dataframe(df.sort_values("Month", ascending=False))
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), "financial_data.csv")

if __name__ == "__main__":
    st.set_page_config(page_title="Silver Spur Analytics", layout="wide")
    if st.session_state.get("authenticated"):
        main_app()
    else:
        login_page()
def main_app():
    st.title("💰 Silver Spur Financial Management")

    try:
        df = pd.read_csv(DATA_FILE, parse_dates=["Month"])
    except Exception:
        df = pd.DataFrame(columns=["Month"] + FIELDS)

    with st.sidebar:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.experimental_rerun()

        st.header("📤 Data Import")

        uploaded_pdf = st.file_uploader("Upload PDF Statement", type=["pdf"])
        if uploaded_pdf:
            st.write("### Select Statement Month")
            statement_month = select_statement_month("Statement Month")
            if st.button("✨ Process PDF"):
                data = parse_pdf(uploaded_pdf)
                if data:
                    new_row = {"Month": statement_month}
                    new_row.update(data)
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ PDF processed successfully!")

    threshold = send_alerts()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Line Graph", "📊 Bar Chart", "📅 Compare Months", "📋 Cost Analysis", "📝 Manual Entry", "📄 Data"])

    with tab1:
        if not df.empty:
            st.subheader("Financial Trends")
            selected_metrics = st.multiselect("Select Metrics", FIELDS, default=["Nett Profit /(Loss)"])
            fig = px.line(df, x="Month", y=selected_metrics, title="Performance Over Time")
            st.plotly_chart(fig)
            # Check for Alerts
            last_profit = df["Nett Profit /(Loss)"].iloc[-1]
            if last_profit < threshold:
                st.session_state.alerts.append(f"Nett Profit of R{last_profit:,.2f} is below the threshold!")
    
    with tab2:
        if not df.empty:
            st.subheader("Monthly Financials Bar Chart")
            selected_metrics = st.multiselect("Select Metrics", FIELDS, default=["Nett Profit /(Loss)"])
            fig = px.bar(df, x="Month", y=selected_metrics, title="Monthly Financials")
            st.plotly_chart(fig)

    with tab3:
        if not df.empty:
            st.subheader("Compare Months")
            months = sorted(df["Month"].unique())
            month1 = st.selectbox("Select First Month", months, index=0)
            month2 = st.selectbox("Select Second Month", months, index=1)
            selected_fields = st.multiselect("Select Fields to Compare", FIELDS, default=["Nett Profit /(Loss)"])
            data1 = df[df["Month"] == month1][selected_fields].iloc[0]
            data2 = df[df["Month"] == month2][selected_fields].iloc[0]
            comparison = pd.DataFrame({"Field": selected_fields, month1: data1.values, month2: data2.values})
            comparison["Difference"] = comparison[month2] - comparison[month1]
            fig = px.bar(comparison, x="Field", y="Difference", title="Comparison of Selected Fields")
            st.plotly_chart(fig)

    with tab4:
        if not df.empty:
            st.subheader("Cost Analysis")
            st.write("### Expense Breakdown")
            expenses = df[FIELDS[3:]]  # Exclude non-expense fields
            expense_totals = expenses.sum()
            fig = px.pie(names=expense_totals.index, values=expense_totals.values, title="Expense Breakdown")
            st.plotly_chart(fig)

            st.write("### Cost Correlations")
            corr = df[FIELDS].corr()
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)

    with tab5:
        with st.form("manual_entry"):
            st.subheader("✍️ Manual Data Entry")
            statement_month = select_statement_month("Entry Month")
            entries = {}

            st.write("### Income Section")
            income_fields = FIELDS[:10]
            inc_cols = st.columns(3)
            for i, field in enumerate(income_fields):
                with inc_cols[i % 3]:
                    entries[field] = st.number_input(field, value=0.0)

            st.write("### Expense Section")
            expense_fields = FIELDS[10:]
            exp_cols = st.columns(3)
            for i, field in enumerate(expense_fields):
                with exp_cols[i % 3]:
                    entries[field] = st.number_input(field, value=0.0)

            if st.form_submit_button("💾 Save Entry"):
                new_row = {"Month": statement_month}
                new_row.update(entries)
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Entry saved!")

    with tab6:
        st.subheader("📄 Financial Records")
        st.dataframe(df.sort_values("Month", ascending=False))
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), "financial_data.csv")

if __name__ == "__main__":
    st.set_page_config(page_title="Silver Spur Analytics", layout="wide")
    if st.session_state.get("authenticated"):
        main_app()
    else:
        login_page()
