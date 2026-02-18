from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import Counter
from datetime import datetime
import pandas as pd, joblib, re, os, json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'symptom_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY", "sympto-care-secret-key")
db = SQLAlchemy(app)

# ── Models ────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    searches      = db.relationship('SearchHistory', backref='user', lazy=True)
    def set_password(self, p):  self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    symptoms       = db.Column(db.String(500), nullable=False)
    top_prediction = db.Column(db.String(200))
    confidence     = db.Column(db.Float)
    alternatives   = db.Column(db.Text)
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    def confidence_pct(self):
        return f"{self.confidence * 100:.1f}%" if self.confidence is not None else "N/A"

with app.app_context():
    try:
        db.create_all(); print("✅ Database tables ready.")
    except Exception as e:
        print(f"⚠️  DB init failed: {e}")

# ── Auth decorator ────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if 'user_id' not in session:
            flash("Please log in.", "warning")
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrap

# ── ML Model ──────────────────────────────────────────────────────
symptom_columns = []
try:
    model = joblib.load("disease_model.pkl")
    symptom_columns = list(model.feature_names_in_)
    print(f"✅ Model loaded. Symptoms: {len(symptom_columns)}")
except Exception as e:
    print(f"⚠️  Model not loaded: {e}")

# ── Remedies data ─────────────────────────────────────────────────
GENERIC = ["Consult a healthcare professional","Rest and get adequate sleep",
           "Stay hydrated","Eat nutritious meals","Monitor symptoms closely",
           "Maintain good hygiene","Avoid stress","Follow prescribed medications"]

REMEDIES = {
    "Fungal infection":      ["Keep skin dry","Use antifungal cream","Avoid tight clothing","See a dermatologist"],
    "Allergy":               ["Avoid allergens","Take antihistamines","Use nasal sprays","Stay hydrated"],
    "GERD":                  ["Eat smaller meals","Avoid spicy foods","Elevate head while sleeping","Chew gum"],
    "Chronic cholestasis":   ["Drink plenty of water","Balanced diet","Avoid alcohol","See a liver specialist"],
    "Drug Reaction":         ["Stop suspected drug","Seek medical help","Monitor symptoms","Use antihistamines if advised"],
    "Peptic ulcer diseae":   ["Avoid NSAIDs","Eat bland foods","Take prescribed meds","Avoid smoking"],
    "AIDS":                  ["Follow antiretroviral therapy","Maintain hygiene","Nutritious food","Regular check-ups"],
    "Diabetes":              ["Monitor blood sugar","Exercise regularly","Low-carb diet","Take insulin/meds as prescribed"],
    "Gastroenteritis":       ["Stay hydrated","BRAT diet","Avoid dairy","Rest"],
    "Bronchial Asthma":      ["Use inhaler","Avoid triggers","Breathing exercises","Keep emergency meds"],
    "Hypertension":          ["Reduce salt","Exercise daily","Monitor BP","Take meds regularly"],
    "Migraine":              ["Rest in dark room","Cold compress","Stay hydrated","Avoid triggers"],
    "Cervical spondylosis":  ["Neck exercises","Ergonomic chair","Heat packs","Physiotherapy"],
    "Paralysis (brain hemorrhage)": ["Rehab therapy","Physical exercises","Healthy diet","Medical supervision"],
    "Jaundice":              ["Drink fluids","Light foods","Avoid fatty foods","Medical monitoring"],
    "Malaria":               ["Antimalarial drugs","Rest","Stay hydrated","Mosquito nets"],
    "Chicken pox":           ["Isolate","Calamine lotion","Antihistamines","Avoid scratching"],
    "Dengue":                ["Drink fluids","Rest","Monitor platelet count","Avoid painkillers without prescription"],
    "Typhoid":               ["Antibiotics","Boiled water","Light foods","Maintain hygiene"],
    "hepatitis A":           ["Rest","Nutritious food","Avoid alcohol","Vaccination if needed"],
    "Hepatitis B":           ["Antiviral meds","Healthy lifestyle","Liver tests","Avoid sharing needles"],
    "Hepatitis C":           ["Antiviral treatment","Avoid alcohol","Healthy diet","Monitor liver health"],
    "Hepatitis D":           ["Similar to Hepatitis B","Specialist care","Vaccination","Lifestyle changes"],
    "Hepatitis E":           ["Hydration","Rest","Nutritious diet","Avoid contaminated water"],
    "Alcoholic hepatitis":   ["Stop alcohol","Liver-supporting diet","Medical detox","Regular check-ups"],
    "Tuberculosis":          ["Complete TB regimen","Isolate if contagious","Nutritious diet","Rest"],
    "Common Cold":           ["Rest","Drink fluids","Gargle salt water","Use humidifier"],
    "Pneumonia":             ["Antibiotics","Rest","Stay hydrated","Oxygen if needed"],
    "Dimorphic hemmorhoids(piles)": ["High-fiber diet","Drink water","Avoid straining","Topical creams"],
    "Heart attack":          ["Call emergency","Chew aspirin","CPR if trained","Lifestyle changes post-recovery"],
    "Varicose veins":        ["Elevate legs","Compression socks","Exercise","Avoid standing long"],
    "Hypothyroidism":        ["Thyroid meds","Iodine-rich diet","Regular thyroid tests","Exercise"],
    "Hyperthyroidism":       ["Antithyroid drugs","Beta-blockers","Radioactive iodine","Surgery if needed"],
    "Hypoglycemia":          ["Small frequent meals","Carry glucose tabs","Monitor sugar","Avoid skipping meals"],
    "Osteoarthristis":       ["Joint exercises","Weight management","Pain relievers","Physical therapy"],
    "Arthritis":             ["Anti-inflammatory meds","Exercise","Heat/cold therapy","Healthy diet"],
    "(vertigo) Paroymsal  Positional Vertigo": ["Epley maneuver","Vestibular rehab","Avoid sudden movements","Hydration"],
    "Acne":                  ["Wash face gently","Acne creams","Avoid picking","Healthy diet"],
    "Urinary tract infection": ["Drink water","Cranberry juice","Antibiotics","Urinate frequently"],
    "Psoriasis":             ["Moisturize skin","UV therapy","Steroid creams","Avoid triggers"],
    "Impetigo":              ["Antibiotic ointments","Keep wounds clean","Isolate","Hygiene"],
}

