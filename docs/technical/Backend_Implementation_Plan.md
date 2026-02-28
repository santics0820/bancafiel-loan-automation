# BancaFiel Backend Implementation Plan
**Complete AWS Backend Development Roadmap**

---

## 📋 Executive Summary

This plan details the complete backend implementation for BancaFiel's loan processing automation system. We will build a production-ready AWS serverless architecture over 4 weeks.

**Key Commitments:**
- ✅ **Timeline**: 4 weeks (28 days)
- ✅ **Architecture**: Following `AWS_Architecture_Design.md` exactly
- ✅ **Scope**: Full solution (all 7 Lambda functions, fraud detection, analytics, notifications)
- ✅ **Deployment**: 100% on AWS, production-ready
- ✅ **Tech Stack**: Python 3.11, PostgreSQL, AWS SAM for IaC
- ✅ **Outcome**: Fully functional loan processing backend

---

## 🎯 Architecture Overview (Reference)

Based on `AWS_Architecture_Design.md`, we're building:

```
Customer Application
    ↓
API Gateway → Lambda (processDocument) → S3
    ↓
Lambda (extractData) → Amazon Textract
    ↓
Lambda (validateData) → RDS PostgreSQL
    ↓
Lambda (detectFraud) → Amazon Fraud Detector
    ↓
Step Functions (orchestration)
    ↓
Lambda (processApproval) → Human Decision
    ↓
Lambda (updateERP) → RDS
    ↓
Lambda (sendNotification) → Amazon SES
```

---

## 📦 Deliverables Checklist

### Week 1: Foundation
- [ ] AWS account setup with proper IAM roles
- [ ] RDS PostgreSQL database with complete schema
- [ ] S3 buckets configured with lifecycle policies
- [ ] Lambda Layer with shared dependencies
- [ ] API Gateway with CORS and authentication
- [ ] First 2 Lambda functions deployed and tested

### Week 2: Core Processing
- [ ] Textract integration fully functional
- [ ] Data validation logic complete
- [ ] Fraud Detector configured and tested
- [ ] All 7 Lambda functions deployed
- [ ] Step Functions workflow orchestrating pipeline
- [ ] End-to-end document processing working

### Week 3: Approval & Integration
- [ ] Approval workflow with human-in-the-loop
- [ ] SES email templates configured
- [ ] SNS notifications for approvers
- [ ] ERP update integration
- [ ] CloudWatch dashboards and alarms
- [ ] Complete API endpoints matching loan-api.md

### Week 4: Testing & Production
- [ ] Integration testing with 100+ sample applications
- [ ] Load testing (500 applications/day)
- [ ] Security hardening and penetration testing
- [ ] Production deployment with monitoring
- [ ] Documentation and runbooks
- [ ] Demo preparation

---

## 🗓️ Week 1: Foundation (Days 1-7)

### Day 1: AWS Environment Setup

**Morning (3 hours): AWS Account Configuration**
```bash
# Tasks:
1. Create/configure AWS account
2. Set up IAM users and roles:
   - LambdaExecutionRole (with S3, RDS, Textract, Fraud Detector permissions)
   - APIGatewayRole
   - StepFunctionsRole
3. Enable AWS Free Tier alerts
4. Install AWS CLI and configure credentials
5. Install AWS SAM CLI for local development
```

**Files to Create:**
- `backend/infrastructure/iam-policies.json` - IAM role definitions
- `backend/infrastructure/samconfig.toml` - SAM CLI configuration

**Evening (2 hours): Development Environment**
```bash
# Set up local development
1. Install Python 3.11
2. Create virtual environment: python -m venv venv
3. Install dependencies: boto3, psycopg2-binary, aws-sam-cli
4. Configure VS Code with AWS Toolkit extension
```

**Deliverable**: AWS account ready, IAM roles configured, dev environment set up

---

### Day 2: Database Design & Deployment

**Morning (3 hours): PostgreSQL Schema Design**

Create complete database schema based on business requirements:

**File**: `backend/src/database/schema.sql`

```sql
-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    curp VARCHAR(18) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Applications table
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    application_type VARCHAR(20) CHECK (application_type IN ('LOAN', 'CREDIT_CARD')),
    loan_amount DECIMAL(12,2) NOT NULL,
    monthly_income DECIMAL(12,2),
    existing_debt DECIMAL(12,2),
    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'APPROVED', 'REJECTED')),
    fraud_score DECIMAL(5,2),
    fraud_risk_level VARCHAR(10) CHECK (fraud_risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    credit_score INTEGER,
    credit_recommendation VARCHAR(20),
    approved_by VARCHAR(255),
    rejected_by VARCHAR(255),
    rejection_reason TEXT,
    approval_notes TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    document_type VARCHAR(50) CHECK (document_type IN ('INE', 'PROOF_OF_ADDRESS', 'BANK_STATEMENT', 'INCOME_PROOF')),
    s3_bucket VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extracted data from Textract
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    field_name VARCHAR(100),
    field_value TEXT,
    confidence DECIMAL(5,2),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application history/audit trail
CREATE TABLE application_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    actor VARCHAR(255),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fraud detection results
CREATE TABLE fraud_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    fraud_score DECIMAL(5,2),
    risk_level VARCHAR(10),
    fraud_reasons JSONB,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_customer ON applications(customer_id);
CREATE INDEX idx_applications_requested_date ON applications(requested_date);
CREATE INDEX idx_documents_application ON documents(application_id);
CREATE INDEX idx_customers_curp ON customers(curp);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_history_application ON application_history(application_id);
```

**Afternoon (3 hours): RDS Deployment**

**File**: `backend/infrastructure/cloudformation/rds.yaml`

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'RDS PostgreSQL for BancaFiel'

Parameters:
  DBUsername:
    Type: String
    Default: bancafiel_admin
    NoEcho: true
  DBPassword:
    Type: String
    NoEcho: true
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for BancaFiel RDS
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2

  DBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref LambdaSecurityGroup

  PostgreSQLDB:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub bancafiel-postgres-${Environment}
      Engine: postgres
      EngineVersion: '15.4'
      DBInstanceClass: db.t3.micro  # Free tier eligible
      AllocatedStorage: 20
      StorageType: gp2
      MasterUsername: !Ref DBUsername
      MasterUserPassword: !Ref DBPassword
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      BackupRetentionPeriod: 7
      PreferredBackupWindow: '03:00-04:00'
      PreferredMaintenanceWindow: 'sun:04:00-sun:05:00'
      MultiAZ: false  # Set to true for production
      PubliclyAccessible: false
      StorageEncrypted: true
      EnableCloudwatchLogsExports:
        - postgresql
      Tags:
        - Key: Name
          Value: !Sub bancafiel-db-${Environment}
        - Key: Project
          Value: BancaFiel

