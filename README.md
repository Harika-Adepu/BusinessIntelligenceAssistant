# Business Intelligence Assistant

An AI-powered Sales Business Intelligence Assistant that converts natural-language questions into meaningful sales insights using Google Gemini, FastAPI, SQLite, and Streamlit.

## Overview

The Business Intelligence Assistant enables users to analyze sales data by asking questions in plain English instead of writing SQL queries.

It uses Gemini to understand user questions and generate structured query plans. The backend validates these plans and executes SQL queries against a SQLite database to produce accurate, data-driven results.

## Key Features

- **Natural Language Queries:** Ask sales-related questions in plain English.
- **Dynamic Query Understanding:** Interpret different question formats and identify relevant metrics, filters, and grouping dimensions.
- **Sales Analytics:** Analyze revenue, quantity, transactions, average order value, unit price, and discounts.
- **Comparative Analysis:** Compare sales performance across products, categories, regions, and sales channels.
- **Record Retrieval:** Retrieve individual sales records based on user-defined conditions.
- **Interactive Visualizations:** Display analytical results using interactive Plotly charts.
- **Data Export:** Download query results as CSV files.
- **Validated SQL Execution:** Use structured query plans, validation, and parameterized SQL to keep numerical results grounded in the database.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Model | Google Gemini |
| Database | SQLite |
| Data Processing | Python, Pandas |
| Visualization | Plotly |
| API Communication | REST API |

## Architecture

```text
          User Question
                |
                v
       Streamlit Frontend
                |
                v
         FastAPI Backend
                |
                v
         Google Gemini
       (Query Interpretation)
                |
                v
       Structured Query Plan
                |
                v
       Python Validation
                |
                v
        SQLite Database
       (SQL Execution)
                |
                v
       Analytical Results
                |
                v
       Answer + Visualization
                |
                v
        Streamlit Frontend
```

**Design Principle:** Gemini interprets the question, while validated SQL queries perform the actual calculations. This helps ensure that numerical results come from the underlying dataset rather than AI-generated estimates.

## Project Structure

```text
RSG-GET-Assessment/
│
├── backend/
│   └── main.py
│
├── frontend/
│   └── app.py
│
├── database/
│   └── sales.db
│
├── test_bi.py
├── test_gemini.py
├── requirements.txt
├── .env
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Harika-Adepu/BusinessIntelligenceAssistant.git
cd BusinessIntelligenceAssistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder with your Google Gemini API key.

### 5. Run the backend

```bash
uvicorn backend.main:app --reload
```

Backend API:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 6. Run the frontend

Open another terminal, activate the virtual environment, and run:

```bash
streamlit run frontend/app.py
```

The application will open in your browser.

## Example Questions

Try asking:

- What is the total revenue?
- Which region generates the highest revenue?
- Compare revenue across different product categories.
- What is the average order value?
- Which products have the highest sales?
- How many transactions were returned?
- Show the details of returned transactions.
- Compare monthly sales performance.

*Results depend on the fields and records available in the sales dataset.*

## Testing

The project includes two test scripts:

**Test Gemini API connectivity:**

```bash
python test_gemini.py
```

**Test the BI query-planning functionality:**

```bash
python test_bi.py
```

## Limitations

- Analysis is restricted to information available in the sales database.
- Supported metrics, grouping dimensions, filters, and query operations are validated against predefined rules.
- Questions requiring unavailable information, such as customer demographics or profit margins, cannot be reliably answered.
- Follow-up questions requiring conversational memory are not currently supported.

## Future Enhancements

- Add conversational context for multi-turn queries.
- Expand analytical capabilities and supported query operations.
- Implement pagination for large datasets.
- Add automated unit and integration test coverage.
- Improve query evaluation, error handling, and performance.

## Author

**Adepu Harika**

B.Tech – Computer Science and Engineering

GitHub: [Harika-Adepu](https://github.com/Harika-Adepu)

**Repository:** [BusinessIntelligenceAssistant](https://github.com/Harika-Adepu/BusinessIntelligenceAssistant)