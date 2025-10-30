#
# This is the final app.py with all AI integration removed 
# and replaced by a simple, rule-based chatbot that pulls data from the BANKS list.
#

import os
from flask import Flask, render_template, request, jsonify, session 
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import json
import re 
import math 
import datetime

# No AI imports needed

app = Flask(__name__)

app.config['SECRET_KEY'] = 'a_very_secret_key_for_session_management_12345'

# --- Mail Configuration (Unchanged) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vinayacharvinu282004@gmail.com'
app.config['MAIL_PASSWORD'] = 'sfor xbea onjy oxju' 
app.config['MAIL_DEFAULT_SENDER'] = ('Loan Recommender', 'vinayacharvinu282004@gmail.com') 

mail = Mail(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/loanDB"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


# --- Bank Data (Unchanged) ---
BANKS = [
    {
        "name": "State Bank of India", "min_amount": 0, "max_amount": 1000000, "interest_rate": 8.55,
        "package": "SBI Student Loan", "min_income": 0, "min_score": 55,
        "url": "https://sbi.co.in/web/personal-banking/loans/education-loans"
    },
    {
        "name": "HDFC", "min_amount":100000, "max_amount":15000000, "interest_rate": 10.50,
        "package": "HDFC Loan", "min_income": 150000, "min_score": 60,
        "url": "https://www.hdfcbank.com/personal/borrow/popular-loans/education-loan"
    },
    {
        "name": "Bank of Baroda", "min_amount": 0, "max_amount": 1500000, "interest_rate": 8.85,
        "package": "Baroda Scholar", "min_income": 100000, "min_score": 60,
        "url": "https://www.bankofbaroda.in/personal-banking/loans/education-loan/baroda-scholar"
    },
    {
        "name": "Canara Bank", "min_amount": 100000, "max_amount": 2000000, "interest_rate": 9.25,
        "package": "Vidya Turant", "min_income": 250000, "min_score": 65,
        "url": "https://canarabank.com/personal-banking/loans/education-loan"
    },
    {
        "name": "Union Bank of India", "min_amount": 200000, "max_amount": 2500000, "interest_rate": 9.0,
        "package": "Union Education", "min_income": 300000, "min_score": 70,
        "url": "https://www.unionbankofindia.co.in/english/education-loan.aspx"
    },
    {
        "name": "Karnataka Bank", "min_amount": 400000, "max_amount": 2000000, "interest_rate": 9.18,
        "package": "KBL Vidhyanidhi", "min_income":250000, "min_score": 80,
        "url": "https://www.google.com/search?q=apply+for+scholar+loan" 
    }
]

# --- New Helper Function to get bank details ---
def get_bank_info():
    info = []
    for bank in BANKS:
        min_loan = f"INR {bank['min_amount'] / 100000:,.0f} Lakh" if bank['min_amount'] >= 100000 else f"INR {bank['min_amount']:,.0f}"
        max_loan = f"INR {bank['max_amount'] / 100000:,.0f} Lakh" if bank['max_amount'] >= 100000 else f"INR {bank['max_amount']:,.0f}"
        
        info.append(
            f"**{bank['name']}** ({bank['package']}): "
            f"Interest **{bank['interest_rate']}%**. "
            f"Loan amounts range from {min_loan} to {max_loan}."
        )
    return "\n\n".join(info)
# --- End of New Helper Function ---


# --- Other Helper Functions (Unchanged) ---
def get_academic_score(data):
    study_type = data.get('study_type')
    try:
        if study_type == 'university':
            level = data.get('univ_level')
            if level == 'ug':
                total = float(data.get('t12_total') or 0)
                obtained = float(data.get('t12_obtained') or 0)
                return (obtained / total) * 100 if total > 0 else 0
            elif level == 'pg':
                cgpa = float(data.get('ug_cgpa') or 0)
                return cgpa * 9.5
        elif study_type == 'college':
            total = float(data.get('t10_total') or 0)
            obtained = float(data.get('t10_obtained') or 0)
            return (obtained / total) * 100 if total > 0 else 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
    return 0

def recommend_banks(amount, income, score):
    eligible_banks = [
        b for b in BANKS
        if b['min_amount'] <= amount <= b['max_amount']
        and b['min_income'] <= income
        and b['min_score'] <= score
    ]
    eligible_banks.sort(key=lambda x: x['interest_rate'])
    return eligible_banks


# --- MODIFIED /chat Route ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip().lower()

    if user_message == 'clear context':
        return jsonify({"response": "Conversation context cleared. How can I help you now?"})

    # Simple Rule-Based Chatbot Logic
    if 'hello' in user_message or 'hi' in user_message or 'hey' in user_message:
        response_text = "Hello! I am a simple bot. I can give you detailed information about our **partner banks** (type 'banks'). Type 'help' to see other commands."
    elif 'help' in user_message or 'what can you do' in user_message:
        response_text = "I am an informative assistant. You can ask me for **'banks'**, the **'lowest interest rate'**, or the **'loan process'**."
    elif 'banks' in user_message or 'who are your partners' in user_message or 'interest' in user_message or 'loan availability' in user_message:
        response_text = "Here are the details for our partner banks:\n\n" + get_bank_info()
        response_text += "\n\nTo get a personalized recommendation, please fill out the main form."
    elif 'lowest interest rate' in user_message or 'best rate' in user_message:
        best_bank = min(BANKS, key=lambda x: x['interest_rate'])
        response_text = (
            f"The best available interest rate is currently **{best_bank['interest_rate']}%** "
            f"from **{best_bank['name']}** ({best_bank['package']}). "
            f"Their minimum score requirement is {best_bank['min_score']}."
        )
    elif 'loan process' in user_message or 'how to apply' in user_message:
        response_text = "The loan process has three steps: 1. Fill out the application form and click **'Get Recommendations'**. 2. Select a bank and click **'Save Application'** to save your details to our system. 3. Click **'Apply at Bank'** to visit the bank's official website and complete their process."
    elif 'emi' in user_message or 'calculate' in user_message:
        response_text = "An **EMI Calculator** will appear on the page after you click 'Get Recommendations' and view the bank options."
    elif 'loan' in user_message or 'recommendation' in user_message or 'eligible' in user_message:
        response_text = "To get a personalized loan recommendation, please **fill out and submit the main application form** on this page. Our system will check your eligibility against all our partner bank criteria."
    else:
        response_text = "I'm a simple information bot. Please try typing **'banks'** or **'help'**."
    
    return jsonify({"response": response_text})

# --- END OF CHAT MODIFICATION ---


# --- Authentication Routes (Unchanged) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    if not all([name, email, password]):
        return jsonify({"error": "Missing name, email, or password"}), 400
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "Email address already in use"}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        user_id = mongo.db.users.insert_one({
            "name": name, "email": email, "password": hashed_password,
            "created_at": datetime.datetime.utcnow()
        }).inserted_id
        session['user_id'] = str(user_id)
        session['user_name'] = name
        return jsonify({"message": "Registration successful!", "name": name}), 201
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({"error": "Missing email or password"}), 400
    user = mongo.db.users.find_one({"email": email})
    if user and bcrypt.check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        session['user_name'] = user['name']
        return jsonify({"message": "Login successful!", "name": user['name']}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear() # Clear all session data
    return jsonify({"message": "Logout successful"}), 200

@app.route('/check_session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "name": session.get('user_name')}), 200
    else:
        return jsonify({"logged_in": False}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    if 'user_id' not in session:
        return jsonify({"error": "You must be logged in to get recommendations."}), 401
    data = request.get_json() or {}
    session['form_data'] = data
    try:
        fee = float(data.get('college_fee', 0) or 0)
        years = int(data.get('loan_years', 0) or 0)
        income = float(data.get('family_income', 0) or 0)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid numeric inputs for fee, years, or income."}), 400
    total_amount = fee * years
    academic_score = get_academic_score(data)
    banks = recommend_banks(total_amount, income, academic_score)
    return jsonify({"total_amount": total_amount, "currency": "INR", "recommended_banks": banks})


# --- Application and Email Route (Unchanged) ---
@app.route('/apply', methods=['POST'])
def apply():
    if 'user_id' not in session:
        return jsonify({"error": "You must be logged in to apply."}), 401

    bank_data = request.get_json() or {}
    bank_name = bank_data.get('bank_name')
    loan_package = bank_data.get('loan_package')
    
    form_data = session.get('form_data')
    if not form_data:
        return jsonify({"error": "No application data found in session. Please submit the form again."}), 400

    student_name = form_data.get('student_name')
    student_email = form_data.get('email')

    if not all([student_name, student_email, bank_name, loan_package]):
        return jsonify({"error": "Missing required application data (name, email, bank, package)."}), 400

    # Find the bank's URL (to include in the email)
    bank_url = "https://google.com/search?q=student+loans" # Default fallback
    for bank in BANKS:
        if bank['name'] == bank_name:
            bank_url = bank.get('url', bank_url)
            break

    try:
        fee = float(form_data.get('college_fee', 0) or 0)
        years = int(form_data.get('loan_years', 0) or 0)
        total_loan_amount = fee * years
        academic_score = get_academic_score(form_data)
        application_doc = {
            **form_data,
            'user_id': ObjectId(session['user_id']),
            'applied_at': datetime.datetime.utcnow(),
            'selected_bank_name': bank_name,
            'selected_loan_package': loan_package,
            'calculated_total_loan': total_loan_amount,
            'calculated_academic_score': academic_score,
            'status': 'Pending'
        }
        mongo.db.applications.insert_one(application_doc)
    except Exception as e:
        print(f"Error saving to MongoDB: {e}") 
        return jsonify({"error": f"Failed to save application to database. Error: {str(e)}"}), 500

    try:
        subject = f"Confirmation: Your Loan Application with {bank_name}"
        phone = form_data.get('phone', 'N/A')
        aadhaar = form_data.get('aadhaar', 'N/A')
        family_income = float(form_data.get('family_income', 0) or 0)
        college_fee = float(form_data.get('college_fee', 0) or 0)
        loan_years = int(form_data.get('loan_years', 0) or 0)
        total_loan_amount_email = college_fee * loan_years
        study_type = form_data.get('study_type', 'N/A')
        academic_detail = "N/A"
        if study_type == 'university' and form_data.get('univ_level') == 'ug':
            academic_detail = f"12th Grade Marks: {form_data.get('t12_obtained', 'N/A')} / {form_data.get('t12_total', 'N/A')}"
        elif study_type == 'university' and form_data.get('univ_level') == 'pg':
            academic_detail = f"UG CGPA: {form_data.get('ug_cgpa', 'N/A')}"
        elif study_type == 'college':
            academic_detail = f"10th Grade Marks: {form_data.get('t10_obtained', 'N/A')} / {form_data.get('t10_total', 'N/A')}"

        body = (
            f"Dear {student_name},\n\n"
            f"This email confirms your initial application for the '{loan_package}' from {bank_name}.\n\n"
            "--- Application Summary ---\n"
            f"**Bank Selected:** {bank_name} - {loan_package}\n"
            f"**Applied Loan Amount:** INR {total_loan_amount_email:,.0f} (Fee: {college_fee:,.0f} x Years: {loan_years})\n\n"
            "--- Personal Details ---\n"
            f"Name: {student_name}\n"
            f"Email: {student_email}\n"
            f"Phone: {phone}\n"
            f"Aadhaar: {aadhaar}\n"
            f"Annual Family Income: INR {family_income:,.0f}\n\n"
            "--- Academic Details ---\n"
            f"Study Type: {study_type.capitalize()}\n"
            f"Academic Score Detail: {academic_detail}\n\n"
            "To complete your application, please visit the bank's official website:\n" 
            f"{bank_url}\n\n"
            "A representative from the bank may also be in touch with you soon.\n"
            "Please keep all required documents ready.\n\n"
            "Thank you for using our Student Loan Recommendation System.\n"
            "Best regards,\nThe Recommendation Team"
        )
        msg = Message(subject=subject, recipients=[student_email], body=body)
        mail.send(msg)
        
        session.pop('form_data', None)
        
        return jsonify({"message": "Application saved and confirmation email sent successfully!"})
    
    except Exception as e:
        print(f"Error sending email: {e}") 
        return jsonify({"error": f"Application saved, but failed to send email. Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)