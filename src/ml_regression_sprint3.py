
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

def main():
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
    y = df["temp_c_plus5min"].values

    # Remove linhas com alvo nulo (por segurança)
    ok = np.isfinite(y)
    X, y = X[ok], y[ok]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", RandomForestRegressor(n_estimators=200, random_state=42))
    ])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)

    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)
    with open(os.path.join(out_dir, "metrics_regression.txt"), "w", encoding="utf-8") as f:
        f.write(f"MAE: {mae:.4f}\nR2: {r2:.4f}\n")

    # Plot real vs pred (100 primeiros pontos)
    fig = plt.figure(figsize=(6,3), dpi=140)
    ax = plt.gca()
    ax.plot(y_test[:100], label="real")
    ax.plot(y_pred[:100], label="pred")
    ax.set_title("Temperatura +5min: real vs predita (amostra)")
    ax.set_xlabel("amostras"); ax.set_ylabel("temp (°C)")
    ax.legend()
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, "regression_real_vs_pred.png"))
    plt.close(fig)

if __name__ == "__main__":
    main()
