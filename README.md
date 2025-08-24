# Sprint 3 – Hermes Reply / FIAP — indusAI Innovations

> **Objetivo:** Modelar um banco de dados relacional para dados de sensores e treinar um modelo **básico** de Machine Learning usando os dados da Sprint 2 (temperatura) **enriquecidos** com novos sensores simulados (**umidade, vibração RMS, corrente do motor, luminosidade, pressão**). O rótulo **estado_operacional** (normal/alerta/falha) foi calculado por regras de negócio simples, coerentes com o domínio industrial.

---

## Estrutura do repositório
```
sprint3_pack/
  data/
    raw/
      sprint2_dados_temperatura.csv
    processed/
      dataset_sprint3_multisensor.csv      # 2.400 leituras, 6 sensores + rótulos
  db/
    schema_oracle.sql
    seed_data.sql
    erd.mmd
    ERD_sprint3_datasql.png                # diagrama exportado (Oracle Data Modeler) - adicionar aqui
  src/
    ml_train_sprint3.py                    # classificação (normal/alerta/falha)
    ml_regression_sprint3.py               # regressão (bônus): prever temp_c em +5 min
  results/
    (gerado após o treino)
  README.md
```

---

## Parte 1 — Banco de Dados

### 1.1 Diagrama ER (DER)
- Arquivo Mermaid: `db/erd.mmd` (pode abrir em https://mermaid.live e exportar PNG).
- Exportado via Oracle SQL Developer Data Modeler: **`db/ERD_sprint3_datasql.png`**.

**Entidades e campos (resumo):**
- **SITE**: `site_id` (PK), `name`, `city`, `state`, `created_at`  
- **ASSET**: `asset_id` (PK), `site_id` (FK→SITE), `name`, `type`, `installed_at`  
- **SENSOR_TYPE**: `sensor_type_id` (PK), `code` (UNIQUE), `description`, `unit`  
- **SENSOR**: `sensor_id` (PK), `asset_id` (FK→ASSET), `sensor_type_id` (FK→SENSOR_TYPE), `model`, `serial_number`, `installed_at`, `is_active` (CHECK IN 'Y','N')  
- **READING**: `reading_id` (PK), `sensor_id` (FK→SENSOR), `ts`, `value_num`, `quality` (CHECK IN 'OK','SUSPECT','MISSING')  
- **ASSET_STATE**: `asset_state_id` (PK), `asset_id` (FK→ASSET), `ts`, `state` (CHECK IN 'normal','alerta','falha'), `note`  

**Relações/Índices relevantes:**
- SITE 1—N ASSET; ASSET 1—N SENSOR; SENSOR_TYPE 1—N SENSOR; SENSOR 1—N READING; ASSET 1—N ASSET_STATE.  
- Índices: `READING(sensor_id, ts)` e `ASSET_STATE(asset_id, ts)` — consultas temporais eficientes.  
- View utilitária: `vw_sensor_latest` (última leitura por sensor).

> **Justificativa**: separar medições brutas (`READING`) de rótulos agregados (`ASSET_STATE`) evita poluir a tabela de leituras e habilita ML supervisionado de forma limpa. `SENSOR_TYPE` normaliza unidade/descrição.

### 1.2 Criar o schema (DDL)
1. Abra `db/schema_oracle.sql` no Oracle SQL Developer e **F5 (Run Script)**.  
2. Saída esperada: *Table created* para cada tabela, *Index created* para índices, *View created* para `vw_sensor_latest`.

### 1.3 Carga inicial (seed)
- Execute `db/seed_data.sql` para inserir 1 `SITE`, 1 `ASSET`, 6 `SENSOR_TYPE` (TEMP/HUM/VIB/CURR/LUX/PRESS) e 6 `SENSOR` (um por tipo).

### 1.4 Validações rápidas (SQL)
```sql
-- contagens
SELECT COUNT(*) sites        FROM site;
SELECT COUNT(*) assets       FROM asset;
SELECT COUNT(*) sensor_types FROM sensor_type;
SELECT COUNT(*) sensors      FROM sensor;
SELECT COUNT(*) readings     FROM reading;
SELECT COUNT(*) asset_states FROM asset_state;

-- sensores + tipos
SELECT s.sensor_id, st.code AS sensor_code, st.unit, a.name AS asset_name
FROM sensor s
JOIN sensor_type st ON st.sensor_type_id = s.sensor_type_id
JOIN asset a        ON a.asset_id        = s.asset_id
ORDER BY s.sensor_id;

-- índices
SELECT index_name, table_name, column_name, column_position
FROM user_ind_columns
WHERE table_name IN ('READING','ASSET_STATE')
ORDER BY table_name, index_name, column_position;
```

> **Opcional (demo da view)**: insira 2 leituras em um sensor TEMP e consulte `vw_sensor_latest` para ver `last_ts` e `last_value` atualizados.

---

## Parte 2 — Machine Learning

### 2.1 Ambiente
Requisitos: Python 3.10+, `pandas`, `numpy`, `scikit-learn`, `matplotlib`  
Instalação:
```bash
pip install -r requirements.txt
# ou
pip install pandas numpy scikit-learn matplotlib
```

### 2.2 Dataset
- `data/processed/dataset_sprint3_multisensor.csv` com **~2.400 linhas** e colunas:  
  `timestamp, temp_c, humidity_pct, vibration_rms, motor_current_a, light_lux, pressure_kpa, estado_operacional, temp_c_plus5min`  
- Garante **>500 leituras por sensor** conforme exigência.

### 2.3 Classificação (exigido)
```bash
python src/ml_train_sprint3.py
```
Gera em `results/`:
- `metrics.txt` (precision/recall/F1 por classe)  
- `confusion_matrix.png` (visualização obrigatória recomendada)  
- `sample_predictions.csv`

**Justificativa do gráfico:** a **matriz de confusão** mostra acertos/erros por classe (**normal/alerta/falha**), ideal para domínios industriais com risco operacional.

### 2.4 Regressão (over‑delivery)
```bash
python src/ml_regression_sprint3.py
```
Gera: `metrics_regression.txt` (MAE/R²) e `regression_real_vs_pred.png` (curvas real vs predita).  
Ajuda a demonstrar **previsão de curto prazo** (temperatura em +5 min).

---

## Como foi gerado o dataset
- Temperatura: baseada na distribuição observada na Sprint 2, com tendência suave e picos esporádicos.  
- Sinais correlacionados de forma plausível:  
  - **Umidade** levemente inversa à temperatura.  
  - **Vibração** e **corrente** aumentam com temperatura/carga (com “shocks”).  
  - **Luminosidade** com padrão diurno. **Pressão** quase constante, com pequenas quedas.  
- **estado_operacional**: regras de limiar simples para marcar `normal`, `alerta` e `falha`.

---

## Vídeo (até 5 min) — Roteiro sugerido
1. **Contexto e objetivo** (0:30)  
2. **DER e normalização** (1:00–1:30)  
3. **Pipeline**: dados → BD → ML (1:00)  
4. **Resultados**: matriz de confusão (+ regressão opcional) (1:00–1:30)  
5. **Próximos passos** (0:30): agregações por janela, particionamento de `READING`, feature importance/SHAP, integração com BI.

---

## Checklist de Entregáveis (FIAP)
- [ ] **DER** exportado (PNG/SVG) + arquivo Mermaid
- [ ] **Script SQL** de criação (`schema_oracle.sql`) + **seed**
- [ ] **CSV** do dataset usado (treino/teste)
- [ ] **Código ML** (classificação obrigatória, regressão opcional)
- [ ] **Gráficos/prints** dos resultados (`confusion_matrix.png`, etc.)
- [ ] **README** com explicações e **link do vídeo (não listado)**

---

## Observações finais
- O modelo relacional está pronto para escalar (índices, checks, view de últimas leituras).  
- O conjunto de dados e o pipeline de ML cumprem as exigências e incluem **over‑delivery** técnico para destacar a entrega.
