# Sprint 3 — Hermes Reply / FIAP · indusAI Innovations (Entrega Técnica)

> **Resumo executivo.** Esta entrega consolida **modelagem relacional** para dados de sensores + **pipeline de Machine Learning** reproduzível. O repositório inclui: DER (imagem e Mermaid), scripts SQL (DDL/seed), dataset multissensor com >500 leituras por sensor, código Python (classificação obrigatória + regressão opcional), **métricas e gráficos** em `results/`, prints de validação do banco em `db/prints/` e **README** com instruções de execução e justificativas técnicas.

---

## 1) Organização do repositório

```
sprint3_pack/
  data/
    raw/
      sprint2_dados_temperatura.csv
    processed/
      dataset_sprint3_multisensor.csv      # ~2.395 linhas, 6 sensores + rótulos
  db/
    schema_oracle.sql
    seed_data.sql
    erd.mmd
    ERD_sprint3_datasql.png                # DER exportado (Oracle Data Modeler)
    prints/                                # evidências: DDL, seed, contagens etc.
  src/
    ml_train_sprint3.py                    # classificação (normal/alerta/falha)
    ml_regression_sprint3.py               # regressão (bônus): prever temp_c +5 min
  results/
    metrics.txt
    confusion_matrix.png
    sample_predictions.csv
    metrics_regression.txt
    regression_real_vs_pred.png
  requirements.txt
  README.md
```

**TL;DR (execução rápida, local):**
```bash
cd sprint3_pack
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python src/ml_train_sprint3.py
python src/ml_regression_sprint3.py      # opcional (bônus)
```
Saídas em `results/`: `metrics.txt`, `confusion_matrix.png`, `sample_predictions.csv`, `metrics_regression.txt`, `regression_real_vs_pred.png`.

---

## 2) Banco de Dados (Oracle) — Modelagem, DDL e Validações

### 2.1 Decisões de modelagem (3NF + domínio industrial)
- **Entidades:** `SITE` (planta), `ASSET` (equipamento), `SENSOR_TYPE` (tipos normalizados), `SENSOR` (instância física), `READING` (telemetria bruta), `ASSET_STATE` (rótulo agregado por ativo/tempo).  
- **Normalização:** 3ª forma normal. Evita redundância e anomalias; `SENSOR_TYPE` remove duplicidade de unidade/código.  
- **Chaves:** PK numéricas (`*_id`) com **IDENTITY** (Oracle 12c+). FKs explícitas preservam integridade referencial.  
- **Domínios (CHECK):**
  - `SENSOR.is_active IN ('Y','N')`
  - `READING.quality IN ('OK','SUSPECT','MISSING')`
  - `ASSET_STATE.state IN ('normal','alerta','falha')`
- **Índices para consultas temporais:**
  - `READING(sensor_id, ts)`
  - `ASSET_STATE(asset_id, ts)`
- **View utilitária:** `vw_sensor_latest` (última leitura por sensor).  
- **Escalabilidade (roadmap):** particionar `READING` por **intervalo de tempo** (ex.: RANGE por mês), compressão de dados frios, retenção e arquivamento, e `materialized views` para agregados.

