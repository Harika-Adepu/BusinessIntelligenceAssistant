
import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.5-flash-lite"
DB_PATH = BASE_DIR / "database" / "sales.db"

client = genai.Client(api_key=API_KEY) if API_KEY else None

app = FastAPI(
    title="AI Sales Business Intelligence Assistant",
    description=(
        "A natural-language business intelligence assistant "
        "for querying and analyzing sales data."
    ),
    version="3.0",
)


# ==================================================
# REQUEST MODEL
# ==================================================

class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


# ==================================================
# DATABASE SCHEMA AND ALLOWED OPERATIONS
# ==================================================

TABLE_NAME = "sales"

COLUMNS = {
    "transaction_id": "Transaction_Id",
    "order_date": "Order_date",
    "product": "Product",
    "category": "Category",
    "region": "Region",
    "sales_channel": "Sales_channel",
    "quantity": "Quantity",
    "unit_price": "Unit_price",
    "discount_amount": "Discount_amount",
    "status": "Status",
    "total_price": "Total_price",
}

METRICS = {
    "revenue": "SUM(Total_price)",
    "quantity": "SUM(Quantity)",
    "transactions": "COUNT(DISTINCT Transaction_Id)",
    "average_order_value": "AVG(Total_price)",
    "average_unit_price": "AVG(Unit_price)",
    "total_discount": "SUM(Discount_amount)",
}

GROUPS = {
    "product": "Product",
    "category": "Category",
    "region": "Region",
    "sales_channel": "Sales_channel",
    "status": "Status",
    "month": "strftime('%Y-%m', Order_date)",
    "year": "strftime('%Y', Order_date)",
    "day_of_week": """
        CASE CAST(strftime('%w', Order_date) AS INTEGER)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END
    """,
}

FILTER_COLUMNS = {
    "transaction_id": "Transaction_Id",
    "order_date": "Order_date",
    "product": "Product",
    "category": "Category",
    "region": "Region",
    "sales_channel": "Sales_channel",
    "quantity": "Quantity",
    "unit_price": "Unit_price",
    "discount_amount": "Discount_amount",
    "status": "Status",
    "revenue": "Total_price",
}

FILTER_OPERATORS = {
    "eq": "=",
    "neq": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
}

TEXT_OPERATORS = {
    "contains",
    "starts_with",
    "ends_with",
}

DEFAULT_AGGREGATE_LIMIT = 10
DEFAULT_RECORD_LIMIT = 20
MAX_RESULT_LIMIT = 100


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Sales database was not found.",
        )

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    except sqlite3.Error as exc:
        print("DATABASE CONNECTION ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Could not connect to the sales database.",
        )


# ==================================================
# GEMINI QUERY UNDERSTANDING
# ==================================================

