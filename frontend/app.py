
# import streamlit as st
# import requests
# import pandas as pd
# import plotly.express as px


# # --------------------------------------------------
# # PAGE CONFIGURATION
# # --------------------------------------------------

# st.set_page_config(
#     page_title="Sales BI Assistant",
#     page_icon="📊",
#     layout="wide"
# )

# API_URL = "http://127.0.0.1:8000/ask"


# # --------------------------------------------------
# # HELPER FUNCTIONS
# # --------------------------------------------------

# def format_category(value):
#     """Convert technical date labels into readable labels."""

#     value = str(value)

#     # Convert YYYY-MM into Month Year
#     try:
#         return pd.to_datetime(
#             value,
#             format="%Y-%m",
#             errors="raise"
#         ).strftime("%B %Y")
#     except (ValueError, TypeError):
#         pass

#     # Convert YYYY-MM-DD into a readable date
#     try:
#         return pd.to_datetime(
#             value,
#             format="%Y-%m-%d",
#             errors="raise"
#         ).strftime("%d %B %Y")
#     except (ValueError, TypeError):
#         pass

#     return value


# def format_column_name(column):
#     """Make column names user-friendly."""

#     return str(column).replace("_", " ").title()


# def format_value(value):
#     """Format numerical values for display."""

#     if pd.isna(value):
#         return "N/A"

#     return f"{value:,.2f}"


# # --------------------------------------------------
# # CUSTOM STYLING
# # --------------------------------------------------

# st.markdown("""
# <style>
# .main-title {
#     font-size: 32px;
#     font-weight: 700;
# }
# .subtitle {
#     color: #808080;
#     font-size: 16px;
# }
# .stButton button {
#     border-radius: 8px;
# }
# </style>
# """, unsafe_allow_html=True)


# # --------------------------------------------------
# # HEADER
# # --------------------------------------------------

# st.markdown(
#     '<div class="main-title">📊 Sales BI Assistant</div>',
#     unsafe_allow_html=True
# )

# st.markdown(
#     '<div class="subtitle">'
#     'Ask questions about your sales data and discover meaningful business insights.'
#     '</div>',
#     unsafe_allow_html=True
# )

# st.divider()


# # --------------------------------------------------
# # SIDEBAR
# # --------------------------------------------------

# with st.sidebar:

#     st.title("About")

#     st.write(
#         "Your sales analytics assistant. "
#         "Explore business performance using natural language questions."
#     )

#     st.subheader("Example Questions")

#     examples = [
#         "What is the total revenue?",
#         "Which product generates the highest revenue?",
#         "Show monthly revenue trends.",
#         "Which region performs best?",
#         "What is the average unit price?",
#         "Which sales channel generates the most revenue?",
#         "How many returned transactions are there?",
#         "Compare revenue across regions."
#     ]

#     for example in examples:
#         st.write("•", example)

#     st.divider()

#     st.caption("Powered by Gemini AI, FastAPI and SQLite")


# # --------------------------------------------------
# # QUESTION INPUT
# # --------------------------------------------------

# st.subheader("Ask your sales question")

# with st.form("question_form"):

#     question = st.text_area(
#         "Enter your question:",
#         placeholder="Example: Which product generated the highest revenue?",
#         height=100
#     )

#     ask_button = st.form_submit_button(
#         "🔍 Analyze",
#         type="primary",
#         use_container_width=True
#     )


# # --------------------------------------------------
# # API REQUEST
# # --------------------------------------------------

# if ask_button:

#     # Clear previous result for every new question
#     st.session_state.pop("result", None)

#     if not question.strip():

#         st.warning("Please enter a question.")

#     else:

#         with st.spinner("Analyzing your sales data..."):

#             try:

#                 response = requests.post(
#                     API_URL,
#                     json={"question": question.strip()},
#                     timeout=120
#                 )

#                 if response.status_code == 200:

#                     st.session_state["result"] = response.json()

#                 else:

#                     try:
#                         error = response.json().get(
#                             "detail",
#                             "Unable to complete your analysis."
#                         )
#                     except ValueError:
#                         error = response.text

