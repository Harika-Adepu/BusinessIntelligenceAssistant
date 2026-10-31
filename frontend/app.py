import streamlit as st
import requests
import pandas as pd
import plotly.express as px


st.set_page_config(
    page_title="Sales BI Assistant",
    page_icon="📊",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000/ask"

st.markdown("""
<style>
.main-title {
    font-size: 32px;
    font-weight: 700;
}
.subtitle {
    color: #808080;
    font-size: 16px;
}
.stButton button {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


st.markdown(
    '<div class="main-title">📊 AI Business Intelligence Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Ask questions about your sales data '
    'and get insights powered by AI and SQL.</div>',
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.title("About")

    st.write(
        "This assistant analyzes sales transactions "
        "using natural language questions."
    )

    st.subheader("Example Questions")

    examples = [
        "What is the total revenue?",
        "Which category generates the highest revenue?",
        "Show monthly revenue trends.",
        "Which region performs best?",
        "What is the average unit price?",
        "Which sales channel generates the most revenue?",
        "How many returned transactions are there?",
        "Compare revenue across regions."
    ]

    for example in examples:
        st.write("•", example)

    st.divider()

    st.caption("Powered by Gemini AI, FastAPI and SQLite")


st.subheader("Ask your sales question")

question = st.text_area(
    "Enter your question:",
    placeholder="Example: Which product generated the highest revenue?",
    height=100
)

ask_button = st.button(
    "🔍 Analyze",
    type="primary",
    use_container_width=True
)


if ask_button:

    if not question.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Analyzing your question..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=120
                )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state["result"] = result

                else:
                    try:
                        error = response.json().get(
                            "detail", "Something went wrong."
                        )
                    except ValueError:
                        error = response.text

                    st.error(f"Analysis failed: {error}")
                    st.session_state.pop("result", None)

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the backend. "
                    "Please start FastAPI first."
                )
                st.session_state.pop("result", None)

            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")

            except requests.exceptions.RequestException as e:
                st.error(f"Request error: {e}")

if "result" in st.session_state:

    result = st.session_state["result"]

    st.divider()

    st.subheader("💡 AI Analysis")

    st.success(result["answer"])

    st.markdown("**Question:** " + result["question"])

    with st.expander("View AI Query Interpretation"):
        st.json(result["intent"])


    st.subheader("📋 Supporting Data")

    data = result.get("supporting_data", [])

    if data:

        df = pd.DataFrame(data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


        if "value" in df.columns and len(df) > 1:

            group_columns = [
                col for col in df.columns if col != "value"
            ]

            if group_columns:

                chart_column = group_columns[0]

                st.subheader("📈 Data Visualization")

                chart_df = df.copy()

                fig = px.bar(
                    chart_df,
                    x=chart_column,
                    y="value",
                    title=f"{result['intent']['metric']} by {chart_column}",
                    text_auto=".2s"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Results",
            data=csv,
            file_name="sales_analysis.csv",
            mime="text/csv"
        )

    else:
        st.info("No supporting records found.")



st.divider()

st.caption(
    "AI Business Intelligence Assistant | "
    "Powered by Python, Gemini, FastAPI and SQLite"
)

