import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

df = pd.read_csv(
    "dataset/financial_risk_assessment.csv"
)

df["Previous Defaults"] = (
    df["Previous Defaults"]
    .map({"Yes": 1, "No": 0})
)

X = df[
    [
        "Income",
        "Credit Score",
        "Loan Amount",
        "Debt-to-Income Ratio",
        "Assets Value",
        "Previous Defaults"
    ]
]

y = df["Risk Rating"]

model = RandomForestClassifier()

model.fit(X, y)

pickle.dump(
    model,
    open("risk_model.pkl", "wb")
)

print("Risk Model Trained Successfully")