#                     st.error(f"Analysis failed: {error}")

#             except requests.exceptions.ConnectionError:

#                 st.error(
#                     "Cannot connect to the analytics service. "
#                     "Please start FastAPI first."
#                 )

#             except requests.exceptions.Timeout:

#                 st.error(
#                     "The request timed out. Please try again."
#                 )

#             except requests.exceptions.RequestException as e:

#                 st.error(f"Request error: {e}")


# # --------------------------------------------------
# # DISPLAY RESULTS
# # --------------------------------------------------

# if "result" in st.session_state:

#     result = st.session_state["result"]

#     st.divider()

#     # ----------------------------------------------
#     # BUSINESS INSIGHT
#     # ----------------------------------------------

#     st.subheader("💡 Business Insight")

#     st.success(
#         result.get(
#             "answer",
#             "Analysis completed successfully."
#         )
#     )

#     # ----------------------------------------------
#     # SUPPORTING DATA
#     # ----------------------------------------------

#     data = result.get("supporting_data", [])

#     if data:

#         df = pd.DataFrame(data)

#         # Create a separate display dataframe
#         # Keep original df unchanged for calculations
#         display_df = df.copy()

#         # Format date/category labels consistently
#         for col in display_df.columns:

#             if (
#                 display_df[col].dtype == "object"
#                 or pd.api.types.is_string_dtype(display_df[col])
#             ):

#                 display_df[col] = display_df[col].apply(
#                     format_category
#                 )

#         # Friendly column names
#         display_df.columns = [
#             format_column_name(col)
#             for col in display_df.columns
#         ]

#         st.subheader("📋 Detailed Results")

#         st.dataframe(
#             display_df,
#             use_container_width=True,
#             hide_index=True
#         )

#         # ------------------------------------------
#         # IDENTIFY RESULT COLUMNS
#         # ------------------------------------------

#         numeric_columns = df.select_dtypes(
#             include="number"
#         ).columns.tolist()

#         category_columns = [
#             col for col in df.columns
#             if col not in numeric_columns
#         ]

#         intent = result.get("intent", {})
#         metric = intent.get("metric", "result")
#         metric_name = format_column_name(metric)

#         # ------------------------------------------
#         # DATA VISUALIZATION
#         # ------------------------------------------

#         if (
#             numeric_columns
#             and category_columns
#             and len(df) > 1
#         ):

#             value_column = numeric_columns[0]
#             category_column = category_columns[0]

#             st.subheader("📈 Data Visualization")

#             chart_df = df.copy()

#             chart_df[category_column] = chart_df[
#                 category_column
#             ].apply(format_category)

#             fig = px.bar(
#                 chart_df,
#                 x=category_column,
#                 y=value_column,
#                 title=(
#                     f"{format_column_name(value_column)} "
#                     f"by {format_column_name(category_column)}"
#                 ),
#                 text_auto=".2s",
#                 labels={
#                     category_column: format_column_name(category_column),
#                     value_column: format_column_name(value_column)
#                 }
#             )

#             fig.update_layout(
#                 xaxis_title=None,
#                 yaxis_title=None,
#                 showlegend=False
#             )

#             st.plotly_chart(
#                 fig,
#                 use_container_width=True
#             )

#         # ------------------------------------------
#         # FINAL ANSWER / COMPARISON
#         # ------------------------------------------

#         st.divider()

#         st.subheader("🎯 Final Answer")

#         if numeric_columns:

#             value_column = numeric_columns[0]

#             if len(df) == 1:

#                 # Single aggregate result
#                 value = df.iloc[0][value_column]

#                 st.success(
#                     f"**{metric_name}:** {format_value(value)}"
#                 )

#             elif category_columns:

#                 # Grouped comparison
#                 category_column = category_columns[0]

#                 valid_df = df.dropna(
#                     subset=[value_column, category_column]
#                 )

#                 if not valid_df.empty:

#                     highest_row = valid_df.loc[
#                         valid_df[value_column].idxmax()
#                     ]

#                     lowest_row = valid_df.loc[
#                         valid_df[value_column].idxmin()
#                     ]

