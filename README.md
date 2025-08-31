# Sprint 3 – Hermes Reply / FIAP — indusAI Innovations

> **Objetivo:** Modelar um banco de dados relacional para dados de sensores e treinar um modelo **básico** de Machine Learning usando os dados da Sprint 2 (temperatura) **enriquecidos** com novos sensores simulados (**umidade, vibração RMS, corrente do motor, luminosidade, pressão**). O rótulo **estado_operacional** (normal/alerta/falha) foi calculado por regras simples e plausíveis para o domínio industrial.

---

## Estrutura do repositório
```
sprint3_pack/
  data/
    raw/
      sprint2_dados_temperatura.csv
    processed/
      dataset_sprint3_multisensor.csv      # ~2.400 leituras, 6 sensores + rótulos
  db/
    schema_oracle.sql
    seed_data.sql
    erd.mmd
    ERD_sprint3_datasql.png                # DER exportado pelo Oracle Data Modeler
    prints/                                # evidências (DDL, seed, contagens etc.)
  src/
    ml_train_sprint3.py                    # classificação (normal/alerta/falha)
    ml_regression_sprint3.py               # regressão (bônus): prever temp_c +5 min
  results/                                 # saídas geradas pelos scripts de ML
  README.md
```

---

## ⚙️ Preparação rápida (ambiente Python)
Requisitos: **Python 3.10+**

```bash
# Windows (PowerShell)
cd sprint3_pack
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install pandas numpy scikit-learn matplotlib

# macOS / Linux
cd sprint3_pack
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pandas numpy scikit-learn matplotlib
```

---

## 🗄️ Parte 1 — Banco de Dados

