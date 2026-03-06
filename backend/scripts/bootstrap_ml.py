import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Features defined in ml_engine.py
PACKET_FEATURES = [
    "packet_length", "payload_size", "source_port", "dest_port",
    "protocol_num", "tcp_flags_num", "ttl", "ip_version",
]

def bootstrap_model():
    print("🚀 Bootstrapping initial ML model...")
    
    # Create synthetic data for training
    # 0 = Normal, 1 = Attack
    n_samples = 1000
    X = np.random.rand(n_samples, len(PACKET_FEATURES))
    y = np.random.randint(0, 2, n_samples)
    
    # Simple logic to make the model "learn" something basic
    # If packet length is very high, more likely to be an "attack"
    X[:, 0] = X[:, 0] * 1500  # Normalizing packet length
    y[X[:, 0] > 1400] = 1   # High packet length = potential attack
    
    # Train
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_scaled, y)
    
    # Save artifacts
    model_path = "app/ml_models/nids_model.joblib"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    joblib.dump({
        "model": model,
        "scaler": scaler,
        "label_encoder": LabelEncoder().fit(["normal", "attack"]),
        "feature_columns": PACKET_FEATURES,
    }, model_path)
    
    print(f"✅ Baseline model saved to: {model_path}")

if __name__ == "__main__":
    bootstrap_model()