#                     highest_name = format_category(
#                         highest_row[category_column]
#                     )

#                     lowest_name = format_category(
#                         lowest_row[category_column]
#                     )

#                     highest_value = highest_row[value_column]
#                     lowest_value = lowest_row[value_column]

#                     # Final conclusion
#                     st.success(
#                         f"**{highest_name}** has the highest "
#                         f"{metric_name}, with "
#                         f"**{format_value(highest_value)}**."
#                     )

#                     # Comparison details
#                     with st.expander("View comparison details"):

#                         col1, col2 = st.columns(2)

#                         with col1:

#                             st.metric(
#                                 "Highest",
#                                 highest_name,
#                                 format_value(highest_value)
#                             )

#                         with col2:

#                             st.metric(
#                                 "Lowest",
#                                 lowest_name,
#                                 format_value(lowest_value)
#                             )

#                 else:

#                     st.info(
#                         "No valid values are available for comparison."
#                     )

#             else:

#                 st.info(
#                     "Your analysis results are displayed above."
#                 )

#         else:

#             st.info(
#                 "Your analysis results are displayed in the table above."
#             )

#         # ------------------------------------------
#         # DOWNLOAD RESULTS
#         # ------------------------------------------

#         csv = display_df.to_csv(
#             index=False
#         ).encode("utf-8")

#         st.download_button(
#             "⬇️ Download Results",
#             data=csv,
#             file_name="sales_analysis.csv",
#             mime="text/csv"
#         )

#     else:

#         st.info(
#             "No supporting records were returned for this question."
#         )


# # --------------------------------------------------
# # FOOTER
# # --------------------------------------------------

# st.divider()

# st.caption(
#     "Sales BI Assistant | "
#     "Turning sales data into business insights"
# )




import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Sales BI Assistant",
    page_icon="📊",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000/ask"


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "result" not in st.session_state:
    st.session_state.result = None

if "last_question" not in st.session_state:
    st.session_state.last_question = ""


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def get_response_data(response):
    """
    Extract result data from different possible API response formats.
    Supports data, results, records, and rows.
    """

    if not isinstance(response, dict):
        return None

    for key in ["data", "results", "records", "rows"]:
        value = response.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            return [value]

    return None


def get_query_plan(response):
    """
    Extract the AI-generated query interpretation.
    """

    if not isinstance(response, dict):
        return {}

    return (
        response.get("query_plan")
        or response.get("plan")
        or response.get("interpretation")
        or {}
    )


def get_metric_name(response, df):
    """
    Identify the metric using backend metadata.
    Falls back to the first numeric column.
    """

    plan = get_query_plan(response)

    metric = plan.get("metric")

    if metric and metric in df.columns:
        return metric

    summary = response.get("summary", {})

    if isinstance(summary, dict):
        metric = summary.get("metric")

        if metric in df.columns:
            return metric

    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    return numeric_columns[0] if numeric_columns else None


def get_group_column(response, df, metric):
    """
    Identify the grouping column using backend metadata.
    Falls back to a non-numeric column.
    """

    plan = get_query_plan(response)

    group_by = plan.get("group_by", [])

    if isinstance(group_by, str):
        group_by = [group_by]

    for column in group_by:
        if column in df.columns:
            return column

    summary = response.get("summary", {})

    if isinstance(summary, dict):
        group_column = summary.get("group_by")

        if group_column in df.columns:
            return group_column

    categorical_columns = [
        column for column in df.columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]

    return categorical_columns[0] if categorical_columns else None


def format_category(value):
    """
    Convert date labels into readable formats.
    Examples:
        2026-05 -> May 2026
        2026-05-12 -> 12 May 2026
    """

    value = str(value)

    for date_format, output_format in [
        ("%Y-%m", "%B %Y"),
        ("%Y-%m-%d", "%d %B %Y")
    ]:
        try:
            return datetime.strptime(value, date_format).strftime(
                output_format
            )
        except ValueError:
            continue

    return value


def format_column_name(column):
    return str(column).replace("_", " ").title()


