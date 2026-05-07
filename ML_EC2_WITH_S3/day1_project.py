# Train a model, save to s3, load from s3, predict

import boto3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os

BUCKET = 'arunesh-ml-bucket1-2026'

print("=" * 50)
print("STEP 1: Train ML Model")
print("=" * 50)

# Load iris dataset
iris = load_iris()
X = pd.DataFrame(iris.data, columns=iris.feature_names)
y = iris.target

# split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X_train, y_train)

# Evaluate
accuracy = accuracy_score(y_test, model.predict(X_test))
print(f"Model Accuracy: {accuracy:.2%}")

print("\n" + "=" * 50)
print("STEP 2: Save Model to S3")
print("=" * 50)

# Save model locally first
os.makedirs('model', exist_ok=True)
joblib.dump(model, 'model/iris_classifier.joblib')
print("Model saved locally")

# Upload to s3
s3 = boto3.client('s3', region_name='ap-south-1')
s3.upload_file(
    'model/iris_classifier.joblib',
    BUCKET,
    'models/iris_classifier.joblib'
)
print("Model uploaded to S3://{BUCKET}/models/iris_classifier.joblib")

print("\n" + "=" * 50)
print("STEP 3: Load Model FROM S3 and Predict")
print("=" * 50)

# Delete local model file to prove we are loading from S3 (simulate loading from scratch)
os.remove('model/iris_classifier.joblib')
print("Local model file deleted to simulate loading from S3")

# Download from S3
s3.download_file(
    BUCKET,
    'models/iris_classifier.joblib',
    'model/iris_classifier.joblib'
)
print("Model downloaded from S3")

# Load and predict
loaded_model = joblib.load('model/iris_classifier.joblib')

# Make predictions
sample = np.array([[5.1, 3.5, 1.4, 0.2]])  # Should be Setosa
prediction = loaded_model.predict(sample)
class_names = ['Setosa', 'Versicolor', 'Virginica']
print(f"\n Sample input: {sample[0]}")
print(f"Predicted class: {class_names[prediction[0]]}")
print("\n✅ Full pipeline working: Train → Save to S3 → Load from S3 → Predict")