# ── Helpers ───────────────────────────────────────────────────────
def load_dataset():
    default = ["fever","cough","headache","fatigue","nausea","body_pain","sore_throat","runny_nose"]
    checks  = [s.lower().replace(" ","_") for s in (symptom_columns or default)]
    for fname in ("sample_dataset.csv","data.csv","dataset.csv"):
        try:
            df = pd.read_csv(fname)
            if any(s in [c.lower().replace(" ","_") for c in df.columns] for s in checks):
                return df
        except Exception:
            continue
    return pd.DataFrame()

def to_int(val):
    try: return int(val)
    except Exception:
        try: return int(float(val))
        except Exception: return 1 if str(val).strip().lower() in ("1","true","yes","y") else 0

def get_remedies(name):
    if name in REMEDIES: return REMEDIES[name]
    for k, v in REMEDIES.items():
        if k.lower() == name.lower() or name.lower() in k.lower() or k.lower() in name.lower():
            return v
    return GENERIC

def save_to_session(uid, uname): session['user_id'] = uid; session['username'] = uname

# ── Auth routes ───────────────────────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def register():
    if 'user_id' in session: return redirect(url_for('predict'))
    if request.method == "POST":
        u, p, c = (request.form.get(x,"").strip() for x in ("username","password","confirm_password"))
        if not u or not p:             flash("Username and password required.", "error")
        elif len(u) < 3:               flash("Username must be 3+ characters.", "error")
        elif len(p) < 6:               flash("Password must be 6+ characters.", "error")
        elif p != c:                   flash("Passwords do not match.", "error")
        elif User.query.filter_by(username=u).first(): flash("Username taken.", "error")
        else:
            user = User(username=u); user.set_password(p)
            db.session.add(user); db.session.commit()
            save_to_session(user.id, user.username)
            flash(f"Welcome, {u}!", "success")
            return redirect(url_for('predict'))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if 'user_id' in session: return redirect(url_for('predict'))
    if request.method == "POST":
        u, p = (request.form.get(x,"").strip() for x in ("username","password"))
        user = User.query.filter_by(username=u).first()
        if user and user.check_password(p):
            save_to_session(user.id, user.username)
            flash(f"Welcome back, {u}!", "success")
            return redirect(url_for('predict'))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

# ── App routes ────────────────────────────────────────────────────
@app.route("/")
def home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template("home.html")

