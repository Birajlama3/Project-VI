from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)
model = joblib.load("disease_model.pkl")

# 🏥 Home remedies database
remedies = {
    "Flu": [
        "Drink warm fluids",
        "Take proper rest",
        "Steam inhalation",
        "Gargle with salt water"
    ],
    "Cold": [
        "Stay hydrated",
        "Drink ginger tea",
        "Use nasal spray",
        "Rest well"
    ],
    "Dengue": [
        "Drink plenty of fluids",
        "Papaya leaf juice (consult doctor)",
        "Take rest",
        "Avoid painkillers without prescription"
    ],
    "Migraine": [
        "Rest in dark quiet room",
        "Apply cold compress",
        "Stay hydrated",
        "Avoid loud noise"
    ],
    "Typhoid": [
        "Drink boiled water",
        "Eat light foods",
        "Take prescribed antibiotics",
        "Maintain hygiene"
    ]
}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    prediction = ""
    disease_remedies = []

    if request.method == "POST":
        symptom_columns = [
            "fever","cough","headache","fatigue",
            "nausea","body_pain","sore_throat","runny_nose"
        ]

        symptoms = {col: int(request.form[col]) if col in request.form else 0 for col in symptom_columns}
        df = pd.DataFrame([symptoms])
        pred = model.predict(df)

        prediction = pred[0]

        # Get remedies for predicted disease
        disease_remedies = remedies.get(prediction, [])

    return render_template("predict.html",
                           prediction=prediction,
                           remedies=disease_remedies)

if __name__ == "__main__":
    app.run(debug=True)
