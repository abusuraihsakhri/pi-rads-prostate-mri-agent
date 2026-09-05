# Pi Rads Prostate MRI Agent

> **Domain:** Diagnostic Radiology & Medical Imaging AI
> **Reference Guidelines & Standards:** `American College of Radiology (ACR) RADS & Fleischner Society`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Pi Rads Prostate MRI Agent** is an advanced analytical and computational platform implementing Multiparametric Prostate MRI PI-RADS v2.1 Scoring Engine. It provides:

- **PI-RADS v2.1 Scoring**: Automated scoring of prostate lesions based on ACR guidelines
- **Multi-Agent Architecture**: Distributed component system with specialized evaluation agents
- **Zero-PHI Security**: AST and regex inspection blocking sensitive patient identifiers
- **Tamper-Evident Audit Trail**: HMAC-SHA256 chained cryptographic logs
- **FastAPI REST API**: OpenAPI 3.1 endpoints with Prometheus telemetry

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core PI-RADS Scoring Engine

- **`score_lesion()`**: Routes lesions to zone-specific scoring (PZ or TZ)
- **`score_peripheral_zone()`**: PZ scoring with DWI primary, DCE secondary
- **`score_transition_zone()`**: TZ scoring with T2W primary, DWI secondary
- **`assess_patient()`**: Multi-lesion patient assessment

### 🤖 Agent Framework

- **`PZSequenceEvaluatorAgent`**: Primary metric threshold evaluation
- **`TZSequenceEvaluatorAgent`**: Secondary kinetics and STAT escalation
- **`PIRADSCompositeScorerAgent`**: Biomarker concordance checking
- **`SystemSupervisor`**: Master orchestrator with multi-worker consensus

### 🛡️ Security & Audit

- **`PHIGuard`**: Zero-PHI outbound interceptor (SSN, MRN, phone, email patterns)
- **`AuditTrail`**: HMAC-SHA256 tamper-evident chained audit log
- **`ClinicalDomainEngine`**: Clinical threshold evaluation engine

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/pi-rads-prostate-mri-agent.git
cd pi-rads-prostate-mri-agent

# Install dependencies
pip install pydantic fastapi uvicorn pytest

# Optional: Set audit secret key for persistent audit integrity
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

---

## 💻 CLI Quickstart & Usage

### 1. Score a Single Lesion
```bash
python cli.py score --zone peripheral --t2w 3 --dwi 4 --dce-positive
```

### 2. Assess Multiple Lesions
```bash
python cli.py assess -l peripheral:3:4:dce:12 -l transition:2:2:0:8
```

### 3. Get PI-RADS Score Information
```bash
python cli.py info
python cli.py info 4
```

### 4. JSON Output
```bash
python cli.py score --zone peripheral --t2w 3 --dwi 4 --json
python cli.py assess -l peripheral:3:4:dce --json
```

### Parameter Reference
| Parameter | Description | Values |
|:----------|:------------|:-------|
| `--zone` | Prostate zone | `peripheral`, `transition`, `anterior_fibromuscular`, `central` |
| `--t2w` | T2-weighted score | 1-5 |
| `--dwi` | Diffusion-weighted imaging score | 1-5 |
| `--dce-positive` | DCE positivity flag | (boolean flag) |
| `--size` | Lesion size in mm | (float) |
| `--location` | Anatomical location | (string) |

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Unique case identifier | Required |
| `patient_synthetic_id` | De-identified patient token | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary kinetic/confidence score | Required |
| `status_flag` | Clinical status descriptor | Required |
| `is_stat` | Emergency escalation flag | Required |

---

## 🔌 REST API Server

### Start the Server
```bash
python cli.py serve --host 0.0.0.0 --port 8000
```

### API Endpoints
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/audit` | Submit case for evaluation |
| `POST` | `/api/chat` | Query supervisory assistant |
| `GET` | `/metrics` | Prometheus telemetry |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "CASE-2026-001",
    "patient_synthetic_id": "SYNTH-PT-001",
    "primary_metric": 24.5,
    "secondary_metric": 14.0,
    "status_flag": "DISCORDANT",
    "is_stat": true
  }'
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).
* **Path Traversal Protection:** Input validation on file paths prevents directory traversal attacks.

---

## 🧪 Testing & Verification

### Run All Tests
```bash
pytest -v
```

### Run Specific Test Suites
```bash
pytest tests/test_pi_rads.py -v          # PI-RADS scoring engine tests
pytest tests/test_enrichment.py -v       # Enrichment module tests
pytest test_prostate_mri_sentinel.py -v  # Sentinel agent tests
pytest tests/test_pi_rads_prostate_mri_agent.py -v  # Agent framework tests
```

### Batch Simulation Benchmark
```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

### Docker Build & Run
```bash
docker build -t pi-rads-prostate-mri-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secure-key" pi-rads-prostate-mri-agent
```

### Docker Compose
```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
pi-rads-prostate-mri-agent/
├── pi_rads_prostate_mri_agent/    # Core PI-RADS scoring package
│   ├── __init__.py               # Package exports
│   ├── models.py                 # Data models (Pydantic + dataclasses)
│   ├── engine.py                 # PI-RADS scoring engine + ClinicalDomainEngine
│   ├── agents.py                 # Agent coordinator framework
│   ├── cli.py                    # CLI entry point for agent framework
│   └── server.py                 # FastAPI REST server
├── agents/                        # Enterprise agent framework
│   ├── base.py                   # PHI guard, audit trail, security
│   ├── models.py                 # Pydantic schemas
│   ├── workers.py                # Specialized evaluation workers
│   ├── supervisor.py             # Master orchestrator
│   ├── api.py                    # FastAPI endpoints
│   ├── learning.py               # Bayesian calibration engine
│   ├── metrics.py                # Prometheus metrics collector
│   └── streamer.py               # WebSocket telemetry
├── tests/                         # Test suite
│   ├── test_pi_rads.py           # PI-RADS engine tests
│   ├── test_enrichment.py        # Enrichment module tests
│   └── test_pi_rads_prostate_mri_agent.py  # Agent framework tests
├── cli.py                        # Main CLI entry point (PI-RADS scoring)
├── prostate_mri_sentinel.py      # Legacy sentinel agent
├── enrichment.py                 # Feature enrichment engines
├── simulator.py                  # High-throughput simulation
├── web/                          # Operations console (HTML)
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-service orchestration
└── pyproject.toml                # Project metadata and dependencies
```

---

## 📚 PI-RADS v2.1 Scoring Reference

### Score Interpretation
| Score | Clinical Significance |
|:------|:---------------------|
| 1 | Very low - clinically significant cancer is highly unlikely |
| 2 | Low - clinically significant cancer is unlikely |
| 3 | Intermediate - clinically significant cancer is equivocal |
| 4 | High - clinically significant cancer is likely |
| 5 | Very high - clinically significant cancer is highly likely |

### Zone-Based Scoring Rules
- **Peripheral Zone (PZ):** DWI is primary, DCE is secondary
  - DCE positivity upgrades score 3 to 4
- **Transition Zone (TZ):** T2W is primary, DWI is secondary
  - DWI score 4-5 upgrades T2W score 3 to 4
- **Biopsy Recommendation:** PI-RADS >= 3

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
