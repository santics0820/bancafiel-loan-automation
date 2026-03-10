"""
Lambda #2: Extract Data
Now a lightweight pass-through — data extraction is performed directly in processDocument
using Claude Sonnet 4.5 on Amazon Bedrock. This Lambda triggers validateData.
"""
import json
import boto3
import os

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_query_single
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
lambda_client = boto3.client('lambda')


def handler(event, context):
    """
    Pass-through Lambda — invoked by processDocument after Bedrock extraction.

    Event: {document_id, application_id}
    Actions:
        1. Verify document exists in DB
        2. Trigger validateData Lambda

    Returns:
        dict: Success/error response
    """
    try:
        log_event(logger, 'lambda_invoked', {
            'function': 'extractData',
            'event_type': 'direct invoke from processDocument'
        })

        document_id = event.get('document_id')
        application_id = event.get('application_id')

        if not document_id or not application_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing document_id or application_id'})
            }

        # Verify document exists
        document = execute_query_single(
            "SELECT id, document_type, textract_status FROM documents WHERE id = %s",
            (document_id,)
        )

        if not document:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }

        log_event(logger, 'document_verified', {
            'document_id': document_id,
            'document_type': document['document_type'],
            'status': document['textract_status']
        })

        # Trigger validateData Lambda
        try:
            lambda_client.invoke(
                FunctionName=os.environ.get('VALIDATE_DATA_FUNCTION', 'bancafiel-validateData-dev'),
                InvocationType='Event',
                Payload=json.dumps({
                    'document_id': document_id,
                    'application_id': application_id
                })
            )

            log_event(logger, 'triggered_validate_data', {
                'application_id': application_id,
                'document_id': document_id
            })

        except Exception as e:
            log_error(logger, 'lambda_invoke_failed', e)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data extraction verified, validation triggered',
                'document_id': document_id,
                'application_id': application_id
            })
        }

    except Exception as e:
        log_error(logger, 'handler_error', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
