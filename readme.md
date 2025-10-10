Install Node.js
Install Python

Install PostgreSQL
Port: 5432

Python Environment setup: 
1. cd to backend folder
2. py -m pip install -r requirements.txt


Conda Environment Setup:
1. Create new environment -> Python 3.12.11
2. conda install --yes --file requirements.txt


View Database

http://127.0.0.1:8000/docs


Design a system architecture from the sensor box to the dashboard. It has 9 IEQ monitoring sensor modules: Temperature, Humidity, carbon dioxide, oxygen, carbon monoxide, nitrogen dioxide, noise, light, and PM2.5. It uses ESP32 and LoRaWAN for data transmission. The server is built, database is Postgre SQL, backend is build by FastAPI (Python), frontend is HTML-CSS-Js. The dashboard allows to register a sensor box, and is for real-time monitoring for 3 plots: time series plots for parameters, risk heat map and parameter vs. parameter, and the system sends an email alert to householder via SMTP server





## Frontend:
```
cd frontend

npm install

npm run dev
```

## Backend:
In `/backend`:

- Within a .py file
- Select Python Interpreter
- Create Virtual Environment
- Venv
- Select Python (version must > 3.11)
- Select requirement.txt and press create

### If not first time
in `/backend`, run
```
uvicorn app.main:app --reload
```

### If first time
In terminal
```
.venv\Scripts\deactivate
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

In `/backend`, run
```
uvicorn app.main:app --reload
```

To install missing dependencies from `requirements.txt`
```
py -m pip install [required files]
```

## Simulation

```
cd Simulation
```

### If first time
Follow Database section to create the tables before running simulation

Then replace config.json's house_id with your households table item's house_id

### If not first time

Run 
```
py simulation.py
```

## Database:

into cmd

```
psql -U postgres
enter password: [set by user when installed postgreSQL]
```

Normally, connect as user sensoruser
```
psql -U sensoruser -d sensordb -h localhost -p 5432
```

### Create tables for initial run
```
CREATE USER sensoruser WITH PASSWORD 'secret123';
CREATE DATABASE sensordb OWNER sensoruser;
GRANT ALL PRIVILEGES ON DATABASE sensordb TO sensoruser;

-- Enable UUID generation helper (optional)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =========================
-- Table: households
-- =========================
CREATE TABLE IF NOT EXISTS public.households (
  id             SERIAL PRIMARY KEY,
  serial_number  VARCHAR(64)  NOT NULL UNIQUE,
  householder    VARCHAR(128) NOT NULL,
  phone          VARCHAR(32)  NOT NULL,
  email          VARCHAR(255) NOT NULL,
  address        VARCHAR(255) NOT NULL,
  zone           VARCHAR(1)   NOT NULL,
  house_id       VARCHAR(16)  NOT NULL UNIQUE,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- =========================
-- Table: sensors
-- =========================
CREATE TABLE IF NOT EXISTS public.sensors (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name           VARCHAR(120) NOT NULL,
  type           VARCHAR(80)  NOT NULL,
  location       VARCHAR(120),
  serial_number  VARCHAR(64),
  owner_id       INTEGER,
  meta           JSONB,
  CONSTRAINT fk_sensors_owner
    FOREIGN KEY (owner_id) REFERENCES public.households(id)
    ON DELETE SET NULL
);

-- =========================
-- Table: sensor_readings
-- =========================
CREATE TABLE IF NOT EXISTS public.sensor_readings (
  id          BIGSERIAL PRIMARY KEY,
  sensor_id   UUID NOT NULL,
  ts          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  value       DOUBLE PRECISION NOT NULL,
  attributes  JSONB,
  CONSTRAINT fk_readings_sensor
    FOREIGN KEY (sensor_id) REFERENCES public.sensors(id)
    ON DELETE CASCADE
);

-- =========================
-- Table: sensor_configs
-- =========================
CREATE TABLE IF NOT EXISTS public.sensor_configs (
  id          SERIAL PRIMARY KEY,
  sensor_id   UUID NOT NULL,
  revision    INTEGER NOT NULL DEFAULT 1,
  data        JSONB NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_configs_sensor
    FOREIGN KEY (sensor_id) REFERENCES public.sensors(id)
    ON DELETE CASCADE
);
ALTER TABLE public.sensor_readings OWNER TO sensoruser;
ALTER SEQUENCE public.sensor_readings_id_seq OWNER TO sensoruser;
```

### Insert one household to enable simulation
```
INSERT INTO households (
    serial_number,
    householder,
    phone,
    email,
    address,
    zone,
    house_id
) VALUES (
    'SN-20251010-001',
    'John Doe',
    '+64-210-555-1234',
    'john.doe@example.com',
    '123 Queen Street, Auckland, NZ',
    'A',
    'NJDOE456'
);
```

test with: select * from households;  (if table pops up, then setup is successful)


















