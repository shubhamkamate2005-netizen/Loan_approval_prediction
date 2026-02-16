import numpy as np
import pandas as pd
import pickle
from flask import jsonify, request
from flask import Flask, render_template, request, url_for, redirect, session, flash
from flask_mysqldb import MySQL
from flask import jsonify, request
app = Flask(__name__)
app.secret_key = 'super_secret_key'
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the password from the .env file

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('your_password'),  # Securely grabs password
    'database': 'loan_database'
}

mysql = MySQL(app)

# --- 2. LOAD MODEL ---
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Error: 'model.pkl' not found. Make sure you ran train_model.py")
    model = None

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
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

    return render_template('admin_login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# --- 3. ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

# This route displays the Application Form (which is your predict.html file)
@app.route('/apply')
def apply():
    return render_template('predict.html') 

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    # If someone tries to visit /predict directly, send them to the form
    # if request.method == 'GET':
    #     return redirect(url_for('apply'))

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
            
            # Manual Encoding (must match training data)
            married = 1 if request.form['married'] == 'Yes' else 0
            
            dep_val = request.form['dependents']
            dependents = 3 if dep_val == '3+' else int(dep_val)
            
            education = 0 if request.form['education'] == 'Graduate' else 1
            self_employed = 1 if request.form['self_employed'] == 'Yes' else 0
            
            prop_map = {'Rural': 0, 'Semiurban': 1, 'Urban': 2}
            property_area_val = prop_map[request.form['property_area']]

            # C. Predict
            # --- C. PREDICT (Updated to fix Warning) ---
            status = "Pending"
            if model:
                # 1. Define the exact column names used during training
                feature_names = ['Married', 'Dependents', 'Education', 'Self_Employed', 
                                 'Applicant_Income', 'Coapplicant_Income', 'Loan_Amount', 
                                 'Loan_Amount_Term', 'Credit_History', 'Property_Area']

                # 2. Prepare the data
                features = [married, dependents, education, self_employed, 
                            income, co_income, loan_amt, loan_term, 
                            credit, property_area_val]
                
                # 3. Create a DataFrame (This fixes the warning)
                df_features = pd.DataFrame([features], columns=feature_names)
                
                # 4. Predict
                prediction = model.predict(df_features)
                
                # Handle Result
                pred_str = str(prediction[0]).strip().upper()
                if pred_str in ['1', 'Y', 'YES', 'APPROVED']:
                    status = "Approved"
                else:
                    status = "Rejected"

            # D. Save to Database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO applicants 
                (full_name, dob, email, phone, address,state, district, bank_name, loan_purpose, 
                 applicant_income, coapplicant_income, loan_amount, loan_term, 
                 credit_history, property_area, loan_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s) 
            """, (full_name, dob, email, phone, address,state, district, bank_name, loan_purpose,
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
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM applicants ")
    data = cur.fetchall()
    # after fetching the data came in the form of the tuple of tuple
    # and it store the data by index [0,1,2,3,4....] important 
    print(data)
    cur.close()
    return render_template('applicants.html', applicants=data)

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/doc')
def documentation():
    return render_template('doc.html')
#chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').lower()
    response = "I didn't understand that. Please try one of the suggested options."

    # --- RULE 1: GREETINGS ---
    if any(x in user_input for x in ['hello', 'hi', 'hey']):
        response = "Hello! 👋 I am your Loan Assistant. Select a topic below or ask me a question."

    # --- RULE 2: APPLY ---
    elif 'apply' in user_input:
        response = "To apply, click the 'Apply Now' tab in the top menu. It takes about 2 minutes to get a result! 🚀"

    # --- RULE 3: DOCUMENTS ---
    elif 'document' in user_input:
        response = "You typically need: <br>1. <b>personal document</b><br>2. <b>applicant Income</b>(salary Details) <br>3. <b>credit Score</b>."

    # --- RULE 4: STATUS ---
    elif 'status' in user_input:
        # Check if they provided a number (e.g. "Status 5")
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
