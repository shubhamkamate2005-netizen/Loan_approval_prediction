import os
import pickle
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, url_for, redirect, session, flash, jsonify
from flask_mysqldb import MySQL
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'super_secret_key'

load_dotenv()  # This loads the password from the .env file

# FIX: Changed 'localhost' to '127.0.0.1' to prevent Windows Socket Errno 22
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'momdad@com'
app.config['MYSQL_DB'] = 'loan_database'

mysql = MySQL(app)

# --- MODEL LOADING ---
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(BASE_DIR, 'model.pkl')

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
except Exception as e:
    print("Model load error:", e)
    model = None


# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            cur = mysql.connection.cursor()
            # Check if username and password match
            cur.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
            admin = cur.fetchone()
            cur.close()

            if admin:
                session['admin_logged_in'] = True
                return redirect(url_for('applicants'))
            else:
                error = "Invalid Username or Password"
                
        except Exception as e:
            # If the database fails to connect, it will show this error on the webpage instead of crashing
            error = f"Database connection error: {e}"

    return render_template('admin_login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


@app.route('/apply')
def apply():
    return render_template('predict.html') 


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'GET':
        return redirect(url_for('apply'))

    if request.method == 'POST':
        try:
            # A. Get Personal Data
            full_name = request.form['full_name']
            dob = request.form['dob']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            loan_purpose = request.form['loan_purpose']
            state = request.form['state']
            district = request.form['district']
            bank_name = request.form['bank_name']

            # B. Get & Convert Model Features
            income = float(request.form['applicant_income'])
            co_income = float(request.form['coapplicant_income'])
            loan_amt = float(request.form['loan_amount'])
            loan_term = float(request.form['loan_amount_term'])
            credit = float(request.form['credit_history'])
            
            # Manual Encoding
            married = 1 if request.form['married'] == 'Yes' else 0
            
            dep_val = request.form['dependents']
            dependents = 3 if dep_val == '3+' else int(dep_val)
            
            education = 0 if request.form['education'] == 'Graduate' else 1
            self_employed = 1 if request.form['self_employed'] == 'Yes' else 0
            
            prop_map = {'Rural': 0, 'Semiurban': 1, 'Urban': 2}
            property_area_val = prop_map[request.form['property_area']]

            # C. Predict
            status = "Pending"
            if model:
                feature_names = ['Married', 'Dependents', 'Education', 'Self_Employed', 
                                 'Applicant_Income', 'Coapplicant_Income', 'Loan_Amount', 
                                 'Loan_Amount_Term', 'Credit_History', 'Property_Area']

                features = [married, dependents, education, self_employed, 
                            income, co_income, loan_amt, loan_term, 
                            credit, property_area_val]
                
                df_features = pd.DataFrame([features], columns=feature_names)
                prediction = model.predict(df_features)
                
                pred_str = str(prediction[0]).strip().upper()
                if pred_str in ['1', 'Y', 'YES', 'APPROVED']:
                    status = "Approved"
                else:
                    status = "Rejected"

            # D. Save to Database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO applicants 
                (full_name, dob, email, phone, address, state, district, bank_name, loan_purpose, 
                 applicant_income, coapplicant_income, loan_amount, loan_term, 
                 credit_history, property_area, loan_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            """, (full_name, dob, email, phone, address, state, district, bank_name, loan_purpose,
                  income, co_income, loan_amt, loan_term, 
                  credit, property_area_val, status))
            
            mysql.connection.commit()
            cur.close()

            return render_template('result.html', prediction=status, name=full_name)

        except Exception as e:
            return f"Error processing application: {e}"


@app.route('/status', methods=['GET', 'POST'])
def check_status():
    application = None
    error = None
    if request.method == 'POST':
        app_id = request.form['app_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM applicants WHERE id = %s", (app_id,))
        application = cur.fetchone()
        cur.close()
        
        if not application:
            error = f"No application found with ID {app_id}"
            
    return render_template('status.html', application=application, error=error)


@app.route('/applicants')
def applicants():
    # SECURITY FIX: Ensure the user is actually logged in before showing the data
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM applicants ")
    data = cur.fetchall()
    cur.close()
    return render_template('applicants.html', applicants=data)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/doc')
def documentation():
    return render_template('doc.html')


# --- CHATBOT ---
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').lower()
    response = "I didn't understand that. Please try one of the suggested options."

    if any(x in user_input for x in ['hello', 'hi', 'hey']):
        response = "Hello! 👋 I am your Loan Assistant. Select a topic below or ask me a question."

    elif 'apply' in user_input:
        response = "To apply, click the 'Apply Now' tab in the top menu. It takes about 2 minutes to get a result! 🚀"

    elif 'document' in user_input:
        response = "You typically need: <br>1. <b>personal document</b><br>2. <b>applicant Income</b>(salary Details) <br>3. <b>credit Score</b>."

    elif 'status' in user_input:
        import re
        match = re.search(r'\d+', user_input)
        if match:
            app_id = match.group()
            try:
                cur = mysql.connection.cursor()
                cur.execute("SELECT full_name, loan_status FROM applicants WHERE id = %s", (app_id,))
                data = cur.fetchone()
                cur.close()
                if data:
                    icon = "✅" if data[1] == "Approved" else "❌"
                    response = f"Application <b>#{app_id}</b> for {data[0]} is: <b>{data[1]} {icon}</b>"
                else:
                    response = f"🚫 ID {app_id} not found."
            except:
                response = "Database connection error."
        else:
            response = "To check status, please type <b>'Status'</b> followed by your <b>ID Number</b> (e.g., <i>Status 1</i>)."

    return jsonify({'response': response})


if __name__ == "__main__":
    app.run(debug=True)
    