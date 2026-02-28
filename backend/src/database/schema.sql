-- BancaFiel Loan Processing Database Schema
-- PostgreSQL 15+
-- Created: February 16, 2026

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================
-- CUSTOMERS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    curp VARCHAR(18) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    CONSTRAINT curp_format CHECK (curp ~ '^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]$')
);

CREATE INDEX idx_customers_curp ON customers(curp);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_created_at ON customers(created_at DESC);

-- ==============================================
-- APPLICATIONS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,

    -- Application details
    application_type VARCHAR(20) NOT NULL CHECK (application_type IN ('LOAN', 'CREDIT_CARD')),
    loan_amount DECIMAL(12,2) NOT NULL CHECK (loan_amount > 0),
    monthly_income DECIMAL(12,2),
    existing_debt DECIMAL(12,2) DEFAULT 0,

    -- Timestamps
    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- Status tracking
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'APPROVED', 'REJECTED')),

    -- Fraud detection
    fraud_score DECIMAL(5,2) CHECK (fraud_score >= 0 AND fraud_score <= 1000),
    fraud_risk_level VARCHAR(10) CHECK (fraud_risk_level IN ('LOW', 'MEDIUM', 'HIGH')),

    -- Credit assessment
    credit_score INTEGER CHECK (credit_score >= 300 AND credit_score <= 850),
    credit_recommendation VARCHAR(20) CHECK (credit_recommendation IN ('APPROVE', 'REVIEW', 'REJECT')),

    -- Approval/Rejection
    approved_by VARCHAR(255),
    rejected_by VARCHAR(255),
    rejection_reason TEXT,
    approval_notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_customer ON applications(customer_id);
CREATE INDEX idx_applications_requested_date ON applications(requested_date DESC);
CREATE INDEX idx_applications_fraud_score ON applications(fraud_score);
CREATE INDEX idx_applications_type ON applications(application_type);

-- ==============================================
-- DOCUMENTS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,

    -- Document details
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('INE', 'PROOF_OF_ADDRESS', 'BANK_STATEMENT', 'INCOME_PROOF')),

    -- S3 storage
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,

    -- File metadata
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- Textract
    textract_job_id VARCHAR(255),
    textract_status VARCHAR(20) CHECK (textract_status IN ('PENDING', 'IN_PROGRESS', 'SUCCEEDED', 'FAILED')),

    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    CONSTRAINT unique_s3_location UNIQUE(s3_bucket, s3_key)
);

CREATE INDEX idx_documents_application ON documents(application_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_textract_job ON documents(textract_job_id);

-- ==============================================
-- EXTRACTED DATA TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS extracted_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,

    -- Extracted fields
    field_name VARCHAR(100) NOT NULL,
    field_value TEXT,
    confidence DECIMAL(5,2) CHECK (confidence >= 0 AND confidence <= 100),

    -- Metadata
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_field_per_document UNIQUE(document_id, field_name)
);

CREATE INDEX idx_extracted_data_document ON extracted_data(document_id);
CREATE INDEX idx_extracted_data_field ON extracted_data(field_name);

-- ==============================================
-- APPLICATION HISTORY (Audit Trail)
-- ==============================================
CREATE TABLE IF NOT EXISTS application_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,

    -- Event details
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    notes TEXT,

    -- Additional metadata as JSON
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_history_application ON application_history(application_id);
CREATE INDEX idx_history_created_at ON application_history(created_at DESC);
CREATE INDEX idx_history_action ON application_history(action);

-- GIN index for JSONB metadata queries
CREATE INDEX idx_history_metadata ON application_history USING GIN (metadata);

-- ==============================================
-- FRAUD CHECKS TABLE
-- ==============================================
CREATE TABLE IF NOT EXISTS fraud_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,

    -- Fraud detection results
    fraud_score DECIMAL(5,2) NOT NULL CHECK (fraud_score >= 0 AND fraud_score <= 1000),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),

    -- Fraud reasons as JSON array
    fraud_reasons JSONB,

    -- Additional fraud signals
    duplicate_applications_count INTEGER DEFAULT 0,
    velocity_flags JSONB,

    -- Timestamp
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fraud_checks_application ON fraud_checks(application_id);
CREATE INDEX idx_fraud_checks_risk_level ON fraud_checks(risk_level);
CREATE INDEX idx_fraud_checks_score ON fraud_checks(fraud_score);

