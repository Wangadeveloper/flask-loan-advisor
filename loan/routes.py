# loan/routes.py
from flask import Blueprint, render_template, url_for, redirect, request, flash, make_response, current_app, jsonify
from loan.forms import RegistrationForm, LoginForm, UserProfileForm, LoanRiskAssessmentForm, PeerToPeerAdviceForm, FinalizeLoanApplicationForm
from loan.models import User, UserProfile, PeerToPeerAdvice
from loan import db, bcrypt, login_manager  # Import the global objects
from flask_login import login_user, logout_user, login_required, current_user
import re
import os
from fpdf import FPDF
from io import BytesIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loan.gemini_engine import * # Import Gemini functions
import markdown as md # Ensure markdown is installed

main = Blueprint('main', __name__)  # Define the blueprint

@main.route('/')
@main.route('/home')
def home():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.user_account')) # Use blueprint name
    form = RegistrationForm()
    if form.validate_on_submit():
        enc_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=enc_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', category='success')
        return redirect(url_for('main.login')) # Use blueprint name
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.user_account')) # Use blueprint name
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.user_account')) # Use blueprint name
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.login')) # Use blueprint name

def generate_pdf(content: str) -> BytesIO:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=14)

    cleaned_content = content.replace('\u2013', '-')
    pdf.multi_cell(0, 5, cleaned_content)

    pdf_output = BytesIO()
    pdf_output.write(pdf.output(dest='S').encode('latin1', errors='replace'))
    pdf_output.seek(0)
    return pdf_output

@main.route('/user_account')
@login_required
def user_account():
    return render_template('account_info.html')

@main.route('/account')
@login_required
def account():
    return render_template("account.html")

@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UserProfileForm()
    if form.validate_on_submit():
        if current_user.profile:
            flash("Profile already exists!", "warning")
            return redirect(url_for("main.user_account")) # Use blueprint name

        profile = UserProfile(
            full_names=form.full_names.data,
            monthly_income=form.monthly_income.data,
            business_type=form.business_type.data,
            business_level=form.business_level.data,
            phone_no=form.phone.data,
            country=form.country.data,
            location=form.location.data,
            user_id=current_user.id
        )
        db.session.add(profile)
        db.session.commit()
        flash("Profile created successfully!", "success")
        return redirect(url_for("main.user_account")) # Use blueprint name
    return render_template("profile.html", form=form)

@main.route("/loan-risk-assessment", methods=["GET", "POST"])
@login_required
def loan_risk_assessment():
    form = LoanRiskAssessmentForm()
    if form.validate_on_submit():

        query = f"""advice me on what amount of
                    loan to apply in kenya having a monthly
                    income of kenya shillings {form.monthly_income.data},
                    and {form.business_type.data} business at a
                    {form.business_level.data} level and a repayment period
                    of {form.repayment_period.data} months
                    based on the given information
                    recommend on how to invest on this loan,if the description of my business
                    is :{form.business_desc.data}"""

        formatted_response = chat_with_gemini().send_message(query).text
        formatted_response=re.sub(r'\*+','\n',formatted_response)
        pdf_output = generate_pdf(formatted_response)
        response = make_response(pdf_output.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline;filename="loan_advice.pdf"'
        return response
    return render_template("loan-risk-assessment.html", form=form)

@main.route("/credit-risk-dashboard", methods=["GET"])
@login_required
def credit_risk_dashboard():
    file_path = os.path.join(current_app.root_path, 'static', 'ml_ready_features.csv')
    if not os.path.exists(file_path):
        flash('Financial report not found!', 'danger')
        return redirect(url_for('main.home')) # Use blueprint name

    try:
        df = pd.read_csv(file_path)
        df['Month'] = pd.to_datetime(df['Month'])
        df['Savings_Rate'] = df['Net Amount'] / (df['Paid In'] + 1e-6)
        df['Expense_Ratio'] = abs(df['Withdrawn']) / (df['Paid In'] + 1e-6)
        df['Risk_Score'] = (df['Expense_Ratio'] * 0.4 +
                           df['Loan Expense Ratio'].abs() * 0.3 +
                           df['Bill Expense Ratio'] * 0.3) * 100

        graphs = []

        fig1 = px.line(df, x='Month', y='Net Amount', title='Monthly Net Amount Trend')
        graphs.append(fig1.to_html(full_html=False))

        transaction_cols = ['Bill Payment', 'Gambling', 'Income', 'Loan Related',
                            'Other', 'Peer Transfer', 'Utilities']
        fig2 = px.bar(df, x='Month', y=transaction_cols, title='Transaction Composition by Type')
        graphs.append(fig2.to_html(full_html=False))

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df['Month'], y=df['Risk_Score'],
                          mode='lines+markers', name='Risk Score'))
        fig3.add_trace(go.Scatter(x=df['Month'], y=df['Expense_Ratio'] * 100,
                          mode='lines', name='Expense Ratio (%)'))
        fig3.update_layout(title='Risk Score and Expense Ratio Trend')
        graphs.append(fig3.to_html(full_html=False))

        fig4 = px.bar(df, x='Month', y=['Loan Expense Ratio', 'Bill Expense Ratio'],
                     title='Loan and Bill Expense Ratios')
        graphs.append(fig4.to_html(full_html=False))

        fig5 = px.line(df, x='Month', y='Savings_Rate', title='Monthly Savings Rate')
        graphs.append(fig5.to_html(full_html=False))

        summary_stats = {
            'avg_net_amount': df['Net Amount'].mean(),
            'avg_risk_score': df['Risk_Score'].mean(),
            'total_transactions': df['Transaction Count'].sum(),
            'highest_risk_month': df.loc[df['Risk_Score'].idxmax(), 'Month'].strftime('%B %Y')
        }

        return render_template('credit_risk_dashboard.html',
                             graphs=graphs,
                             summary_stats=summary_stats,
                             table_data=df.to_html(classes='table table-striped'))

    except Exception as e:
        flash(f"Error processing financial report: {str(e)}", 'danger')
        return redirect(url_for('main.home')) # Use blueprint name

