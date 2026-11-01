CREATE EXTENSION IF NOT EXISTS vector;

-- 1. PURE TRANSACTIONAL TABLE (No vector here)
CREATE TABLE IF NOT EXISTS patient_encounters (
    id BIGSERIAL PRIMARY KEY,

    subject_id BIGINT NOT NULL,
    hadm_id BIGINT,

    admission_type VARCHAR(50),
    admission_location VARCHAR(100),
    discharge_location VARCHAR(100),

    insurance VARCHAR(50),
    marital_status VARCHAR(50),
    race VARCHAR(100),
    gender VARCHAR(10),
    anchor_age INT,

    drug VARCHAR(150),
    formulary_drug_cd VARCHAR(100),
    prod_strength VARCHAR(150),
    dose_val_rx VARCHAR(100),
    dose_unit_rx VARCHAR(50),
    form_unit_disp VARCHAR(50),
    route VARCHAR(50),

    eventtype VARCHAR(50),
    careunit VARCHAR(100),
    order_type VARCHAR(100),
    order_subtype VARCHAR(100),
    transaction_type VARCHAR(100),

    spec_type_desc VARCHAR(150),
    test_name VARCHAR(150),
    org_name VARCHAR(150),
    ab_name VARCHAR(150),

    comments TEXT,
    drg_type VARCHAR(50),
    description TEXT,
    drg_severity VARCHAR(50),
    drg_mortality VARCHAR(50),

    clinical_embedding VECTOR(768)
);

-- 2. DEDICATED VECTOR TABLE (Linked to Admission or Patient)
CREATE TABLE IF NOT EXISTS patient_clinical_embeddings (
    id BIGSERIAL PRIMARY KEY,
    subject_id BIGINT NOT NULL,
    hadm_id BIGINT, -- Links semantic search to a specific hospital admission context
    
    -- The core text chunk that was embedded (highly recommended for debugging/display)
    embedding_source_text TEXT, 
    
    clinical_embedding VECTOR(768) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. USER ACCESS CONTROL (Unchanged)
CREATE TABLE IF NOT EXISTS ehr_user_patient_access (
    principal_id VARCHAR(255) NOT NULL,
    subject_id BIGINT NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by VARCHAR(255),
    PRIMARY KEY (principal_id, subject_id)
);

-- 4. OPTIMIZED INDEXES
CREATE INDEX IF NOT EXISTS idx_encounters_subject ON patient_encounters(subject_id);
CREATE INDEX IF NOT EXISTS idx_user_patient_access ON ehr_user_patient_access(principal_id, subject_id);

-- HNSW Vector index moves to the dedicated table
CREATE INDEX IF NOT EXISTS idx_clinical_embeddings_hnsw
ON patient_clinical_embeddings
USING hnsw (clinical_embedding vector_cosine_ops);

-- User 1: Limited access
INSERT INTO ehr_user_access (
    principal_id,
    access_level
)
VALUES (
    'COGNITO_SUB_LIMITED_USER',
    'limited'
);

-- User 2: Full access
INSERT INTO ehr_user_access (
    principal_id,
    access_level
)
VALUES (
    'COGNITO_SUB_FULL_ACCESS_USER',
    'all'
);

INSERT INTO ehr_user_patient_access (
    principal_id,
    subject_id,
    granted_by
)
VALUES
(
    'COGNITO_SUB_LIMITED_USER',
    10004235,
    'admin'
);