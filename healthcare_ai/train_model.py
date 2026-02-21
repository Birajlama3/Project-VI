import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import psutil  # For RAM monitoring

# Target column (adjust if wrong)
TARGET = "prognosis" 
# Test mode: Use a small subset to avoid RAM crashes
TEST_MODE = True  
SUBSET_SIZE = 2000  

print("Loading dataset...")
data = None
try:
    # Load normally first to check dtypes
    data = pd.read_csv("sample_dataset.csv")
    print(f"Full dataset shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print(f"Target column '{TARGET}' exists: {TARGET in data.columns}")
    print(f"Sample dtypes:\n{data.dtypes.head(10)}") 
    
    # Optimize dtypes for memory: Convert binary/numeric columns to int8, leave strings as is
    dtype_dict = {}
    for col in data.columns:
        if col != TARGET and data[col].dtype == 'int64':  # Assume symptoms are int64; convert to int8
            dtype_dict[col] = 'int8'
    if dtype_dict:
        data = pd.read_csv("data.csv", dtype=dtype_dict)  # Reload with optimized dtypes
        print("Reloaded with optimized dtypes for memory.")
    
    print(f"RAM usage after load: {psutil.virtual_memory().percent}%")
except FileNotFoundError:
    print("Warning: 'data.csv' not found. Check the file path. Skipping training.")
    # No exit() - continue without data
except Exception as e:
    print(f"Error loading data: {e}. Skipping training.")
    # No exit() - continue

if data is not None:
    # Sample for testing (to prevent RAM crashes)
    if TEST_MODE:
        data = data.sample(n=SUBSET_SIZE, random_state=42)
        print(f"Using subset shape: {data.shape}")

    # Prepare X and y
    if TARGET not in data.columns:
        print(f"Warning: Target column '{TARGET}' not found. Available: {list(data.columns)}. Skipping training.")
    else:
        X = data.drop(TARGET, axis=1)
        y = data[TARGET]

        # If y is strings (e.g., disease names), encode to numbers
        from sklearn.preprocessing import LabelEncoder
        if y.dtype == 'object':  # Strings
            le = LabelEncoder()
            y = le.fit_transform(y)
            print("Encoded target to integers.")

        print("Splitting dataset...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y  # Stratify for imbalance
        )

        print("Training model...")
        model = RandomForestClassifier(n_estimators=100, random_state=42)  # Reduced from 200 for speed/RAM
        model.fit(X_train, y_train)
        print(f"RAM usage after training: {psutil.virtual_memory().percent}%")

        print("Evaluating model...")
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model Accuracy: {accuracy:.4f}")

        # Save model
        joblib.dump(model, "disease_model.pkl")
        print("Model saved successfully.")
        print(f"Final RAM usage: {psutil.virtual_memory().percent}%")
else:
    print("No data loaded. Please fix file issues and rerun.")