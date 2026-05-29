# Intelligent Data Pipeline for Real-Time Decisions

A final year research project implementing an intelligent real-time data pipeline using **Redis** and **PostgreSQL**, designed for IoT sensor data processing with adaptive caching, intelligent routing, and automated alert lifecycle management.

> **Author:** Bashir Muhammed Nur (S122202079)  
> **Supervisor:** Mr. Omisore  
> **Institution:** Crescent University Abeokuta — Department of Computer Science  
> **Degree:** B.Sc. Computer Science, July 2026

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [System Components](#system-components)
- [API Endpoints](#api-endpoints)
- [Alert Lifecycle](#alert-lifecycle)
- [Intelligent Routing Logic](#intelligent-routing-logic)
- [Performance Evaluation](#performance-evaluation)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the Simulation](#running-the-simulation)
- [Running Benchmarks](#running-benchmarks)
- [Database Schema](#database-schema)
- [Thresholds](#thresholds)
- [Research Context](#research-context)

---

## Overview

This system demonstrates how a **lightweight dual-storage architecture** can support real-time decision-making for IoT applications without requiring large-scale distributed infrastructure.

The pipeline continuously ingests simulated IoT sensor data (temperature and humidity), applies intelligent routing to distribute data between fast in-memory storage (Redis) and durable persistent storage (PostgreSQL), and manages an automated alert lifecycle that detects, tracks and resolves environmental threshold violations.

The core thesis claim: **Redis-based caching reduces read latency by orders of magnitude compared to direct PostgreSQL queries**, while maintaining full data durability through dual-write architecture.

---

## Architecture

The system follows a **hybrid Kappa architecture** — treating all sensor data as streams while using dual storage to separate hot data (recent readings) from cold data (historical records).

```
IoT Sensor Simulation
        │
        ▼
┌─────────────────────┐
│   FastAPI (REST)    │  ← Entry point, validation, routing
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  Intelligent Router │  ← Threshold evaluation, alert lifecycle
└─────────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
┌──────┐  ┌──────────────┐
│Redis │  │  PostgreSQL  │
│(Hot) │  │   (Cold)     │
│      │  │              │
│Latest│  │All events    │
│reads │  │All alerts    │
│Active│  │Full history  │
│alerts│  │Audit trail   │
└──────┘  └──────────────┘
```

**Hot data (Redis):** Latest reading per device, active alerts — accessed in < 5ms  
**Cold data (PostgreSQL):** Every sensor event ever recorded, full alert history — authoritative source of truth

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API Framework | FastAPI (Python) | REST endpoints, request validation |
| In-Memory Store | Redis | Hot data cache, active alert state |
| Persistent Store | PostgreSQL | Durable storage, historical queries |
| ORM | SQLAlchemy | Database models, session management |
| Validation | Pydantic | Request body schema validation |
| DB Driver | psycopg2-binary | PostgreSQL connection driver |
| Server | Uvicorn | ASGI server |

---

## Project Structure

```
final_year_project/
│
├── main.py                     # App entry point, table creation
├── simulate.py                 # Sensor data simulation script
├── benchmark.py                # Latency benchmarking script
├── chart.py                    # Benchmark result visualisation
├── requirements.txt            # Python dependencies
├── .gitignore
├── README.md
│
└── app/
    ├── __init__.py
    ├── models.py               # SQLAlchemy ORM models (SensorEvent, Alert)
    ├── schemas.py              # Pydantic request/response schemas
    │
    ├── db/
    │   ├── __init__.py
    │   ├── psql.py             # PostgreSQL engine, session factory, get_db()
    │   └── redis.py            # Redis client, get_redis()
    │
    ├── routes/
    │   ├── __init__.py
    │   └── sensors.py          # All sensor and alert endpoints
    │
    └── services/
        ├── __init__.py
        └── alert_service.py    # Threshold evaluation, alert lifecycle logic
```

---

## System Components

### 1. API and Ingestion Layer (`app/routes/sensors.py`)
Receives incoming sensor readings via REST, validates the payload using Pydantic schemas, triggers the dual-write to Redis and PostgreSQL, and calls the alert processing service.

### 2. Intelligent Routing Layer (`app/services/alert_service.py`)
The core intelligence of the system. Evaluates every incoming reading against predefined environmental thresholds. Manages alert state using Redis as the active-alert whiteboard and PostgreSQL as the permanent incident log. Prevents duplicate alerts through state-aware creation logic.

### 3. In-Memory Storage Layer (`app/db/redis.py`)
Redis stores two categories of data:
- `sensor:latest:{device_id}` — most recent reading per device, with 60-second TTL
- `alert:active:{device_id}:{alert_code}` — currently active (pending) alerts

### 4. Persistent Storage Layer (`app/db/psql.py`)
PostgreSQL stores everything permanently:
- Every sensor event ever received
- Every alert ever triggered, including resolution timestamps

### 5. Simulation Layer (`simulate.py`)
Automatically fires configurable numbers of sensor readings with randomised values — some within safe range, some violating thresholds — to generate realistic data for benchmarking.

---

## API Endpoints

### Sensor Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sensors/data` | Ingest a sensor reading |
| `GET` | `/sensors/{device_id}/latest` | Get latest reading (cache-first) |
| `GET` | `/sensors/{device_id}/history` | Get historical readings (PostgreSQL) |

### POST `/sensors/data`
**Request body:**
```json
{
  "device_id": "sensor_01",
  "temperature": 27.3,
  "humidity": 55.0
}
```
**Response:**
```json
{
  "status": "success",
  "id": 1
}
```
Performs a dual-write: persists to PostgreSQL, updates Redis cache, then runs alert evaluation.

---

### GET `/sensors/{device_id}/latest`
Returns the most recent reading for a device. Checks Redis first — if the key exists and hasn't expired, returns immediately without hitting PostgreSQL. On cache miss, queries PostgreSQL and repopulates the cache.

**Response (cache hit):**
```json
{
  "device_id": "sensor_01",
  "temperature": 27.3,
  "humidity": 55.0,
  "recorded_at": "2026-05-26T13:42:19.968088+01:00",
  "source": "cache"
}
```

**Response (cache miss):**
```json
{
  "device_id": "sensor_01",
  "temperature": 27.3,
  "humidity": 55.0,
  "recorded_at": "2026-05-26T13:42:19.968088+01:00",
  "source": "database"
}
```

The `source` field is key for benchmarking — it tells you exactly which storage layer served each request.

---

### GET `/sensors/{device_id}/history?limit=50`
Returns historical readings from PostgreSQL, newest first. Accepts optional `limit` query parameter (default: 50).

---

## Alert Lifecycle

Each alert progresses through two states:

```
Threshold violated → PENDING → Condition normalises → FIXED
```

### Alert Codes

| Code | Condition | Threshold |
|---|---|---|
| `TEMP_HIGH` | Temperature too high | > 30°C |
| `TEMP_LOW` | Temperature too low | < 18°C |
| `HUMID_HIGH` | Humidity too high | > 70% |
| `HUMID_LOW` | Humidity too low | < 40% |

### State Logic

**On each incoming reading, for each of the 4 alert codes:**

```
Is this code currently violating?
│
├── YES
│   ├── Active alert in Redis?
│   │   ├── NO  → Create new alert in PostgreSQL (status: pending)
│   │   │         Cache alert ID in Redis
│   │   └── YES → Update current_value in PostgreSQL only
│   │             (no duplicate alert created)
│
└── NO
    ├── Active alert in Redis?
    │   ├── YES → Update PostgreSQL status to "fixed"
    │   │         Record resolved_at timestamp
    │   │         Delete from Redis
    │   └── NO  → Do nothing
```

This prevents alert flooding — repeated violations update the same record rather than creating duplicates.

---

## Intelligent Routing Logic

The `source` field in API responses reveals the routing decision made for each request:

- **`"source": "cache"`** — served from Redis in < 5ms, PostgreSQL not touched
- **`"source": "database"`** — Redis key expired or missing, served from PostgreSQL, cache repopulated

The TTL on Redis keys (60 seconds) defines the "hot data window". A reading older than 60 seconds is considered cold and will trigger a PostgreSQL fallback on next request.

---

## Performance Evaluation

The system is benchmarked across three key metrics:

### 1. Latency
- Redis read latency (target: < 5ms)
- PostgreSQL read latency (baseline comparison)
- End-to-end ingestion latency

### 2. Cache Efficiency
- Cache hit rate (% of requests served from Redis)
- Cache miss rate and PostgreSQL fallback frequency

### 3. Throughput
- Sensor events ingested per second
- Concurrent device support

Run `benchmark.py` to generate latency comparison data. Run `chart.py` to visualise results.

---

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL running locally
- Redis running locally

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd final_year_project

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
Create the PostgreSQL database:
```bash
psql -U postgres -c "CREATE DATABASE intelligent_data_pipeline;"
```

Tables are created automatically on first run via SQLAlchemy's `Base.metadata.create_all()`.

### Running the Server
```bash
fastapi dev main.py
```

Server starts at `http://127.0.0.1:8000`  
API docs available at `http://127.0.0.1:8000/docs`

---

## Environment Variables

The app reads database and Redis connection strings directly from `app/db/psql.py` and `app/db/redis.py`. Update these files to match your local setup:

```python
# app/db/psql.py
DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/intelligent_data_pipeline"

# app/db/redis.py
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
```

---

## Running the Simulation

```bash
python simulate.py
```

Fires 100 randomised sensor readings to the API, mixing normal and threshold-violating values. Prints response time per request and a summary of total time and average latency.

---

## Running Benchmarks

```bash
python benchmark.py
```

Runs a controlled latency comparison between Redis reads and PostgreSQL reads. Outputs results to the console and saves data for charting.

```bash
python chart.py
```

Generates a visual latency comparison chart from benchmark results.

---

## Database Schema

### `sensor_events`
| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `device_id` | String | Sensor identifier |
| `temperature` | Float | Temperature reading in °C |
| `humidity` | Float | Humidity reading in % |
| `recorded_at` | DateTime (TZ) | Defaults to current UTC time |

### `alerts`
| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `device_id` | String | Sensor that triggered the alert |
| `alert_code` | String | TEMP_HIGH, TEMP_LOW, HUMID_HIGH, HUMID_LOW |
| `status` | String (NOT NULL) | pending or fixed |
| `current_value` | Float | Most recent violating value |
| `triggered_at` | DateTime (TZ) | When the alert was first created |
| `resolved_at` | DateTime (TZ) | When the condition normalised (nullable) |

---

## Thresholds

Based on ASHRAE data center environmental guidelines:

| Parameter | Safe Range | Low Alert | High Alert |
|---|---|---|---|
| Temperature | 18°C – 30°C | < 18°C (TEMP_LOW) | > 30°C (TEMP_HIGH) |
| Humidity | 40% – 70% | < 40% (HUMID_LOW) | > 70% (HUMID_HIGH) |

---

## Research Context

This project is the implementation component of a final year thesis titled **"Intelligent Data Pipelines for Real-Time Decisions"**. It addresses documented gaps in existing literature around practical, resource-constrained IoT pipeline implementations.

**Key references:**
- Kleppmann (2019) — *Designing Data-Intensive Applications*
- Reis & Housley (2022) — *Fundamentals of Data Engineering*
- Penka et al. (2021) — Kappa architecture for IoT data management
- Shevchenko et al. (2025) — Adaptive TTL strategies for Redis
- Wang et al. (2022) — Dual-space storage architectures

The system proves that sophisticated real-time IoT data processing is achievable on modest hardware using open-source technologies — without cloud infrastructure or distributed processing frameworks.