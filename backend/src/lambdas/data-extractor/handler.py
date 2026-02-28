"""
Lambda #2: Extract Data
Triggered by SNS (from Textract) -> Extracts structured data from documents
"""
import json
import boto3
import re
import unicodedata
from datetime import datetime, timezone

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
                datetime.now(timezone.utc)
            ))

        # Update document status
        update_query = """
            UPDATE documents
            SET textract_status = %s, processed_at = %s
            WHERE id = %s
        """
        execute_insert(update_query, ('SUCCEEDED', datetime.now(timezone.utc), document_id))

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
            'body': json.dumps({'error': 'Internal server error'})
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

    for line in lines:
        text = normalize_text(line['text'])
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
        if 'DOMICILIO' in text or 'DIRECCION' in text:
            address = extract_after_label(text, ['DOMICILIO', 'DIRECCION'])
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


def _pick_best(best, candidate):
    if not candidate:
        return best
    if not best:
        return candidate
    return candidate if candidate[1] >= best[1] else best


def _extract_dates(text):
    return re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}', text)


def _clean_digits(value):
    return re.sub(r'\D', '', value or '')


def extract_bank_statement_fields(lines):
    """Extract data from bank statement"""
    fields = {}
    bank_name = None
    clabe = None
    account_number = None
    rfc = None
    period_start = None
    period_end = None
    balance = None
    avg_balance = None
    total_deposits = None
    total_withdrawals = None

    bank_keywords = [
        'BBVA MEXICO', 'BBVA', 'BANAMEX', 'CITIBANAMEX', 'BANORTE', 'SANTANDER', 'HSBC',
        'SCOTIABANK', 'BANBAJIO', 'BANCO AZTECA', 'AZTECA', 'INBURSA', 'BANREGIO', 'BANCOMER'
    ]

    normalized = [
        {'raw': line['text'], 'norm': normalize_text(line['text']), 'confidence': line['confidence']}
        for line in lines
    ]

    prev_period_label = False
    for idx, line in enumerate(normalized):
        text = line['norm']
        confidence = line['confidence']

        for kw in bank_keywords:
            if kw in text:
                bank_name = _pick_best(bank_name, (kw, confidence))
                break
        if not bank_name and re.search(r'\bBANCO\b', text):
            bank_name = _pick_best(bank_name, (text, confidence))

        if 'CLABE' in text or 'INTERBANCARIA' in text:
            clabe_match = re.search(r'\bCLABE(?: INTERBANCARIA)?\b[:\s-]*([0-9 ]{18,})\b', text)
            if not clabe_match:
                clabe_match = re.search(r'\b[0-9 ]{18,}\b', text)
            if clabe_match:
                clabe_value = _clean_digits(clabe_match.group(1) if clabe_match.lastindex else clabe_match.group(0))
                if len(clabe_value) == 18:
                    clabe = _pick_best(clabe, (clabe_value, confidence))

        if 'CUENTA' in text or 'CTA' in text:
            acct_match = re.search(r'\b(?:NO\.?\s*)?(?:CUENTA|CTA)(?:\s*BANCARIA)?\b[:\s-]*([0-9 ]{10,20})\b', text)
            if acct_match:
                acct_value = _clean_digits(acct_match.group(1))
                if acct_value and acct_value != (clabe[0] if clabe else None):
                    account_number = _pick_best(account_number, (acct_value, confidence))

        if 'RFC' in text or not rfc:
            rfc_match = re.search(r'\b[A-Z&]{3,4}\d{6}[A-Z0-9]{3}\b', text)
            if rfc_match:
                rfc = _pick_best(rfc, (rfc_match.group(0), confidence))

        period_label = 'PERIODO' in text or ('DEL' in text and 'AL' in text)
        if period_label or prev_period_label:
            dates = _extract_dates(text)
            if len(dates) >= 2:
                period_start = _pick_best(period_start, (dates[0], confidence))
                period_end = _pick_best(period_end, (dates[1], confidence))
            elif idx + 1 < len(normalized) and period_label:
                dates = _extract_dates(normalized[idx + 1]['norm'])
                if len(dates) >= 2:
                    period_start = _pick_best(period_start, (dates[0], normalized[idx + 1]['confidence']))
                    period_end = _pick_best(period_end, (dates[1], normalized[idx + 1]['confidence']))
        prev_period_label = period_label

        if any(k in text for k in ['SALDO FINAL', 'SALDO ACTUAL', 'SALDO TOTAL', 'BALANCE']):
            amount = extract_amount(text)
            if amount:
                balance = _pick_best(balance, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    balance = _pick_best(balance, (amount, normalized[idx + 1]['confidence']))

        if any(k in text for k in ['SALDO PROMEDIO', 'PROMEDIO']):
            amount = extract_amount(text)
            if amount:
                avg_balance = _pick_best(avg_balance, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    avg_balance = _pick_best(avg_balance, (amount, normalized[idx + 1]['confidence']))

        if any(k in text for k in ['DEPOSITOS', 'ABONOS', 'INGRESOS', 'TOTAL ABONOS']):
            amount = extract_amount(text)
            if amount:
                total_deposits = _pick_best(total_deposits, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    total_deposits = _pick_best(total_deposits, (amount, normalized[idx + 1]['confidence']))

        if any(k in text for k in ['RETIROS', 'CARGOS', 'EGRESOS', 'TOTAL CARGOS']):
            amount = extract_amount(text)
            if amount:
                total_withdrawals = _pick_best(total_withdrawals, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    total_withdrawals = _pick_best(total_withdrawals, (amount, normalized[idx + 1]['confidence']))

    if bank_name:
        fields['bank_name'] = {'value': bank_name[0], 'confidence': bank_name[1]}
    if clabe:
        fields['clabe'] = {'value': clabe[0], 'confidence': clabe[1]}
    if account_number:
        fields['account_number'] = {'value': account_number[0], 'confidence': account_number[1]}
    if rfc:
        fields['rfc'] = {'value': rfc[0], 'confidence': rfc[1]}
    if period_start:
        fields['period_start'] = {'value': period_start[0], 'confidence': period_start[1]}
    if period_end:
        fields['period_end'] = {'value': period_end[0], 'confidence': period_end[1]}
    if balance:
        fields['balance'] = {'value': balance[0], 'confidence': balance[1]}
    if avg_balance:
        fields['average_balance'] = {'value': avg_balance[0], 'confidence': avg_balance[1]}
    if total_deposits:
        fields['total_deposits'] = {'value': total_deposits[0], 'confidence': total_deposits[1]}
    if total_withdrawals:
        fields['total_withdrawals'] = {'value': total_withdrawals[0], 'confidence': total_withdrawals[1]}

    return fields


def extract_income_fields(lines):
    """Extract income information"""
    fields = {}
    employer = None
    rfc = None
    period_start = None
    period_end = None
    payment_frequency = None
    net_income = None
    gross_income = None

    normalized = [
        {'raw': line['text'], 'norm': normalize_text(line['text']), 'confidence': line['confidence']}
        for line in lines
    ]

    prev_period_label = False
    for idx, line in enumerate(normalized):
        text = line['norm']
        confidence = line['confidence']

        if any(k in text for k in ['EMPRESA', 'PATRON', 'RAZON SOCIAL', 'EMPLEADOR']):
            value = extract_after_label(text, ['EMPRESA', 'PATRON', 'RAZON SOCIAL', 'EMPLEADOR'])
            value_conf = confidence
            if not value and idx + 1 < len(normalized):
                value = normalized[idx + 1]['norm']
                value_conf = normalized[idx + 1]['confidence']
            if value:
                employer = _pick_best(employer, (value, value_conf))

        if 'RFC' in text or not rfc:
            rfc_match = re.search(r'\b[A-Z&]{3,4}\d{6}[A-Z0-9]{3}\b', text)
            if rfc_match:
                rfc = _pick_best(rfc, (rfc_match.group(0), confidence))

        if not payment_frequency:
            for freq in ['SEMANAL', 'QUINCENAL', 'MENSUAL']:
                if freq in text:
                    payment_frequency = (freq, confidence)
                    break

        period_label = 'PERIODO' in text or ('DEL' in text and 'AL' in text)
        if period_label or prev_period_label:
            dates = _extract_dates(text)
            if len(dates) >= 2:
                period_start = _pick_best(period_start, (dates[0], confidence))
                period_end = _pick_best(period_end, (dates[1], confidence))
        prev_period_label = period_label

        if any(k in text for k in ['NETO', 'TOTAL NETO', 'NETO A PAGAR', 'SUELDO NETO']):
            amount = extract_amount(text)
            if amount:
                net_income = _pick_best(net_income, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    net_income = _pick_best(net_income, (amount, normalized[idx + 1]['confidence']))

        if any(k in text for k in ['BRUTO', 'TOTAL PERCEPCIONES', 'PERCEPCIONES']):
            amount = extract_amount(text)
            if amount:
                gross_income = _pick_best(gross_income, (amount, confidence))
            elif idx + 1 < len(normalized):
                amount = extract_amount(normalized[idx + 1]['norm'])
                if amount:
                    gross_income = _pick_best(gross_income, (amount, normalized[idx + 1]['confidence']))

    if employer:
        fields['employer_name'] = {'value': employer[0], 'confidence': employer[1]}
    if rfc:
        fields['rfc'] = {'value': rfc[0], 'confidence': rfc[1]}
    if payment_frequency:
        fields['payment_frequency'] = {'value': payment_frequency[0], 'confidence': payment_frequency[1]}
    if period_start:
        fields['period_start'] = {'value': period_start[0], 'confidence': period_start[1]}
    if period_end:
        fields['period_end'] = {'value': period_end[0], 'confidence': period_end[1]}
    if net_income:
        fields['net_income'] = {'value': net_income[0], 'confidence': net_income[1]}
    if gross_income:
        fields['gross_income'] = {'value': gross_income[0], 'confidence': gross_income[1]}

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
                value = parts[1].strip()
                value = re.sub(r'^[\s:.-]+', '', value)
                return value

    return None


def extract_date(text):
    """Extract date from text (DD/MM/YYYY or DD-MM-YYYY)"""
    pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def _maybe_fix_mojibake(text):
    if not text:
        return text
    if not any(ch in text for ch in ['Ã', 'Â', 'â', '�']):
        return text
    try:
        fixed = text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    original_bad = sum(text.count(ch) for ch in ['Ã', 'Â', 'â', '�'])
    fixed_bad = sum(fixed.count(ch) for ch in ['Ã', 'Â', 'â', '�'])
    return fixed if fixed_bad < original_bad else text


def normalize_text(text):
    """Normalize text for parsing (fix mojibake, uppercase, remove accents, collapse spaces)."""
    text = _maybe_fix_mojibake(text)
    text = text.upper()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_amount(text):
    """Extract numeric amount from text and normalize to a plain number string."""
    match = re.search(r'\$?\s*[\d.,]+', text)
    if not match:
        return None
    value = match.group(0)
    value = value.replace('$', '').replace(' ', '')
    last_comma = value.rfind(',')
    last_dot = value.rfind('.')
    decimal_sep = None
    if last_comma > last_dot:
        if len(value) - last_comma - 1 == 2:
            decimal_sep = ','
    elif last_dot > last_comma:
        if len(value) - last_dot - 1 == 2:
            decimal_sep = '.'
    if decimal_sep == ',':
        value = value.replace('.', '')
        value = value.replace(',', '.')
    else:
        value = value.replace(',', '')
    return value