### 2.2 DER
- **Imagem:** `db/ERD_sprint3_datasql.png` (gerada no Oracle SQL Developer Data Modeler).
- **Mermaid (para visualização rápida):** `db/erd.mmd` (abrir em https://mermaid.live).

### 2.3 Criação do schema e seed
1. **DDL**: abrir `db/schema_oracle.sql` no **Oracle SQL Developer (IDE)** → **Run Script (F5)**.  
2. **Seed**: abrir `db/seed_data.sql` → **Run Script (F5)** → `COMMIT;`.

### 2.4 Validações mínimas (prints em `db/prints/`)
- **Contagens** (`01_counts.png`):
```sql
SELECT
  (SELECT COUNT(*) FROM site)        AS sites,
  (SELECT COUNT(*) FROM asset)       AS assets,
  (SELECT COUNT(*) FROM sensor_type) AS sensor_types,
  (SELECT COUNT(*) FROM sensor)      AS sensors,
  (SELECT COUNT(*) FROM reading)     AS readings,
  (SELECT COUNT(*) FROM asset_state) AS asset_states
FROM dual;
```
- **Sensores × tipos** (`02_sensors_map.png`):
```sql
SELECT s.sensor_id, st.code AS sensor_code, st.unit, a.name AS asset_name
FROM sensor s
JOIN sensor_type st ON st.sensor_type_id = s.sensor_type_id
JOIN asset a        ON a.asset_id        = s.asset_id
ORDER BY s.sensor_id;
```
- **Índices** (`03_indexes.png`) e **constraints** (`04_constraints_pks.png`, `05_constraints_fks.png`, `06_constraints_checks.png`):
```sql
SELECT index_name, table_name, column_name, column_position
FROM user_ind_columns
WHERE table_name IN ('READING','ASSET_STATE')
ORDER BY table_name, index_name, column_position;

SELECT table_name, constraint_name
FROM user_constraints
WHERE constraint_type = 'P'
  AND table_name IN ('SITE','ASSET','SENSOR_TYPE','SENSOR','READING','ASSET_STATE')
ORDER BY table_name;

SELECT c.table_name, c.constraint_name, r.table_name AS referenced_table
FROM user_constraints c
JOIN user_constraints r ON c.r_constraint_name = r.constraint_name
WHERE c.constraint_type = 'R'
  AND c.table_name IN ('ASSET','SENSOR','READING','ASSET_STATE')
ORDER BY c.table_name, c.constraint_name;

SELECT table_name, constraint_name, search_condition
FROM user_constraints
WHERE constraint_type = 'C'
  AND table_name IN ('SENSOR','READING','ASSET_STATE')
ORDER BY table_name, constraint_name;
```
- **View (opcional, `07_view_latest.png`)**: inserir 2 leituras em `TEMP` e consultar `vw_sensor_latest`.

### 2.5 Padrões e práticas
- **Nomenclatura:** `singular`, `snake_case`, PK `*_id`, FK com prefixo `fk_*`, índices `idx_*`.  
- **Tipos e fuso:** `TIMESTAMP` (UTC recomendado via aplicação/ETL) + `CHECK` em domínios qualitativos.  
- **Integridade e desempenho:** FKs com `CASCADE CONSTRAINTS` nos DROPs, índices compostos em `(chave, ts)`, e **explain plan** para queries críticas.  
- **Observabilidade:** visão `vw_sensor_latest` para dashboards rápidos; monitor de crescimento em `READING`.

---

## 3) Dados & Ingestão

### 3.1 Dataset para ML
Arquivo: `data/processed/dataset_sprint3_multisensor.csv` (≈2.395 linhas). Colunas:
```
timestamp, temp_c, humidity_pct, vibration_rms, motor_current_a,
light_lux, pressure_kpa, estado_operacional, temp_c_plus5min
```
- **Coerência física:** umidade levemente inversa à temperatura; vibração e corrente sobem com carga/temperatura; luminosidade com padrão diurno; pressão quase constante (ruído branco).  
- **Rótulo `estado_operacional`** (supervisionado):  
  - `falha` se (temp>42) **OU** (vib>3.0) **OU** (corr>14.5)  
  - `alerta` se (temp>37) **OU** (vib>2.2) **OU** (corr>12.5)  
  - `normal` caso contrário
- **Alvo de regressão:** `temp_c_plus5min` (= temperatura +5 min; `shift(-5)`).

### 3.2 Qualidade de dados (checagens)
- Estatísticas de faixa/limites por sensor; valores negativos inválidos; consistência de unidades; verificação de `NaN`/`Inf` (dataset final sem nulos).  
- Amostragem temporal uniforme (1 min) — adequada ao exercício de sprint.  
- **Risco:** dataset sintético tende a separar bem classes (pode superestimar a acurácia). Registrado em “Limitações”.

---

## 4) Machine Learning (Classificação obrigatória + Regressão bônus)

### 4.1 Ambiente e reprodutibilidade
- `requirements.txt` (pinned por major versions).  
- `random_state=42` e **estratificação** no `train_test_split` para estabilidade entre rodadas.  
- Saídas padrão em `results/` para facilitar avaliação e versionamento.

### 4.2 Classificação — `src/ml_train_sprint3.py`
- **Features:** `temp_c, humidity_pct, vibration_rms, motor_current_a, light_lux, pressure_kpa`.  
- **Target:** `estado_operacional ∈ {normal, alerta, falha}`.  
- **Pipeline:** `StandardScaler` + `RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)`.  
- **Split:** 80/20 estratificado.  
- **Métricas geradas:** `precision/recall/F1 por classe`, `accuracy` (em `results/metrics.txt`).  
- **Visualização:** `results/confusion_matrix.png` (rende ponto na banca).  
- **Amostras:** `results/sample_predictions.csv` (primeiros 100 testes).

**Execução:**
```bash
cd sprint3_pack
python src/ml_train_sprint3.py
```
**Interpretação da saída (exemplo esperado):**
- Acurácia alta (dataset sintético) e matriz de confusão com poucos erros entre `alerta`×`falha`.  
- Se necessário, ajustar `class_weight` ou `n_estimators`.

### 4.3 Regressão (bônus) — `src/ml_regression_sprint3.py`
- **Target:** `temp_c_plus5min`.  
- **Modelo:** `RandomForestRegressor(n_estimators=200, random_state=42)`.  
- **Métricas:** `MAE`, `R²` em `results/metrics_regression.txt`.  
- **Gráfico:** `results/regression_real_vs_pred.png` (100 primeiras amostras).

**Execução:**
```bash
cd sprint3_pack
python src/ml_regression_sprint3.py
```
**Interpretação:** MAE baixo (≈0,5–1,0 °C) e R² alto (≈0,9) são adequados para esse dataset.

### 4.4 Boas práticas e extensões
- **Validação k-fold** (estratificada) e curva de aprendizado.  
- **Explainability:** importância de features e (bônus) SHAP.  
- **MLOps:** fixar versão de libs, salvar `model.pkl` (não exigido), script de inferência isolado, e logs de execução.  
- **Ética/privacidade:** dados sintéticos; em produção, anonimizar metadados e seguir LGPD.

---

## 5) Evidências & Documentação para a banca

### 5.1 Prints do banco (`db/prints/`)
- `00_schema_created.png`, `00_seed_ok.png`, `01_counts.png`, `02_sensors_map.png`,  
  `03_indexes.png`, `04_constraints_pks.png`, `05_constraints_fks.png`, `06_constraints_checks.png`,  
  `07_view_latest.png` (opcional).

### 5.2 Resultados de ML (`results/`)
- `metrics.txt`, `confusion_matrix.png`, `sample_predictions.csv`,  
  `metrics_regression.txt`, `regression_real_vs_pred.png`.

### 5.3 Vídeo (≤5 min, não listado no YouTube)
**Roteiro objetivo:**
1) Contexto e objetivo (0:30) — digitalização industrial + ML.  
2) DER (1:00) — entidades, FKs, índices temporais, view.  
3) Pipeline (1:00) — dados → BD → dataset → ML.  
4) Resultados (1:30) — matriz de confusão e (bônus) regressão.  
5) Próximos passos (0:30) — partição de `READING`, janelas temporais, SHAP, BI.