-- ==============================================
-- APPROVAL TOKENS TABLE (For Step Functions)
-- ==============================================
CREATE TABLE IF NOT EXISTS approval_tokens (
    application_id UUID PRIMARY KEY REFERENCES applications(id) ON DELETE CASCADE,
    task_token TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

CREATE INDEX idx_approval_tokens_status ON approval_tokens(status);
CREATE INDEX idx_approval_tokens_expires ON approval_tokens(expires_at);

-- ==============================================
-- TRIGGERS FOR UPDATED_AT
-- ==============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for customers table
CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for applications table
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==============================================
-- VIEWS FOR ANALYTICS
-- ==============================================

-- View: Application statistics by day
CREATE OR REPLACE VIEW daily_application_stats AS
SELECT
    DATE(requested_date) as date,
    COUNT(*) as total_applications,
    SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
    AVG(CASE WHEN processed_at IS NOT NULL THEN
        EXTRACT(EPOCH FROM (processed_at - requested_date))/60
        ELSE NULL END) as avg_processing_minutes,
    SUM(CASE WHEN fraud_risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk_count
FROM applications
GROUP BY DATE(requested_date)
ORDER BY date DESC;

-- View: Current pending applications with customer info
CREATE OR REPLACE VIEW pending_applications_view AS
SELECT
    a.id,
    a.application_type,
    a.loan_amount,
    a.requested_date,
    a.fraud_score,
    a.fraud_risk_level,
    a.credit_score,
    c.full_name,
    c.email,
    c.curp,
    c.phone,
    COUNT(d.id) as documents_count
FROM applications a
JOIN customers c ON a.customer_id = c.id
LEFT JOIN documents d ON a.id = d.application_id
WHERE a.status = 'PENDING'
GROUP BY a.id, c.id
ORDER BY a.requested_date ASC;

-- ==============================================
-- INITIAL DATA SEED (Optional)
-- ==============================================

-- Insert sample test customer (for development)
INSERT INTO customers (full_name, curp, email, phone, address, date_of_birth)
VALUES
    ('Test User', 'TEUS850315HDFRST01', 'test@bancafiel.com', '+52 55 1234 5678',
     'Calle Reforma 123, CDMX', '1985-03-15')
ON CONFLICT (curp) DO NOTHING;

-- ==============================================
-- GRANTS AND PERMISSIONS
-- ==============================================

-- Create read-only role for analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_readonly') THEN
        CREATE ROLE analytics_readonly;
    END IF;
END
$$;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
GRANT SELECT ON daily_application_stats TO analytics_readonly;
GRANT SELECT ON pending_applications_view TO analytics_readonly;

-- ==============================================
-- COMMENTS FOR DOCUMENTATION
-- ==============================================

COMMENT ON TABLE customers IS 'Customer master data - Mexican banking customers';
COMMENT ON TABLE applications IS 'Loan and credit card applications with full workflow tracking';
COMMENT ON TABLE documents IS 'Document storage references (S3) and Textract processing status';
COMMENT ON TABLE extracted_data IS 'Data extracted from documents via Amazon Textract';
COMMENT ON TABLE application_history IS 'Complete audit trail of all application state changes';
COMMENT ON TABLE fraud_checks IS 'Fraud detection results from AWS Fraud Detector';
COMMENT ON TABLE approval_tokens IS 'Step Functions task tokens for human approval workflow';

COMMENT ON COLUMN customers.curp IS 'Mexican CURP (Clave Única de Registro de Población)';
COMMENT ON COLUMN applications.fraud_score IS 'Fraud risk score from AWS Fraud Detector (0-1000)';
COMMENT ON COLUMN applications.credit_score IS 'Credit score from bureau (300-850)';

-- ==============================================
-- END OF SCHEMA
-- ==============================================

-- Verify schema creation
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'
ORDER BY table_name;
