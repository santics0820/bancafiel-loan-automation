"""
Lambda #3: Validate Data
Validates extracted data against business rules and database
"""
import json
import boto3
import re
import os
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single, execute_query, create_application_history
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")

logger = setup_logger(__name__)
lambda_client = boto3.client('lambda')


def handler(event, context):
    try:
        document_id = event.get('document_id')
        application_id = event.get('application_id')

        log_event(logger, 'validateData_invoked', {
            'document_id': document_id,
            'application_id': application_id
        })

        # Get extracted fields from this document
        query = """
            SELECT field_name, field_value, confidence
            FROM extracted_data
            WHERE document_id = %s
        """
        extracted_fields = execute_query(query, (document_id,))
        data = {f['field_name']: f['field_value'] for f in extracted_fields}

        # Run validation rules
        validation = {'is_valid': True, 'errors': [], 'warnings': []}

        # 1. CURP format validation
        curp = data.get('curp')
        if curp:
            if not validate_curp(curp):
                validation['is_valid'] = False
                validation['errors'].append('Invalid CURP format')
        else:
            validation['warnings'].append('CURP not found in document')

        # 2. Required name check
        if not data.get('full_name'):
            validation['warnings'].append('Name not extracted from document')

        # 3. Customer lookup / creation
        customer_id = None
        if curp:
            existing = execute_query_single(
                "SELECT id, full_name FROM customers WHERE curp = %s", (curp,)
            )
            if existing:
                customer_id = str(existing['id'])
                # Cross-check name
                if data.get('full_name') and not names_similar(existing['full_name'], data['full_name']):
                    validation['warnings'].append(f"Name mismatch: DB has '{existing['full_name']}', document has '{data['full_name']}'")
            else:
                # Create new customer from extracted data
                result = execute_query("""
                    INSERT INTO customers (full_name, curp, address, date_of_birth)
                    VALUES (%s, %s, %s, %s) RETURNING id
                """, (
                    data.get('full_name', 'Unknown'),
                    curp,
                    data.get('address'),
                    data.get('date_of_birth')
                ))
                customer_id = str(result[0]['id'])
                log_event(logger, 'new_customer_created', {'customer_id': customer_id, 'curp': curp})

        # 4. Link customer to application
        if customer_id and application_id:
            execute_insert("""
                UPDATE applications
                SET customer_id = %s, status = 'PROCESSING', updated_at = %s
                WHERE id = %s
            """, (customer_id, datetime.now(UTC), application_id))

        # 5. Log audit trail
        create_application_history(
            application_id, 'validation_completed', 'system',
            notes='Document validation completed',
            metadata={'validation': validation, 'customer_id': customer_id}
        )

        log_event(logger, 'validation_complete', {
            'application_id': application_id,
            'is_valid': validation['is_valid'],
            'errors': validation['errors']
        })

        # 6. Trigger fraud detection
        detect_fraud_fn = os.environ.get('DETECT_FRAUD_FUNCTION', 'bancafiel-detectFraud-dev')
        lambda_client.invoke(
            FunctionName=detect_fraud_fn,
            InvocationType='Event',
            Payload=json.dumps({'application_id': application_id})
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'is_valid': validation['is_valid'],
                'customer_id': customer_id,
                'errors': validation['errors'],
                'warnings': validation['warnings']
            })
        }

    except Exception as e:
        log_error(logger, 'validateData_error', e)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def validate_curp(curp):
    pattern = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[A-Z0-9][0-9]$'
    return bool(re.match(pattern, curp.upper()))


def names_similar(name1, name2):
    n1 = ''.join(name1.lower().split())
    n2 = ''.join(name2.lower().split())
    shorter = min(len(n1), len(n2))
    if shorter == 0:
        return False
    matches = sum(c1 == c2 for c1, c2 in zip(n1, n2))
    return (matches / max(len(n1), len(n2))) >= 0.75
