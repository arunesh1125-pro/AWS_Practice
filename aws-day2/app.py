# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os
from typing import List

# Initialize FastAPI
app = FastAPI(
    title="Iris Classifier API",
    description="ML API deployed on AWS — Built by Arunesh",
    version="1.0.0"
)

# Load model at startup (not on every request — important for performance)
MODEL_PATH = "model/iris_model.joblib"
model = None

@app.on_event("startup")
def load_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"✅ Model loaded from {MODEL_PATH}")
    else:
        print("❌ Model file not found!")

# Define input schema
class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

    class Config:
        json_schema_extra = {
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
        }

# Define output schema
class PredictionOutput(BaseModel):
    predicted_class: str
    class_id: int
    confidence: float
    all_probabilities: dict

# Class names
CLASS_NAMES = ['Setosa', 'Versicolor', 'Virginica']

@app.get("/")
def home():
    return {
        "message": "Iris Classifier API",
        "status": "running",
        "deployed_on": "AWS Elastic Beanstalk",
        "built_by": "Arunesh",
        "endpoints": {
            "predict": "POST /predict",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "model_type": "RandomForestClassifier"
    }

@app.post("/predict", response_model=PredictionOutput)
def predict(data: IrisInput):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Check server logs."
        )

    # Prepare input
    features = np.array([[
        data.sepal_length,
        data.sepal_width,
        data.petal_length,
        data.petal_width
    ]])

    # Predict
    class_id = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    confidence = float(probabilities[class_id])

    return PredictionOutput(
        predicted_class=CLASS_NAMES[class_id],
        class_id=class_id,
        confidence=round(confidence, 4),
        all_probabilities={
            name: round(float(prob), 4)
            for name, prob in zip(CLASS_NAMES, probabilities)
        }
    )

@app.post("/predict/batch")
def predict_batch(items: List[IrisInput]):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    results = []
    for item in items:
        features = np.array([[
            item.sepal_length, item.sepal_width,
            item.petal_length, item.petal_width
        ]])
        class_id = int(model.predict(features)[0])
        probs = model.predict_proba(features)[0]
        results.append({
            "predicted_class": CLASS_NAMES[class_id],
            "confidence": round(float(probs[class_id]), 4)
        })
    return {"predictions": results, "count": len(results)}