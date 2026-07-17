import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle

df = pd.read_csv(
    "dataset/personal_expense_dataset.csv"
)

df["Month_Number"] = range(
    1,
    len(df) + 1
)

X = df[["Month_Number"]]

y = df["Amount"]

model = LinearRegression()

model.fit(X, y)

pickle.dump(
    model,
    open("expense_model.pkl", "wb")
)

print("Expense Model Trained Successfully")