"""
API Routes: Applications
Handlers for all /api/loans endpoints
"""
import json
import boto3
import os
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_query, execute_query_single, execute_insert
    from utils.response import success_response, error_response, not_found_response, created_response
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d, default=str)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}
    def not_found_response(m='Not found'): return {'statusCode': 404, 'body': json.dumps({'error': m})}
    def created_response(d, l=None): return {'statusCode': 201, 'body': json.dumps(d, default=str)}

logger = setup_logger(__name__)
s3_client = boto3.client('s3')


def get_application_status(event, context):
    """GET /api/loans/status?folio=&email="""
    try:
        params = event.get('queryStringParameters') or {}
        folio = (params.get('folio') or '').strip().upper()
        email = (params.get('email') or '').strip().lower()

        if not folio or not email:
            return error_response('folio y email requeridos', 400)

        app = execute_query_single("""
            SELECT a.id, a.status, a.loan_amount, a.created_at,
                   UPPER(LEFT(a.id::text, 8)) as folio,
                   COALESCE(c.full_name, a.applicant_name) as name,
                   a.fraud_risk_level as risk_level
            FROM applications a
            LEFT JOIN customers c ON a.customer_id = c.id
            WHERE UPPER(LEFT(a.id::text, 8)) = %s
              AND LOWER(COALESCE(c.email, a.applicant_email)) = %s
        """, (folio, email))

        if not app:
            return not_found_response('Solicitud no encontrada')

        history = execute_query("""
            SELECT action FROM application_history
            WHERE application_id = %s ORDER BY created_at ASC
        """, (str(app['id']),))

        actions = {h['action'] for h in (history or [])}

        def step_status(done_action, active_action=None):
            if done_action in actions:
                return 'done'
            if active_action and active_action in actions:
                return 'active'
            return 'pending'

        steps = [
            {'label': 'Solicitud recibida',        'status': 'done'},
            {'label': 'Verificación de identidad', 'status': step_status('validation_completed', 'document_processed')},
            {'label': 'Análisis de documentos',    'status': 'done' if ('approved' in actions or 'rejected' in actions) else step_status('fraud_checked', 'validation_completed')},
            {'label': 'Resolución final',          'status': 'done' if ('approved' in actions or 'rejected' in actions) else ('active' if 'fraud_checked' in actions else 'pending')},
        ]

        # If nothing is active yet, mark first pending as active
        if not any(s['status'] == 'active' for s in steps):
            for s in steps:
                if s['status'] == 'pending':
                    s['status'] = 'active'
                    break

        return success_response({
            'folio':      app['folio'],
            'status':     app['status'],
            'riskLevel':  app.get('risk_level'),
            'name':       app.get('name'),
            'loanAmount': app.get('loan_amount'),
            'steps':      steps,
        })

    except Exception as e:
        log_error(logger, 'get_application_status_error', e)
        return error_response('Error al obtener estado', 500)


def list_applications(event, context):
    """GET /api/loans?status=pending"""
    try:
        params = event.get('queryStringParameters') or {}
        status = params.get('status', 'pending').upper()

        rows = execute_query("""
            SELECT
                a.id, a.application_type, a.loan_amount, a.monthly_income,
                a.requested_date, a.status, a.fraud_score, a.credit_score,
                a.fraud_risk_level, a.credit_recommendation,
                c.full_name AS applicant_name,
                c.email AS applicant_email,
                fc.fraud_reasons
            FROM applications a
            LEFT JOIN customers c ON a.customer_id = c.id
            LEFT JOIN fraud_checks fc ON fc.application_id = a.id
            WHERE a.status = %s
            ORDER BY a.requested_date DESC
            LIMIT 100
        """, (status,))

        applications = [
            {
                'id': str(r['id']),
                'applicantName': r['applicant_name'],
                'applicantEmail': r['applicant_email'],
                'loanAmount': float(r['loan_amount']),
                'monthlyIncome': float(r['monthly_income']) if r['monthly_income'] else None,
                'requestedDate': r['requested_date'].isoformat() if r['requested_date'] else None,
                'status': r['status'].lower(),
                'fraudScore': float(r['fraud_score']) if r['fraud_score'] else None,
                'fraudRiskLevel': r['fraud_risk_level'].lower() if r['fraud_risk_level'] else None,
                'fraudReasons': r['fraud_reasons'] if r['fraud_reasons'] else [],
                'creditScore': r['credit_score'],
                'creditRecommendation': r['credit_recommendation']
            }
            for r in rows
        ]

        return success_response({'applications': applications, 'total': len(applications)})

    except Exception as e:
        log_error(logger, 'list_applications_error', e)
        return error_response('Failed to retrieve applications', 500)