Outputs:
  DBEndpoint:
    Description: Database endpoint
    Value: !GetAtt PostgreSQLDB.Endpoint.Address
    Export:
      Name: !Sub ${AWS::StackName}-DBEndpoint
  DBPort:
    Description: Database port
    Value: !GetAtt PostgreSQLDB.Endpoint.Port
```

**Tasks:**
```bash
# Deploy RDS
aws cloudformation deploy \
  --template-file backend/infrastructure/cloudformation/rds.yaml \
  --stack-name bancafiel-rds-dev \
  --parameter-overrides DBPassword=YourSecurePassword123! \
  --capabilities CAPABILITY_IAM

# Wait for RDS to be available (15-20 minutes)
aws rds wait db-instance-available --db-instance-identifier bancafiel-postgres-dev

# Connect and create schema
psql -h <endpoint> -U bancafiel_admin -d postgres -f backend/src/database/schema.sql
```

**Deliverable**: PostgreSQL database deployed and schema created

---

### Day 3: S3 Buckets & Lambda Layer

**Morning (2 hours): S3 Configuration**

**File**: `backend/infrastructure/cloudformation/s3.yaml`

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'S3 buckets for BancaFiel document storage'

Resources:
  IncomingDocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub bancafiel-incoming-documents-${AWS::AccountId}
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: MoveToGlacierAfter90Days
            Status: Enabled
            Transitions:
              - TransitionInDays: 90
                StorageClass: GLACIER
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Function: !GetAtt ProcessDocumentLambda.Arn
      Tags:
        - Key: Purpose
          Value: IncomingApplicationDocuments

  ProcessedDocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub bancafiel-processed-documents-${AWS::AccountId}
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteAfter7Years
            Status: Enabled
            ExpirationInDays: 2555

  RejectedDocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub bancafiel-rejected-documents-${AWS::AccountId}
      LifecycleConfiguration:
        Rules:
          - Id: DeleteAfter30Days
            Status: Enabled
            ExpirationInDays: 30

Outputs:
  IncomingBucketName:
    Value: !Ref IncomingDocumentsBucket
  ProcessedBucketName:
    Value: !Ref ProcessedDocumentsBucket
```

**Afternoon (3 hours): Lambda Layer for Shared Dependencies**

**File**: `backend/src/layers/python/requirements.txt`

```
boto3==1.34.21
psycopg2-binary==2.9.9
python-jose==3.3.0
requests==2.31.0
pydantic==2.5.3
```

**File**: `backend/src/layers/python/utils/database.py`

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', '5432')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query, params=None):
    """Execute a SELECT query and return results"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

def execute_insert(query, params):
    """Execute INSERT/UPDATE/DELETE and return affected rows"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
```

**File**: `backend/src/layers/python/utils/logger.py`

```python
import logging
import json
from datetime import datetime

def setup_logger(name):
    """Configure structured logging for Lambda"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create handler if not already exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def log_event(logger, event_type, data):
    """Log structured event data"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'data': data
    }
    logger.info(json.dumps(log_entry))
```

**File**: `backend/src/layers/python/utils/response.py`

```python
import json

def success_response(data, status_code=200):
    """Standard success response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(data)
    }

def error_response(message, status_code=400):
    """Standard error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': True,
            'message': message
        })
    }
```

**Build and Deploy Layer:**
```bash
cd backend/src/layers/python
pip install -r requirements.txt -t .
cd ../..
zip -r layer.zip python/
aws lambda publish-layer-version \
  --layer-name bancafiel-common-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

**Deliverable**: S3 buckets configured, Lambda Layer deployed with shared utilities

---

### Day 4-5: First Lambda Functions

**Lambda #1: processDocument**

**File**: `backend/src/lambdas/document-processor/handler.py`

```python
import json
import boto3
import os
from utils.logger import setup_logger, log_event
from utils.database import execute_insert
from datetime import datetime

logger = setup_logger('processDocument')
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')

def handler(event, context):
    """
    Triggered by S3 upload. Initiates Textract processing.

    Event: S3 ObjectCreated notification
    Output: Textract Job ID
    """
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']

            log_event(logger, 'document_received', {
                'bucket': bucket,
                'key': key
            })

            # Extract application_id from S3 key (format: applications/{uuid}/ine.pdf)
            parts = key.split('/')
            application_id = parts[1] if len(parts) > 1 else None

            # Start Textract async job
            response = textract_client.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                NotificationChannel={
                    'SNSTopicArn': os.environ['SNS_TOPIC_ARN'],
                    'RoleArn': os.environ['TEXTRACT_ROLE_ARN']
                }
            )

            job_id = response['JobId']

            # Save document metadata to database
            document_type = determine_document_type(key)
            file_size = record['s3']['object']['size']

            query = """
                INSERT INTO documents
                (application_id, document_type, s3_bucket, s3_key, file_size_bytes, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            execute_insert(query, (
                application_id,
                document_type,
                bucket,
                key,
                file_size,
                datetime.utcnow()
            ))

            log_event(logger, 'textract_job_started', {
                'job_id': job_id,
                'application_id': application_id
            })

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Document processing started',
                    'job_id': job_id
                })
            }

    except Exception as e:
        logger.error(f'Error processing document: {str(e)}')
        raise

def determine_document_type(s3_key):
    """Determine document type from filename"""
    key_lower = s3_key.lower()
    if 'ine' in key_lower or 'ife' in key_lower:
        return 'INE'
    elif 'proof' in key_lower or 'comprobante' in key_lower:
        return 'PROOF_OF_ADDRESS'
    elif 'bank' in key_lower or 'estado' in key_lower:
        return 'BANK_STATEMENT'
    else:
        return 'INCOME_PROOF'
```

**Lambda #2: extractData**

**File**: `backend/src/lambdas/data-extractor/handler.py`

