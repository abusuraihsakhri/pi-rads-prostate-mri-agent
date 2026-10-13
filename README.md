# PI-RADS Prostate MRI Agent

A deterministic implementation of **PI-RADS v2.1 category combination rules** for prostate multiparametric MRI. It accepts sequence scores assigned by a reader; it does **not** analyze MRI pixels, classify images, detect lesions, diagnose cancer, or determine treatment.

The repository includes a browser calculator, Python scoring API and CLI, and separate legacy agent/audit demonstration components.

## Browser calculator

Open [the local browser interface](web/index.html) to assess peripheral-zone or transition-zone lesions, add multiple lesions and export an assessment as JSON. It uses standard browser JavaScript, with **no backend, login, tracking, or external services required**. No information is saved between page sessions; exported JSON stays on the user's device. Avoid entering any identifiable patient information.

A GitHub Pages deployment workflow is included; the public URL should only be used once deployment and live functionality are verified.

## Scoring methodology

| Zone | Primary sequence | v2.1 combination rule |
| --- | --- | --- |
| Peripheral (PZ) | DWI | DWI 3 + positive DCE → PI-RADS 4; otherwise PI-RADS equals DWI score |
| Transition (TZ) | T2W | T2W 2 + DWI 4–5 → PI-RADS 3; T2W 3 + DWI 5 → PI-RADS 4; otherwise T2W determines category |

Central-zone and anterior fibromuscular stromal findings are **not automatically scored using TZ rules**. Sequence-level scores must already reflect appropriate morphology, lesion size and extension findings; a number-only input cannot verify those properties.

PI-RADS categories describe MRI likelihood, not a management algorithm. **PI-RADS 3 is not an automatic biopsy indication**; biopsy decisions for all categories require clinical context and local guidelines. The legacy API field named `biopsy_recommended` is retained for compatibility and becomes true only for PI-RADS 4–5; it denotes *consideration*, not a clinical directive.

Primary standard: [American College of Radiology, PI-RADS v2.1](https://www.acr.org/Clinical-Resources/Reporting-and-Data-Systems/PI-RADS).

## Installation

Requires Python 3.10 or later.

~~~bash
git clone https://github.com/abusuraihsakhri/pi-rads-prostate-mri-agent.git
cd pi-rads-prostate-mri-agent
python -m pip install -e ".[server,test]"
python -m pytest -q
~~~

No cloud API keys are required for the deterministic scoring engine.

## Python CLI

~~~bash
pi-rads-score score --zone peripheral --t2w 3 --dwi 3 --dce-positive --json
pi-rads-score score --zone transition --t2w 2 --dwi 4 --json
pi-rads-score assess -l peripheral:3:3:dce:12 -l transition:2:4:0:8 --json
pi-rads-score info
~~~

The repository-root `python cli.py` provides the same score/assess/info interface. A separate compatibility command, `pi-rads-prostate-mri-engine`, provides deterministic `audit`, `batch`, `chat`, and `serve` agent utilities, **not** lesion scoring. The audit metrics are demonstration thresholds and must not be interpreted as validated medical criteria.

## REST API

~~~bash
uvicorn pi_rads_prostate_mri_agent.server:create_app --factory --host 127.0.0.1 --port 8000
~~~

Available routes: `GET /health`, `POST /api/score`, `POST /api/assess`; the legacy deterministic `POST /api/audit` and `POST /api/chat` are retained.

Example:

~~~bash
curl -s http://127.0.0.1:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{"zone":"transition","t2w_score":2,"dwi_score":4}'
~~~

Swagger/OpenAPI documentation is at `/docs`. The application can also be built with the included Dockerfile; `docker compose up --build` starts the same scoring API.

Do **not** submit real patient data to an untrusted or publicly exposed server. The API and agent utilities do not provide an independently validated HIPAA-compliant patient-data service.

## Additional components and limitations

- `pi_rads_prostate_mri_agent/` — Python category-combination engine, FastAPI service, and deterministic audit coordinator
- `agents/` — separate demonstration workers, regex identifier guard, HMAC audit log, and mock-only language interface
- `prostate_mri_sentinel.py` and `enrichment.py` — retained legacy demonstration utilities; these are not image interpretation systems
- `web/` — static HTML/JavaScript calculator with unit tests
- `tests/` — scoring, validation, CLI, API, audit, and legacy tests

The identifier guard recognizes selected patterns but **cannot guarantee de-identification**. The HMAC audit trail is held in process memory; without a stable `AUDIT_SECRET_KEY`, a fresh random signing key is generated each run. It does not provide persistent, independently verifiable archival records. The mock language adapter performs no model inference or clinical validation.

## Testing

~~~bash
python -m pytest -q
python -m compileall -q agents pi_rads_prostate_mri_agent
node --check web/app.js
node --test web/app.test.cjs
~~~

The browser implementation uses ordinary JavaScript rather than Pyodide, because the combination rules need no Python runtime or native libraries. The web page is designed for modern browsers; clinical or regulatory validation has **not** been performed.

## License

[MIT](LICENSE).
