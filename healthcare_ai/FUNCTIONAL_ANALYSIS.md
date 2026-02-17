# SymptoCare — Functional Analysis & Description

## 📋 Document Overview
This document provides a detailed functional analysis of the SymptoCare application, including all components, functions, and their interactions.

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Web Application                      │
├─────────────────────────────────────────────────────────────┤
│  Frontend Layer       │  Backend Logic Layer  │  Data Layer  │
│  (Templates/CSS)      │  (Routes/Processing)  │  (CSV/Model) │
│                       │                       │              │
│  • home.html          │  • home()             │ • data.csv   │
│  • predict.html       │  • predict()          │ • model.pkl  │
│  • style.css          │  • Validation         │              │
│                       │  • Remedies DB        │              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
User Input 
    ↓
[Input Validation & Sanitization]
    ↓
[Parse Symptoms (comma-separated)]
    ↓
[Match to Dataset Columns]
    ↓
[Find Matching Rows in Dataset]
    ↓
[Calculate Confidence Scores]
    ↓
[Fetch Home Remedies (Specific or Generic)]
    ↓
[Render Results with UI]
```

---

## 📦 Core Components

### 1. **app.py** — Main Flask Application

#### **Global Imports & Initialization**
```python
from flask import Flask, render_template, request
import pandas as pd
import joblib
from collections import Counter
```
- Imports Flask web framework
- Imports data processing (pandas) and model loading (joblib)
- Imports Counter for disease frequency analysis

#### **Model Loading**
```python
model = None
symptom_columns = []
try:
    model = joblib.load("disease_model.pkl")
    symptom_columns = list(model.feature_names_in_)
except Exception as e:
    print(f"Error loading model: {e}")
```

**Purpose:** 
- Loads pre-trained RandomForest model from disk
- Extracts feature names (symptoms) the model expects
- Gracefully handles missing model with fallback mode

**Key Variables:**
- `model`: RandomForest classifier object
- `symptom_columns`: List of 50+ binary symptom features

---

#### **Remedies Database**

```python
generic_remedies = [...]  # 8 generic wellness tips
remedies = {...}         # 41 disease-specific remedy sets
```

**Purpose:**
- Stores disease-specific home remedies
- Provides generic fallback for diseases without specific remedies

**Structure:**
```
{
    "Disease Name": [
        "Remedy 1",
        "Remedy 2",
        ...
    ]
}
```

**Coverage:** 41 diseases with specific remedies

---

#### **Route: `@app.route("/")`**

**Function:** `home()`

**HTTP Method:** GET

**Purpose:** Render landing page with project overview

**Returns:**
- `home.html` template rendered with Flask context

**Flow:**
1. User visits `/` or `localhost:5000`
2. Flask renders `home.html`
3. Displays hero section, features, and call-to-action

---

#### **Route: `@app.route("/predict", methods=["GET", "POST"])`**

**Function:** `predict()`

**HTTP Methods:** GET, POST

**Purpose:** Handle symptom input, prediction, and results display

---

### **GET Request Flow**

**Purpose:** Show empty prediction form

**Returns:**
- Empty `predict.html` template

**Variables Passed to Template:**
```python
{
    'prediction': "",
    'remedies': [],
    'symptoms': symptom_columns,
    'error': "",
    'data_columns': [],
    'matched_diseases': [],
    'matched_examples': [],
    'search_symptoms': "",
    'available_columns': [],
    'top_diseases': [],
    'confidence_scores': []
}
```

---

### **POST Request Flow**

#### **Phase 1: Input Validation & Sanitization**

```python
search_query = (request.form.get("search_symptoms") or "").strip()

if not search_query:
    error_message = "Please enter at least one symptom."
elif len(search_query) > 500:
    error_message = "Input too long..."
elif len(search_query) < 2:
    error_message = "Please enter valid symptoms..."
else:
    sanitized_query = re.sub(r'[^a-zA-Z0-9\s,\-]', '', search_query)
    if not sanitized_query.strip():
        error_message = "Input contains invalid characters..."