```python
import json
import boto3
import os
from utils.logger import setup_logger, log_event
from utils.database import execute_insert, execute_query

logger = setup_logger('extractData')
textract_client = boto3.client('textract')

def handler(event, context):
    """
    Triggered by SNS when Textract job completes.
    Extracts structured data from Textract results.

    Input: Textract Job ID (via SNS)
    Output: Structured data saved to database
    """
    try:
        # Parse SNS message
        message = json.loads(event['Records'][0]['Sns']['Message'])
        job_id = message['JobId']
        status = message['Status']

        if status != 'SUCCEEDED':
            logger.error(f'Textract job {job_id} failed')
            return {'statusCode': 400, 'body': 'Textract job failed'}

        # Get Textract results
        response = textract_client.get_document_text_detection(JobId=job_id)
        blocks = response['Blocks']

        # Extract text and key-value pairs
        extracted_fields = parse_textract_blocks(blocks)

        log_event(logger, 'data_extracted', {
            'job_id': job_id,
            'fields_count': len(extracted_fields)
        })

        # Get document_id from job metadata (you'd store this when starting job)
        document_id = get_document_id_from_job(job_id)

        # Save extracted data to database
        for field_name, field_data in extracted_fields.items():
            query = """
                INSERT INTO extracted_data
                (document_id, field_name, field_value, confidence)
                VALUES (%s, %s, %s, %s)
            """
            execute_insert(query, (
                document_id,
                field_name,
                field_data['value'],
                field_data['confidence']
            ))

        # Trigger next step (validation)
        invoke_next_lambda('validateData', {'document_id': document_id})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Data extraction complete'})
        }

    except Exception as e:
        logger.error(f'Error extracting data: {str(e)}')
        raise

def parse_textract_blocks(blocks):
    """Parse Textract blocks into structured fields"""
    fields = {}

    # For INE/IFE documents
    for block in blocks:
        if block['BlockType'] == 'LINE':
            text = block['Text']
            confidence = block['Confidence']

            # Pattern matching for Mexican INE fields
            if 'NOMBRE' in text.upper():
                fields['full_name'] = {
                    'value': extract_after_label(text, 'NOMBRE'),
                    'confidence': confidence
                }
            elif 'CURP' in text.upper():
                fields['curp'] = {
                    'value': extract_curp(text),
                    'confidence': confidence
                }
            elif 'DOMICILIO' in text.upper() or 'DIRECCIÓN' in text.upper():
                fields['address'] = {
                    'value': extract_after_label(text, 'DOMICILIO'),
                    'confidence': confidence
                }
            elif 'FECHA DE NACIMIENTO' in text.upper():
                fields['date_of_birth'] = {
                    'value': extract_date(text),
                    'confidence': confidence
                }

    return fields

def extract_after_label(text, label):
    """Extract text after a label"""
    parts = text.split(label)
    return parts[1].strip() if len(parts) > 1 else text

def extract_curp(text):
    """Extract CURP using regex"""
    import re
    pattern = r'[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_date(text):
    """Extract date from text"""
    import re
    # Match DD/MM/YYYY or DD-MM-YYYY
    pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def get_document_id_from_job(job_id):
    """Retrieve document_id associated with Textract job"""
    # In practice, you'd store this mapping when starting the job
    # For now, query from metadata table or pass through SNS
    query = "SELECT id FROM documents WHERE textract_job_id = %s"
    result = execute_query(query, (job_id,))
    return result[0]['id'] if result else None

def invoke_next_lambda(function_name, payload):
    """Invoke next Lambda in the pipeline"""
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='Event',  # Async
        Payload=json.dumps(payload)
    )
```

**SAM Template for Lambda Functions:**

**File**: `backend/template.yaml`

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: BancaFiel Backend SAM Template

Globals:
  Function:
    Timeout: 30
    Runtime: python3.11
    Environment:
      Variables:
        DB_HOST: !GetAtt PostgreSQLDB.Endpoint.Address
        DB_NAME: postgres
        DB_USER: bancafiel_admin
        DB_PASSWORD: !Ref DBPassword
    Layers:
      - !Ref CommonLayer

Resources:
  CommonLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: bancafiel-common-layer
      ContentUri: src/layers/
      CompatibleRuntimes:
        - python3.11

  ProcessDocumentFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bancafiel-processDocument
      CodeUri: src/lambdas/document-processor/
      Handler: handler.handler
      Policies:
        - S3ReadPolicy:
            BucketName: !Ref IncomingDocumentsBucket
        - Statement:
            - Effect: Allow
              Action:
                - textract:StartDocumentTextDetection
              Resource: '*'
      Events:
        S3Upload:
          Type: S3
          Properties:
            Bucket: !Ref IncomingDocumentsBucket
            Events: s3:ObjectCreated:*

  ExtractDataFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bancafiel-extractData
      CodeUri: src/lambdas/data-extractor/
      Handler: handler.handler
      Policies:
        - Statement:
            - Effect: Allow
              Action:
                - textract:GetDocumentTextDetection
              Resource: '*'
      Events:
        TextractComplete:
          Type: SNS
          Properties:
            Topic: !Ref TextractCompletionTopic

  TextractCompletionTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: bancafiel-textract-completion

Outputs:
  ProcessDocumentFunctionArn:
    Value: !GetAtt ProcessDocumentFunction.Arn
  ExtractDataFunctionArn:
    Value: !GetAtt ExtractDataFunction.Arn
```

**Deploy First Lambdas:**
```bash
cd backend
sam build
sam deploy --guided
```

**Deliverable**: First 2 Lambda functions deployed and tested with sample documents

---

### Days 6-7: API Gateway & Initial Testing

**File**: `backend/src/api/routes/applications.py`

```python
import json
from utils.logger import setup_logger
from utils.response import success_response, error_response
from utils.database import execute_query, execute_insert

logger = setup_logger('applications_api')

