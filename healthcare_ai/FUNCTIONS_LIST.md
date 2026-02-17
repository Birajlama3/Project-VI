# SymptoCare — Functions & Descriptions

## 🔧 Backend Functions (app.py)

| Function | Type | Description |
|----------|------|-------------|
| `home()` | Route Handler | Renders home page with project overview |
| `predict()` | Route Handler | Handles symptom input, processes queries, and displays results |
| (implicit) Input Validation | Sub-function | Validates user input (length, characters, format) |
| (implicit) Dataset Loading | Sub-function | Loads CSV file and checks for symptom columns |
| (implicit) Symptom Parsing | Sub-function | Tokenizes user input and maps to dataset columns |
| (implicit) Row Matching | Sub-function | Finds all dataset rows with matching symptoms |
| (implicit) Disease Extraction | Sub-function | Extracts disease labels from matched rows |
| (implicit) Confidence Calculation | Sub-function | Computes confidence as (disease_count / total_matches) |
| (implicit) Remedies Lookup | Sub-function | Fetches specific or generic remedies for top disease |

---

## 📚 Frontend Functions (Templates/CSS)

| Component | Type | Description |
|-----------|------|-------------|
| Symptom Form | HTML/JS | Text input for symptom entry with submit button |
| Loading Spinner | JS/CSS | Shows rotating animation during processing |
| Results Display | Jinja2 Template | Renders disease prediction with confidence scores |
| Remedies Display | Jinja2 Template | Shows specific or generic health tips |
| Error Display | Jinja2 Template | Shows validation/error messages |
| Medical Disclaimer | HTML | Yellow warning banner (always visible) |
| Spinner Animation | CSS | `@keyframes spin` - rotating circle animation |

---

## 🤖 Model & Training (train_model.py)

| Function | Description |
|----------|-------------|
| Data Loading | Reads `data.csv` and optimizes memory with dtype conversion |
| Target Encoding | Converts disease names (strings) to numbers using LabelEncoder |
| Train-Test Split | Splits data 80/20 with stratified sampling |
| Model Training | Trains RandomForestClassifier with 100 trees |
| Accuracy Evaluation | Calculates accuracy_score on test set |
| Model Saving | Saves trained model to `disease_model.pkl` using joblib |

---

## 📊 Data Processing (app.py)

| Function | Description |
|----------|-------------|
| Symptom Tokenization | Splits user input by commas/spaces into symptom list |
| Column Mapping | Matches user symptoms to actual CSV column names |
| Row Filtering | Finds rows where ALL requested symptoms are present (=1) |
| Disease Counting | Uses Counter to count disease frequency in matched rows |
| Confidence Scoring | Calculates: disease_count ÷ total_matched_rows |
| Remedies Fallback | Uses generic remedies if disease not in remedies database |

---

## 🔐 Validation & Security (app.py)

| Function | Description |
|----------|-------------|
| Length Validation | Checks input is between 2-500 characters |
| Character Sanitization | Removes special characters (keeps only alphanumeric, commas, hyphens) |
| Empty Check | Ensures user entered something |
| Error Messaging | Returns specific error message for each validation fail |

---

## 📁 File Processing (app.py)

| Function | Description |
|----------|-------------|
| Dataset Selection | Tries multiple CSV files (sample_dataset, data, dataset) |
| Symptom Detection | Checks if CSV contains symptom-like columns |
| Row Iteration | Loops through all dataset rows for matching |
| Value Conversion | Converts various data types (int, float, string) to binary |

---

## 🎯 Quick Reference

**Main Entry Point:** `predict()` — handles all prediction logic  
**Data Source:** `data.csv` or `sample_dataset.csv`  
**Model Source:** `disease_model.pkl` (RandomForest)  
**Remedies:** Hardcoded dictionary in `app.py`  
**Frontend:** `predict.html` + `style.css`  

---

**End of Functions List**