@main.route("/peer-to-peer-advice", methods=["GET", "POST"])
@login_required
def peer_to_peer_advice():
    form = PeerToPeerAdviceForm()
    if form.validate_on_submit():
        new_message = PeerToPeerAdvice(
            message=form.message.data
        )

        db.session.add(new_message)
        db.session.commit()

        flash("Your message has been posted!", "success")
        return redirect(url_for("main.peer_to_peer_advice")) # Use blueprint name

    all_messages = PeerToPeerAdvice.query.order_by(PeerToPeerAdvice.id.desc()).all()

    return render_template("peer-advice.html", messages=all_messages)

@main.route("/finalize-loan-application", methods=["GET", "POST"])
@login_required
def finalize_loan_application():
    form = FinalizeLoanApplicationForm()
    if form.validate_on_submit():
        return redirect(url_for("main.confirmation")) # Use blueprint name
    return render_template("finalize-loan-application.html")

@main.route("/confirmation")
@login_required
def confirmation():
    return "<h1>Thank you! Your loan application has been submitted successfully.</h1>"

@main.route("/post-loan-monitoring", methods=["GET"])
@login_required
def post_loan_monitoring():
    return render_template("post-loan-monitoring.html")


@main.route('/analyze', methods=['POST'])
def analyze():
    pdf_file = request.files['pdf']
    query = """ The provided document is a report concerning gender equality,
    use it to give insights and summary on gender equality for a particular given country
    the insight should look like this :
    Uploaded Document:
"Gender Equality Progress Report — Country (capture country name here) (2024)"
Key Insights:
1. Gender Wage Gap:

Women earn 23% less than men on average across all
sectors.

In the tech industry, the gap widens to 30% despite equal qualification levels.
SDG Alignment:

SDG 5.1: End all forms of discrimination against women and girls.
SDG 10.3: Ensure equal opportunity and reduce outcome inequalities.

2. Political Representation:

Women occupy only 18% of parliamentary seats, below the global average of 26%.
No laws mandating minimum female representation in government positions.

SDG Alignment:

SDG 5.5: Ensure full participation in leadership and decision-making.
    add general summary.

"""
    try:
        response = analyze_pdf(pdf_file, query)
        resp = md.markdown(response)

        return jsonify({'response': resp})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"}), 500

@main.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        uploads_folder = current_app.config['UPLOAD_FOLDER']
        pdf_files = [f for f in os.listdir(uploads_folder) if f.lower().endswith('.pdf')]

        if pdf_files:
            pdf_path = os.path.join(uploads_folder, pdf_files[0])
            extracted_text = extract_pdf_text(pdf_path)
            final_prompt = f"{user_message}\n\nHere is relevant document content you can use:\n{extracted_text}"
        else:
            final_prompt = user_message

        chat = chat_with_gemini()
        response = chat.send_message(final_prompt)
        html_resp = md.markdown(response.text)
        return jsonify({'response': html_resp})
    except Exception as e:
        return jsonify({'response': f"Chat Error: {str(e)}"}), 500
    

import os
from werkzeug.utils import secure_filename

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("statement")
        password = request.form.get("password")

        if not file or not password:
            flash("Both statement and password are required.", "danger")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        save_path = os.path.join("uploads", filename)
        file.save(save_path)

        try:
            recommendation = analyze_mpesa_pdf_and_recommend(save_path, password)
            return render_template("result.html", rec=recommendation)
        except Exception as e:
            flash(f"Error: {e}", "danger")
            return redirect(request.url)

    return render_template("statement.html")
