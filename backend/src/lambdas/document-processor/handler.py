"""
Lambda #1: Process Document
Triggered by S3 upload → Starts Amazon Textract processing
"""
import json
import boto3
import os
from datetime import datetime

# These imports will come from Lambda Layer
try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single
except ImportError:
    # Fallback for local testing
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
textract_client = boto3.client('textract')


def handler(event, context):
    """
    Process document upload from S3.

    Event: S3 ObjectCreated notification
    Actions:
        1. Extract application_id from S3 key
        2. Start Textract async job
        3. Save document metadata to database

    Returns:
        dict: Success/error response
    """
    try:
        log_event(logger, 'lambda_invoked', {
            'function': 'processDocument',
            'event_type': 'S3 ObjectCreated'
        })

        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            file_size = record['s3']['object']['size']

            log_event(logger, 'document_received', {
                'bucket': bucket,
                'key': key,
                'size_bytes': file_size
            })

            # Extract application_id from S3 key
            # Expected format: applications/{application_id}/{document_type}.pdf
            application_id = extract_application_id(key)
            if not application_id:
                logger.error(f"Invalid S3 key format: {key}")
                continue

            # Determine document type from filename
            document_type = determine_document_type(key)

            # Start Textract async job
            sns_topic_arn = os.environ.get('TEXTRACT_SNS_TOPIC_ARN')
            textract_role_arn = os.environ.get('TEXTRACT_ROLE_ARN')

            try:
                textract_response = textract_client.start_document_text_detection(
                    DocumentLocation={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': key
                        }
                    },
                    NotificationChannel={
                        'SNSTopicArn': sns_topic_arn,
                        'RoleArn': textract_role_arn
                    }
                )

                job_id = textract_response['JobId']

                log_event(logger, 'textract_job_started', {
                    'job_id': job_id,
                    'application_id': application_id,
                    'document_type': document_type
                })

            except Exception as e:
                log_error(logger, 'textract_start_failed', e, {
                    'bucket': bucket,
                    'key': key
                })
                # Continue to save document metadata even if Textract fails
                job_id = None

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
                    job_id,
                    'IN_PROGRESS' if job_id else 'PENDING',
                    datetime.utcnow()
                ))

                log_event(logger, 'document_saved_to_db', {
                    'application_id': application_id,
                    'document_type': document_type,
                    'textract_job_id': job_id
                })

            except Exception as e:
                log_error(logger, 'database_insert_failed', e, {
                    'application_id': application_id
                })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processing started',
                'job_id': job_id if 'job_id' in locals() else None
            })
        }

    except Exception as e:
        log_error(logger, 'handler_error', e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def extract_application_id(s3_key):
    """
    Extract application_id from S3 key.

    Expected format: applications/{application_id}/filename.pdf
    Returns application_id or None if invalid format
    """
    parts = s3_key.split('/')
    if len(parts) >= 2 and parts[0] == 'applications':
        return parts[1]
    return None


def determine_document_type(s3_key):
    """
    Determine document type from filename.

    Args:
        s3_key (str): S3 object key

    Returns:
        str: Document type (INE, PROOF_OF_ADDRESS, BANK_STATEMENT, INCOME_PROOF)
    """
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
        # Default to INCOME_PROOF if can't determine
        return 'INCOME_PROOF'
