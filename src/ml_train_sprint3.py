# src/ml_train_sprint3.py
# Treino de modelo simples (classificação multiclass) usando scikit-learn
# Entrada: data/processed/dataset_sprint3_multisensor.csv
# Saídas: results/confusion_matrix.png, results/metrics.txt, results/sample_predictions.csv

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed", "dataset_sprint3_multisensor.csv")
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["timestamp"])

# Features e alvo
feat_cols = ["temp_c","humidity_pct","vibration_rms","motor_current_a","light_lux","pressure_kpa"]
X = df[feat_cols].values
y = df["estado_operacional"].values

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Modelo: RandomForest (robusto e simples)
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(n_estimators=200, random_state=42))
])

pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)

# Métricas
report = classification_report(y_test, y_pred, digits=4)
cm = confusion_matrix(y_test, y_pred, labels=["normal","alerta","falha"])

# Salva métricas
with open(os.path.join(RESULTS, "metrics.txt"), "w", encoding="utf-8") as f:
    f.write(report)

# Gráfico da matriz de confusão (sem especificar cores)
plt.figure()
plt.imshow(cm, interpolation="nearest")
plt.title("Matriz de Confusão")
plt.colorbar()
tick_marks = np.arange(3)
classes = ["normal","alerta","falha"]
plt.xticks(tick_marks, classes, rotation=45)
plt.yticks(tick_marks, classes)
plt.tight_layout()
plt.xlabel("Predito")
plt.ylabel("Real")
plt.savefig(os.path.join(RESULTS, "confusion_matrix.png"), dpi=150, bbox_inches="tight")

# Amostras de predição
out = pd.DataFrame(X_test, columns=feat_cols).copy()
out["y_true"] = y_test
out["y_pred"] = y_pred
out.to_csv(os.path.join(RESULTS, "sample_predictions.csv"), index=False)

print("Treino concluído. Veja results/metrics.txt e results/confusion_matrix.png")
