import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

df = pd.read_csv('Loan_data.csv')

feature_cols = [
    'Married', 
    'Dependents', 
    'Education', 
    'Self_Employed', 
    'Applicant_Income', 
    'Coapplicant_Income', 
    'Loan_Amount', 
    'Loan_Amount_Term', 
    'Credit_History', 
    'Property_Area'
]
target_col = 'Loan_Status'


X = df[feature_cols].copy()
y = df[target_col].copy()


cat_cols = ['Married', 'Dependents', 'Education', 'Self_Employed', 'Property_Area']
imputer_cat = SimpleImputer(strategy='most_frequent')
X[cat_cols] = imputer_cat.fit_transform(X[cat_cols])


num_cols = ['Applicant_Income', 'Coapplicant_Income', 'Loan_Amount', 'Loan_Amount_Term', 'Credit_History']
imputer_num = SimpleImputer(strategy='mean')
X[num_cols] = imputer_num.fit_transform(X[num_cols])


X['Married'] = X['Married'].map({'No': 0, 'Yes': 1})


le_edu = LabelEncoder()
X['Education'] = le_edu.fit_transform(X['Education']) 

X['Self_Employed'] = X['Self_Employed'].map({'No': 0, 'Yes': 1})


le_prop = LabelEncoder()
X['Property_Area'] = le_prop.fit_transform(X['Property_Area']) 


X['Dependents'] = X['Dependents'].replace('3+', 3).astype(float)

Y=1
y = y.map({'N': 0, 'Y': 1})


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)


print(f"Model Accuracy: {model.score(X_test, y_test) * 100:.2f}%")


with open('model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model saved as 'model.pkl'")