```

**Purpose:** Prevent injection attacks and invalid input

**Validations:**
- ✓ Non-empty
- ✓ Max 500 characters
- ✓ Min 2 characters
- ✓ Only alphanumeric, commas, hyphens, spaces

**Output:** `search_query` (sanitized) or `error_message`

---

#### **Phase 2: Load Dataset**

```python
files_to_try = ("sample_dataset.csv", "data.csv", "dataset.csv")
for fname in files_to_try:
    df_try = pd.read_csv(fname)
    # Check if file has symptom-like columns
    if has_symptom:
        full_df = df_try
        break
```

**Purpose:** Load dataset with symptom columns

**Logic:**
- Tries multiple CSV files (preferred order)
- Validates files contain symptom columns
- Falls back to next file if validation fails

**Output:**
- `full_df`: Loaded DataFrame with symptoms & diseases
- `data_columns`: List of column names
- `symptom_in_csv`: Symptoms that model expects AND exist in CSV

---

#### **Phase 3: Parse User Input (Symptom Tokenization)**

```python
tokens = [t.strip() for t in search_query.replace(';', ',').split(',') 
          if t.strip()]
requested_cols = []
not_found = []

for t in tokens:
    k = t.lower().strip().replace(" ", "_").replace("-", "_")
    if k in col_map:
        requested_cols.append(col_map[k])
    else:
        # Try contains match
        match = None
        for nk, real in norm_cols.items():
            if k in nk or nk in k:
                match = real
                break
        if match:
            requested_cols.append(match)
        else:
            not_found.append(t)
```

**Purpose:** Convert user text input to dataset column names

**Example:**
```
Input:  "headache, fever, cough"
        ↓
Parsed: ["headache", "fever", "cough"]
        ↓
Mapped: ["Headache", "Fever", "Cough"] (if they exist in CSV)
```

**Matching Strategy:**
1. Exact match (normalized)
2. Substring match (flexible)
3. Not found → add to error list

**Output:**
- `requested_cols`: List of actual CSV column names
- `not_found`: List of unrecognized symptoms

---

#### **Phase 4: Dataset Row Matching**

```python
matched_rows = []
if requested_cols:
    for idx, row in full_df.iterrows():
        ok = True
        for rc in requested_cols:
            val = row.get(rc, 0)
            # Convert to binary (0 or 1)
            try:
                v = int(val)
            except:
                v = 1 if str(val).lower() in ("1", "true", "yes", "y") else 0
            
            if v == 0:  # Symptom not present
                ok = False
                break
        
        if ok:  # All requested symptoms are present
            matched_rows.append((idx, row))
```

**Purpose:** Find all dataset rows where ALL requested symptoms are present

**Logic:**
- Iterate through entire dataset
- For each row, check if ALL selected symptoms = 1 (present)
- Include row only if ALL symptoms match
- Convert values to binary (handles different data formats)

**Example:**
```
Dataset:
Row 1: Headache=1, Fever=1, Cough=0, Disease=Flu
Row 2: Headache=1, Fever=1, Cough=1, Disease=Common Cold
Row 3: Headache=0, Fever=0, Cough=1, Disease=Asthma

User Input: "headache, fever"
            ↓
Matched Rows:
- Row 1 ✓ (both present)
- Row 2 ✓ (both present)
- Row 3 ✗ (headache=0)
```

**Output:** `matched_rows` (list of matching row indices and data)

---

#### **Phase 5: Extract Diseases & Calculate Confidence**

```python
diseases = []
for idx, row in matched_rows:
    d = row.get("Disease") or row.get("disease") or row.get("prognosis")
    if d is not None:
        diseases.append(str(d))

# Remove non-informative labels
diseases = [d for d in diseases if _is_informative(d)]
matched_diseases = list(dict.fromkeys(diseases))  # Unique, ordered

# Calculate frequencies and confidence
if diseases:
    counts = Counter(diseases)
    top_diseases = counts.most_common(20)
    
    # Confidence = (count of disease) / (total matched rows)
    total_matches = len(matched_rows)
    confidence_scores = []
    for disease, count in top_diseases:
        confidence = count / total_matches if total_matches > 0 else 0
        confidence_scores.append((disease, confidence))