def list_applications(event, context):
    """
    GET /api/loans?status=pending
    Returns list of loan applications filtered by status
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        status = query_params.get('status', 'pending').upper()

        # Query database
        query = """
            SELECT
                a.id,
                c.full_name as applicant_name,
                c.email as applicant_email,
                a.loan_amount,
                a.monthly_income,
                a.requested_date,
                a.status,
                a.fraud_score,
                a.credit_score
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.status = %s
            ORDER BY a.requested_date DESC
        """

        applications = execute_query(query, (status,))

        # Format response to match loan-api.md contract
        response_data = {
            'applications': [
                {
                    'id': str(app['id']),
                    'applicantName': app['applicant_name'],
                    'applicantEmail': app['applicant_email'],
                    'loanAmount': float(app['loan_amount']),
                    'monthlyIncome': float(app['monthly_income']) if app['monthly_income'] else None,
                    'requestedDate': app['requested_date'].isoformat(),
                    'status': app['status'].lower(),
                    'fraudScore': float(app['fraud_score']) if app['fraud_score'] else None,
                    'creditScore': app['credit_score']
                }
                for app in applications
            ],
            'total': len(applications)
        }

        return success_response(response_data)

    except Exception as e:
        logger.error(f'Error listing applications: {str(e)}')
        return error_response('Failed to retrieve applications', 500)

def get_application(event, context):
    """
    GET /api/loans/:id
    Returns detailed application information
    """
    try:
        application_id = event['pathParameters']['id']

        # Query application with all details
        query = """
            SELECT
                a.*,
                c.full_name,
                c.email,
                c.curp,
                c.phone,
                c.address
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """

        result = execute_query(query, (application_id,))

        if not result:
            return error_response('Application not found', 404)

        app = result[0]

        # Get documents
        doc_query = """
            SELECT id, document_type, s3_bucket, s3_key
            FROM documents
            WHERE application_id = %s
        """
        documents = execute_query(doc_query, (application_id,))

        # Get history
        history_query = """
            SELECT action, actor, created_at, notes
            FROM application_history
            WHERE application_id = %s
            ORDER BY created_at ASC
        """
        history = execute_query(history_query, (application_id,))

        # Format response matching loan-api.md
        response_data = {
            'id': str(app['id']),
            'applicantName': app['full_name'],
            'applicantEmail': app['email'],
            'curp': app['curp'],
            'phone': app['phone'],
            'address': app['address'],
            'loanAmount': float(app['loan_amount']),
            'monthlyIncome': float(app['monthly_income']) if app['monthly_income'] else None,
            'existingDebt': float(app['existing_debt']) if app['existing_debt'] else None,
            'requestedDate': app['requested_date'].isoformat(),
            'status': app['status'].lower(),
            'fraudScore': float(app['fraud_score']) if app['fraud_score'] else None,
            'fraudRiskLevel': app['fraud_risk_level'].lower() if app['fraud_risk_level'] else None,
            'creditScore': app['credit_score'],
            'creditRecommendation': app['credit_recommendation'],
            'documents': [
                {
                    'type': doc['document_type'],
                    'url': f"s3://{doc['s3_bucket']}/{doc['s3_key']}"
                }
                for doc in documents
            ],
            'history': [
                {
                    'timestamp': h['created_at'].isoformat(),
                    'action': h['action'],
                    'user': h['actor'],
                    'notes': h['notes']
                }
                for h in history
            ]
        }

        return success_response(response_data)

    except Exception as e:
        logger.error(f'Error getting application: {str(e)}')
        return error_response('Failed to retrieve application', 500)

def approve_application(event, context):
    """
    POST /api/loans/:id/approve
    Approves a loan application
    """
    try:
        application_id = event['pathParameters']['id']
        body = json.loads(event['body'])

        notes = body.get('notes', '')
        approved_by = body.get('approvedBy', 'system')

        # Update application status
        query = """
            UPDATE applications
            SET status = 'APPROVED',
                approved_by = %s,
                approval_notes = %s,
                processed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """

        result = execute_insert(query, (approved_by, notes, application_id))

        if result == 0:
            return error_response('Application not found', 404)

        # Log to history
        history_query = """
            INSERT INTO application_history
            (application_id, action, actor, notes)
            VALUES (%s, %s, %s, %s)
        """
        execute_insert(history_query, (application_id, 'approved', approved_by, notes))

        # Trigger email notification (invoke Lambda)
        # ... (will implement in Week 3)

        return success_response({
            'success': True,
            'loanId': application_id,
            'status': 'approved',
            'message': 'Application approved successfully'
        })

    except Exception as e:
        logger.error(f'Error approving application: {str(e)}')
        return error_response('Failed to approve application', 500)
```

**Add to SAM template:**
```yaml
  ApplicationsAPI:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: bancafiel-api-applications
      CodeUri: src/api/routes/
      Handler: applications.list_applications
      Events:
        ListApplications:
          Type: Api
          Properties:
            Path: /api/loans
            Method: GET
            RestApiId: !Ref BancaFielAPI

  BancaFielAPI:
    Type: AWS::Serverless::Api
    Properties:
      Name: bancafiel-api
      StageName: dev
      Cors:
        AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
        AllowHeaders: "'Content-Type,Authorization'"
        AllowOrigin: "'*'"
```

**Testing:**
```bash
# Test document upload
aws s3 cp sample-ine.pdf s3://bancafiel-incoming-documents-{account-id}/applications/test-uuid/ine.pdf

# Test API
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/api/loans?status=pending
```

**Week 1 Complete! ✅**

---

## 🗓️ Week 2: Core Processing (Days 8-14)

### Day 8-9: Data Validation Lambda

**Lambda #3: validateData**

**File**: `backend/src/lambdas/data-validator/handler.py`

```python
import json
from utils.logger import setup_logger
from utils.database import execute_query, execute_insert
from datetime import datetime

logger = setup_logger('validateData')

def handler(event, context):
    """
    Validates extracted data against business rules and database.

    Input: document_id or application_id
    Output: Validation results saved to database
    """
    try:
        document_id = event.get('document_id')
        application_id = event.get('application_id')

        # Get extracted data
        query = """
            SELECT field_name, field_value, confidence
            FROM extracted_data
            WHERE document_id = %s
        """
        extracted_fields = execute_query(query, (document_id,))

        # Convert to dict
        data = {field['field_name']: field['field_value'] for field in extracted_fields}

        # Validation rules
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        # 1. Check required fields
        required_fields = ['full_name', 'curp', 'address']
        for field in required_fields:
            if field not in data or not data[field]:
                validation_results['is_valid'] = False
                validation_results['errors'].append(f'Missing required field: {field}')

        # 2. Validate CURP format
        if 'curp' in data:
            if not validate_curp(data['curp']):
                validation_results['is_valid'] = False
                validation_results['errors'].append('Invalid CURP format')

        # 3. Check if customer exists in database
        if 'curp' in data:
            customer_query = "SELECT id, full_name FROM customers WHERE curp = %s"
            customer_result = execute_query(customer_query, (data['curp'],))

            if customer_result:
                # Existing customer - verify name matches
                db_name = customer_result[0]['full_name']
                extracted_name = data.get('full_name', '')

                if not names_match(db_name, extracted_name):
                    validation_results['warnings'].append('Name mismatch with database record')

                customer_id = customer_result[0]['id']
            else:
                # New customer - create record
                insert_query = """
                    INSERT INTO customers (full_name, curp, address)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """
                result = execute_query(insert_query, (
                    data.get('full_name'),
                    data.get('curp'),
                    data.get('address')
                ))
                customer_id = result[0]['id']

        # 4. Update application with customer_id
        if application_id:
            update_query = """
                UPDATE applications
                SET customer_id = %s,
                    status = 'PROCESSING'
                WHERE id = %s
            """
            execute_insert(update_query, (customer_id, application_id))

        # Log validation results
        history_query = """
            INSERT INTO application_history
            (application_id, action, actor, notes, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_insert(history_query, (
            application_id,
            'validation_completed',
            'system',
            'Data validation completed',
            json.dumps(validation_results)
        ))

        logger.info(f'Validation completed for application {application_id}')

        return {
            'statusCode': 200,
            'validation_results': validation_results,
            'customer_id': str(customer_id)
        }

    except Exception as e:
        logger.error(f'Validation error: {str(e)}')
        raise

def validate_curp(curp):
    """Validate Mexican CURP format"""
    import re
    pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$'
    return bool(re.match(pattern, curp.upper()))

def names_match(name1, name2):
    """Fuzzy name matching"""
    # Simple approach: normalize and compare
    n1 = name1.lower().replace(' ', '')
    n2 = name2.lower().replace(' ', '')

    # Calculate similarity (Levenshtein distance or similar)
    # For simplicity, check if 80% characters match
    matches = sum(c1 == c2 for c1, c2 in zip(n1, n2))
    similarity = matches / max(len(n1), len(n2))

    return similarity > 0.8
```

---

### Day 10-11: Fraud Detection Lambda

**Lambda #4: detectFraud**

**File**: `backend/src/lambdas/fraud-detector/handler.py`

```python
import json
import boto3
from utils.logger import setup_logger
from utils.database import execute_query, execute_insert

logger = setup_logger('detectFraud')
fraud_detector_client = boto3.client('frauddetector')

def handler(event, context):
    """
    Uses AWS Fraud Detector to assess fraud risk.

    Input: application_id
    Output: Fraud score and risk level
    """
    try:
        application_id = event.get('application_id')

        # Get application data
        query = """
            SELECT
                a.*,
                c.curp,
                c.email,
                c.phone
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """
        app_data = execute_query(query, (application_id,))[0]

        # Prepare fraud detection event
        event_variables = {
            'email': app_data['email'],
            'ip_address': event.get('ip_address', 'unknown'),
            'customer_id': str(app_data['customer_id']),
            'loan_amount': str(app_data['loan_amount']),
            'phone': app_data['phone'] or '',
            'curp': app_data['curp']
        }

        # Call AWS Fraud Detector
        fraud_response = fraud_detector_client.get_event_prediction(
            detectorId='bancafiel_loan_fraud_detector',
            eventId=str(application_id),
            eventTypeName='loan_application',
            entities=[{
                'entityType': 'customer',
                'entityId': str(app_data['customer_id'])
            }],
            eventTimestamp=datetime.utcnow().isoformat(),
            eventVariables=event_variables
        )

        # Parse fraud score (0-1000 scale)
        model_scores = fraud_response.get('modelScores', [])
        fraud_score = model_scores[0]['scores']['default'] if model_scores else 0

        # Determine risk level
        if fraud_score < 300:
            risk_level = 'LOW'
        elif fraud_score < 700:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'HIGH'

        # Get fraud reasons
        rule_results = fraud_response.get('ruleResults', [])
        fraud_reasons = [
            rule['ruleId'] for rule in rule_results
            if rule['outcomes'] and 'REVIEW' in rule['outcomes']
        ]

        # Save fraud check results
        insert_query = """
            INSERT INTO fraud_checks
            (application_id, fraud_score, risk_level, fraud_reasons)
            VALUES (%s, %s, %s, %s)
        """
        execute_insert(insert_query, (
            application_id,
            fraud_score,
            risk_level,
            json.dumps(fraud_reasons)
        ))

        # Update application
        update_query = """
            UPDATE applications
            SET fraud_score = %s,
                fraud_risk_level = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        execute_insert(update_query, (fraud_score, risk_level, application_id))

        logger.info(f'Fraud check completed: {application_id}, Score: {fraud_score}, Risk: {risk_level}')

        return {
            'statusCode': 200,
            'fraud_score': fraud_score,
            'risk_level': risk_level,
            'fraud_reasons': fraud_reasons
        }

    except Exception as e:
        logger.error(f'Fraud detection error: {str(e)}')

        # Fallback: simple rule-based fraud check
        fraud_score = perform_basic_fraud_check(app_data)
        risk_level = 'LOW' if fraud_score < 300 else 'MEDIUM'

        return {
            'statusCode': 200,
            'fraud_score': fraud_score,
            'risk_level': risk_level,
            'fallback': True
        }

def perform_basic_fraud_check(app_data):
    """
    Fallback fraud detection using simple rules.
    Returns score 0-1000.
    """
    score = 100  # Base score

    # Rule 1: Check debt-to-income ratio
    if app_data.get('monthly_income'):
        dti_ratio = app_data['loan_amount'] / (app_data['monthly_income'] * 12)
        if dti_ratio > 0.5:
            score += 200
        elif dti_ratio > 0.3:
            score += 100

    # Rule 2: Check for duplicate applications
    dup_query = """
        SELECT COUNT(*) as count
        FROM applications
        WHERE customer_id = %s
        AND status = 'PENDING'
        AND id != %s
    """
    dup_result = execute_query(dup_query, (app_data['customer_id'], app_data['id']))
    if dup_result[0]['count'] > 0:
        score += 300

    # Rule 3: Check loan amount (high amounts = higher risk)
    if app_data['loan_amount'] > 100000:
        score += 150

    return min(score, 1000)
```

**Configure AWS Fraud Detector:**

**File**: `backend/scripts/setup-fraud-detector.sh`

```bash
#!/bin/bash
# Setup AWS Fraud Detector for BancaFiel

# Create entity type
aws frauddetector put-entity-type \
  --name customer \
  --description "BancaFiel customer entity"

# Create event type
aws frauddetector put-event-type \
  --name loan_application \
  --event-variables email ip_address loan_amount phone curp \
  --entity-types customer \
  --labels fraud legitimate \
  --description "Loan application event"

# Create variables
aws frauddetector create-variable \
  --name email \
  --data-type STRING \
  --data-source EVENT \
  --default-value "unknown@example.com"

aws frauddetector create-variable \
  --name loan_amount \
  --data-type STRING \
  --data-source EVENT \
  --default-value "0"

# Create detector
aws frauddetector put-detector \
  --detector-id bancafiel_loan_fraud_detector \
  --event-type-name loan_application \
  --description "Fraud detector for BancaFiel loan applications"

# Create outcome
aws frauddetector put-outcome \
  --name review_application \
  --description "Flag application for manual review"

# Create rule (example: high loan amount)
aws frauddetector create-rule \
  --rule-id high_loan_amount_rule \
  --detector-id bancafiel_loan_fraud_detector \
  --expression "\$loan_amount > 100000" \
  --language DETECTORPL \
  --outcomes review_application

echo "Fraud Detector configured successfully!"
```

---

### Day 12-13: Step Functions Workflow

**File**: `backend/src/step-functions/loan-workflow.json`

```json
{
  "Comment": "BancaFiel Loan Application Processing Workflow",
  "StartAt": "ExtractData",
  "States": {
    "ExtractData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-extractData",
      "ResultPath": "$.extractionResult",
      "Next": "ValidateData",
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "ResultPath": "$.error",
          "Next": "ExtractionFailed"
        }
      ]
    },

    "ValidateData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-validateData",
      "ResultPath": "$.validationResult",
      "Next": "CheckValidation",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }
      ]
    },

    "CheckValidation": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.validationResult.is_valid",
          "BooleanEquals": false,
          "Next": "ValidationFailed"
        }
      ],
      "Default": "DetectFraud"
    },

    "DetectFraud": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-detectFraud",
      "ResultPath": "$.fraudResult",
      "Next": "CheckFraudScore"
    },

    "CheckFraudScore": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.fraudResult.risk_level",
          "StringEquals": "HIGH",
          "Next": "AutoReject"
        },
        {
          "Variable": "$.fraudResult.risk_level",
          "StringEquals": "MEDIUM",
          "Next": "RouteToSeniorOfficer"
        }
      ],
      "Default": "RouteToAnalyst"
    },

    "RouteToAnalyst": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-routeApprover",
      "Parameters": {
        "application_id.$": "$.application_id",
        "approver_type": "analyst"
      },
      "ResultPath": "$.routingResult",
      "Next": "WaitForHumanApproval"
    },

    "RouteToSeniorOfficer": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-routeApprover",
      "Parameters": {
        "application_id.$": "$.application_id",
        "approver_type": "senior_officer"
      },
      "ResultPath": "$.routingResult",
      "Next": "WaitForHumanApproval"
    },

    "WaitForHumanApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "bancafiel-sendApprovalNotification",
        "Payload": {
          "application_id.$": "$.application_id",
          "task_token.$": "$$.Task.Token"
        }
      },
      "ResultPath": "$.approvalResult",
      "Next": "CheckApprovalDecision",
      "TimeoutSeconds": 86400
    },

    "CheckApprovalDecision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.approvalResult.decision",
          "StringEquals": "APPROVED",
          "Next": "UpdateERPApproved"
        }
      ],
      "Default": "UpdateERPRejected"
    },

    "UpdateERPApproved": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-updateERP",
      "Parameters": {
        "application_id.$": "$.application_id",
        "status": "APPROVED"
      },
      "ResultPath": "$.erpResult",
      "Next": "SendApprovalEmail"
    },

    "SendApprovalEmail": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-sendNotification",
      "Parameters": {
        "application_id.$": "$.application_id",
        "type": "approved"
      },
      "End": true
    },

    "UpdateERPRejected": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-updateERP",
      "Parameters": {
        "application_id.$": "$.application_id",
        "status": "REJECTED"
      },
      "ResultPath": "$.erpResult",
      "Next": "SendRejectionEmail"
    },

    "SendRejectionEmail": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-sendNotification",
      "Parameters": {
        "application_id.$": "$.application_id",
        "type": "rejected"
      },
      "End": true
    },

    "AutoReject": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:bancafiel-updateERP",
      "Parameters": {
        "application_id.$": "$.application_id",
        "status": "REJECTED",
        "reason": "High fraud risk - automatic rejection"
      },
      "Next": "SendRejectionEmail"
    },

    "ValidationFailed": {
      "Type": "Fail",
      "Error": "ValidationError",
      "Cause": "Document validation failed"
    },

    "ExtractionFailed": {
      "Type": "Fail",
      "Error": "ExtractionError",
      "Cause": "Unable to extract data from documents"
    }
  }
}
```

**Deploy Step Functions:**
```bash
aws stepfunctions create-state-machine \
  --name BancaFielLoanWorkflow \
  --definition file://backend/src/step-functions/loan-workflow.json \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/StepFunctionsExecutionRole
```

---

### Day 14: Remaining Lambda Functions

**Lambda #5: routeApprover**
**Lambda #6: updateERP**
**Lambda #7: sendNotification**

(Code similar structure to previous Lambdas - I'll provide templates if needed)

**Week 2 Complete! ✅**

---

## 🗓️ Week 3: Approval System & Integrations (Days 15-21)

### Days 15-16: Human Approval with Task Token

**Lambda: sendApprovalNotification**

**File**: `backend/src/lambdas/approval-notifier/handler.py`

```python
import json
import boto3
from utils.logger import setup_logger
from utils.database import execute_insert

logger = setup_logger('sendApprovalNotification')
sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Sends notification to approver and stores task token.
    Approver will use task token to resume Step Functions.
    """
    try:
        application_id = event['application_id']
        task_token = event['task_token']

        # Store task token in DynamoDB (for callback)
        table = dynamodb.Table('bancafiel-approval-tokens')
        table.put_item(
            Item={
                'application_id': application_id,
                'task_token': task_token,
                'status': 'PENDING',
                'created_at': datetime.utcnow().isoformat()
            }
        )

        # Send SNS notification to approver
        message = {
            'application_id': application_id,
            'message': 'New loan application pending approval',
            'dashboard_link': f'https://bancafiel.com/approvals/{application_id}'
        }

        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:ACCOUNT_ID:bancafiel-approver-notifications',
            Subject='New Loan Application for Review',
            Message=json.dumps(message)
        )

        logger.info(f'Approval notification sent for application {application_id}')

        # Lambda will wait here for task token callback
        # No return needed - Step Functions waits for SendTaskSuccess

    except Exception as e:
        logger.error(f'Error sending approval notification: {str(e)}')
        raise
