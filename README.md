# Sprint 3 – Hermes Reply / FIAP – indusAI Innovations

> **Objetivo:** Modelar um banco de dados relacional para dados de sensores e treinar um modelo **básico** de Machine Learning usando os dados da Sprint 2 (temperatura) enriquecidos com **novos sensores simulados**.

## Estrutura do repositório
```
sprint3_pack/
  data/
    raw/
      sprint2_dados_temperatura.csv
    processed/
      dataset_sprint3_multisensor.csv
  db/
    schema_oracle.sql
    seed_data.sql
    erd.mmd
  src/
    ml_train_sprint3.py
  results/
    (gerado após o treino)
```

## Parte 1 – Banco de Dados
1. **Modelagem ER**  
   - Entidades principais: `site`, `asset`, `sensor_type`, `sensor`, `reading`, `asset_state`.
   - Exportar o diagrama do arquivo `db/erd.mmd` (abre em <https://mermaid.live>, exporte PNG).
2. **Criação do schema**  
   - Use Oracle SQL Developer Data Modeler **ou** rode o script base `db/schema_oracle.sql` para criar tabelas.
3. **Carga inicial**  
   - Execute `db/seed_data.sql` para cadastrar site, asset e tipos de sensores.
4. **Ingestão de leituras**  
   - Use `data/processed/dataset_sprint3_multisensor.csv` como fonte e insira os valores na tabela `reading` (um registro por sensor/leitura), associando `asset_state` pelo timestamp.
5. **Consulta de validação**  
   - Verifique a última leitura por sensor via `vw_sensor_latest`.

## Parte 2 – Machine Learning
1. **Problema**: **classificação multiclasses** do `estado_operacional` (`normal`, `alerta`, `falha`) a partir de 6 sensores.
2. **Dataset**: `data/processed/dataset_sprint3_multisensor.csv` (2.400 leituras; > 500 por sensor).
3. **Treino**:  
   ```bash
   python src/ml_train_sprint3.py
   ```
   Resultados em `results/metrics.txt`, `results/confusion_matrix.png` e `results/sample_predictions.csv`.
4. **Justificativa do gráfico**: Matriz de confusão evidencia acertos e erros por classe, ideal para classificação industrial.

## Como foi gerado o dataset
- Baseado na temperatura da Sprint 2 (quando disponível).  
- Foram simulados **umidade**, **vibração RMS**, **corrente do motor**, **luminosidade** e **pressão** com correlação física plausível.  
- O rótulo `estado_operacional` segue regras de negócio (limiares).

## Vídeo (até 5 min)
Sugestão de roteiro:
- **(0:30)** Contexto e objetivo.
- **(1:30)** DER e por que normalizar.
- **(2:30)** Pipeline de dados → BD → ML.
- **(3:30)** Métricas e próximos passos (ex.: regressão de `temp_c_plus5min`).

## Próximos passos (over‑delivery)
- Regressão para prever `temp_c_plus5min` (baseline comparativo).
- Feature importance/SHAP (interpretabilidade).
- Particionamento por data nas leituras (performance).
- Agregações por janela (1m/5m/1h) para reduzir ruído e volume.
