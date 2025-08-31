
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance
import matplotlib.pyplot as plt

def main():
    # Resolve dataset path
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

    # === Modelo final (Pipeline: scaler + RF) ===
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced"))
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)

    # === Relatório de métricas do modelo final ===
    report = classification_report(y_test, y_pred, digits=4)
    with open(os.path.join(out_dir, "metrics.txt"), "w", encoding="utf-8") as f:
        f.write(report)

    # === Matriz de confusão (figura) ===
    labels = ["normal","alerta","falha"]
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    fig = plt.figure(figsize=(5,4), dpi=140)
    ax = plt.gca()
    im = ax.imshow(cm)  # não especificar cores
    ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predita"); ax.set_ylabel("Real")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, int(cm[i,j]), ha="center", va="center")
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, "confusion_matrix.png"))
    plt.close(fig)

    # === Amostras ===
    sample = pd.DataFrame(X_test, columns=features).copy()
    sample["y_real"] = y_test
    sample["y_pred"] = y_pred
    sample.head(100).to_csv(os.path.join(out_dir, "sample_predictions.csv"), index=False)

    # === (1) Baseline: Logistic Regression ===
    base = Pipeline([("scaler", StandardScaler()),
                     ("logreg", LogisticRegression(max_iter=1000))])
    base.fit(X_train, y_train)
    yb = base.predict(X_test)
    report_base = classification_report(y_test, yb, digits=4)
    with open(os.path.join(out_dir, "baseline_metrics.txt"), "w", encoding="utf-8") as f:
        f.write(report_base)

    # === (2) Cross-validation (5-fold) ===
    scorings = ["accuracy", "f1_macro", "precision_macro", "recall_macro"]
    lines = []
    for sc in scorings:
        scores = cross_val_score(pipe, X, y, cv=5, scoring=sc)
        lines.append(f"{sc}: mean={scores.mean():.4f} std={scores.std():.4f}")
    with open(os.path.join(out_dir, "cv_metrics.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # === (3) Probabilidades + Top-K risco (P_falha) ===
    proba = pipe.predict_proba(X_test)  # classes em pipe.named_steps["clf"].classes_
    classes_ = list(pipe.named_steps["clf"].classes_)
    cls_to_idx = {c:i for i,c in enumerate(classes_)}
    assert "falha" in cls_to_idx, "Classe 'falha' não encontrada nas classes do modelo."
    p_falha = proba[:, cls_to_idx["falha"]]
    sample_prob = pd.DataFrame(X_test, columns=features)
    sample_prob["y_real"] = y_test
    sample_prob["y_pred"] = y_pred
    # Map probabilities per class (ensure order)
    for c in classes_:
        sample_prob[f"P_{c}"] = proba[:, cls_to_idx[c]]
    sample_prob.sort_values("P_falha", ascending=False).head(50)\
        .to_csv(os.path.join(out_dir, "top_risk_predictions.csv"), index=False)

    # === (4) Permutation Importance ===
    perm = permutation_importance(pipe, X_test, y_test, n_repeats=5, random_state=42)
    importances = pd.Series(perm.importances_mean, index=features).sort_values(ascending=True)
    fig = plt.figure(figsize=(6,3), dpi=140)
    ax = plt.gca()
    ax.barh(importances.index, importances.values)  # sem cores customizadas
    ax.set_title("Permutation Importance")
    ax.set_xlabel("Δscore (médio)")
    fig.tight_layout()
    plt.savefig(os.path.join(out_dir, "feature_importance.png"))
    plt.close(fig)

    # === (5) Custo simples baseado na matriz de confusão ===
    # Custos (exemplo): FN_falha=10, FP_falha=2, demais erros=1
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cost = 0
    # FN_falha: real falha (idx=2), predito != falha
    cost += (cm[2,0] + cm[2,1]) * 10
    # FP_falha: real != falha, predito falha (col idx=2)
    cost += (cm[0,2] + cm[1,2]) * 2
    # demais erros
    cost += (cm[0,1] + cm[1,0]) * 1
    with open(os.path.join(out_dir, "cost_summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"labels: {labels}\ncm:\n{cm}\nCusto total (regras exemplo): {cost}\n")

if __name__ == "__main__":
    main()
