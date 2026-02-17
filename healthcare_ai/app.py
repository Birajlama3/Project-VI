from flask import Flask, render_template, request
import pandas as pd
import joblib
from collections import Counter

app = Flask(__name__)

# Load the model
model = None
symptom_columns = []
try:
    model = joblib.load("disease_model.pkl")
    # Get the expected symptom columns from the trained model
    symptom_columns = list(model.feature_names_in_)
    print(f"Model loaded successfully. Expected symptoms: {len(symptom_columns)}")  # Debug print
except FileNotFoundError:
    print("Warning: 'disease_model.pkl' not found. Please train and save the model first. Using fallback (no predictions possible).")
    # No exit() - continue with None
except Exception as e:
    print(f"Error loading model: {e}. Using fallback.")
    # No exit() - continue

# 🏥 Generic remedies for diseases without specific remedies
generic_remedies = [
    "Consult a healthcare professional for proper diagnosis",
    "Rest and get adequate sleep",
    "Stay hydrated by drinking plenty of water",
    "Eat nutritious, balanced meals",
    "Monitor your symptoms closely",
    "Maintain good hygiene practices",
    "Avoid stress and manage anxiety",
    "Follow prescribed medications if advised"
]

# 🏥 Expanded home remedies database (based on the 41 diseases in the dataset)
remedies = {
    "Fungal infection": ["Keep skin dry", "Use antifungal cream", "Avoid tight clothing", "Consult a dermatologist"],
    "Allergy": ["Avoid allergens", "Take antihistamines", "Use nasal sprays", "Stay hydrated"],
    "GERD": ["Eat smaller meals", "Avoid spicy foods", "Elevate head while sleeping", "Chew gum to increase saliva"],
    "Chronic cholestasis": ["Drink plenty of water", "Eat a balanced diet", "Avoid alcohol", "Consult a liver specialist"],
    "Drug Reaction": ["Stop the suspected drug", "Seek medical help", "Monitor symptoms", "Use antihistamines if advised"],
    "Peptic ulcer diseae": ["Avoid NSAIDs", "Eat bland foods", "Take prescribed meds", "Avoid smoking"],
    "AIDS": ["Follow antiretroviral therapy", "Maintain hygiene", "Eat nutritious food", "Regular check-ups"],
    "Diabetes": ["Monitor blood sugar", "Exercise regularly", "Eat low-carb diet", "Take insulin/meds as prescribed"],
    "Gastroenteritis": ["Stay hydrated", "Eat BRAT diet", "Avoid dairy", "Rest and recover"],
    "Bronchial Asthma": ["Use inhaler", "Avoid triggers", "Practice breathing exercises", "Keep emergency meds"],
    "Hypertension": ["Reduce salt intake", "Exercise daily", "Monitor BP", "Take meds regularly"],
    "Migraine": ["Rest in dark room", "Apply cold compress", "Stay hydrated", "Avoid triggers like stress"],
    "Cervical spondylosis": ["Do neck exercises", "Use ergonomic chair", "Apply heat packs", "Consult physiotherapist"],
    "Paralysis (brain hemorrhage)": ["Rehabilitation therapy", "Physical exercises", "Healthy diet", "Medical supervision"],
    "Jaundice": ["Drink fluids", "Eat light foods", "Avoid fatty foods", "Medical monitoring"],
    "Malaria": ["Take antimalarial drugs", "Rest well", "Stay hydrated", "Use mosquito nets"],
    "Chicken pox": ["Isolate yourself", "Use calamine lotion", "Take antihistamines", "Avoid scratching"],
    "Dengue": ["Drink fluids", "Rest", "Monitor platelet count", "Avoid painkillers without prescription"],
    "Typhoid": ["Take antibiotics", "Drink boiled water", "Eat light foods", "Maintain hygiene"],
    "hepatitis A": ["Rest", "Eat nutritious food", "Avoid alcohol", "Vaccination if needed"],
    "Hepatitis B": ["Antiviral meds", "Healthy lifestyle", "Regular liver tests", "Avoid sharing needles"],
    "Hepatitis C": ["Antiviral treatment", "Avoid alcohol", "Healthy diet", "Monitor liver health"],
    "Hepatitis D": ["Similar to Hepatitis B", "Seek specialist care", "Vaccination", "Lifestyle changes"],
    "Hepatitis E": ["Hydration", "Rest", "Nutritious diet", "Avoid contaminated water"],
    "Alcoholic hepatitis": ["Stop alcohol", "Liver-supporting diet", "Medical detox", "Regular check-ups"],
    "Tuberculosis": ["Complete TB regimen", "Isolate if contagious", "Nutritious diet", "Rest"],
    "Common Cold": ["Rest", "Drink fluids", "Gargle salt water", "Use humidifier"],
    "Pneumonia": ["Antibiotics", "Rest", "Stay hydrated", "Use oxygen if needed"],
    "Dimorphic hemmorhoids(piles)": ["High-fiber diet", "Drink water", "Avoid straining", "Topical creams"],
    "Heart attack": ["Call emergency", "Chew aspirin", "CPR if trained", "Lifestyle changes post-recovery"],
    "Varicose veins": ["Elevate legs", "Wear compression socks", "Exercise", "Avoid standing long"],
    "Hypothyroidism": ["Thyroid meds", "Iodine-rich diet", "Regular thyroid tests", "Exercise"],
    "Hyperthyroidism": ["Antithyroid drugs", "Beta-blockers", "Radioactive iodine", "Surgery if needed"],
    "Hypoglycemia": ["Eat small frequent meals", "Carry glucose tabs", "Monitor sugar", "Avoid skipping meals"],
    "Osteoarthristis": ["Joint exercises", "Weight management", "Pain relievers", "Physical therapy"],
    "Arthritis": ["Anti-inflammatory meds", "Exercise", "Heat/cold therapy", "Healthy diet"],
    "(vertigo) Paroymsal  Positional Vertigo": ["Epley maneuver", "Vestibular rehab", "Avoid sudden movements", "Hydration"],
    "Acne": ["Wash face gently", "Use acne creams", "Avoid picking", "Healthy diet"],
    "Urinary tract infection": ["Drink water", "Cranberry juice", "Antibiotics", "Urinate frequently"],
    "Psoriasis": ["Moisturize skin", "UV therapy", "Steroid creams", "Avoid triggers"],
    "Impetigo": ["Antibiotic ointments", "Keep wounds clean", "Isolate", "Hygiene"]
}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    prediction = ""
    disease_remedies = []
    error_message = ""
    matched_diseases = []
    matched_examples = []
    search_query = ""
    confidence_scores = []  # NEW: Store confidence scores

    # Load latest data.csv for display (reload each request so newest file is used)
    # Try data.csv first, but prefer a file that contains symptom-like columns
    full_df = pd.DataFrame()
    # prefer the small sample dataset for development/testing
    files_to_try = ("sample_dataset.csv", "data.csv", "dataset.csv")

    # helper to detect symptom-like columns
    default_symptoms = ["fever", "cough", "headache", "fatigue", "nausea", "body_pain", "sore_throat", "runny_nose"]
    for fname in files_to_try:
        try:
            df_try = pd.read_csv(fname)
        except Exception:
            continue

        # decide whether this file looks suitable: contains at least one symptom-like column
        lower_cols = [str(c).lower().replace(" ", "_") for c in df_try.columns]
        # use model symptom list if available, otherwise fallback to default_symptoms
        symptom_checks = [s.lower().replace(" ", "_") for s in (symptom_columns or default_symptoms)]
        has_symptom = any(s in lower_cols for s in symptom_checks)

        if has_symptom:
            full_df = df_try
            print(f"Loaded dataset from {fname} (contains symptom-like columns)")
            break
        else:
            # keep as candidate but continue to next file
            full_df = df_try
            print(f"Loaded dataset from {fname} (no symptom-like columns detected)")
            # continue loop to try next file


    data_columns = list(full_df.columns) if not full_df.empty else []
    # Determine which columns in the CSV correspond to symptoms the model expects
    symptom_in_csv = [c for c in symptom_columns if c in full_df.columns] if not full_df.empty else []

    # Handle symptom-search (Option C): find dataset rows that match entered symptoms
    if request.method == "POST":
        # Get text input
        search_query = (request.form.get("search_symptoms") or "").strip()
        
        # NEW: Input validation and sanitization
        if not search_query:
            error_message = "Please enter at least one symptom."
        elif len(search_query) > 500:
            error_message = "Input too long. Please keep symptoms under 500 characters."
        elif len(search_query) < 2:
            error_message = "Please enter valid symptoms (at least 2 characters)."
        else:
            # Sanitize: remove special characters except commas, spaces, hyphens
            import re
            sanitized_query = re.sub(r'[^a-zA-Z0-9\s,\-]', '', search_query)
            if not sanitized_query.strip():
                error_message = "Input contains invalid characters. Use letters, numbers, commas, and hyphens only."
            else:
                search_query = sanitized_query
        
        if search_query and not error_message:
            # Build normalized map of CSV column normalized-name -> actual column
            col_map = {}
            norm_cols = {}
            for c in full_df.columns:
                raw = str(c)
                key = raw.lower().strip()
                # normalize: replace spaces/dashes and collapse repeated chars
                key = key.replace(" ", "_").replace("-", "_")
                col_map[key] = raw
                norm_cols[key] = raw

            print(f"DEBUG: available columns -> {list(full_df.columns)[:20]}")

            # detect disease column (any column name containing 'disease')
            disease_col = None
            for k, v in norm_cols.items():
                if "disease" in k:
                    disease_col = v
                    break
            if not disease_col:
                # try common variants
                for cand in ("prognosis", "diagnosis", "label"):
                    for k, v in norm_cols.items():
                        if cand in k:
                            disease_col = v
                            break
                    if disease_col:
                        break
            print(f"DEBUG: detected disease column -> {disease_col}")

            # Parse user input (comma or space separated)
            tokens = [t.strip() for t in search_query.replace(';', ',').split(',') if t.strip()]
            requested_cols = []
            not_found = []
            for t in tokens:
                k = t.lower().strip().replace(" ", "_").replace("-", "_")
                if k in col_map:
                    requested_cols.append(col_map[k])
                else:
                    # try contains match (token contained in column or column contained in token)
                    match = None
                    for nk, real in norm_cols.items():
                        if k in nk or nk in k:
                            match = real
                            break
                    if match:
                        requested_cols.append(match)
                    else:
                        not_found.append(t)

            # Search dataset rows where all requested_cols are truthy (1/yes/true)
            matched_rows = []
            if requested_cols:
                for idx, row in full_df.iterrows():
                    ok = True
                    for rc in requested_cols:
                        val = row.get(rc, 0)
                        try:
                            v = int(val)
                        except Exception:
                            try:
                                v = int(float(val))
                            except Exception:
                                sval = str(val).strip().lower()
                                v = 1 if sval in ("1", "true", "yes", "y") else 0
                        if v == 0:
                            ok = False
                            break
                    if ok:
                        matched_rows.append((idx, row))

            # Build matched disease list and small preview (limit 5)
            diseases = []
            for idx, row in matched_rows:
                d = row.get("Disease") or row.get("disease") or row.get("prognosis")
                if d is not None:
                    diseases.append(str(d))

            # filter out non-informative labels (e.g. 'No Disease')
            def _is_informative(name):
                if not name:
                    return False
                s = str(name).strip().lower()
                return s not in ("no disease", "no_disease", "none", "nan", "no")

            diseases = [d for d in diseases if _is_informative(d)]
            matched_diseases = list(dict.fromkeys(diseases))  # unique in order
            # compute top disease counts for UI ranking
            if diseases:
                counts = Counter(diseases)
                top_diseases = counts.most_common(20)
                
                # NEW: Calculate confidence scores based on frequency
                total_matches = len(matched_rows)
                confidence_scores = []
                for disease, count in top_diseases:
                    confidence = count / total_matches if total_matches > 0 else 0
                    confidence_scores.append((disease, confidence))
            else:
                top_diseases = []
                confidence_scores = []

            # prepare recommended home remedies for the top disease (if available)
            disease_remedies = []
            if confidence_scores:
                top_name = str(confidence_scores[0][0])
                # direct match
                if top_name in remedies:
                    disease_remedies = remedies[top_name]
                else:
                    # case-insensitive or contains match fallback
                    found = False
                    for rk, rv in remedies.items():
                        if rk.lower() == top_name.lower() or top_name.lower() in rk.lower() or rk.lower() in top_name.lower():
                            disease_remedies = rv
                            found = True
                            break
                    # NEW: If no specific remedies found, use generic remedies
                    if not found:
                        disease_remedies = generic_remedies
            print(f"DEBUG: requested_cols -> {requested_cols}")
            print(f"DEBUG: matched {len(matched_rows)} rows")
            print(f"DEBUG: confidence_scores -> {confidence_scores[:3]}")
            for idx, row in matched_rows[:5]:
                rec = {"_idx": str(idx), "Disease": row.get("Disease")}
                # build short summary using symptom_in_csv
                present = []
                for name in symptom_in_csv:
                    try:
                        val = int(row.get(name, 0))
                    except Exception:
                        try:
                            val = int(float(row.get(name, 0)))
                        except Exception:
                            sval = str(row.get(name, "")).strip().lower()
                            val = 1 if sval in ("1", "true", "yes", "y") else 0
                    if val:
                        present.append(name.replace("_", " ").title())
                rec["_summary"] = ", ".join(present[:5]) or "No flagged symptoms"
                matched_examples.append(rec)

            if not requested_cols:
                error_message = "No matching dataset columns found for input symptoms: " + ", ".join(not_found)
    # Note: Option A/B removed — predictions are sourced from dataset matching (Option C)

    available_columns = list(full_df.columns)
    # ensure top_diseases is defined even if no search executed
    try:
        top_diseases
    except NameError:
        top_diseases = []

    return render_template("predict.html",
                           prediction=prediction,
                           remedies=disease_remedies,
                           symptoms=symptom_columns,  # Pass to template for dynamic form
                           error=error_message,
                           data_columns=data_columns,
                           matched_diseases=matched_diseases,
                           matched_examples=matched_examples,
                           search_symptoms=search_query,
                           available_columns=available_columns,
                           top_diseases=top_diseases,
                           confidence_scores=confidence_scores)  # NEW: Pass confidence scores

if __name__ == "__main__":
    print("Starting Flask app...")  # Debug print
    app.run(debug=True)  # Set debug=False for production