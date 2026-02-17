# 🏥 SymptoCare — Intelligent Health Predictor

A friendly, AI-powered symptom checker that helps you understand common health conditions based on your symptoms.

## ⚠️ Medical Disclaimer

**IMPORTANT:** SymptoCare is an **educational tool for informational purposes only**. It is **NOT a substitute** for professional medical advice, diagnosis, or treatment. 

- Always consult with a qualified healthcare provider for accurate medical guidance
- Never delay seeking professional help based on information from this tool
- This app is not a replacement for emergency medical services
- Use this tool to supplement, not replace, medical consultations

---

## ✨ Features

- 🔍 **Smart Symptom Matching** — Enter symptoms naturally or comma-separated; the app matches them to common conditions
- **Confidence Scores** — See likelihood percentages for each predicted condition
-  **Home Remedies** — Get suggested remedies and self-care tips for each condition
-  **Dataset-Based** — Predictions based on real symptom-disease patterns in the training data
-  **Responsive Design** — Works seamlessly on desktop, tablet, and mobile devices
-  **Fast & Lightweight** — No account required; instant results

---

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd healthcare_ai
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train the model** (if `disease_model.pkl` doesn't exist)
   ```bash
   python3 train_model.py
   ```

5. **Run the app**
   ```bash
   python3 app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## 📖 How to Use

### Home Page
- Learn about SymptoCare and its features
- Click "Check My Symptoms" to get started

### Predict Page
1. **Enter Your Symptoms**
   - Type naturally: "I have a headache and feel nauseous"
   - Or use comma-separated format: "headache, nausea, fever"
   - Max 500 characters

2. **Click "Analyze"**
   - The app searches the dataset for matching symptom patterns
   - Shows a loading spinner while processing

3. **Review Results**
   - **Primary Prediction** — Most likely condition with confidence %
   - **Alternatives** — Other possible conditions ranked by likelihood
   - **Home Remedies** — Suggested self-care tips for the primary condition

---

## 📁 Project Structure

```
healthcare_ai/
├── app.py                    # Flask app & prediction logic
├── train_model.py            # Model training script
├── check_data.py             # Data validation utility
├── requirements.txt          # Python dependencies
├── disease_model.pkl         # Trained RandomForest model
├── data.csv                  # Full training dataset
├── sample_dataset.csv        # Small sample for testing
├── static/
│   └── style.css            # Styling & animations
└── templates/
    ├── home.html            # Home page
    └── predict.html         # Prediction page
```

---

## 🔧 Technologies

- **Backend:** Flask (Python web framework)
- **ML Model:** scikit-learn (RandomForest Classifier)
- **Frontend:** HTML, CSS, Jinja2 templating
- **Data:** Pandas, NumPy

---

## 📊 Model Information

- **Algorithm:** Random Forest Classifier
- **Training Data:** 41 common diseases with symptom patterns
- **Features:** Multiple health symptoms (binary encoding)
- **Accuracy:** Varies based on input clarity and data quality

---

## 🚀 What Gets Displayed

### For Each Prediction:

1. **Confidence Score** — Percentage likelihood based on symptom matches
2. **Top Disease** — Most probable condition
3. **Alternatives** — Up to 5 other possible conditions with percentages
4. **Home Remedies**
   - Disease-specific remedies if available
   - Generic wellness tips if disease not in database

---

## 🛡 Data Privacy

- ✅ **No data storage** — Your symptom input is NOT saved
- ✅ **No tracking** — No analytics or cookies tracking your usage
- ✅ **Local processing** — All analysis happens locally on the server
- ✅ **No third-party sharing** — Your data is never shared

---

## 🐛 Troubleshooting

### App won't start
```bash
# Check if port 5000 is in use
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows
```

### Model not found error
```bash
# Retrain the model
python3 train_model.py
```

### No symptoms matching
- Try different phrasing: "headache" vs "head pain"
- Use symptoms that exist in the dataset
- Separate symptoms with commas

---

## 📝 Example Inputs

✅ **Good examples:**
- "fever and cough"
- "headache, nausea, fatigue"
- "I have body pain and feel tired"

❌ **Avoid:**
- Very vague: "I don't feel good"
- Made-up symptoms: "zxyzblorp"
- Too many symptoms: 10+ at once (narrows results too much)

---

## 🔄 Model Training

To retrain with new data:

```bash
python3 train_model.py
```

This script:
- Loads data from `data.csv`
- Splits into 80% training, 20% testing
- Trains a RandomForest model
- Saves to `disease_model.pkl`
- Displays accuracy metrics

---

## 📚 Limitations

- ⚠️ **Not a diagnostic tool** — Cannot replace professional medical evaluation
- ⚠️ **Dataset-dependent** — Only works with known symptom patterns
- ⚠️ **No severity assessment** — Doesn't evaluate symptom severity
- ⚠️ **No emergency detection** — Cannot identify life-threatening conditions
- ⚠️ **General knowledge only** — Limited to 41 common diseases

**If you experience severe symptoms, chest pain, difficulty breathing, or other emergencies, call emergency services immediately.**

---

## 🤝 Contributing

Found a bug or want to improve the app?
- Check data quality in `check_data.py`
- Improve the remedies dictionary in `app.py`
- Enhance styling in `static/style.css`
- Add more diseases to the training data

---

## 📄 License

This project is provided for educational purposes.

---

## 🎓 Educational Note

This project demonstrates:
- Machine Learning basics (classification)
- Web development with Flask
- Data processing with Pandas
- Front-end UI/UX design
- Responsible AI practices (disclaimers, limitations)

---

## 💬 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the example inputs
3. Verify your environment setup
4. Check console logs in `app.py`

---

**Stay healthy! 💚 Remember: This tool is for learning and information only.**

---

*Last Updated: February 17, 2026*