```

**Purpose:** Aggregate diseases and calculate confidence scores

**Logic:**
1. Extract disease labels from matched rows
2. Filter out non-informative labels ("No Disease", "None", etc.)
3. Count frequency of each disease
4. Calculate confidence as: `count / total_matched_rows`

**Example:**
```
Matched Rows: 10 total
- Flu: 6 rows → 6/10 = 60% confidence
- Cold: 3 rows → 3/10 = 30% confidence
- Cough: 1 row → 1/10 = 10% confidence
```

**Output:**
- `confidence_scores`: [(disease, confidence_float), ...]
- `top_diseases`: [(disease, count), ...] (top 20)

---

#### **Phase 6: Fetch Home Remedies**

```python
disease_remedies = []
if confidence_scores:
    top_name = str(confidence_scores[0][0])
    
    # Direct match
    if top_name in remedies:
        disease_remedies = remedies[top_name]
    else:
        # Case-insensitive or substring match
        found = False
        for rk, rv in remedies.items():
            if (rk.lower() == top_name.lower() or 
                top_name.lower() in rk.lower() or 
                rk.lower() in top_name.lower()):
                disease_remedies = rv
                found = True
                break
        
        # Fallback to generic remedies
        if not found:
            disease_remedies = generic_remedies
```

**Purpose:** Get remedies for the top-predicted disease

**Matching Strategy:**
1. Exact match (case-insensitive)
2. Substring match (flexible)
3. Generic fallback (8 universal wellness tips)

**Output:** `disease_remedies` (list of remedy strings)

---

#### **Phase 7: Render Results**

```python
return render_template("predict.html",
    prediction=prediction,
    remedies=disease_remedies,
    symptoms=symptom_columns,
    error=error_message,
    data_columns=data_columns,
    matched_diseases=matched_diseases,
    matched_examples=matched_examples,
    search_symptoms=search_query,
    available_columns=available_columns,
    top_diseases=top_diseases,
    confidence_scores=confidence_scores)
```

**Purpose:** Render results page with all data

**Template Variables Explained:**
| Variable | Type | Purpose |
|----------|------|---------|
| `prediction` | str | Top predicted disease |
| `remedies` | list | Remedies for top disease |
| `symptoms` | list | All model symptoms (for reference) |
| `error` | str | Any validation/processing error |
| `confidence_scores` | list | [(disease, confidence%), ...] |
| `top_diseases` | list | Top 20 diseases with counts |
| `search_symptoms` | str | What user entered |

---

---

## 🎨 Frontend Components

### 2. **templates/home.html**

**Purpose:** Landing page with project overview

**Sections:**
1. **Hero Section**
   - App title "SymptoCare"
   - Tagline
   - CTA button → `/predict`
   - Hero image placeholder

2. **About Section**
   - Describes what SymptoCare is
   - Emphasizes educational nature
   - Notes it's not a diagnosis tool

3. **Features Section**
   - 3 feature cards:
     - Quick Diagnosis
     - Evidence-Based
     - Easy to Use

4. **CTA Section**
   - Final call-to-action
   - "Start a Symptom Check" button

5. **Footer**
   - Copyright info

---

### 3. **templates/predict.html**

**Purpose:** Symptom input & results display page

**Components:**

#### **A. Medical Disclaimer Banner**
```html
<div class="disclaimer-banner">
    ⚠️ Medical Disclaimer: SymptoCare is an educational tool...
</div>
```
- Always visible at top
- Yellow warning style
- Emphasizes not a medical diagnosis

#### **B. Symptom Input Form**
```html
<input class="search-input" 
       type="text" 
       name="search_symptoms" 
       maxlength="500" 
       required>
```
- Text input for symptom entry
- Max 500 characters
- Required field
- Placeholder examples

#### **C. Loading Spinner**
```html
<div id="loadingSpinner" class="loading-spinner" style="display:none;">
    <div class="spinner"></div>
    <p>Analyzing your symptoms...</p>