def format_dataframe(df):
    """
    Prepare a display copy without modifying original data.
    """

    display_df = df.copy()

    for column in display_df.columns:
        if (
            pd.api.types.is_object_dtype(display_df[column])
            or pd.api.types.is_string_dtype(display_df[column])
        ):
            display_df[column] = display_df[column].apply(
                lambda value: (
                    format_category(value)
                    if pd.notna(value)
                    else value
                )
            )

    display_df.columns = [
        format_column_name(column)
        for column in display_df.columns
    ]

    return display_df


def format_number(value):
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)


def get_record_count(response, df):
    """
    Get the number of returned records from backend metadata.
    """

    for key in ["record_count", "total_records", "count"]:
        value = response.get(key)

        if isinstance(value, (int, float)):
            return int(value)

    if df is not None:
        return len(df)

    return None


def get_summary(response):
    """
    Extract backend-generated summary information.
    """

    summary = response.get("summary", {})

    if isinstance(summary, str):
        return summary

    if isinstance(summary, dict):
        return summary.get("text") or summary.get("answer")

    return None


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.title("📊 Sales BI Assistant")

st.caption(
    "Ask questions about your sales data in natural language. "
    "Explore business insights, trends, comparisons, and transaction details."
)

st.divider()


# --------------------------------------------------
# QUESTION INPUT
# --------------------------------------------------

with st.form("question_form"):

    question = st.text_area(
        "Ask your business question",
        placeholder=(
            "For example: What insights can you find in the sales data?"
        ),
        height=100
    )

    submitted = st.form_submit_button(
        "Analyze",
        type="primary",
        use_container_width=True
    )


# --------------------------------------------------
# API REQUEST
# --------------------------------------------------

if submitted:

    if not question.strip():
        st.warning("Please enter a question.")
    else:

        # Remove the previous result before starting a new analysis.
        st.session_state.result = None
        st.session_state.last_question = question.strip()

        with st.spinner("Analyzing your question and retrieving results..."):

            try:
                response = requests.post(
                    API_URL,
                    json={"question": question.strip()},
                    timeout=120
                )

                response.raise_for_status()

                result = response.json()

                if not isinstance(result, dict):
                    raise ValueError(
                        "The backend returned an unexpected response."
                    )

                if result.get("error"):
                    st.error(result["error"])

                elif result.get("supported") is False:
                    st.warning(
                        result.get(
                            "answer",
                            "This question could not be answered from the available data."
                        )
                    )

                else:
                    st.session_state.result = result

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the backend. "
                    "Please make sure the FastAPI server is running."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "The request took too long. Please try again."
                )

            except requests.exceptions.HTTPError as error:
                st.error(
                    f"API request failed: {error}"
                )

                try:
                    st.code(response.text)
                except Exception:
                    pass

            except (ValueError, json.JSONDecodeError) as error:
                st.error(
                    f"Could not process the backend response: {error}"
                )

            except Exception as error:
                st.error(
                    f"Unexpected error: {error}"
                )


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

result = st.session_state.result

