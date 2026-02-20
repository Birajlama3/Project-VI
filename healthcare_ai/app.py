from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from collections import Counter
from datetime import datetime
import pandas as pd, joblib, re, os, json

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(os.path.abspath(os.path.dirname(__file__)),'symptom_tracker.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.environ.get("SECRET_KEY","sympto-care-secret-key"))
db = SQLAlchemy(app)

# ── Models ───────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    searches      = db.relationship('SearchHistory', backref='user', lazy=True)
    def set_password(self, p):   self.password_hash = generate_password_hash(p)
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
    def confidence_pct(self): return f"{self.confidence*100:.1f}%" if self.confidence else "N/A"

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(120), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    hospital  = db.Column(db.String(150))
    available = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    disease   = db.Column(db.String(200))
    appt_date = db.Column(db.String(20))
    appt_time = db.Column(db.String(10))
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    doctor    = db.relationship('Doctor', backref='appointments')
    user      = db.relationship('User', backref='appointments')

# ── Disease → Specialty ──────────────────────────────────────────────────
DS = {
    "Fungal infection":"Dermatologist","Acne":"Dermatologist","Psoriasis":"Dermatologist",
    "Impetigo":"Dermatologist","Chicken pox":"Dermatologist",
    "Allergy":"Allergist","Drug Reaction":"Allergist",
    "GERD":"Gastroenterologist","Peptic ulcer diseae":"Gastroenterologist",
    "Gastroenteritis":"Gastroenterologist","Chronic cholestasis":"Gastroenterologist",
    "Dimorphic hemmorhoids(piles)":"Gastroenterologist",
    "Jaundice":"Hepatologist","hepatitis A":"Hepatologist","Hepatitis B":"Hepatologist",
    "Hepatitis C":"Hepatologist","Hepatitis D":"Hepatologist","Hepatitis E":"Hepatologist",
    "Alcoholic hepatitis":"Hepatologist",
    "Bronchial Asthma":"Pulmonologist","Tuberculosis":"Pulmonologist","Pneumonia":"Pulmonologist",
    "Common Cold":"General Physician",
    "Hypertension":"Cardiologist","Heart attack":"Cardiologist","Varicose veins":"Cardiologist",
    "Migraine":"Neurologist","Paralysis (brain hemorrhage)":"Neurologist",
    "(vertigo) Paroymsal  Positional Vertigo":"Neurologist","Cervical spondylosis":"Neurologist",
    "Diabetes":"Endocrinologist","Hypothyroidism":"Endocrinologist",
    "Hyperthyroidism":"Endocrinologist","Hypoglycemia":"Endocrinologist",
    "AIDS":"Infectious Disease Specialist","Malaria":"Infectious Disease Specialist",
    "Dengue":"Infectious Disease Specialist","Typhoid":"Infectious Disease Specialist",
    "Osteoarthristis":"Orthopedist","Arthritis":"Orthopedist",
    "Urinary tract infection":"Urologist",
}

DOCTORS_SEED = [
    ("Dr. Anika Sharma","Dermatologist","Kathmandu Medical Center"),
    ("Dr. Rohan Thapa","Dermatologist","Skin & Care Clinic"),
    ("Dr. Priya Karki","Allergist","Allergy & Asthma Institute"),
    ("Dr. Suman Rai","Allergist","Kathmandu Hospital"),
    ("Dr. Bikash Shrestha","Gastroenterologist","Digestive Health Center"),
    ("Dr. Nisha Poudel","Gastroenterologist","Norvic International Hospital"),
    ("Dr. Arjun Maharjan","Hepatologist","Liver Disease Institute"),
    ("Dr. Sunita Basnet","Hepatologist","Grande International Hospital"),
    ("Dr. Deepak Adhikari","Pulmonologist","Chest & Lung Clinic"),
    ("Dr. Mina Tamang","Pulmonologist","B&B Hospital"),
    ("Dr. Rajesh Gautam","Cardiologist","Heart Care Center"),
    ("Dr. Sarita Joshi","Cardiologist","Shahid Gangalal Hospital"),
    ("Dr. Amit Pandey","Neurologist","Neuro Care Hospital"),
    ("Dr. Pooja Limbu","Neurologist","Teaching Hospital"),
    ("Dr. Suresh Koirala","Endocrinologist","Diabetes & Hormone Clinic"),
    ("Dr. Anita Hamal","Endocrinologist","Medicare Hospital"),
    ("Dr. Gopal Dhakal","Infectious Disease Specialist","Tropical Disease Center"),
    ("Dr. Rita Shrestha","Infectious Disease Specialist","Patan Hospital"),
    ("Dr. Nabin Gurung","Orthopedist","Bone & Joint Clinic"),
    ("Dr. Sabina KC","Orthopedist","National Ortho Hospital"),
    ("Dr. Binod Acharya","Urologist","Urology & Kidney Center"),
    ("Dr. Kamala Yadav","Urologist","Nepal Medical College"),
    ("Dr. Hari Prasad","General Physician","City General Hospital"),
    ("Dr. Laxmi Bhandari","General Physician","Community Health Clinic"),
]

REMEDIES = {
    "Fungal infection":["Keep skin dry","Use antifungal cream","Avoid tight clothing"],
    "Allergy":["Avoid allergens","Take antihistamines","Stay hydrated"],
    "GERD":["Eat smaller meals","Avoid spicy foods","Elevate head while sleeping"],
    "Chronic cholestasis":["Drink plenty of water","Balanced diet","Avoid alcohol"],
    "Drug Reaction":["Stop suspected drug","Seek medical help","Use antihistamines if advised"],
    "Peptic ulcer diseae":["Avoid NSAIDs","Eat bland foods","Take prescribed meds"],
    "AIDS":["Follow antiretroviral therapy","Maintain hygiene","Regular check-ups"],
    "Diabetes":["Monitor blood sugar","Exercise regularly","Low-carb diet"],
    "Gastroenteritis":["Stay hydrated","BRAT diet","Avoid dairy"],
    "Bronchial Asthma":["Use inhaler","Avoid triggers","Breathing exercises"],
    "Hypertension":["Reduce salt","Exercise daily","Monitor BP"],
    "Migraine":["Rest in dark room","Cold compress","Stay hydrated"],
    "Cervical spondylosis":["Neck exercises","Ergonomic chair","Physiotherapy"],
    "Paralysis (brain hemorrhage)":["Rehab therapy","Physical exercises","Medical supervision"],
    "Jaundice":["Drink fluids","Light foods","Medical monitoring"],
    "Malaria":["Antimalarial drugs","Rest","Mosquito nets"],
    "Chicken pox":["Isolate","Calamine lotion","Avoid scratching"],
    "Dengue":["Drink fluids","Rest","Monitor platelet count"],
    "Typhoid":["Antibiotics","Boiled water","Maintain hygiene"],
    "hepatitis A":["Rest","Nutritious food","Avoid alcohol"],
    "Hepatitis B":["Antiviral meds","Liver tests","Avoid sharing needles"],
    "Hepatitis C":["Antiviral treatment","Avoid alcohol","Monitor liver health"],
    "Hepatitis D":["Specialist care","Vaccination","Lifestyle changes"],
    "Hepatitis E":["Hydration","Rest","Avoid contaminated water"],
    "Alcoholic hepatitis":["Stop alcohol","Medical detox","Regular check-ups"],
    "Tuberculosis":["Complete TB regimen","Nutritious diet","Rest"],
    "Common Cold":["Rest","Drink fluids","Gargle salt water"],
    "Pneumonia":["Antibiotics","Rest","Stay hydrated"],
    "Dimorphic hemmorhoids(piles)":["High-fiber diet","Drink water","Avoid straining"],
    "Heart attack":["Call emergency","Chew aspirin","Lifestyle changes post-recovery"],
    "Varicose veins":["Elevate legs","Compression socks","Exercise"],
    "Hypothyroidism":["Thyroid meds","Iodine-rich diet","Exercise"],
    "Hyperthyroidism":["Antithyroid drugs","Beta-blockers","Surgery if needed"],
    "Hypoglycemia":["Small frequent meals","Carry glucose tabs","Avoid skipping meals"],
    "Osteoarthristis":["Joint exercises","Weight management","Physical therapy"],
    "Arthritis":["Anti-inflammatory meds","Exercise","Heat/cold therapy"],
    "(vertigo) Paroymsal  Positional Vertigo":["Epley maneuver","Avoid sudden movements","Hydration"],
    "Acne":["Wash face gently","Acne creams","Healthy diet"],
    "Urinary tract infection":["Drink water","Cranberry juice","Antibiotics"],
    "Psoriasis":["Moisturize skin","UV therapy","Avoid triggers"],
    "Impetigo":["Antibiotic ointments","Keep wounds clean","Hygiene"],
}
GENERIC = ["Consult a healthcare professional","Rest","Stay hydrated","Monitor symptoms closely"]

# ── Init DB ──────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    if not Doctor.query.count():
        db.session.bulk_save_objects([Doctor(name=n,specialty=s,hospital=h) for n,s,h in DOCTORS_SEED])
        db.session.commit()

# ── Helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrap(*a,**kw):
        if 'user_id' not in session: flash("Please log in.","warning"); return redirect(url_for('login'))
        return f(*a,**kw)
    return wrap

def get_remedies(name):
    if name in REMEDIES: return REMEDIES[name]
    for k,v in REMEDIES.items():
        if k.lower() in name.lower() or name.lower() in k.lower(): return v
    return GENERIC

def get_doctors(disease):
    spec = DS.get(disease) or next((v for k,v in DS.items() if k.lower() in disease.lower()),None) or "General Physician"
    docs = Doctor.query.filter_by(specialty=spec,available=True).limit(2).all()
    return (docs or Doctor.query.filter_by(specialty="General Physician").limit(2).all()), spec

symptom_columns = []
try: model=joblib.load("disease_model.pkl"); symptom_columns=list(model.feature_names_in_)
except: pass

def load_df():
    for f in ("sample_dataset.csv","data.csv","dataset.csv"):
        try:
            df=pd.read_csv(f)
            if any(c.lower().replace(" ","_") in [s.lower() for s in symptom_columns] for c in df.columns): return df
        except: pass
    return pd.DataFrame()

def to_int(v):
    try: return int(v)
    except:
        try: return int(float(v))
        except: return 1 if str(v).strip().lower() in ("1","true","yes","y") else 0

# ── Auth ─────────────────────────────────────────────────────────────────
@app.route("/register",methods=["GET","POST"])
def register():
    if 'user_id' in session: return redirect(url_for('predict'))
    if request.method=="POST":
        u,p,c=(request.form.get(x,"").strip() for x in ("username","password","confirm_password"))
        if not u or not p:                              flash("Username and password required.","error")
        elif len(u)<3:                                  flash("Username must be 3+ characters.","error")
        elif len(p)<6:                                  flash("Password must be 6+ characters.","error")
        elif p!=c:                                      flash("Passwords do not match.","error")
        elif User.query.filter_by(username=u).first():  flash("Username taken.","error")
        else:
            usr=User(username=u); usr.set_password(p); db.session.add(usr); db.session.commit()
            session.update(user_id=usr.id,username=u); flash(f"Welcome, {u}!","success")
            return redirect(url_for('predict'))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if 'user_id' in session: return redirect(url_for('predict'))
    if request.method=="POST":
        u,p=(request.form.get(x,"").strip() for x in ("username","password"))
        usr=User.query.filter_by(username=u).first()
        if usr and usr.check_password(p):
            session.update(user_id=usr.id,username=u); flash(f"Welcome back, {u}!","success")
            return redirect(url_for('predict'))
        flash("Invalid username or password.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); flash("Logged out.","success"); return redirect(url_for('login'))

# ── Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return redirect(url_for('predict') if 'user_id' in session else url_for('login'))

@app.route("/history")
@login_required
def history():
    pg=request.args.get('page',1,type=int)
    searches=SearchHistory.query.filter_by(user_id=session['user_id']).order_by(SearchHistory.timestamp.desc()).paginate(page=pg,per_page=20,error_out=False)
    return render_template("history.html",searches=searches)

@app.route("/history/delete/<int:rid>",methods=["POST"])
@login_required
def delete_history(rid):
    r=SearchHistory.query.filter_by(id=rid,user_id=session['user_id']).first_or_404()
    db.session.delete(r); db.session.commit(); flash("Deleted.","success")
    return redirect(url_for('history'))

@app.route("/history/clear",methods=["POST"])
@login_required
def clear_history():
    SearchHistory.query.filter_by(user_id=session['user_id']).delete(); db.session.commit()
    flash("History cleared.","success"); return redirect(url_for('history'))

@app.route("/appointments")
@login_required
def appointments():
    appts=Appointment.query.filter_by(user_id=session['user_id']).order_by(Appointment.booked_at.desc()).all()
    return render_template("appointments.html",appointments=appts)

@app.route("/book/<int:doctor_id>",methods=["POST"])
@login_required
def book_appointment(doctor_id):
    disease=request.form.get("disease","")
    appt_date=request.form.get("appt_date","")
    appt_time=request.form.get("appt_time","")
    if not appt_date or not appt_time:
        flash("Please select a date and time.","error"); return redirect(url_for('predict'))
    doctor=Doctor.query.get_or_404(doctor_id)
    db.session.add(Appointment(user_id=session['user_id'],doctor_id=doctor_id,
                               disease=disease,appt_date=appt_date,appt_time=appt_time))
    db.session.commit()
    flash(f"✅ Appointment booked with {doctor.name} on {appt_date} at {appt_time}!","success")
    return redirect(url_for('appointments'))

@app.route("/appointments/cancel/<int:appt_id>",methods=["POST"])
@login_required
def cancel_appointment(appt_id):
    appt=Appointment.query.filter_by(id=appt_id,user_id=session['user_id']).first_or_404()
    db.session.delete(appt); db.session.commit()
    flash("Appointment cancelled and removed.","success"); return redirect(url_for('appointments'))

@app.route("/predict",methods=["GET","POST"])
@login_required
def predict():
    err,sq,scores,rem,docs,spec="","",[],"",[],"",
    matched,top=[],[]
    df=load_df(); cols=list(df.columns) if not df.empty else []
    syms=[c for c in symptom_columns if c in df.columns]

    if request.method=="POST":
        sq=re.sub(r'[^a-zA-Z0-9\s,\-]','',request.form.get("search_symptoms","").strip())
        if not sq: err="Please enter at least one symptom."
        else:
            col_map={str(c).lower().strip().replace(" ","_").replace("-","_"):str(c) for c in df.columns}
            req=[]
            for t in [t.strip() for t in sq.replace(';',',').split(',') if t.strip()]:
                k=t.lower().replace(" ","_").replace("-","_")
                m=col_map.get(k) or next((v for nk,v in col_map.items() if k in nk or nk in k),None)
                if m: req.append(m)
            rows=[(i,r) for i,r in df.iterrows() if all(to_int(r.get(c,0)) for c in req)]
            diseases=[str(d) for _,r in rows for d in [r.get("Disease") or r.get("disease") or r.get("prognosis")]
                      if d and str(d).strip().lower() not in ("no disease","none","nan","no")]
            matched=list(dict.fromkeys(diseases))
            if diseases:
                cnt=Counter(diseases); top=cnt.most_common(20); total=len(rows)
                scores=[(d,c/total) for d,c in top]
                rem=get_remedies(str(scores[0][0]))
                docs,spec=get_doctors(str(scores[0][0]))
                try:
                    alts=[{"disease":str(d),"confidence":round(float(c),4)} for d,c in scores[1:6]]
                    db.session.add(SearchHistory(user_id=session['user_id'],symptoms=sq,
                        top_prediction=str(scores[0][0]),confidence=float(scores[0][1]),alternatives=json.dumps(alts)))
                    db.session.commit()
                except: db.session.rollback()
            elif not req: err=f"No matching symptoms found for: {sq}"

    return render_template("predict.html",remedies=rem,symptoms=symptom_columns,error=err,
        search_symptoms=sq,top_diseases=top,confidence_scores=scores,matched_diseases=matched,
        recommended_doctors=docs,recommended_specialty=spec,prediction="",
        data_columns=cols,matched_examples=[],available_columns=cols)

if __name__=="__main__":
    app.run(debug=True)