# Secure EHR Insight: Clinical Validator

Secure EHR Insight is a proof-of-concept clinical retrieval-augmented generation (RAG) system for exploring hospital encounter data. It retrieves only the selected patient's semantically relevant records, removes identifiable information before the context reaches the model, and applies guardrails that refuse requests for new diagnoses, prescriptions, or dosage changes.

> **Important:** This project is for educational and demonstration purposes. It is not a diagnostic, prescribing, or production clinical-decision system. Do not use it to make patient-care decisions.

## Key capabilities

- **Patient-scoped retrieval:** Every chat request includes a selected `patient_id`; the database query filters records to that patient before applying semantic similarity search.
- **Clinical semantic search:** The `NeuML/bioclinical-modernbert-base-embeddings` model generates 768-dimensional embeddings stored and queried with PostgreSQL `pgvector` cosine distance.
- **PII/PHI redaction:** Microsoft Presidio analyzes retrieved context and anonymizes people, phone numbers, email addresses, SSNs, locations, organizations, and dates before context is sent to the LLM.
- **Custom redaction detectors:** The Presidio middleware adds a catch-all U.S. SSN pattern and hospital-name recognition for Massachusetts General Hospital, Mayo Clinic, and Cleveland Clinic.
- **Medical-advice guardrail:** NeMo Guardrails recognizes examples of medication, diagnosis, treatment, and dosage requests and returns a fixed compliance-focused refusal.
- **API and UI:** A FastAPI backend exposes patient and chat endpoints; a Streamlit app provides a searchable patient selector and conversational interface.

## Architecture

```text
Streamlit UI
    |
    v
FastAPI /api/v1/chat
    |
    +--> BioClinical ModernBERT embeds the latest question
    |
    +--> PostgreSQL + pgvector retrieves top 5 records for the selected patient
    |
    +--> Microsoft Presidio redacts PII/PHI in retrieved context
    |
    +--> NeMo Guardrails checks the request and calls Groq-hosted openai/gpt-oss-120b
    |
    v
Safe retrieval response + UI disclaimer
```

The database is queried before any model call. The application creates an augmented prompt from the redacted clinical context and the user's question, then sends that prompt through NeMo Guardrails. The UI also adds a visible warning that generated output is not for diagnostic use.

## Technology stack

| Area | Technology |
| --- | --- |
| Backend API | FastAPI, Uvicorn |
| Web interface | Streamlit |
| Database | PostgreSQL 14+ with pgvector |
| Embeddings | Sentence Transformers, BioClinical ModernBERT |
| Vector similarity | pgvector cosine-distance operator (`<=>`) |
| PII/PHI protection | Microsoft Presidio Analyzer and Anonymizer, spaCy |
| Safety policy | NVIDIA NeMo Guardrails / Colang |
| LLM provider | Groq OpenAI-compatible API using `openai/gpt-oss-120b` |
| Source data | MIMIC-IV-derived encounter transcript CSV included in `data/raw/` |

## Repository layout

```text
.
├── data/raw/MIMIC_IV_Transcript.csv       # Source clinical encounter data
├── scripts/
│   ├── 00_test_groq.py                     # Verifies Groq API connectivity
│   ├── 01_ingest_baseline_data.py          # Creates table and loads CSV data
│   ├── 02_verify_ingestion.py              # Checks row count and sample data
│   ├── 03_apply_vector_schema.py           # Adds vector(768) column
│   ├── 04_generate_embeddings.py           # Builds and persists embeddings
│   ├── 05_test_vector_search.py            # Tests semantic retrieval
│   └── 06_test_guardrails.py               # Tests allowed and blocked prompts
├── src/
│   ├── api/main.py                          # FastAPI application and RAG workflow
│   ├── database/schema.sql                  # patient_encounters table schema
│   ├── guardrails/config.yaml               # Model/provider configuration
│   ├── guardrails/rails.co                  # Medical-advice refusal flow
│   ├── pii_redaction/presidio_service.py    # Presidio redaction middleware
│   └── ui/app.py                            # Streamlit chat UI
├── requirements.txt
└── Steps-To_Execute.md                      # Original infrastructure notes
```

