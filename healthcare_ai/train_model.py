import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

print("Loading dataset...")

data = pd.read_csv("dataset.csv")

X = data.drop("Disease", axis=1)
y = data["Disease"]

print("Splitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training model...")

model = RandomForestClassifier(n_estimators=200)
model.fit(X_train, y_train)

print("Evaluating model...")

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("Model Accuracy:", accuracy)

joblib.dump(model, "disease_model.pkl")
print("Model saved successfully.")