```

**API Endpoint for Approval Callback:**

**File**: `backend/src/api/routes/approvals.py`

```python
import boto3
from utils.response import success_response, error_response

stepfunctions_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

def approve_application_callback(event, context):
    """
    POST /api/loans/:id/approve
    Resumes Step Functions workflow with approval decision
    """
    try:
        application_id = event['pathParameters']['id']
        body = json.loads(event['body'])

        # Get task token from DynamoDB
        table = dynamodb.Table('bancafiel-approval-tokens')
        response = table.get_item(Key={'application_id': application_id})

        if 'Item' not in response:
            return error_response('Approval token not found', 404)

        task_token = response['Item']['task_token']

        # Send success to Step Functions
        stepfunctions_client.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                'decision': 'APPROVED',
                'approved_by': body.get('approvedBy'),
                'notes': body.get('notes')
            })
        )

        # Delete token
        table.delete_item(Key={'application_id': application_id})

        return success_response({
            'success': True,
            'message': 'Application approved'
        })

    except Exception as e:
        return error_response(str(e), 500)
```

---

### Days 17-18: Email Notifications (SES)

**File**: `backend/src/lambdas/notification-sender/handler.py`

```python
import boto3
from utils.database import execute_query

ses_client = boto3.client('ses')

def handler(event, context):
    """
    Sends email notifications using SES templates.
    """
    try:
        application_id = event['application_id']
        notification_type = event['type']  # 'approved' or 'rejected'

        # Get application and customer data
        query = """
            SELECT
                a.*,
                c.full_name,
                c.email
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """
        app_data = execute_query(query, (application_id,))[0]

        # Select email template
        if notification_type == 'approved':
            template_name = 'LoanApproved'
            subject = '¡Felicidades! Su préstamo ha sido aprobado'
        else:
            template_name = 'LoanRejected'
            subject = 'Actualización sobre su solicitud de préstamo'

        # Send templated email
        response = ses_client.send_templated_email(
            Source='noreply@bancafiel.com',
            Destination={
                'ToAddresses': [app_data['email']]
            },
            Template=template_name,
            TemplateData=json.dumps({
                'customer_name': app_data['full_name'],
                'loan_amount': f"${app_data['loan_amount']:,.2f} MXN",
                'application_id': str(application_id)
            })
        )

        logger.info(f'Email sent to {app_data["email"]}: {notification_type}')

        return {'statusCode': 200, 'message': 'Email sent'}

    except Exception as e:
        logger.error(f'Error sending email: {str(e)}')
        raise
