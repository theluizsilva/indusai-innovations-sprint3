
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

def main():
    # Locate dataset
    candidates = [
        os.path.join("data","processed","dataset_sprint3_multisensor.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "processed", "dataset_sprint3_multisensor.csv"),
    ]
    dataset_path = None
    for c in candidates:
        if os.path.exists(c):
            dataset_path = c
            break
    if dataset_path is None:
        raise FileNotFoundError("dataset_sprint3_multisensor.csv não encontrado em data/processed/")
    
    df = pd.read_csv(dataset_path, parse_dates=["timestamp"])
    features = ["temp_c","humidity_pct","vibration_rms","motor_current_a","light_lux","pressure_kpa"]
    X = df[features].values
    y = df["estado_operacional"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Pipeline: scaler + RandomForest (robusto para features mistas)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced"))
    ])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    # Outputs folder
    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)

    # Metrics
    report = classification_report(y_test, y_pred, digits=4)
    with open(os.path.join(out_dir, "metrics.txt"), "w", encoding="utf-8") as f:
        f.write(report)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=["normal","alerta","falha"])
    fig = plt.figure(figsize=(5,4), dpi=140)
    ax = plt.gca()
    im = ax.imshow(cm)  # não especificar cores
    ax.set_xticks(range(3)); ax.set_yticks(range(3))
    ax.set_xticklabels(["normal","alerta","falha"], rotation=45, ha="right")
    ax.set_yticklabels(["normal","alerta","falha"])
    ax.set_xlabel("Predita"); ax.set_ylabel("Real")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, int(cm[i,j]), ha="center", va="center")
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, "confusion_matrix.png"))
    plt.close(fig)

    # Sample predictions
    sample = pd.DataFrame(X_test, columns=features).copy()
    sample["y_real"] = y_test
    sample["y_pred"] = y_pred
    sample.head(100).to_csv(os.path.join(out_dir, "sample_predictions.csv"), index=False)

if __name__ == "__main__":
    main()
