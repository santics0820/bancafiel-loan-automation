"""
Lambda #2: Extract Data
Triggered by SNS (from Textract) → Extracts structured data from documents
"""
import json
import boto3
import re
from datetime import datetime

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    def setup_logger(name):
        return logger

logger = setup_logger(__name__)
textract_client = boto3.client('textract')
lambda_client = boto3.client('lambda')


def handler(event, context):
    """
    Extract data from Textract results.

    Event: SNS notification from Textract completion
    Actions:
        1. Get Textract results
        2. Parse and extract structured data
        3. Save to database
        4. Trigger next Lambda (validateData)

    Returns:
        dict: Success/error response
    """
    try:
        log_event(logger, 'lambda_invoked', {
            'function': 'extractData',
            'event_type': 'SNS from Textract'
        })

        # Parse SNS message
        sns_record = event['Records'][0]['Sns']
        message = json.loads(sns_record['Message'])

        job_id = message.get('JobId')
        status = message.get('Status')

        log_event(logger, 'textract_notification_received', {
            'job_id': job_id,
            'status': status
        })

        if status != 'SUCCEEDED':
            logger.error(f'Textract job {job_id} failed with status: {status}')
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Textract job failed: {status}'})
            }

        # Get document info from database
        doc_query = "SELECT * FROM documents WHERE textract_job_id = %s"
        document = execute_query_single(doc_query, (job_id,))

        if not document:
            logger.error(f'Document not found for Textract job {job_id}')
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }

        document_id = str(document['id'])
        application_id = str(document['application_id'])

        # Get Textract results
        textract_results = get_textract_results(job_id)

        # Parse blocks and extract structured data
        extracted_fields = parse_textract_blocks(textract_results, document['document_type'])

        log_event(logger, 'data_extracted', {
            'job_id': job_id,
            'document_id': document_id,
            'fields_count': len(extracted_fields)
        })

        # Save extracted data to database
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
                datetime.utcnow()
            ))

        # Update document status
        update_query = """
            UPDATE documents
            SET textract_status = %s, processed_at = %s
            WHERE id = %s
        """
        execute_insert(update_query, ('SUCCEEDED', datetime.utcnow(), document_id))

        # Trigger next Lambda (validateData)
        try:
            validate_payload = {
                'document_id': document_id,
                'application_id': application_id
            }

            lambda_client.invoke(
                FunctionName='bancafiel-validateData-dev',  # TODO: Get from environment
                InvocationType='Event',  # Async
                Payload=json.dumps(validate_payload)
            )

            log_event(logger, 'triggered_next_lambda', {
                'next_function': 'validateData',
                'application_id': application_id
            })

        except Exception as e:
            log_error(logger, 'lambda_invoke_failed', e)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data extraction complete',
                'document_id': document_id,
                'fields_extracted': len(extracted_fields)
            })
        }

    except Exception as e:
        log_error(logger, 'handler_error', e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_textract_results(job_id):
    """
    Get complete Textract results (handles pagination).

    Args:
        job_id (str): Textract job ID

    Returns:
        list: List of all blocks from Textract
    """
    blocks = []
    next_token = None

    while True:
        if next_token:
            response = textract_client.get_document_text_detection(
                JobId=job_id,
                NextToken=next_token
            )
        else:
            response = textract_client.get_document_text_detection(JobId=job_id)

        blocks.extend(response.get('Blocks', []))

        next_token = response.get('NextToken')
        if not next_token:
            break

    return blocks


def parse_textract_blocks(blocks, document_type):
    """
    Parse Textract blocks into structured fields.

    Args:
        blocks (list): Textract blocks
        document_type (str): Type of document

    Returns:
        dict: Extracted fields with confidence scores
    """
    fields = {}

    # Extract text from all LINE blocks
    lines = [
        {'text': block['Text'], 'confidence': block['Confidence']}
        for block in blocks
        if block['BlockType'] == 'LINE'
    ]

    if document_type == 'INE':
        fields = extract_ine_fields(lines)
    elif document_type == 'PROOF_OF_ADDRESS':
        fields = extract_address_fields(lines)
    elif document_type == 'BANK_STATEMENT':
        fields = extract_bank_statement_fields(lines)
    elif document_type == 'INCOME_PROOF':
        fields = extract_income_fields(lines)

    return fields


def extract_ine_fields(lines):
    """Extract fields from Mexican INE/IFE document"""
    fields = {}
    full_text = ' '.join([line['text'] for line in lines])

    for line in lines:
        text = line['text'].upper()
        confidence = line['confidence']

        # Extract CURP (18-character Mexican ID)
        if 'CURP' in text:
            curp = extract_curp(text)
            if curp:
                fields['curp'] = {'value': curp, 'confidence': confidence}

        # Extract name
        if 'NOMBRE' in text:
            name = extract_after_label(text, 'NOMBRE')
            if name:
                fields['full_name'] = {'value': name, 'confidence': confidence}

        # Extract address
        if 'DOMICILIO' in text or 'DIRECCIÓN' in text:
            address = extract_after_label(text, ['DOMICILIO', 'DIRECCIÓN'])
            if address:
                fields['address'] = {'value': address, 'confidence': confidence}

        # Extract date of birth
        if 'FECHA' in text and 'NACIMIENTO' in text:
            dob = extract_date(text)
            if dob:
                fields['date_of_birth'] = {'value': dob, 'confidence': confidence}

    return fields


def extract_address_fields(lines):
    """Extract address from proof of address document"""
    fields = {}

    # Look for address patterns
    for line in lines:
        text = line['text']

        # Look for common address indicators
        if any(word in text.upper() for word in ['CALLE', 'AV', 'AVENIDA', 'COLONIA']):
            fields['address'] = {
                'value': text,
                'confidence': line['confidence']
            }
            break

    return fields


def extract_bank_statement_fields(lines):
    """Extract data from bank statement"""
    fields = {}
    # TODO: Implement bank statement parsing
    return fields


def extract_income_fields(lines):
    """Extract income information"""
    fields = {}
    # TODO: Implement income proof parsing
    return fields


def extract_curp(text):
    """Extract CURP using regex (18-character Mexican ID)"""
    pattern = r'[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_after_label(text, labels):
    """Extract text after a label"""
    if isinstance(labels, str):
        labels = [labels]

    for label in labels:
        if label in text:
            parts = text.split(label)
            if len(parts) > 1:
                return parts[1].strip()

    return None


def extract_date(text):
    """Extract date from text (DD/MM/YYYY or DD-MM-YYYY)"""
    pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None