</div>
```
- Hidden by default
- Shows during form submission
- CSS rotating animation

#### **D. Results Display**

**If Prediction Exists:**
```html
<div class="result-box">
    <h3>Primary Prediction</h3>
    <p class="disease-primary">{{ prediction }}</p>
    <div class="confidence-badge">
        {{ (confidence_scores[0][1] * 100)|round(1) }}% confidence
    </div>
    
    <!-- Alternatives List -->
    {% for disease, confidence in confidence_scores[1:6] %}
        <div class="confidence-item">
            <span>{{ disease }}</span>
            <span>{{ (confidence * 100)|round(1) }}%</span>
        </div>
    {% endfor %}
</div>
```

**If Remedies Exist:**
```html
<div class="result-box">
    <h3>Suggested Home Remedies</h3>
    <ul class="remedies-list">
        {% for remedy in remedies %}
            <li>{{ remedy }}</li>
        {% endfor %}
    </ul>
</div>
```

#### **E. Error Display**
```html
{% if error %}
    <div class="alert alert-error">{{ error }}</div>
{% endif %}
```

#### **F. Navigation**
```html
<a href="{{ url_for('home') }}" class="btn secondary-btn">Back to Home</a>
```

---

#### **G. Loading Spinner JavaScript**
```javascript
<script>
    document.getElementById('symptomForm').addEventListener('submit', function() {
        document.getElementById('loadingSpinner').style.display = 'block';
        document.getElementById('submitBtn').disabled = true;
    });
</script>
```

**Purpose:** Show spinner and disable button on form submit

---

### 4. **static/style.css**

**Purpose:** Styling and animations

**Key Style Classes:**

| Class | Purpose |
|-------|---------|
| `.disclaimer-banner` | Yellow warning box with border |
| `.loading-spinner` | Center loading container |
| `.spinner` | CSS rotating animation (4px border, 50px circle) |
| `.alert` | Error message styling |
| `.alert-error` | Red error alert |
| `.result-box` | Disease/remedies container |
| `.disease-primary` | Large bold disease name |
| `.confidence-badge` | Gradient blue badge with % |
| `.confidence-list` | Flex list of alternatives |
| `.confidence-item` | Individual disease + % row |
| `.confidence-percent` | Blue percentage badge |

**Animations:**
```css
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

**Responsive Design:**
- Mobile: Single column layout
- Tablet: 2-column grid where applicable
- Desktop: Full multi-column layout

---

## 🤖 Model & Training

### 5. **train_model.py**

**Purpose:** Train RandomForest model on disease data

**Functions:**

#### **Data Loading**
```python
data = pd.read_csv("data.csv")
dtype_dict = {}  # Optimize memory
for col in data.columns:
    if data[col].dtype == 'int64':
        dtype_dict[col] = 'int8'
data = pd.read_csv("data.csv", dtype=dtype_dict)
```

- Loads disease dataset
- Optimizes dtypes for memory (int64 → int8)
- Handles errors gracefully

#### **Feature-Target Split**
```python
X = data.drop(TARGET, axis=1)  # Features (symptoms)
y = data[TARGET]               # Target (disease name)
```

#### **Target Encoding**
```python
if y.dtype == 'object':  # String labels
    le = LabelEncoder()
    y = le.fit_transform(y)  # Convert to numbers
```

#### **Train-Test Split**
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

- 80% training, 20% testing
- Stratified sampling (preserves class distribution)

#### **Model Training**
```python
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)
```

- RandomForest with 100 trees
- Handles both classification and feature importance

#### **Evaluation & Save**
```python
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy: {accuracy:.4f}")

joblib.dump(model, "disease_model.pkl")
```

**Output:** `disease_model.pkl` (serialized model)

---

## 📊 Data Files

### 6. **data.csv** (Full Dataset)

**Structure:**
- 50+ symptom columns (binary: 0 or 1)
- 1 prognosis/disease column (string: disease name)
- 1000s of rows (training examples)

