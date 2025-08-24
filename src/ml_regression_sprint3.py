# src/ml_regression_sprint3.py
# Baseline de regressão: prever temp_c_plus5min a partir dos sensores atuais
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data", "processed", "dataset_sprint3_multisensor.csv")
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["timestamp"])

feat_cols = ["temp_c","humidity_pct","vibration_rms","motor_current_a","light_lux","pressure_kpa"]
X = df[feat_cols].values
y = df["temp_c_plus5min"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestRegressor(n_estimators=200, random_state=42))
])

pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

with open(os.path.join(RESULTS, "metrics_regression.txt"), "w", encoding="utf-8") as f:
    f.write(f"MAE: {mae:.4f}\nR2: {r2:.4f}\n")

# Gráfico simples: valores reais vs preditos (ordem por timestamp original não preservada)
plt.figure()
plt.plot(y_test[:200], label="Real")
plt.plot(y_pred[:200], label="Predito")
plt.title("Regressão: temp_c_plus5min (amostra de 200 pontos)")
plt.xlabel("Índice")
plt.ylabel("Temperatura (°C)")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(RESULTS, "regression_real_vs_pred.png"), dpi=150, bbox_inches="tight")

print("Regressão concluída. Métricas em results/metrics_regression.txt")
