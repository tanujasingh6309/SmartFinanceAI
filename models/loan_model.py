import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

df = pd.read_csv("dataset/finance_dataset.csv")

df["loan_status"] = (
    (df["credit_score"] >= 700)
).astype(int)

X = df[
    [
        "monthly_income_usd",
        "credit_score"
    ]
]

y = df["loan_status"]

model = RandomForestClassifier()

model.fit(X, y)

pickle.dump(
    model,
    open("loan_model.pkl", "wb")
)

print("Model Trained Successfully")