def get_application(event, context):
    """GET /api/loans/{id}"""
    try:
        application_id = event['pathParameters']['id']

        app = execute_query_single("""
            SELECT a.*, c.full_name, c.email, c.curp, c.phone, c.address
            FROM applications a LEFT JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        if not app:
            return not_found_response('Application not found')

        documents = execute_query("""
            SELECT document_type, s3_bucket, s3_key
            FROM documents WHERE application_id = %s
        """, (application_id,))

        history = execute_query("""
            SELECT action, actor, notes, created_at
            FROM application_history WHERE application_id = %s
            ORDER BY created_at ASC
        """, (application_id,))

        extracted = execute_query("""
            SELECT ed.field_name, ed.field_value
            FROM extracted_data ed
            JOIN documents d ON ed.document_id = d.id
            WHERE d.application_id = %s
        """, (application_id,))

        fraud_check = execute_query_single("""
            SELECT fraud_reasons FROM fraud_checks WHERE application_id = %s
        """, (application_id,))

        return success_response({
            'id': str(app['id']),
            'applicantName': app['full_name'],
            'applicantEmail': app['email'],
            'curp': app['curp'],
            'phone': app['phone'],
            'address': app['address'],
            'loanAmount': float(app['loan_amount']),
            'monthlyIncome': float(app['monthly_income']) if app['monthly_income'] else None,
            'existingDebt': float(app['existing_debt']) if app['existing_debt'] else None,
            'requestedDate': app['requested_date'].isoformat() if app['requested_date'] else None,
            'status': app['status'].lower(),
            'fraudScore': float(app['fraud_score']) if app['fraud_score'] else None,
            'fraudRiskLevel': app['fraud_risk_level'].lower() if app['fraud_risk_level'] else None,
            'fraudReasons': fraud_check['fraud_reasons'] if fraud_check else [],
            'creditScore': app['credit_score'],
            'creditRecommendation': app['credit_recommendation'],
            'documents': [{'type': d['document_type'], 'url': f"s3://{d['s3_bucket']}/{d['s3_key']}"} for d in documents],
            'extractedData': {e['field_name']: e['field_value'] for e in extracted},
            'history': [
                {
                    'timestamp': h['created_at'].isoformat(),
                    'action': h['action'],
                    'user': h['actor'],
                    'notes': h['notes']
                }
                for h in history
            ]
        })

    except Exception as e:
        log_error(logger, 'get_application_error', e)
        return error_response('Failed to retrieve application', 500)


def submit_application(event, context):
    """POST /api/loans - Submit new application"""
    try:
        body = json.loads(event.get('body') or '{}')

        # Validate required fields
        required = ['applicantName', 'applicantEmail', 'loanAmount', 'applicationType']
        missing = [f for f in required if not body.get(f)]
        if missing:
            return error_response(f"Missing required fields: {', '.join(missing)}", 400)

        loan_amount = float(body['loanAmount'])
        application_type = body['applicationType'].upper()

        if application_type not in ('LOAN', 'CREDIT_CARD'):
            return error_response("applicationType must be 'LOAN' or 'CREDIT_CARD'", 400)

        # Create application record (customer linked later after OCR)
        result = execute_query("""
            INSERT INTO applications
            (application_type, loan_amount, monthly_income, existing_debt,
             applicant_name, applicant_email, applicant_phone, status, requested_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING', %s)
            RETURNING id
        """, (
            application_type,
            loan_amount,
            float(body.get('monthlyIncome') or 0),
            float(body.get('existingDebt') or 0),
            body.get('applicantName'),
            body.get('applicantEmail'),
            body.get('applicantPhone'),
            datetime.now(UTC)
        ))

        application_id = str(result[0]['id'])

        # Generate pre-signed S3 URLs for document uploads
        incoming_bucket = os.environ.get('INCOMING_BUCKET', '')
        upload_urls = {}

        doc_configs = {
            'ine':              {'ext': 'jpg',  'content_type': 'image/jpeg'},
            'proof_of_address': {'ext': 'pdf',  'content_type': 'application/pdf'},
            'bank_statement':   {'ext': 'pdf',  'content_type': 'application/pdf'},
        }
        for doc_type, cfg in doc_configs.items():
            if incoming_bucket:
                key = f"applications/{application_id}/{doc_type}.{cfg['ext']}"
                url = s3_client.generate_presigned_url(
                    'put_object',
                    Params={'Bucket': incoming_bucket, 'Key': key, 'ContentType': cfg['content_type']},
                    ExpiresIn=3600
                )
                upload_urls[doc_type] = {'url': url, 'key': key}

        log_event(logger, 'application_submitted', {
            'application_id': application_id,
            'type': application_type,
            'amount': loan_amount
        })

        return created_response({
            'applicationId': application_id,
            'status': 'pending',
            'message': 'Application submitted. Upload documents to the provided URLs.',
            'uploadUrls': upload_urls
        })

    except Exception as e:
        log_error(logger, 'submit_application_error', e)
        return error_response('Failed to submit application', 500)