### 1.1 Diagrama ER (DER)
- Arquivo Mermaid: `db/erd.mmd` (abre em https://mermaid.live e exporta PNG, se quiser).
- Exportado via Oracle SQL Developer Data Modeler: **`db/ERD_sprint3_datasql.png`**.

**Entidades e campos (resumo funcional):**
- **SITE**: `site_id` (PK), `name`, `city`, `state`, `created_at`
- **ASSET**: `asset_id` (PK), `site_id` (FK→SITE), `name`, `type`, `installed_at`
- **SENSOR_TYPE**: `sensor_type_id` (PK), `code` (UNIQUE), `description`, `unit`
- **SENSOR**: `sensor_id` (PK), `asset_id` (FK→ASSET), `sensor_type_id` (FK→SENSOR_TYPE), `model`, `serial_number`, `installed_at`, `is_active` (CHECK IN 'Y','N')
- **READING**: `reading_id` (PK), `sensor_id` (FK→SENSOR), `ts`, `value_num`, `quality` (CHECK IN 'OK','SUSPECT','MISSING')
- **ASSET_STATE**: `asset_state_id` (PK), `asset_id` (FK→ASSET), `ts`, `state` (CHECK IN 'normal','alerta','falha'), `note`

**Relacionamentos e índices:**
- SITE 1—N ASSET; ASSET 1—N SENSOR; SENSOR_TYPE 1—N SENSOR; SENSOR 1—N READING; ASSET 1—N ASSET_STATE.
- Índices essenciais: `READING(sensor_id, ts)` e `ASSET_STATE(asset_id, ts)` (consultas temporais).
- View utilitária: `vw_sensor_latest` (última leitura por sensor).

> **Por que assim?** Dados **brutos** ficam em `READING`; o **rótulo agregado** por ativo/tempo fica em `ASSET_STATE`, o que facilita ML supervisionado e mantém a tabela de leituras limpa. `SENSOR_TYPE` normaliza unidade/descrição.

### 1.2 Criação do schema
No **Oracle SQL Developer (IDE)**:
1. Abra `db/schema_oracle.sql` → **Run Script (F5)**.
2. Abra `db/seed_data.sql` → **Run Script (F5)** → `COMMIT;`.

### 1.3 Validações (SQL)
Use como **evidências** (prints em `db/prints/`):
```sql
-- 1) Contagens (print: 01_counts.png)
SELECT
  (SELECT COUNT(*) FROM site)        AS sites,
  (SELECT COUNT(*) FROM asset)       AS assets,
  (SELECT COUNT(*) FROM sensor_type) AS sensor_types,
  (SELECT COUNT(*) FROM sensor)      AS sensors,
  (SELECT COUNT(*) FROM reading)     AS readings,
  (SELECT COUNT(*) FROM asset_state) AS asset_states
FROM dual;

-- 2) Sensores x Tipos (print: 02_sensors_map.png)
SELECT s.sensor_id, st.code AS sensor_code, st.unit, a.name AS asset_name
FROM sensor s
JOIN sensor_type st ON st.sensor_type_id = s.sensor_type_id
JOIN asset a        ON a.asset_id        = s.asset_id
ORDER BY s.sensor_id;

-- 3) Índices (print: 03_indexes.png)
SELECT index_name, table_name, column_name, column_position
FROM user_ind_columns
WHERE table_name IN ('READING','ASSET_STATE')
ORDER BY table_name, index_name, column_position;

-- 4) PKs, FKs, CHECKs (prints: 04_constraints_pks.png, 05_constraints_fks.png, 06_constraints_checks.png)
-- PKs
SELECT table_name, constraint_name
FROM user_constraints
WHERE constraint_type = 'P'
  AND table_name IN ('SITE','ASSET','SENSOR_TYPE','SENSOR','READING','ASSET_STATE')
ORDER BY table_name;
-- FKs
SELECT c.table_name, c.constraint_name, r.table_name AS referenced_table
FROM user_constraints c
JOIN user_constraints r ON c.r_constraint_name = r.constraint_name
WHERE c.constraint_type = 'R'
  AND c.table_name IN ('ASSET','SENSOR','READING','ASSET_STATE')
ORDER BY c.table_name, c.constraint_name;
-- CHECKs
SELECT table_name, constraint_name, search_condition
FROM user_constraints
WHERE constraint_type = 'C'
  AND table_name IN ('SENSOR','READING','ASSET_STATE')
ORDER BY table_name, constraint_name;
```

**Opcional (07_view_latest.png):**
```sql
-- Insira 2 leituras no sensor TEMP e consulte:
-- SELECT s.sensor_id FROM sensor s JOIN sensor_type st ON st.sensor_type_id=s.sensor_type_id WHERE st.code='TEMP';
-- INSERT INTO reading(...) VALUES (...); COMMIT;
SELECT * FROM vw_sensor_latest WHERE sensor_id = <id_temp>;
```

---

## 🤖 Parte 2 — Machine Learning

### 2.1 Dataset
`data/processed/dataset_sprint3_multisensor.csv` (≈2.400 linhas) com:
```
timestamp, temp_c, humidity_pct, vibration_rms, motor_current_a,
light_lux, pressure_kpa, estado_operacional, temp_c_plus5min
```
> **Exigência atendida:** >500 leituras por sensor.

### 2.2 Classificação (entrega obrigatória)
```bash
# na raiz sprint3_pack, com o venv ativado
python src/ml_train_sprint3.py
```
**Saídas esperadas em `results/`:**
- `metrics.txt` — precisão/recall/F1 por classe e acurácia geral
- `confusion_matrix.png` — visualização dos acertos/erros por classe
- `sample_predictions.csv` — amostras com predições

> **Justificativa do gráfico:** a **matriz de confusão** evidencia erros entre `normal/alerta/falha`, típica em uso industrial.  
> **Reprodutibilidade:** o script usa semente fixa (`random_state`) e `train_test_split` estratificado.

### 2.3 Regressão (over-delivery)
```bash
python src/ml_regression_sprint3.py
```
**Saídas em `results/`:**
- `metrics_regression.txt` — MAE e R²
- `regression_real_vs_pred.png` — série real vs predita (amostra)

> **Motivação:** prever temperatura em +5 min ajuda manutenção preditiva e controle.

### 2.4 Próximos passos (documentar)
- Janelas temporais (1/5/15 min), partição por data em `READING`, importância de atributos/SHAP, views para BI/Power BI.

---

## 🎬 Vídeo (até 5 min) — roteiro sugerido
1. Contexto e objetivo (0:30)  
2. DER e normalização (1:00–1:30)  
3. Pipeline: dados → BD → ML (1:00)  
4. Resultados: matriz de confusão (+ regressão) (1:00–1:30)  
5. Próximos passos (0:30)

---

## ✅ Checklist de Entregáveis (FIAP)
- [x] **DER** (PNG/SVG) + Mermaid  
- [x] **Script SQL** (`schema_oracle.sql`) + **seed**  
- [x] **CSV** do dataset  
- [x] **Código ML** (classificação) + (regressão opcional)  
- [x] **Gráficos/prints**: `confusion_matrix.png`, `regression_real_vs_pred.png`, e `db/prints/*.png`  
- [x] **README** claro + link do vídeo (não listado)

---

## Observações finais
- O modelo foi pensado para escalar: índices por tempo, checks de domínio e view de últimas leituras.  
- O pipeline de ML é reproduzível e cobre **classificação** (exigida) e **regressão** (bônus), reforçando a aplicação prática em ambiente industrial.