## Prerequisites

Before starting, install:

- Python 3.10 or newer (Python 3.11 is a good default)
- PostgreSQL 14 or newer
- The PostgreSQL `pgvector` extension compatible with the installed PostgreSQL version
- A Groq API key
- Git and a virtual-environment tool such as `venv` or `uv`

The provided dependency list includes the `en_core_web_lg` spaCy model, which Presidio uses for entity detection.

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <YOUR-REPOSITORY-URL>
cd Secure-EHR-Insight-Clinical-Validator

python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

If you use `uv`, the equivalent command is:

```bash
uv pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the repository root. Do not commit it.

```dotenv
# PostgreSQL connection used by ingestion and utility scripts
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ehr_db

# Required by NeMo Guardrails / Groq
GROQ_API_KEY=your_groq_api_key
```

The API also supports a single SQLAlchemy URL through `POSTGRES_URL` as a fallback:

```dotenv
POSTGRES_URL=postgresql+psycopg://your_database_user:your_database_password@localhost:5432/ehr_db
```

For the current API implementation, provide either the individual `DB_*` values or `POSTGRES_URL`. The ingestion and setup scripts use the individual `DB_*` variables.

### 3. Create the database and enable pgvector

Create the database using an administrator account:

```sql
CREATE DATABASE ehr_db;
```

Then connect to it and enable the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Ensure that the database user in `.env` can create tables, alter the application table, read/write rows, and use the `vector` extension. On Ubuntu with PostgreSQL 14, the original project notes use the package `postgresql-14-pgvector`.

### 4. Verify Groq connectivity

```bash
python scripts/00_test_groq.py
```

Expected output:

```text
Groq connection successful
```

### 5. Ingest the source data

This creates `patient_encounters` from `src/database/schema.sql` and appends the CSV data from `data/raw/MIMIC_IV_Transcript.csv`.

```bash
python scripts/01_ingest_baseline_data.py
python scripts/02_verify_ingestion.py
```

The ingestion script uses `append` mode. If it is rerun against the same populated database, it will add duplicate rows. For a clean re-ingestion, use a fresh database or deliberately clear the target table after backing up any data you need.

### 6. Add the vector column and generate embeddings

```bash
python scripts/03_apply_vector_schema.py
python scripts/04_generate_embeddings.py
```

`04_generate_embeddings.py` builds a text representation from encounter fields such as admission type, drug, test name, severity, diagnosis, and notes. It confirms that the embedding model produces 768 dimensions, then writes each vector to `patient_encounters.clinical_embedding`.

Embedding the full dataset can take a significant amount of time and requires adequate disk, RAM, database storage, and network capacity. The script processes records in batches of 10 and skips records that already have an embedding.

### 7. Validate vector search and guardrails

```bash
python scripts/05_test_vector_search.py
python scripts/06_test_guardrails.py
```

The vector-search test prints the top three semantically similar clinical records. The guardrail test sends one permitted historical-retrieval question and one prohibited dosage/prescribing question; the latter should return the configured refusal.

### 8. Optionally test PII redaction by itself

```bash
python src/pii_redaction/presidio_service.py
```

This runs a sample clinical note containing a patient name, SSN, hospital, date, phone number, and email address, then prints its redacted version.

## Run the application

Start the API from the repository root:

```bash
uvicorn src.api.main:app --reload
```

The FastAPI server starts at `http://127.0.0.1:8000`. Interactive endpoint documentation is available at `http://127.0.0.1:8000/docs`.

In another terminal with the same environment activated, start the web interface:

```bash
streamlit run src/ui/app.py
```

Open the URL Streamlit prints (normally `http://localhost:8501`), select an embedded patient ID, and ask a retrieval-focused question.

