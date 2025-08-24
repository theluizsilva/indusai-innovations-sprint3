-- seed_data.sql
INSERT INTO site (name, city, state) VALUES ('Planta SP - Linha 1', 'São Paulo', 'SP');

INSERT INTO asset (site_id, name, type, installed_at)
SELECT site_id, 'Esteira 7', 'CONVEYOR', SYSTIMESTAMP FROM site WHERE name='Planta SP - Linha 1';

INSERT INTO sensor_type (code, description, unit) VALUES ('TEMP','Temperatura','°C');
INSERT INTO sensor_type (code, description, unit) VALUES ('HUM','Umidade Relativa','%');
INSERT INTO sensor_type (code, description, unit) VALUES ('VIB','Vibração RMS','mm/s');
INSERT INTO sensor_type (code, description, unit) VALUES ('CURR','Corrente do Motor','A');
INSERT INTO sensor_type (code, description, unit) VALUES ('LUX','Luminosidade','lux');
INSERT INTO sensor_type (code, description, unit) VALUES ('PRESS','Pressão','kPa');

-- Cria um conjunto de sensores para o asset
INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-TEMP-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='TEMP';

INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-HUM-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='HUM';

INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-VIB-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='VIB';

INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-CUR-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='CURR';

INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-LUX-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='LUX';

INSERT INTO sensor (asset_id, sensor_type_id, model, serial_number, installed_at, is_active)
SELECT a.asset_id, st.sensor_type_id, 'Model-X','SN-PRE-001', SYSTIMESTAMP, 'Y'
  FROM asset a, sensor_type st WHERE a.name='Esteira 7' AND st.code='PRESS';
