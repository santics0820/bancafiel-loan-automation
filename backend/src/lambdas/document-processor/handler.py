"""
Lambda #1: Process Document
Triggered by S3 upload → Invokes Claude Sonnet 4.5 on Bedrock for OCR extraction
"""
import json
import boto3
import base64
import os
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    def setup_logger(name):
        return logger
    def log_event(logger, event_type, data):
        logger.info(f"{event_type}: {data}")
    def log_error(logger, error_type, error, context=None):
        logger.error(f"{error_type}: {error}")

logger = setup_logger(__name__)
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
lambda_client = boto3.client('lambda')

BEDROCK_MODEL_ID = 'us.anthropic.claude-sonnet-4-5-20250929-v1:0'

EXTRACTION_PROMPTS = {
    'INE': """You are a Mexican government document OCR specialist.
Extract the following fields from this INE/IFE identity document image.
Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "full_name": "complete name as it appears",
  "curp": "18-character CURP code",
  "date_of_birth": "DD/MM/YYYY",
  "address": "full address",
  "voter_key": "voter registration key",
  "expiry_date": "DD/MM/YYYY"
}
Do not include any explanation, only the JSON.""",

    'PROOF_OF_ADDRESS': """You are a Mexican document OCR specialist.
Extract the following fields from this proof of address document.
Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "full_name": "account holder name",
  "address": "complete address",
  "city": "city",
  "state": "state",
  "zip_code": "postal code",
  "document_date": "DD/MM/YYYY",
  "issuer": "company or institution that issued the document"
}
Do not include any explanation, only the JSON.""",

    'BANK_STATEMENT': """You are a Mexican banking document OCR specialist.
Extract the following fields from this bank statement.
Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "bank_name": "name of the bank",
  "account_holder": "account holder full name",
  "account_number": "account number",
  "clabe": "18-digit CLABE interbank code",
  "rfc": "RFC tax ID",
  "period_start": "DD/MM/YYYY",
  "period_end": "DD/MM/YYYY",
  "balance": "final balance as plain number",
  "average_balance": "average balance as plain number",
  "total_deposits": "total deposits as plain number",
  "total_withdrawals": "total withdrawals as plain number"
}
Do not include any explanation, only the JSON.""",

    'INCOME_PROOF': """You are a Mexican payroll document OCR specialist.
Extract the following fields from this income/payroll document.
Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "employer_name": "company or employer name",
  "employee_name": "employee full name",
  "rfc": "RFC tax ID",
  "period_start": "DD/MM/YYYY",
  "period_end": "DD/MM/YYYY",
  "payment_frequency": "SEMANAL, QUINCENAL, or MENSUAL",
  "gross_income": "gross salary as plain number",
  "net_income": "net salary as plain number"
}
Do not include any explanation, only the JSON."""
}