if result:

    st.divider()

    # ----------------------------------------------
    # FINAL ANSWER
    # ----------------------------------------------

    st.subheader("💡 Analysis Result")

    answer = result.get("answer")

    if answer:
        st.markdown(answer)

    summary = get_summary(result)

    if summary and summary != answer:
        st.info(summary)

    st.caption(
        f"Question: {st.session_state.last_question}"
    )

    # ----------------------------------------------
    # EXTRACT RESULT DATA
    # ----------------------------------------------

    data = get_response_data(result)

    df = None

    if data is not None:
        try:
            df = pd.DataFrame(data)
        except Exception:
            df = None

    # ----------------------------------------------
    # RESULT COUNT
    # ----------------------------------------------

    record_count = get_record_count(result, df)

    if record_count is not None:
        st.metric(
            "Records returned",
            f"{record_count:,}"
        )

    # ----------------------------------------------
    # NO TABULAR DATA
    # ----------------------------------------------

    if df is None or df.empty:

        if not answer:
            st.info(
                "The backend did not return any displayable records."
            )

    else:

        # ------------------------------------------
        # DISPLAY DATA TABLE
        # ------------------------------------------

        st.subheader("📋 Retrieved Data")

        display_df = format_dataframe(df)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # DOWNLOAD RESULTS
        # ------------------------------------------

        csv_data = display_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Results as CSV",
            data=csv_data,
            file_name="sales_analysis_results.csv",
            mime="text/csv"
        )

        # ------------------------------------------
        # DETERMINE METRIC AND GROUPING
        # ------------------------------------------

        metric_column = get_metric_name(result, df)

        group_column = get_group_column(
            result,
            df,
            metric_column
        )

        # ------------------------------------------
        # AUTOMATIC COMPARISON AND RANKING
        # ------------------------------------------

        is_grouped_analysis = (
            metric_column is not None
            and group_column is not None
            and len(df) > 1
        )

        if is_grouped_analysis:

            comparison_df = df[
                [group_column, metric_column]
            ].copy()

            comparison_df[metric_column] = pd.to_numeric(
                comparison_df[metric_column],
                errors="coerce"
            )

            comparison_df = comparison_df.dropna(
                subset=[metric_column]
            )

            if not comparison_df.empty:

                comparison_df = comparison_df.sort_values(
                    by=metric_column,
                    ascending=False
                ).reset_index(drop=True)

                best_row = comparison_df.iloc[0]
                worst_row = comparison_df.iloc[-1]

                best_label = format_category(
                    best_row[group_column]
                )

                worst_label = format_category(
                    worst_row[group_column]
                )

                best_value = best_row[metric_column]
                worst_value = worst_row[metric_column]

                st.divider()

                st.subheader("🏆 Performance Comparison")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        label=f"Top Performer: {best_label}",
                        value=format_number(best_value)
                    )

                with col2:
                    st.metric(
                        label=f"Lowest Performer: {worst_label}",
                        value=format_number(worst_value)
                    )

                # ----------------------------------
                # RANKED COMPARISON TABLE
                # ----------------------------------

                ranked_df = comparison_df.copy()

                ranked_df.insert(
                    0,
                    "Rank",
                    range(1, len(ranked_df) + 1)
                )

                ranked_display = format_dataframe(ranked_df)

                st.markdown("**Detailed ranking**")

                st.dataframe(
                    ranked_display,
                    use_container_width=True,
                    hide_index=True
                )

                # ----------------------------------
                # AUTOMATIC COMPARISON CHART
                # ----------------------------------

                chart_df = comparison_df.copy()

                chart_df[group_column] = chart_df[
                    group_column
                ].apply(format_category)

                chart_title = (
                    f"{format_column_name(metric_column)} "
                    f"by {format_column_name(group_column)}"
                )

                fig = px.bar(
                    chart_df,
                    x=group_column,
                    y=metric_column,
                    title=chart_title,
                    text_auto=".2s"
                )

                fig.update_layout(
                    xaxis_title=format_column_name(group_column),
                    yaxis_title=format_column_name(metric_column),
                    xaxis_tickangle=-30,
                    showlegend=False
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        # ------------------------------------------
        # SINGLE AGGREGATE RESULT
        # ------------------------------------------

        elif len(df) == 1 and metric_column:

            value = df.iloc[0][metric_column]

            st.divider()

            st.subheader("📌 Key Result")

            st.metric(
                label=format_column_name(metric_column),
                value=format_number(value)
            )

        # ------------------------------------------
        # MULTI-COLUMN DATA VISUALIZATION
        # ------------------------------------------

        elif metric_column and group_column:

            chart_df = df.copy()

            chart_df[group_column] = chart_df[
                group_column
            ].apply(format_category)

            fig = px.bar(
                chart_df,
                x=group_column,
                y=metric_column,
                title=(
                    f"{format_column_name(metric_column)} "
                    f"by {format_column_name(group_column)}"
                ),
                text_auto=".2s"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    
    # ----------------------------------------------
    # ERROR / EXPLANATION MESSAGE
    # ----------------------------------------------

    if result.get("message"):
        st.caption(result["message"])
