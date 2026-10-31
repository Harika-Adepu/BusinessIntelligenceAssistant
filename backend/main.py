import os
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.8-flash"

DB_PATH = BASE_DIR / "database" / "sales.db"

client = genai.Client(api_key=API_KEY) if API_KEY else None

app = FastAPI(
    title="AI Sales Business Intelligence Assistant",
    description="Ask natural-language questions about sales data",
    version="2.0"
)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def get_connection():

    if not DB_PATH.exists():
        raise HTTPException(500, "Database not found.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


METRICS = {
    "revenue": "SUM(revenue)",
    "quantity": "SUM(quantity)",
    "transactions": "COUNT(DISTINCT transaction_id)",
    "average_order_value": "AVG(revenue)",
    "average_unit_price": "AVG(unit_price)",
    "total_discount": "SUM(discount_amount)"
}

GROUPS = {
    "product": "product",
    "category": "category",
    "region": "region",
    "sales_channel": "sales_channel",
    "status": "status",
    "month": "strftime('%Y-%m', order_date)",
    "year": "strftime('%Y', order_date)"
}

FILTER_COLUMNS = {
    "product", "category", "region", "sales_channel",
    "status", "order_date", "quantity",
    "unit_price", "discount_amount", "revenue"
}

FILTER_OPERATORS = {
    "eq": "=",
    "gte": ">=",
    "lte": "<="
}


def understand_question(question):

    if client is None:
        raise HTTPException(
            503, "Gemini API key is not configured."
        )

    prompt = f"""
You are an expert Business Intelligence query planner.

Understand the user's question about this sales database.

DATABASE TABLE: sales

AVAILABLE COLUMNS:
transaction_id, order_date, product, category,
region, sales_channel, quantity, unit_price,
discount_amount, revenue, status.

IMPORTANT:
- Revenue is already calculated after discounts.
- Completed and Returned are possible transaction statuses.
- Do not invent columns or information.
- Only answer questions that can be answered using this dataset.
- Questions about trends should group by month or year.
- Questions about comparisons should group by the relevant dimension.
- For highest/top/best use descending order.
- For lowest/worst use ascending order.
- If a user specifies a particular month or date range,
  represent it using order_date filters.
- If the question asks about returned transactions or
  all transaction statuses, set include_all_statuses to true.
- Otherwise, use completed transactions by default.
- Use only the allowed metrics and grouping dimensions below.
- If the question is unrelated to this dataset, set supported=false.

ALLOWED METRICS:
revenue, quantity, transactions,
average_order_value, average_unit_price, total_discount

ALLOWED GROUPS:
product, category, region, sales_channel,
status, month, year

ALLOWED FILTER OPERATORS:
eq, gte, lte

Return ONLY valid JSON in this format:

{{
  "supported": true,
  "metric": "revenue",
  "group_by": ["product"],
  "filters": [
    {{
      "column": "region",
      "operator": "eq",
      "value": "North"
    }}
  ],
  "sort_by": "metric",
  "sort_order": "desc",
  "limit": 10,
  "include_all_statuses": false,
  "compare_periods": false,
  "reason": "Revenue grouped by product"
}}

If no grouping is needed, use [].
If no filters are needed, use [].
Use compare_periods=true only when comparing time periods.

USER QUESTION:
{question}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0
            )
        )

        return json.loads(response.text)

    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        print("Gemini response:", response.text)
        raise HTTPException(
            status_code=502,
            detail="Gemini returned invalid JSON."
        )

    except Exception as e:
        print("Gemini API error:", type(e).__name__, str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API error: {type(e).__name__}: {str(e)}"
        )
   
     


def validate_plan(plan):

    if not isinstance(plan, dict):
        raise HTTPException(422, "Invalid AI response.")

    if plan.get("supported") is not True:
        raise HTTPException(
            422,
            "This question cannot be answered using the available sales data."
        )

    metric = plan.get("metric")

    if metric not in METRICS:
        raise HTTPException(422, "Unsupported metric.")

    groups = plan.get("group_by", [])
    filters = plan.get("filters", [])

    if not isinstance(groups, list) or len(groups) > 2:
        raise HTTPException(422, "Invalid grouping dimensions.")

    if any(group not in GROUPS for group in groups):
        raise HTTPException(422, "Unsupported grouping column.")

    if not isinstance(filters, list) or len(filters) > 10:
        raise HTTPException(422, "Invalid filters.")

    for f in filters:

        if not isinstance(f, dict):
            raise HTTPException(422, "Invalid filter.")

        column = f.get("column")
        operator = f.get("operator")
        value = f.get("value")

        if column not in FILTER_COLUMNS:
            raise HTTPException(422, "Unsupported filter column.")

        if operator not in FILTER_OPERATORS:
            raise HTTPException(422, "Unsupported filter operator.")

        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise HTTPException(422, "Invalid filter value.")

        if isinstance(value, str) and len(value) > 100:
            raise HTTPException(422, "Filter value too long.")

        if operator == "eq" and column in {
            "quantity", "unit_price", "discount_amount", "revenue"
        }:
            try:
                float(value)
            except (TypeError, ValueError):
                raise HTTPException(422, "Numeric filter required.")

        if operator in {"gte", "lte"} and column == "order_date":
            try:
                from datetime import date
                date.fromisoformat(str(value))
            except ValueError:
                raise HTTPException(422, "Invalid date filter.")

    if plan.get("sort_by", "metric") not in {"metric", "group"}:
        raise HTTPException(422, "Invalid sort option.")

    if plan.get("sort_order", "desc") not in {"asc", "desc"}:
        raise HTTPException(422, "Invalid sort order.")

    if not isinstance(plan.get("limit", 20), int):
        raise HTTPException(422, "Invalid result limit.")

    if not 1 <= plan.get("limit", 20) <= 100:
        raise HTTPException(422, "Result limit must be 1–100.")

    if not isinstance(plan.get("include_all_statuses", False), bool):
        raise HTTPException(422, "Invalid status option.")

    if not isinstance(plan.get("compare_periods", False), bool):
        raise HTTPException(422, "Invalid comparison option.")

    if plan.get("compare_periods") and not any(
        g in {"month", "year"} for g in groups
    ):
        raise HTTPException(422, "Time comparison requires a time grouping.")

    return plan


def execute_analytics(plan):

    metric = plan["metric"]
    groups = plan.get("group_by", [])
    filters = plan.get("filters", [])

    select_parts = []

    for group in groups:
        select_parts.append(
            f"{GROUPS[group]} AS {group}"
        )

    select_parts.append(
        f"{METRICS[metric]} AS value"
    )

    sql = "SELECT " + ", ".join(select_parts) + " FROM sales"

    conditions = []
    params = []

    has_status_filter = any(
        f["column"] == "status" for f in filters
    )

    if not plan.get("include_all_statuses", False) and not has_status_filter:
        conditions.append("status = ?")
        params.append("Completed")

    for f in filters:

        column = f["column"]
        operator = f["operator"]
        value = f["value"]

        if operator == "eq":
            conditions.append(f"{column} = ?")
            params.append(value)

        elif operator == "gte":
            conditions.append(f"{column} >= ?")
            params.append(value)

        elif operator == "lte":
            conditions.append(f"{column} <= ?")
            params.append(value)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    if groups:

        group_expressions = [
            GROUPS[group] for group in groups
        ]

        sql += " GROUP BY " + ", ".join(group_expressions)

        sort_order = plan.get("sort_order", "desc").upper()

        if plan.get("compare_periods"):
            sql += f" ORDER BY {groups[0]} ASC"

        elif plan.get("sort_by") == "group":
            sql += f" ORDER BY {groups[0]} {sort_order}"

        else:
            sql += f" ORDER BY value {sort_order}"

        sql += " LIMIT ?"
        params.append(plan.get("limit", 20))

    conn = get_connection()

    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    except sqlite3.Error:
        raise HTTPException(500, "Analytics query failed.")

    finally:
        conn.close()


def generate_answer(plan, results):

    if not results:
        return "No matching sales records were found."

    metric = plan["metric"]

    if not plan.get("group_by"):

        value = results[0]["value"] or 0

        return (
            f"The {metric.replace('_', ' ')} is "
            f"{value:.2f}."
        )

    groups = ", ".join(plan["group_by"])

    answer = (
        f"Retrieved {len(results)} results grouped by "
        f"{groups}, using {metric.replace('_', ' ')}."
    )

    if plan.get("compare_periods") and len(results) >= 2:

        previous = results[-2]
        latest = results[-1]

        old_value = previous["value"] or 0
        new_value = latest["value"] or 0

        change = new_value - old_value

        percentage = (
            (change / old_value) * 100
            if old_value != 0 else None
        )

        answer += (
            f" Change from {previous[plan['group_by'][0]]} "
            f"to {latest[plan['group_by'][0]]}: "
            f"{change:.2f}."
        )

        if percentage is not None:
            answer += f" Percentage change: {percentage:.2f}%."

    return answer


@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if len(question) < 3:
        raise HTTPException(422, "Please enter a valid question.")

    plan = understand_question(question)
    plan = validate_plan(plan)

    results = execute_analytics(plan)
    answer = generate_answer(plan, results)

    return {
        "success": True,
        "question": question,
        "intent": plan,
        "answer": answer,
        "supporting_data": results
    }


@app.get("/health")
def health_check():

    try:
        conn = get_connection()

        count = conn.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "sales_records": count,
            "gemini_configured": client is not None
        }

    except sqlite3.Error:
        raise HTTPException(500, "Database connection failed.")