Examples:

- “What medications were prescribed to this patient upon discharge?”
- “Can you summarize the last few reports of this patient?”
- “What liver-related diagnoses are noted in the patient's file?”
- “Was the patient admitted urgently or routinely?”

Requests such as “Should I increase the patient's dosage?” or “Recommend a drug for fluid retention” are intentionally blocked by the NeMo Guardrails policy.

## API reference

### `GET /api/v1/patients`

Returns patient IDs that have at least one generated embedding. The Streamlit selector uses this endpoint.

### `POST /api/v1/chat`

Runs the production patient-scoped RAG pipeline.

Request body:

```json
{
  "patient_id": "10000032",
  "messages": [
    {
      "role": "user",
      "content": "What medication is listed in this patient's records?"
    }
  ]
}
```

Response shape:

```json
{
  "status": "success",
  "llm_response": "..."
}
```

### `POST /api/v1/clinical-query`

Demonstrates the same redaction-and-guardrails path using a hard-coded example context. It is useful for validating the middleware but does not perform database retrieval.

## Security design and limitations

The application follows a defense-in-depth design, but it is still a prototype and requires additional work before any real-world use.

| Control | What this project does |
| --- | --- |
| Patient isolation | Adds `WHERE subject_id = :subject_id` to each vector retrieval query. |
| Minimum-context retrieval | Retrieves only the top five semantically related records for the selected patient. |
| Context redaction | Uses Presidio to analyze retrieved context, then anonymizes recognized entities before model invocation. |
| Custom detection | Adds custom SSN and named-hospital recognizers to compensate for domain-specific detection gaps. |
| Unsafe-intent handling | Uses NeMo Guardrails examples and a refusal flow for medication, treatment, diagnosis, and dosage advice. |
| User-facing warning | The Streamlit UI appends a non-diagnostic disclaimer to every successful chatbot response. |

Important limitations:

- Presidio is probabilistic. It may miss or incorrectly classify entities; test it against the data and policies relevant to your environment.
- The current guardrail policy is example-driven and narrow. It should be expanded with broader policies, adversarial tests, output checks, audit logs, and human escalation workflows.
- Authentication, authorization, encryption strategy, secrets management, rate limiting, observability, retention controls, and compliance controls are not implemented as production features.
- The UI selects a patient but does not provide real user identity or role-based access control. Patient filtering is not a substitute for healthcare-grade authorization.
- Do not send real protected health information to a third-party model provider unless your legal, privacy, security, and contractual requirements are satisfied.

## Troubleshooting

| Problem | Suggested check |
| --- | --- |
| `vector` type or extension error | Install pgvector for the matching PostgreSQL version and run `CREATE EXTENSION IF NOT EXISTS vector;` as a privileged database user. |
| Database connection failure | Verify `DB_*` values, PostgreSQL service status, firewall/network rules, and user privileges. |
| No patients in the UI | Run the ingestion, vector-schema, and embedding scripts; `/api/v1/patients` returns only patient IDs with non-null embeddings. |
| Embedding dimension mismatch | Ensure both the API and embedding script use `NeuML/bioclinical-modernbert-base-embeddings`, which is expected to return 768 dimensions. |
| Groq authentication/model error | Confirm `GROQ_API_KEY` is set, then run `python scripts/00_test_groq.py`. |
| Presidio/spaCy model error | Reinstall dependencies so the included `en_core_web_lg` package is installed, or install the required spaCy English model explicitly. |
| API cannot load Guardrails config | Start Uvicorn from the project root so `./src/guardrails` resolves correctly. |

## Responsible use

Treat generated answers as retrieval assistance only. Clinicians and authorized reviewers must verify the underlying source record and retain responsibility for every clinical decision. The project intentionally refuses new medical advice because it is designed to summarize and retrieve existing records, not to diagnose or prescribe.

## License

No license file is currently included. Add an appropriate license before distributing or reusing this project publicly.