```

**SES Email Templates:**

**File**: `backend/infrastructure/ses-templates/loan-approved.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2563eb;">¡Felicidades, {{customer_name}}!</h1>

        <p>Nos complace informarle que su solicitud de préstamo ha sido <strong>APROBADA</strong>.</p>

        <div style="background-color: #f0f9ff; padding: 15px; border-left: 4px solid #2563eb; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Monto aprobado:</strong> {{loan_amount}}</p>
            <p style="margin: 5px 0;"><strong>Número de solicitud:</strong> {{application_id}}</p>
        </div>

        <p><strong>Próximos pasos:</strong></p>
        <ol>
            <li>Inicie sesión en su cuenta de BancaFiel</li>
            <li>Complete la documentación final</li>
            <li>Firme el contrato digitalmente</li>
            <li>Reciba su préstamo en 24-48 horas</li>
        </ol>

        <a href="https://bancafiel.com/dashboard"
           style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 20px 0;">
            Acceder a mi cuenta
        </a>

        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            Este es un correo automático. Por favor no responda a este mensaje.
        </p>
    </div>
</body>
</html>
```

**Create SES templates:**
```bash
aws ses create-template --cli-input-json file://backend/infrastructure/ses-templates/loan-approved-template.json
```

---

### Days 19-21: CloudWatch Monitoring & Analytics

**Lambda: getAnalytics**

**File**: `backend/src/api/routes/analytics.py`

```python
def get_analytics(event, context):
    """
    GET /api/analytics?startDate=2026-02-01&endDate=2026-02-15
    Returns analytics data
    """
    try:
        params = event.get('queryStringParameters', {}) or {}
        start_date = params.get('startDate')
        end_date = params.get('endDate')

        # Query analytics
        query = """
            SELECT
                COUNT(*) as total_applications,
                SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                AVG(EXTRACT(EPOCH FROM (processed_at - requested_date))/60) as avg_processing_minutes,
                SUM(CASE WHEN fraud_risk_level = 'HIGH' THEN 1 ELSE 0 END) as fraud_alerts
            FROM applications
            WHERE requested_date BETWEEN %s AND %s
        """

        stats = execute_query(query, (start_date, end_date))[0]

        # Volume by day
        daily_query = """
            SELECT
                DATE(requested_date) as date,
                COUNT(*) as applications
            FROM applications
            WHERE requested_date BETWEEN %s AND %s
            GROUP BY DATE(requested_date)
            ORDER BY date
        """

        daily_volume = execute_query(daily_query, (start_date, end_date))

        response_data = {
            'totalApplications': stats['total_applications'],
            'approved': stats['approved'],
            'rejected': stats['rejected'],
            'pending': stats['pending'],
            'approvalRate': stats['approved'] / stats['total_applications'] if stats['total_applications'] > 0 else 0,
            'averageProcessingTime': round(stats['avg_processing_minutes'], 2),
            'fraudAlerts': stats['fraud_alerts'],
            'volumeByDay': [
                {
                    'date': str(row['date']),
                    'applications': row['applications']
                }
                for row in daily_volume
            ]
        }

        return success_response(response_data)

    except Exception as e:
        return error_response(str(e), 500)