@app.route("/history")
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    searches = (SearchHistory.query.filter_by(user_id=session['user_id'])
                .order_by(SearchHistory.timestamp.desc())
                .paginate(page=page, per_page=20, error_out=False))
    return render_template("history.html", searches=searches)

@app.route("/history/delete/<int:rid>", methods=["POST"])
@login_required
def delete_history(rid):
    r = SearchHistory.query.filter_by(id=rid, user_id=session['user_id']).first_or_404()
    try:    db.session.delete(r); db.session.commit(); flash("Record deleted.", "success")
    except: db.session.rollback(); flash("Could not delete.", "error")
    return redirect(url_for('history'))

@app.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    try:    SearchHistory.query.filter_by(user_id=session['user_id']).delete(); db.session.commit(); flash("History cleared.", "success")
    except: db.session.rollback(); flash("Could not clear history.", "error")
    return redirect(url_for('history'))

@app.route("/predict", methods=["GET","POST"])
@login_required
def predict():
    error_msg, search_query, confidence_scores, disease_remedies = "", "", [], []
    matched_diseases, matched_examples, top_diseases = [], [], []

    full_df      = load_dataset()
    data_columns = list(full_df.columns) if not full_df.empty else []
    symptom_in_csv = [c for c in symptom_columns if c in full_df.columns]

    if request.method == "POST":
        search_query = (request.form.get("search_symptoms") or "").strip()
        if not search_query:          error_msg = "Please enter at least one symptom."
        elif len(search_query) > 500: error_msg = "Input too long (max 500 chars)."
        elif len(search_query) < 2:   error_msg = "Please enter valid symptoms."
        else:
            sq = re.sub(r'[^a-zA-Z0-9\s,\-]', '', search_query).strip()
            if not sq: error_msg = "Invalid characters in input."
            else:      search_query = sq

        if search_query and not error_msg:
            # Build column map
            col_map = {str(c).lower().strip().replace(" ","_").replace("-","_"): str(c) for c in full_df.columns}

            # Match symptom tokens to columns
            requested_cols, not_found = [], []
            for t in [t.strip() for t in search_query.replace(';',',').split(',') if t.strip()]:
                k = t.lower().strip().replace(" ","_").replace("-","_")
                match = col_map.get(k) or next((v for nk,v in col_map.items() if k in nk or nk in k), None)
                (requested_cols if match else not_found).append(match or t)

            # Find matching rows
            matched_rows = []
            for idx, row in full_df.iterrows():
                if all(to_int(row.get(rc, 0)) for rc in requested_cols):
                    matched_rows.append((idx, row))

            # Extract diseases
            diseases = [str(d) for _, row in matched_rows
                        for d in [row.get("Disease") or row.get("disease") or row.get("prognosis")]
                        if d and str(d).strip().lower() not in ("no disease","no_disease","none","nan","no")]

            matched_diseases = list(dict.fromkeys(diseases))

            if diseases:
                counts      = Counter(diseases)
                top_diseases = counts.most_common(20)
                total        = len(matched_rows)
                confidence_scores = [(d, c/total) for d,c in top_diseases]
                disease_remedies  = get_remedies(str(confidence_scores[0][0]))

                # Save to DB
                try:
                    alts = [{"disease": str(d), "confidence": round(float(c),4)} for d,c in confidence_scores[1:6]]
                    db.session.add(SearchHistory(
                        user_id=session['user_id'], symptoms=search_query,
                        top_prediction=str(confidence_scores[0][0]),
                        confidence=float(confidence_scores[0][1]),
                        alternatives=json.dumps(alts)))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback(); print(f"⚠️  DB save failed: {e}")

            # Build examples
            for idx, row in matched_rows[:5]:
                present = [n.replace("_"," ").title() for n in symptom_in_csv if to_int(row.get(n,0))]
                matched_examples.append({"_idx": str(idx), "Disease": row.get("Disease"),
                                         "_summary": ", ".join(present[:5]) or "No flagged symptoms"})
            if not requested_cols:
                error_msg = "No matching columns for: " + ", ".join(not_found)

    return render_template("predict.html",
        prediction="", remedies=disease_remedies, symptoms=symptom_columns,
        error=error_msg, data_columns=data_columns, matched_diseases=matched_diseases,
        matched_examples=matched_examples, search_symptoms=search_query,
        available_columns=list(full_df.columns), top_diseases=top_diseases,
        confidence_scores=confidence_scores)

if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)