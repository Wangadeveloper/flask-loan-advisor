# loan/gemini_engine.py
import os
import google.generativeai as genai
from flask import current_app
import google.genai as gemini
from google.genai import types
import PyPDF2
from io import BytesIO

generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

def configure_gemini():
    genai.configure(api_key=current_app.config['GOOGLE_API_KEY'])
    return genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)

def analyze_pdf(file, query):
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    model = configure_gemini()
    try:
        with open(filepath, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        return f"Error reading PDF: {e}"

    response = model.generate_content([text, "\n\n", query])
    return response.text

def chat_with_gemini():
    instruction="""you are a helpful chatbot help answer users questions """
    client = gemini.Client(api_key=current_app.config['GOOGLE_API_KEY'])
    chat = client.chats.create(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction=instruction,
        ))
    return chat

def extract_pdf_text(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        return f"Error extracting text from PDF: {e}"
    return text


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