def handler(event, context):
    """
    Process document upload from S3.

    Event: S3 ObjectCreated notification
    Actions:
        1. Extract application_id from S3 key
        2. Download document from S3
        3. Send to Claude Sonnet 4.5 on Bedrock for OCR extraction
        4. Save document metadata + extracted data to database
        5. Trigger extractData Lambda with results

    Returns:
        dict: Success/error response
    """
    try:
        log_event(logger, 'lambda_invoked', {
            'function': 'processDocument',
            'event_type': 'S3 ObjectCreated'
        })

        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            file_size = record['s3']['object']['size']

            log_event(logger, 'document_received', {
                'bucket': bucket,
                'key': key,
                'size_bytes': file_size
            })

            application_id = extract_application_id(key)
            if not application_id:
                logger.error(f"Invalid S3 key format: {key}")
                continue

            document_type = determine_document_type(key)

            # Download document from S3
            try:
                s3_response = s3_client.get_object(Bucket=bucket, Key=key)
                document_bytes = s3_response['Body'].read()
                document_b64 = base64.standard_b64encode(document_bytes).decode('utf-8')
            except Exception as e:
                log_error(logger, 's3_download_failed', e, {'bucket': bucket, 'key': key})
                continue

            # Extract data using Claude Sonnet 4.5 on Bedrock
            extracted_fields = {}
            bedrock_job_id = f"bedrock-{application_id}-{document_type}"

            try:
                extracted_fields = extract_with_bedrock(document_b64, document_type)
                log_event(logger, 'bedrock_extraction_complete', {
                    'application_id': application_id,
                    'document_type': document_type,
                    'fields_extracted': len(extracted_fields)
                })
            except Exception as e:
                log_error(logger, 'bedrock_extraction_failed', e, {
                    'application_id': application_id,
                    'document_type': document_type
                })

            # Save document metadata to database
            try:
                query = """
                    INSERT INTO documents
                    (application_id, document_type, s3_bucket, s3_key,
                     file_size_bytes, textract_job_id, textract_status, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                result = execute_insert(query, (
                    application_id,
                    document_type,
                    bucket,
                    key,
                    file_size,
                    bedrock_job_id,
                    'SUCCEEDED' if extracted_fields else 'FAILED',
                    datetime.now(UTC)
                ))

                document_id = result[0]['id'] if isinstance(result, list) and result else None

                log_event(logger, 'document_saved_to_db', {
                    'application_id': application_id,
                    'document_type': document_type,
                    'document_id': str(document_id) if document_id else None
                })

            except Exception as e:
                log_error(logger, 'database_insert_failed', e, {'application_id': application_id})
                document_id = None

            # Save extracted fields to database and trigger next Lambda
            if extracted_fields and document_id:
                try:
                    save_extracted_data(str(document_id), extracted_fields)

                    # Update document status
                    execute_insert(
                        "UPDATE documents SET textract_status = %s, processed_at = %s WHERE id = %s",
                        ('SUCCEEDED', datetime.now(UTC), str(document_id))
                    )

                    # Trigger validateData Lambda
                    lambda_client.invoke(
                        FunctionName=os.environ.get('VALIDATE_DATA_FUNCTION', 'bancafiel-validateData-dev'),
                        InvocationType='Event',
                        Payload=json.dumps({
                            'document_id': str(document_id),
                            'application_id': application_id
                        })
                    )

                    log_event(logger, 'triggered_validate_data', {
                        'application_id': application_id,
                        'document_id': str(document_id)
                    })

                except Exception as e:
                    log_error(logger, 'post_extraction_failed', e, {'application_id': application_id})

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Document processing complete'})
        }

    except Exception as e:
        log_error(logger, 'handler_error', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }


def extract_with_bedrock(document_b64, document_type):
    """
    Send document to Claude Sonnet 4.5 on Bedrock for OCR extraction.

    Args:
        document_b64 (str): Base64-encoded document bytes
        document_type (str): Type of document (INE, BANK_STATEMENT, etc.)

    Returns:
        dict: Extracted fields with confidence scores (confidence set to 99.0 for Claude)
    """
    prompt = EXTRACTION_PROMPTS.get(document_type, EXTRACTION_PROMPTS['INCOME_PROOF'])

    document_bytes = base64.b64decode(document_b64)

    # Detect file type by magic bytes
    is_jpeg = document_bytes[:3] == b'\xff\xd8\xff'
    is_png  = document_bytes[:8] == b'\x89PNG\r\n\x1a\n'

    if is_jpeg or is_png:
        img_format = 'jpeg' if is_jpeg else 'png'
        media_block = {
            "image": {
                "format": img_format,
                "source": {"bytes": document_bytes}
            }
        }
    else:
        media_block = {
            "document": {
                "format": "pdf",
                "name": "document",
                "source": {"bytes": document_bytes}
            }
        }

    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                    media_block
                ]
            }
        ],
        inferenceConfig={"maxTokens": 1024}
    )

    raw_text = response['output']['message']['content'][0]['text'].strip()

    # Parse JSON response from Claude
    if raw_text.startswith('```'):
        raw_text = raw_text.split('```')[1]
        if raw_text.startswith('json'):
            raw_text = raw_text[4:]

    extracted = json.loads(raw_text)

    # Normalize to {field: {value, confidence}} format expected by downstream Lambdas
    fields = {}
    for key, value in extracted.items():
        if value is not None:
            fields[key] = {'value': str(value), 'confidence': 99.0}

    return fields


def save_extracted_data(document_id, extracted_fields):
    """Save extracted fields to the extracted_data table."""
    from datetime import timezone
    for field_name, field_data in extracted_fields.items():
        query = """
            INSERT INTO extracted_data
            (document_id, field_name, field_value, confidence, extracted_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (document_id, field_name)
            DO UPDATE SET
                field_value = EXCLUDED.field_value,
                confidence = EXCLUDED.confidence,
                extracted_at = EXCLUDED.extracted_at
        """
        execute_insert(query, (
            document_id,
            field_name,
            field_data['value'],
            field_data['confidence'],
            datetime.now(timezone.utc)
        ))


def extract_application_id(s3_key):
    """Extract application_id from S3 key: applications/{application_id}/filename.pdf"""
    parts = s3_key.split('/')
    if len(parts) >= 2 and parts[0] == 'applications':
        return parts[1]
    return None


def determine_document_type(s3_key):
    """Determine document type from filename."""
    filename = s3_key.lower()
    if 'ine' in filename or 'ife' in filename:
        return 'INE'
    elif 'proof' in filename or 'comprobante' in filename or 'address' in filename:
        return 'PROOF_OF_ADDRESS'
    elif 'bank' in filename or 'estado' in filename or 'cuenta' in filename:
        return 'BANK_STATEMENT'
    elif 'income' in filename or 'ingreso' in filename or 'nomina' in filename:
        return 'INCOME_PROOF'
    else:
        return 'INCOME_PROOF'