---

## 6) Limitações e próximos passos técnicos
- **Limitações:** dataset **sintético** e balanceado pode inflar métricas; sem particionamento físico em `READING` (prototipação); sem orquestração/ETL real.  
- **Roadmap:** particionamento mensal em `READING`, `materialized views` para KPIs, compressão de dados frios, SHAP para explicar modelos, integração com Power BI, e teste com dados reais.

---

## 7) Como reproduzir do zero (checklist final)

1) **Banco:** rodar `db/schema_oracle.sql` → `db/seed_data.sql` → validações (salvar prints).  
2) **Ambiente Python:** criar venv, `pip install -r requirements.txt`.  
3) **Dataset:** confirmar `data/processed/dataset_sprint3_multisensor.csv` (já fornecido).  
4) **ML:** rodar `src/ml_train_sprint3.py` e (opcional) `src/ml_regression_sprint3.py`.  
5) **Resultados:** conferir `results/` e referenciar no README.  
6) **Vídeo:** gravar 5 min, subir como “não listado” e linkar no README.

---

## 8) Anexo A — SQL de limpeza (idempotente)
Use se precisar recriar tudo rapidamente (ignora “não existe” e mantém ordem de dependências):
```sql
BEGIN EXECUTE IMMEDIATE 'DROP VIEW vw_sensor_latest';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE reading CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE asset_state CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sensor CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE sensor_type CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE asset CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE site CASCADE CONSTRAINTS PURGE';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF; END;
/
```
> Depois, rode `db/schema_oracle.sql` e `db/seed_data.sql` novamente.

---

### Licença
Este projeto é educacional (FIAP · Sprint 3) e utiliza **dados sintéticos**. Ajuste a licença do repositório conforme a diretriz do grupo/disciplina.
