import pandas as pd
import joblib

model = joblib.load("disease_model.pkl")
print("Model ready!")

# Ask user for input
symptoms = {}
for col in ["fever","cough","headache","fatigue","nausea","body_pain","sore_throat","runny_nose"]:
    val = input(f"Does the patient have {col}? (0=no,1=yes): ")
    symptoms[col] = int(val)

data = pd.DataFrame([symptoms])
pred = model.predict(data)
print("Predicted Disease:", pred[0])
