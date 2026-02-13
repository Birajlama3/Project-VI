import pandas as pd

print("Script started...")

data = pd.read_csv("dataset.csv")

print("Rows:", len(data))
print("Columns:", len(data.columns))
print("Data preview:")
print(data)