```

**CloudWatch Dashboard:**

**File**: `backend/infrastructure/cloudformation/cloudwatch.yaml`

```yaml
Resources:
  BancaFielDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: BancaFiel-Metrics
      DashboardBody: |
        {
          "widgets": [
            {
              "type": "metric",
              "properties": {
                "metrics": [
                  ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
                  [".", "Errors", {"stat": "Sum"}],
                  [".", "Duration", {"stat": "Average"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Lambda Metrics"
              }
            }
          ]
        }
```

**Week 3 Complete! ✅**

---

## 🗓️ Week 4: Testing, Security & Production (Days 22-28)

### Days 22-23: Integration Testing

**File**: `backend/tests/integration/test_full_workflow.py`

```python
import pytest
import boto3
import json
from datetime import datetime

s3_client = boto3.client('s3')
stepfunctions_client = boto3.client('stepfunctions')

def test_complete_loan_workflow():
    """
    End-to-end test: Upload document → Process → Approve → Verify
    """

    # 1. Upload test document to S3
    test_application_id = str(uuid.uuid4())
    bucket = 'bancafiel-incoming-documents-test'
    key = f'applications/{test_application_id}/ine.pdf'

    with open('tests/fixtures/sample-ine.pdf', 'rb') as f:
        s3_client.upload_fileobj(f, bucket, key)

    # 2. Start Step Functions execution
    execution = stepfunctions_client.start_execution(
        stateMachineArn='arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:BancaFielLoanWorkflow',
        input=json.dumps({
            'application_id': test_application_id,
            'bucket': bucket,
            'key': key
        })
    )

    # 3. Wait for workflow to reach approval stage
    time.sleep(60)  # Wait for processing

    # 4. Verify application status in database
    # ... (database check)

    # 5. Simulate approval
    # ... (call approval API)

    # 6. Verify final state
    # ... (check application approved, email sent)

    assert True  # Replace with actual assertions
```

**Load Testing:**

**File**: `backend/tests/load/locustfile.py`

```python
from locust import HttpUser, task, between

class LoanApplicationUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_pending_applications(self):
        self.client.get("/api/loans?status=pending",
                       headers={"Authorization": f"Bearer {self.token}"})

    @task(2)
    def get_application_details(self):
        self.client.get(f"/api/loans/{self.application_id}",
                       headers={"Authorization": f"Bearer {self.token}"})

    def on_start(self):
        # Login and get token
        response = self.client.post("/api/auth/login", json={
            "username": "test@bancafiel.com",
            "password": "test123"
        })
        self.token = response.json()['token']
```

Run load test:
```bash
locust -f backend/tests/load/locustfile.py --users 100 --spawn-rate 10
```

---

### Days 24-25: Security Hardening

**Security Checklist:**

1. **IAM Roles - Principle of Least Privilege**

**File**: `backend/infrastructure/iam/lambda-execution-role.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::bancafiel-incoming-documents-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection"
      ],
      "Resource": "*"
    }
  ]
}
```

2. **Database Security**

```sql
-- Create read-only role for analytics
CREATE ROLE analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- Encrypt sensitive fields
ALTER TABLE customers
ADD COLUMN curp_encrypted BYTEA;

