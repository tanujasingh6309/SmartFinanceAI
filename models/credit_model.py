import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pickle

df = pd.read_csv(
    "dataset/credit_score.csv"
)

df["Gender"] = df["Gender"].astype("category").cat.codes
df["Education"] = df["Education"].astype("category").cat.codes
df["Marital Status"] = df["Marital Status"].astype("category").cat.codes
df["Home Ownership"] = df["Home Ownership"].astype("category").cat.codes

X = df[
    [
        "Age",
        "Gender",
        "Income",
        "Education",
        "Marital Status",
        "Number of Children",
        "Home Ownership"
    ]
]

df["Credit Score"] = df["Credit Score"].astype("category").cat.codes

y = df["Credit Score"]

model = RandomForestRegressor()

print(df["Credit Score"].unique())

model.fit(X, y)

pickle.dump(
    model,
    open("credit_model.pkl", "wb")
)

print("Credit Score Model Trained Successfully")