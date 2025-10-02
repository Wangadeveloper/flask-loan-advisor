import os
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from fpdf import FPDF
from flask import current_app

def generate_pdf(content: str, title: str = "AI Advice") -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    # Strip or replace emojis (non-ASCII chars)
    cleaned_content = content.encode("ascii", "ignore").decode()
    pdf.multi_cell(0, 8, cleaned_content)

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest="S").encode("latin1", errors="replace"))
    pdf_output.seek(0)
    return pdf_output



# ✅ Configure Gemini safely inside request context
def get_model(model_name="gemini-1.5-flash"):
    # Get API key from Flask config or fallback to environment variable
    api_key = current_app.config.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise RuntimeError("❌ GOOGLE_API_KEY is not set in environment variables or config")

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    return genai.GenerativeModel(model_name=model_name, generation_config=generation_config)


# 🔹 Financial Advice (return TEXT, not PDF)
def get_financial_advice(farm_data: str) -> str:
    try:
        prompt = f"""
        You are an agricultural financial advisor.
        Given this farm situation:
        {farm_data}

        Provide simple, clear advice on:
        - Revenue optimization
        - Investment opportunities
        - Risk management
        """
        model = get_model("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generating financial advice: {str(e)}"


# 🔹 Translation (return TEXT, not PDF)
def translate_advice(advice: str, target_lang: str = "sw") -> str:
    try:
        prompt = f"""
        Translate the following farming advisory into {target_lang}.
        Keep the meaning clear and simple for farmers.

        Text:
        {advice}
        """
        model = get_model("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error translating advice: {str(e)}"

    
import pandas as pd
import pdfplumber
#import csv
import numpy as np

def extract_table_from_pdf(pdf_path, password, target_header):
    with pdfplumber.open(pdf_path, password=password) as pdf:
        data = []
        found = False
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and ",".join([str(i).strip() for i in table[0]]) == target_header:
                    found = True
                    data.extend(table)
                elif found:
                    data.extend(table)
        if not found:
            raise ValueError("Target table not found.")
        return pd.DataFrame(data[1:], columns=data[0])

def analyze_mpesa_pdf_and_recommend(pdf_path, password):
    header = "Receipt No.,Completion Time,Details,Transaction Status,Paid In,Withdrawn,Balance"
    df = extract_table_from_pdf(pdf_path, password, header)

    df["Paid In"] = pd.to_numeric(df["Paid In"], errors="coerce")
    df["Withdrawn"] = pd.to_numeric(df["Withdrawn"], errors="coerce")
    df["Amount"] = df["Paid In"].fillna(0) - df["Withdrawn"].fillna(0)
    df["Completion Time"] = pd.to_datetime(df["Completion Time"], errors="coerce")
    df["YearMonth"] = df["Completion Time"].dt.to_period("M")

    def categorize_transaction(detail):
        if pd.isna(detail): return "Unknown"
        d = detail.lower()
        if "fuliza" in d or "overdraft" in d: return "Loan"
        if "loan repayment" in d: return "Repayment"
        if "received from" in d or "funds received" in d: return "Income"
        if "buy" in d or "payment" in d: return "Purchase"
        if "sent to" in d or "transfer" in d: return "Transfer"
        return "Other"

    df["Category"] = df["Details"].apply(categorize_transaction)

    summary = df.groupby(["YearMonth", "Category"])["Amount"].sum().unstack(fill_value=0)
    summary["Total Outflow"] = summary[["Loan", "Repayment", "Purchase", "Transfer"]].sum(axis=1)
    summary["Net Cash Flow"] = summary["Income"] - summary["Total Outflow"]
    summary["Loan to Income Ratio"] = (summary["Loan"] / summary["Income"]).replace([np.inf, -np.inf], np.nan)

    avg_income = summary["Income"].mean()
    avg_repayment = summary["Repayment"].mean()
    avg_cash_flow = summary["Net Cash Flow"].mean()
    avg_ratio = summary["Loan to Income Ratio"].mean()

    safe_monthly_repay = min(avg_repayment, max(0.3 * avg_income, 1500))
    term = 4
    safe_loan = round(safe_monthly_repay * term, 2)
    high_risk = avg_cash_flow < 0 or avg_ratio > 1.5

    return {
        "Requested Loan": 20000,
        "Recommended Loan": safe_loan,
        "High Risk": high_risk,
        "Recommended Monthly Repayment": round(safe_monthly_repay, 2),
        "Term": term,
        "Investment Plan": {
            "Inventory": round(safe_loan * 0.7, 2),
            "Emergency": round(safe_loan * 0.2, 2),
            "Marketing": round(safe_loan * 0.1, 2)
        },
        "Note": f"Based on avg. income {avg_income:.0f} and repayment {avg_repayment:.0f}"
    }