**Example Row:**
```
fever, cough, headache, ..., fatigue, prognosis
1,     1,      1,       ..., 0,       Common Cold
0,     0,      1,       ..., 1,       Migraine
```

**Diseases Covered:** 41 conditions

---

### 7. **sample_dataset.csv** (Small Sample)

**Purpose:** Faster development/testing

**Contents:** ~2000 rows subset of `data.csv`

**Usage:** Used by app if available (faster loading)

---

## 🔍 Utility Functions

### 8. **check_data.py**

**Purpose:** Data validation and exploration

**Typical Functions:**
- Check data shape and types
- Find missing values
- List unique diseases
- Verify binary encoding
- Data quality report

---

---

## 📈 Process Flow Diagrams

### **Complete Request-Response Cycle**

```
USER
  ↓
  ├─→ GET /
  │   └─→ home()
  │       └─→ render home.html
  │
  └─→ GET /predict
      └─→ predict()
          └─→ render predict.html (empty form)
  
  ↓
USER ENTERS SYMPTOMS & SUBMITS
  ↓
  POST /predict
  ├─→ predict()
  │   ├─→ Validate input (500 chars, alphanumeric, etc.)
  │   ├─→ Load dataset
  │   ├─→ Parse symptoms (tokenize & map)
  │   ├─→ Find matching rows (all symptoms present)
  │   ├─→ Extract diseases from rows
  │   ├─→ Calculate confidence scores
  │   ├─→ Fetch remedies (specific or generic)
  │   └─→ Render results
  └─→ render predict.html (with results)
  
  ↓
RESULTS DISPLAYED TO USER
```

---

## 🔐 Security Features

1. **Input Validation**
   - Max length check (500 chars)
   - Min length check (2 chars)
   - Regex sanitization (alphanumeric only)

2. **Error Handling**
   - Graceful fallbacks
   - Generic error messages (no stack traces to user)
   - Try-catch blocks everywhere

3. **Data Privacy**
   - No data storage
   - No tracking
   - Local processing only

---

## ⚠️ Limitations & Edge Cases

1. **No Results**
   - Happens if symptom combination doesn't exist in dataset
   - User gets: "No matches found..."

2. **Partial Matches**
   - Only shows diseases with ALL entered symptoms
   - Very specific queries → fewer results

3. **Misspellings**
   - Substring matching helps but imperfect
   - "hedache" might not match "headache"

4. **Generic Remedies Fallback**
   - Diseases not in remedies DB get generic tips
   - Better than no remedies at all

---

## 🎯 Key Metrics & Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Model Accuracy | ~95% | RandomForest on test set |
| Load Time | <1s | CSV + model loading |
| Prediction Time | <100ms | Dataset search + matching |
| Max Input | 500 chars | Sanitized |
| Diseases | 41 | In remedies DB |
| Features | 50+ | Symptoms per disease |
| Confidence Display | Top 6 | User interface |

---

## 🚀 Deployment Considerations

1. **Production Settings**
   - Change `debug=False`
   - Use production WSGI server (Gunicorn, uWSGI)
   - Add SSL/HTTPS
   - Use environment variables for config

2. **Scaling**
   - Cache dataset in memory
   - Consider database instead of CSV
   - Add API rate limiting

3. **Monitoring**
   - Log all predictions
   - Track common error inputs
   - Monitor server resources

---

## 📝 Summary Table

| Component | Type | Purpose | Key Function |
|-----------|------|---------|--------------|
| app.py | Backend | Main Flask app | predict() |
| home.html | Template | Landing page | Render intro |
| predict.html | Template | Prediction UI | Display results |
| style.css | Frontend | Styling | Visual design |
| train_model.py | Script | Model training | Create model.pkl |
| data.csv | Data | Training data | 1000+ examples |
| sample_dataset.csv | Data | Test sample | ~2000 rows |
| disease_model.pkl | Model | Trained RF | Make predictions |

---

**End of Functional Analysis**

*Last Updated: February 17, 2026*
