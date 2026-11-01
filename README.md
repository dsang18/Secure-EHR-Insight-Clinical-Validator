# Secure EHR Insight: Clinical Validator

A clinical RAG application that retrieves relevant patient records, redacts sensitive information, and uses AI guardrails to prevent unsafe medical advice.

> **Disclaimer:** This is an educational proof of concept, not a diagnostic or clinical decision-making system.

## Features

- **Clinical RAG:** Retrieves the top 5 relevant patient records using semantic similarity.
- **Vector Search:** Uses BioClinical ModernBERT embeddings and PostgreSQL with pgvector.
- **PII/PHI Redaction:** Uses Microsoft Presidio to anonymize sensitive information before LLM processing.
- **AI Guardrails:** Uses NVIDIA NeMo Guardrails to restrict diagnosis, prescription, treatment, and dosage recommendations.
- **LLM Integration:** Uses Groq-hosted `openai/gpt-oss-120b`.
- **REST API:** FastAPI backend for patient retrieval and clinical conversations.
- **User Interface:** Streamlit-based patient selector and conversational interface.

## Architecture

```text
Streamlit UI
     |
     v
 FastAPI Backend
     |
     v
BioClinical ModernBERT
     |
     v
PostgreSQL + pgvector
     |
     v
Presidio PII/PHI Redaction
     |
     v
NeMo Guardrails
     |
     v
Groq LLM
     |
     v
Clinical Response
```

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Database | PostgreSQL, pgvector |
| Embeddings | BioClinical ModernBERT |
| Redaction | Microsoft Presidio |
| Guardrails | NVIDIA NeMo Guardrails |
| LLM | Groq API |
| Language | Python |

## Project Structure

```text
Secure-EHR-Insight-Clinical-Validator/
│
├── scripts/
│   ├── 00_test_groq.py
│   ├── 01_ingest_baseline_data.py
│   ├── 02_verify_ingestion.py
│   ├── 03_apply_vector_schema.py
│   ├── 04_generate_embeddings.py
│   ├── 05_test_vector_search.py
│   └── 06_test_guardrails.py
│
├── src/
│   ├── api/main.py
│   ├── database/schema.sql
│   ├── guardrails/
│   │   ├── config.yaml
│   │   └── rails.co
│   ├── pii_redaction/
│   │   └── presidio_service.py
│   └── ui/app.py
│
├── data/raw/
│   └── MIMIC_IV_Transcript.csv
│
├── requirements.txt
└── README.md
```

## Execution Guide

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+
- PostgreSQL pgvector extension
- Groq API key
- MIMIC-IV-derived clinical transcript CSV

### 2. Clone the Repository

```bash
git clone https://github.com/dsang18/Secure-EHR-Insight-Clinical-Validator.git

cd Secure-EHR-Insight-Clinical-Validator
```

Create and activate a virtual environment:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root using .env.example as reference.

### 4. Configure PostgreSQL

Create the database:

```sql
CREATE DATABASE ehr_db;
```

### 5. Prepare and Ingest Clinical Data

Place the source dataset at:

```text
data/raw/MIMIC_IV_Transcript.csv
```

Test Groq connectivity:

```bash
python scripts/00_test_groq.py
```

Create the database table and ingest the dataset:

```bash
python scripts/01_ingest_baseline_data.py
```

Verify ingestion:

```bash
python scripts/02_verify_ingestion.py
```

### 6. Generate Clinical Embeddings

Add the 768-dimensional vector column:

```bash
python scripts/03_apply_vector_schema.py
```

Generate and store embeddings:

```bash
python scripts/04_generate_embeddings.py
```

The embedding script processes records in batches and skips records that already have embeddings.

### 7. Validate the Pipeline

Test semantic vector retrieval:

```bash
python scripts/05_test_vector_search.py
```

Test AI guardrails:

```bash
python scripts/06_test_guardrails.py
```

Optionally test PII redaction independently:

```bash
python src/pii_redaction/presidio_service.py
```


### 8. Generate a JWT Token for the User

Copy and save this JWT token somewhere that will be used on the streamlit tool as access token.
```bash
python scripts/07_generate_token.py
```

### 9. Start the Application

Start the FastAPI backend:

```bash
uvicorn src.api.main:app --reload
```

API documentation:

```text
http://localhost:8000/docs
```

Open another terminal and start the Streamlit frontend:

```bash
streamlit run src/ui/app.py
```

Open:

```text
http://localhost:8501
```

Select a patient and start asking questions about their historical clinical records.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/patients` | Retrieves patients with generated embeddings |
| POST | `/api/v1/chat` | Executes the patient-scoped clinical RAG pipeline |
| POST | `/api/v1/clinical-query` | Demonstrates the redaction and guardrails workflow using mock data |

## Security Considerations

The project implements multiple layers of protection:

- Patient-scoped database retrieval.
- PII/PHI redaction before LLM invocation.
- Guardrails against unsafe medical recommendations.
- A clinical disclaimer in the user interface.

**Current limitations:** Authentication, integrated patient-level authorization, encryption controls, audit logging, and production compliance controls are not yet implemented. The current patient selector is not an authorization mechanism.

Do not use real patient data or deploy this application in a clinical environment without appropriate security, privacy, compliance, and clinical validation.

## License

No license has been added to this repository yet.