def understand_question(question: str) -> dict:

    if client is None:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured.",
        )

    prompt = f"""
You are an expert Business Intelligence analyst and natural-language
database query planner.

Your job is to understand the user's intention and convert it into
a structured JSON query plan for the SQLite database.

Do not answer the business question yourself.
Do not calculate values yourself.
Generate a query plan that Python can validate and SQLite can execute.

DATABASE

Table: sales

Actual database columns:
- Transaction_Id: unique transaction identifier
- Order_date: date and time of the order
- Product: product name
- Category: product category
- Region: sales region
- Sales_channel: channel used for the sale
- Quantity: quantity sold
- Unit_price: price per unit
- Discount_amount: discount amount
- Status: transaction status
- Total_price: transaction total

AVAILABLE METRICS

- revenue: SUM(Total_price)
- quantity: SUM(Quantity)
- transactions: COUNT(DISTINCT Transaction_Id)
- average_order_value: AVG(Total_price)
- average_unit_price: AVG(Unit_price)
- total_discount: SUM(Discount_amount)

AVAILABLE GROUPS

- product
- category
- region
- sales_channel
- status
- month
- year
- day_of_week

AVAILABLE FILTER FIELDS

- transaction_id
- order_date
- product
- category
- region
- sales_channel
- quantity
- unit_price
- discount_amount
- status
- revenue

AVAILABLE FILTER OPERATORS

- eq
- neq
- gt
- gte
- lt
- lte
- contains
- starts_with
- ends_with

IMPORTANT INTENT RULES

1. UNDERSTAND THE MEANING, NOT THE EXACT WORDS

Users may:
- Use different wording for the same business question.
- Make spelling or grammatical mistakes.
- Use informal expressions or abbreviations.
- Ask questions without knowing database terminology.

Interpret their intended meaning instead of requiring exact keywords.

2. AGGREGATE QUESTIONS

Use query_type = "aggregate" for questions asking for:
- Total, sum, average or maximum/minimum.
- How many transactions or products.
- Revenue, quantity or discount calculations.
- Trends, comparisons, rankings or performance.
- Highest, lowest, best or worst performers.

Choose the correct metric and grouping dimensions.

3. COMPARISON AND BEST-PERFORMER QUESTIONS

Questions such as:
- Compare revenue across regions.
- Which region performs best?
- What is the highest revenue region?
- Rank regions by sales.
- Show regional revenue performance.

These should use the SAME underlying analysis:
metric = "revenue"
group_by = ["region"]
sort_by = "metric"
sort_order = "desc"

Do not return only one region when the user asks which region performs best.
Return the grouped comparison data so the dashboard can display all regions
and identify the best performer.

Apply this principle to other dimensions and metrics too.

4. RECORD-LEVEL QUESTIONS

Use query_type = "records" when the user wants to inspect actual rows,
such as:
- Show transaction details.
- List returned transactions.
- Display orders from a particular region.
- Show the records matching these conditions.
- Give me the details of those transactions.

For record retrieval:
- Select actual database columns.
- Use select_columns = [] to return all columns when the user does not
  specify particular columns.
- Apply the requested filters.
- Do not replace record retrieval with an aggregate count.

5. COUNT QUESTIONS

Use query_type = "aggregate" when the user asks how many records,
transactions or orders match a condition.

For example, asking how many transactions were returned means:
metric = "transactions"
filter status = "Returned"

Do not retrieve only one row and mistake that for the total count.

6. STATUS HANDLING

The Status column contains values such as Completed and Returned.

For ordinary sales performance questions, use Completed transactions
by default.

If the user specifically asks about returned transactions, apply a
status = "Returned" filter.

If the user asks for all statuses, set include_all_statuses = true.

If the user explicitly specifies a status filter, do not add a conflicting
default Completed filter.

7. DATE AND TIME QUESTIONS

Use:
- month for monthly trends.
- year for yearly trends.
- day_of_week for weekday analysis.

For weekday order counts, use metric = "transactions".
For weekday revenue, use metric = "revenue".

The day_of_week dimension represents weekdays, not individual calendar dates.

8. FILTERS

Translate natural-language conditions into the available filter fields
and operators.

Examples:
- revenue greater than 5000 -> revenue, gt, 5000
- quantity at least 5 -> quantity, gte, 5
- product containing phone -> product, contains, phone
- region is South -> region, eq, South
- status is returned -> status, eq, Returned

Use only values that are supported by the user's question.
Do not invent filter values.

9. SORTING AND LIMITS

For highest, best, top or most:
sort_by = "metric"
sort_order = "desc"

For lowest, worst or least:
sort_by = "metric"
sort_order = "asc"

For alphabetical or dimension-based ordering:
sort_by = "group"

Use limit = 10 for aggregate queries if the user does not specify a limit.
Use limit = 20 for record queries if the user does not specify a limit.
The maximum allowed limit is 100.

10. UNSUPPORTED QUESTIONS

The database only contains the sales fields listed above.

If the question requires information that cannot be derived from these
fields, set supported = false and explain why.

Do not invent missing customer details, customer identities, costs,
profits, margins or other unavailable information.

11. OUTPUT FORMAT

Return valid JSON only. Do not include Markdown or explanations outside JSON.

Use this exact structure:

{{
    "supported": true,
    "query_type": "aggregate",
    "metric": "revenue",
    "group_by": ["region"],
    "select_columns": [],
    "filters": [],
    "sort_by": "metric",
    "sort_order": "desc",
    "limit": 10,
    "include_all_statuses": false,
    "reason": "Compare revenue across regions."
}}

For record-level queries, use:

{{
    "supported": true,
    "query_type": "records",
    "metric": null,
    "group_by": [],
    "select_columns": [],
    "filters": [
        {{
            "column": "status",
            "operator": "eq",
            "value": "Returned"
        }}
    ],
    "sort_by": "metric",
    "sort_order": "desc",
    "limit": 20,
    "include_all_statuses": true,
    "reason": "Retrieve matching returned transaction records."
}}

For unsupported questions, use the same structure with supported=false
and explain the reason.

USER QUESTION:
{question}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        plan = json.loads(response.text)

        if not isinstance(plan, dict):
            raise ValueError("Gemini response must be a JSON object.")

        return plan

    except json.JSONDecodeError as exc:
        print("GEMINI JSON ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid query plan.",
        )

    except HTTPException:
        raise

    except Exception as exc:
        print("GEMINI API ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail=f"Gemini request failed: {type(exc).__name__}.",
        )


# ==================================================
# QUERY PLAN VALIDATION
# ==================================================

def validate_plan(plan: dict) -> dict:

    if not isinstance(plan, dict):
        raise HTTPException(
            status_code=422,
            detail="Invalid AI query plan.",
        )

    if plan.get("supported") is not True:
        reason = plan.get(
            "reason",
            "This question cannot be answered using the available sales data.",
        )

        return {
            "supported": False,
            "reason": str(reason),
        }

    query_type = plan.get("query_type")

    if query_type not in {"aggregate", "records"}:
        raise HTTPException(
            status_code=422,
            detail="Invalid query type.",
        )

    metric = plan.get("metric")

    if query_type == "aggregate" and metric not in METRICS:
        raise HTTPException(
            status_code=422,
            detail="Unsupported metric.",
        )

    if query_type == "records":
        metric = None

    groups = plan.get("group_by", [])
    filters = plan.get("filters", [])
    select_columns = plan.get("select_columns", [])

    if not isinstance(groups, list) or len(groups) > 2:
        raise HTTPException(
            status_code=422,
            detail="Invalid grouping dimensions.",
        )

    if any(group not in GROUPS for group in groups):
        raise HTTPException(
            status_code=422,
            detail="Unsupported grouping dimension.",
        )

    if query_type == "records" and groups:
        raise HTTPException(
            status_code=422,
            detail="Record queries cannot use aggregate grouping.",
        )

    if not isinstance(filters, list) or len(filters) > 10:
        raise HTTPException(
            status_code=422,
            detail="Invalid filters.",
        )

    validated_filters = []

    for item in filters:

        if not isinstance(item, dict):
            raise HTTPException(
                status_code=422,
                detail="Invalid filter.",
            )

        column = item.get("column")
        operator = item.get("operator")
        value = item.get("value")

        if column not in FILTER_COLUMNS:
            raise HTTPException(
                status_code=422,
                detail="Unsupported filter column.",
            )

        if operator not in FILTER_OPERATORS and operator not in TEXT_OPERATORS:
            raise HTTPException(
                status_code=422,
                detail="Unsupported filter operator.",
            )

        if (
            not isinstance(value, (str, int, float))
            or isinstance(value, bool)
        ):
            raise HTTPException(
                status_code=422,
                detail="Invalid filter value.",
            )

        if isinstance(value, str) and len(value) > 100:
            raise HTTPException(
                status_code=422,
                detail="Filter value is too long.",
            )

        numeric_columns = {
            "quantity",
            "unit_price",
            "discount_amount",
            "revenue",
        }

        if column in numeric_columns:
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=422,
                    detail=f"A numeric value is required for {column}.",
                )

        if operator in TEXT_OPERATORS and not isinstance(value, str):
            raise HTTPException(
                status_code=422,
                detail="Text filters require a text value.",
            )

        validated_filters.append({
            "column": column,
            "operator": operator,
            "value": value,
        })

    if not isinstance(select_columns, list):
        raise HTTPException(
            status_code=422,
            detail="Invalid selected columns.",
        )

    if len(select_columns) > len(COLUMNS):
        raise HTTPException(
            status_code=422,
            detail="Too many selected columns.",
        )

    if any(column not in COLUMNS for column in select_columns):
        raise HTTPException(
            status_code=422,
            detail="Unsupported selected column.",
        )

    if query_type == "aggregate" and select_columns:
        raise HTTPException(
            status_code=422,
            detail="Selected columns are only supported for record queries.",
        )

    sort_by = plan.get("sort_by", "metric")
    sort_order = plan.get("sort_order", "desc")

    if sort_by not in {"metric", "group"}:
        raise HTTPException(
            status_code=422,
            detail="Invalid sorting option.",
        )

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=422,
            detail="Invalid sorting direction.",
        )

    if query_type == "aggregate" and sort_by == "group" and not groups:
        raise HTTPException(
            status_code=422,
            detail="Group sorting requires a grouping dimension.",
        )

    if query_type == "records" and sort_by == "group":
        raise HTTPException(
            status_code=422,
            detail="Record queries must use metric sorting.",
        )

    limit = plan.get("limit")

    if limit is None:
        limit = (
            DEFAULT_RECORD_LIMIT
            if query_type == "records"
            else DEFAULT_AGGREGATE_LIMIT
        )

    if isinstance(limit, str):
        try:
            limit = int(limit.strip())
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Invalid result limit.",
            )

    if isinstance(limit, float) and limit.is_integer():
        limit = int(limit)

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise HTTPException(
            status_code=422,
            detail="Invalid result limit.",
        )

    if not 1 <= limit <= MAX_RESULT_LIMIT:
        raise HTTPException(
            status_code=422,
            detail=f"Result limit must be between 1 and {MAX_RESULT_LIMIT}.",
        )

    include_all_statuses = plan.get("include_all_statuses", False)

    if not isinstance(include_all_statuses, bool):
        raise HTTPException(
            status_code=422,
            detail="Invalid status option.",
        )

    # An explicit status filter takes precedence over the default.
    if any(item["column"] == "status" for item in validated_filters):
        include_all_statuses = True

    plan["query_type"] = query_type
    plan["metric"] = metric
    plan["group_by"] = groups
    plan["select_columns"] = select_columns
    plan["filters"] = validated_filters
    plan["sort_by"] = sort_by
    plan["sort_order"] = sort_order
    plan["limit"] = limit
    plan["include_all_statuses"] = include_all_statuses

    return plan


# ==================================================
# SQL FILTER BUILDER
# ==================================================

def build_where_clause(plan: dict):

    conditions = []
    params = []

    filters = plan["filters"]

    has_status_filter = any(
        item["column"] == "status"
        for item in filters
    )

    # Preserve the existing business rule:
    # ordinary sales analysis defaults to Completed transactions.
    if not plan["include_all_statuses"] and not has_status_filter:
        conditions.append("LOWER(Status) = LOWER(?)")
        params.append("Completed")

    for item in filters:

        column = FILTER_COLUMNS[item["column"]]
        operator = item["operator"]
        value = item["value"]

        if operator in FILTER_OPERATORS:

            sql_operator = FILTER_OPERATORS[operator]

            if (
                item["column"] in {
                    "status",
                    "product",
                    "category",
                    "region",
                    "sales_channel",
                    "transaction_id",
                }
                and operator in {"eq", "neq"}
            ):
                conditions.append(
                    f"LOWER({column}) {sql_operator} LOWER(?)"
                )
            else:
                conditions.append(
                    f"{column} {sql_operator} ?"
                )

            params.append(value)

        elif operator == "contains":
            conditions.append(
                f"{column} LIKE ? ESCAPE '\\'"
            )
            params.append(
                "%" + str(value).replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_") + "%"
            )

        elif operator == "starts_with":
            conditions.append(
                f"{column} LIKE ? ESCAPE '\\'"
            )
            params.append(
                str(value).replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_") + "%"
            )

        elif operator == "ends_with":
            conditions.append(
                f"{column} LIKE ? ESCAPE '\\'"
            )
            params.append(
                "%" + str(value).replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )

    where_sql = ""

    if conditions:
        where_sql = " WHERE " + " AND ".join(conditions)

    return where_sql, params


# ==================================================
# AGGREGATE QUERY EXECUTION
# ==================================================

def execute_aggregate_query(plan: dict):

    groups = plan["group_by"]
    metric = plan["metric"]

    select_parts = []

    for group in groups:
        select_parts.append(
            f"{GROUPS[group]} AS {group}"
        )

    # Use the actual metric name as the SQL result column.
    select_parts.append(
        f"{METRICS[metric]} AS {metric}"
    )

    select_sql = ", ".join(select_parts)

    where_sql, params = build_where_clause(plan)

    sql = (
        f"SELECT {select_sql} "
        f"FROM {TABLE_NAME}"
        f"{where_sql}"
    )

    if groups:

        group_expressions = [
            GROUPS[group]
            for group in groups
        ]

        sql += " GROUP BY " + ", ".join(group_expressions)

        if plan["sort_by"] == "group":
            sql += (
                f" ORDER BY {groups[0]} "
                f"{plan['sort_order'].upper()}"
            )
        else:
            sql += (
                f" ORDER BY {metric} "
                f"{plan['sort_order'].upper()}"
            )

    sql += " LIMIT ?"
    params.append(plan["limit"])

    conn = get_connection()

    try:
        rows = conn.execute(sql, params).fetchall()

        return [dict(row) for row in rows]

    except sqlite3.Error as exc:

        print("AGGREGATE SQL ERROR:", repr(exc))
        print("SQL:", sql)
        print("PARAMETERS:", params)

        raise HTTPException(
            status_code=500,
            detail="The analytics query failed. Check the server terminal.",
        )

    finally:
        conn.close()


# ==================================================
# RECORD-LEVEL QUERY EXECUTION
# ==================================================

def execute_record_query(plan: dict):

    selected_columns = plan["select_columns"]

    # If the user did not request specific fields,
    # return all available transaction columns.
    if not selected_columns:
        selected_columns = list(COLUMNS.keys())

    actual_columns = [
        COLUMNS[column]
        for column in selected_columns
    ]

    select_sql = ", ".join(actual_columns)

    where_sql, params = build_where_clause(plan)

    # Retrieve the total number of matching records separately.
    count_sql = (
        f"SELECT COUNT(*) AS total "
        f"FROM {TABLE_NAME}"
        f"{where_sql}"
    )

    # Retrieve the actual matching records.
    sql = (
        f"SELECT {select_sql} "
        f"FROM {TABLE_NAME}"
        f"{where_sql}"
        f" ORDER BY Order_date {plan['sort_order'].upper()}"
        f" LIMIT ?"
    )

    query_params = params + [plan["limit"]]

    conn = get_connection()

    try:

        total_records = conn.execute(
            count_sql,
            params
        ).fetchone()["total"]

        rows = conn.execute(
            sql,
            query_params
        ).fetchall()

        return {
            "data": [dict(row) for row in rows],
            "total_records": total_records,
            "record_count": len(rows),
        }

    except sqlite3.Error as exc:

        print("RECORD SQL ERROR:", repr(exc))
        print("SQL:", sql)
        print("PARAMETERS:", query_params)

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve transaction records.",
        )

    finally:
        conn.close()


# ==================================================
# DETERMINISTIC ANSWER GENERATION
# ==================================================

def generate_aggregate_answer(plan: dict, results: list) -> str:

    if not results:
        return "No matching sales results were found."

    metric = plan["metric"].replace("_", " ")
    groups = plan["group_by"]

    # Single aggregate result.
    if not groups:

        value = results[0].get(plan["metric"])

        if value is None:
            return f"No data was available for {metric}."

        return f"The {metric} is {float(value):,.2f}."

    # Grouped comparison.
    if len(results) == 1:

        group_value = results[0][groups[0]]
        metric_value = results[0][plan["metric"]]

        return (
            f"{group_value} has {metric} of "
            f"{float(metric_value):,.2f}."
        )

    # Find the best and lowest performers from actual SQL results.
    valid_results = [
        row for row in results
        if row.get(plan["metric"]) is not None
    ]

    if not valid_results:
        return "No comparable results were found."

    best = max(
        valid_results,
        key=lambda row: row[plan["metric"]]
    )

    lowest = min(
        valid_results,
        key=lambda row: row[plan["metric"]]
    )

    group_label = groups[0].replace("_", " ")

    best_value = float(best[plan["metric"]])
    lowest_value = float(lowest[plan["metric"]])

    answer = (
        f"{best[group_label.replace(' ', '_')]} is the top performer "
        f"for {metric}, with {best_value:,.2f}. "
        f"{len(results)} groups were compared."
    )

    if len(groups) == 1 and best_value != lowest_value:

        answer += (
            f" The lowest performer is "
            f"{lowest[groups[0]]}, with {lowest_value:,.2f}."
        )

    return answer


def generate_record_answer(record_result: dict) -> str:

    total = record_result["total_records"]
    returned = record_result["record_count"]

    if total == 0:
        return "No matching transaction records were found."

    if total == 1:
        return "One matching transaction was found. Its details are displayed below."

    if returned < total:
        return (
            f"Found {total:,} matching transaction records. "
            f"Displaying {returned:,} records. "
            f"Increase the result limit to view more."
        )

    return (
        f"Found {total:,} matching transaction records. "
        f"The matching details are displayed below."
    )


# ==================================================
# MAIN API ENDPOINT
# ==================================================

@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if len(question) < 3:
        raise HTTPException(
            status_code=422,
            detail="Please enter a valid question.",
        )

    # Step 1: Understand natural language.
    plan = understand_question(question)

    print(
        "GEMINI QUERY PLAN:",
        json.dumps(plan, indent=2)
    )

    # Step 2: Validate the AI-generated plan.
    plan = validate_plan(plan)

    if plan.get("supported") is False:

        return {
            "success": True,
            "supported": False,
            "question": question,
            "answer": plan["reason"],
            "query_plan": plan,
            "data": [],
        }

    # Step 3: Execute the appropriate SQL operation.
    if plan["query_type"] == "records":

        record_result = execute_record_query(plan)

        data = record_result["data"]

        answer = generate_record_answer(record_result)

        return {
            "success": True,
            "supported": True,
            "question": question,
            "query_plan": plan,
            "answer": answer,
            "summary": answer,
            "data": data,
            "record_count": record_result["record_count"],
            "total_records": record_result["total_records"],
            "comparison": None,
        }

    results = execute_aggregate_query(plan)

    answer = generate_aggregate_answer(
        plan,
        results
    )

    return {
        "success": True,
        "supported": True,
        "question": question,
        "query_plan": plan,
        "answer": answer,
        "summary": answer,
        "data": results,
        "record_count": len(results),
        "total_records": len(results),
        "comparison": {
            "metric": plan["metric"],
            "group_by": plan["group_by"],
            "sort_order": plan["sort_order"],
        },
    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health_check():

    conn = get_connection()

    try:

        count = conn.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        return {
            "status": "healthy",
            "database": "connected",
            "sales_records": count,
            "gemini_configured": client is not None,
            "model": MODEL,
        }

    except sqlite3.Error as exc:

        print("HEALTH CHECK ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail="Database health check failed.",
        )

    finally:
        conn.close()