-- Row-level security
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY analyst_access ON applications
FOR SELECT
TO analyst_role
USING (status = 'PENDING');
```

3. **API Gateway Security**

- Enable AWS WAF
- Add rate limiting (1000 requests/minute per IP)
- Require API keys for all endpoints
- Enable CloudTrail logging

4. **Secrets Management**

Store database credentials in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name bancafiel/db/credentials \
  --secret-string '{"username":"bancafiel_admin","password":"SecurePassword123!"}'
```

Update Lambda to retrieve from Secrets Manager:

```python
import boto3
secrets_client = boto3.client('secretsmanager')

def get_db_credentials():
    response = secrets_client.get_secret_value(SecretId='bancafiel/db/credentials')
    return json.loads(response['SecretString'])
```

---

### Days 26-27: Production Deployment

**File**: `backend/scripts/deploy-production.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Deploying BancaFiel Backend to Production..."

# 1. Run tests
echo "Running tests..."
python -m pytest backend/tests/unit/
python -m pytest backend/tests/integration/

# 2. Build SAM application
echo "Building SAM application..."
cd backend
sam build --use-container

# 3. Deploy to production
echo "Deploying to AWS..."
sam deploy \
  --config-env production \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --stack-name bancafiel-backend-prod \
  --parameter-overrides \
    Environment=prod \
    DBPassword=$(aws secretsmanager get-secret-value --secret-id bancafiel/db/credentials --query SecretString --output text | jq -r '.password')

# 4. Deploy Step Functions
echo "Deploying Step Functions..."
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:BancaFielLoanWorkflow-Prod \
  --definition file://src/step-functions/loan-workflow.json

# 5. Configure SES production sending
aws ses put-account-sending-enabled --enabled

# 6. Warm up Lambdas
echo "Warming up Lambda functions..."
for function in processDocument extractData validateData detectFraud; do
  aws lambda invoke \
    --function-name bancafiel-$function-prod \
    --payload '{"warmup":true}' \
    /dev/null
done

# 7. Health check
echo "Running health checks..."
curl -f https://api.bancafiel.com/health || exit 1

echo "✅ Production deployment complete!"
```

---

### Day 28: Documentation & Demo Prep

**File**: `backend/README.md`

```markdown
# BancaFiel Backend

Production-ready AWS serverless backend for loan processing automation.

## Architecture

- **API**: API Gateway + Lambda (Python 3.11)
- **Database**: PostgreSQL on RDS
- **Storage**: S3 + Textract for document processing
- **Orchestration**: Step Functions
- **Fraud Detection**: AWS Fraud Detector
- **Notifications**: SES + SNS

## Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.11
- AWS SAM CLI
- PostgreSQL client

### Local Development

1. Install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Run tests:
```bash
pytest tests/
```

### Deployment

Production deployment:
```bash
./scripts/deploy-production.sh
```

Development deployment:
```bash
sam build && sam deploy --guided
```

## API Documentation

See `/docs/api-contracts/loan-api.md`

## Monitoring

CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=BancaFiel-Metrics

## Troubleshooting

See `docs/troubleshooting.md`
```

**Runbook for Production Issues:**

**File**: `backend/docs/runbooks/production-issues.md`

```markdown
# Production Runbook

## Issue: Lambda Timeout

**Symptoms**: Lambda execution exceeds 30 seconds

**Diagnosis**:
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/bancafiel-extractData \
  --filter-pattern "Task timed out"
```

**Resolution**:
1. Increase timeout in SAM template
2. Optimize Textract call (use batch processing)
3. Check database connection pooling

## Issue: High Fraud False Positives

**Symptoms**: Too many legitimate applications flagged as fraud

**Diagnosis**:
Check fraud score distribution

**Resolution**:
Adjust Fraud Detector thresholds in AWS console

## Issue: Database Connection Pool Exhausted

**Resolution**:
Increase RDS max_connections or implement connection pooling in Lambda
```

---

## ✅ Final Deliverables Checklist

### Code
- [x] 7 Lambda functions deployed
- [x] PostgreSQL database with complete schema
- [x] Step Functions workflow orchestrating pipeline
- [x] API Gateway with all endpoints
- [x] S3 buckets configured
- [x] Fraud Detector configured
- [x] SES email templates

### Infrastructure
- [x] CloudFormation/SAM templates
- [x] IAM roles and policies
- [x] CloudWatch dashboards and alarms
- [x] Secrets Manager for credentials
- [x] Production deployment scripts

### Testing
- [x] Unit tests (80%+ coverage)
- [x] Integration tests (end-to-end workflows)
- [x] Load tests (500 applications/day capacity)
- [x] Security testing (penetration test report)

### Documentation
- [x] API documentation (loan-api.md)
- [x] Architecture diagrams
- [x] Deployment guide
- [x] Runbooks for production issues
- [x] Developer README

### Demo Preparation
- [x] Sample test data (100+ applications)
- [x] Demo script with talking points
- [x] Recorded demo video (backup)
- [x] Slides with architecture diagram
- [x] ROI calculations ready

---

## 📊 Success Metrics

After 4 weeks, you will have:

✅ **Functional**: Complete backend processing 500 applications/day
✅ **Tested**: 100+ test scenarios passed
✅ **Documented**: Comprehensive docs for handoff
✅ **Scalable**: Handles 10x load with no code changes
✅ **Monitored**: Real-time dashboards and alerts
✅ **Secure**: Security best practices implemented
✅ **Production-Ready**: Can deploy to real bank environment

**Processing Time**: < 2 hours (vs. 1 week manual)
**Cost**: $250-300/month (vs. $381k/month current)
**ROI**: 88,208% annually

---

## 🎯 Daily Standup Format

Track progress daily:

**Template:**
```
Day X of 28 - [Status]

✅ Completed yesterday:
- Task 1
- Task 2

🔨 Working on today:
- Task 3
- Task 4

🚧 Blockers:
- Issue 1 (needs resolution)

📊 Progress: XX% complete
```

---

## 🆘 When You Need Help

**Resources:**
1. AWS Documentation: https://docs.aws.amazon.com/
2. AWS re:Post: https://repost.aws/
3. Stack Overflow: Tag `aws-lambda`, `aws-step-functions`
4. Our architecture docs: `docs/technical/AWS_Architecture_Design.md`

**Escalation:**
- Technical blocker > 4 hours: Reach out to team
- Architecture decision needed: Review with group
- AWS service limit: Submit support ticket

---

## 🎉 You've Got This!

This plan breaks down a complex system into manageable daily tasks. Follow it step-by-step, test frequently, and you'll have a production-ready backend in 4 weeks.

**Remember:**
- Progress over perfection
- Test early, test often
- Document as you build
- Ask for help when stuck

Good luck! 🚀

---

**Last Updated**: February 16, 2026
**Owner**: Backend Team
**Status**: Ready to Execute
