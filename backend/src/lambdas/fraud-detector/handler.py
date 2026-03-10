"""
Lambda #4: Detect Fraud
Calls AWS Fraud Detector, scores risk, triggers Step Functions
"""
import json
import boto3
import os
import re
from datetime import datetime, timezone, UTC, date

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single, execute_query, create_application_history
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")

logger = setup_logger(__name__)
fraud_detector_client = boto3.client('frauddetector')
stepfunctions_client = boto3.client('stepfunctions')


def handler(event, context):
    try:
        application_id = event.get('application_id')

        log_event(logger, 'detectFraud_invoked', {'application_id': application_id})

        # Get application + customer data
        app_data = execute_query_single("""
            SELECT a.*, c.curp, c.email, c.phone, c.full_name, c.date_of_birth
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        if not app_data:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Application not found'})}

        # Guard: skip if fraud check already completed (prevents double execution)
        already_done = execute_query_single(
            "SELECT id FROM application_history WHERE application_id = %s AND action = 'fraud_check_completed'",
            (application_id,)
        )
        if already_done:
            log_event(logger, 'detectFraud_skipped_duplicate', {'application_id': application_id})
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed'})}

        # Try AWS Fraud Detector, fallback to rule-based
        fraud_score, risk_level, reasons = run_fraud_detection(app_data, application_id)
        dup_count = count_duplicate_applications(app_data['customer_id'], application_id)

        # Save fraud check result (upsert — detectFraud may run multiple times per application)
        execute_insert("""
            INSERT INTO fraud_checks
            (application_id, fraud_score, risk_level, fraud_reasons, duplicate_applications_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (application_id) DO UPDATE
            SET fraud_score = EXCLUDED.fraud_score,
                risk_level = EXCLUDED.risk_level,
                fraud_reasons = EXCLUDED.fraud_reasons,
                duplicate_applications_count = EXCLUDED.duplicate_applications_count
        """, (
            application_id,
            fraud_score,
            risk_level,
            json.dumps(reasons),
            dup_count,
        ))

        # Update application with fraud results
        execute_insert("""
            UPDATE applications
            SET fraud_score = %s, fraud_risk_level = %s, updated_at = %s
            WHERE id = %s
        """, (fraud_score, risk_level, datetime.now(UTC), application_id))

        create_application_history(
            application_id, 'fraud_check_completed', 'system',
            notes=f'Fraud score: {fraud_score} | Risk: {risk_level}',
            metadata={'fraud_score': fraud_score, 'risk_level': risk_level, 'reasons': reasons}
        )

        log_event(logger, 'fraud_check_complete', {
            'application_id': application_id,
            'fraud_score': fraud_score,
            'risk_level': risk_level
        })

        # Start Step Functions workflow
        workflow_arn = os.environ.get('LOAN_WORKFLOW_ARN')
        if workflow_arn:
            stepfunctions_client.start_execution(
                stateMachineArn=workflow_arn,
                name=f"loan-{application_id[:8]}-{int(datetime.now().timestamp())}",
                input=json.dumps({
                    'application_id': application_id,
                    'fraud_score': fraud_score,
                    'fraud_risk_level': risk_level
                })
            )
            log_event(logger, 'step_functions_started', {'application_id': application_id})

        return {
            'statusCode': 200,
            'body': json.dumps({
                'fraud_score': fraud_score,
                'risk_level': risk_level,
                'reasons': reasons
            })
        }

    except Exception as e:
        log_error(logger, 'detectFraud_error', e)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def run_fraud_detection(app_data, application_id):
    """Try AWS Fraud Detector, fallback to rules-based scoring"""
    try:
        response = fraud_detector_client.get_event_prediction(
            detectorId='bancafiel_loan_fraud_detector',
            eventId=str(application_id),
            eventTypeName='loan_application',
            entities=[{'entityType': 'customer', 'entityId': str(app_data['customer_id'])}],
            eventTimestamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            eventVariables={
                'email': app_data.get('email', ''),
                'phone': app_data.get('phone', ''),
                'curp': app_data.get('curp', ''),
                'loan_amount': str(app_data.get('loan_amount', 0)),
                'ip_address': '0.0.0.0'
            }
        )
        scores = response.get('modelScores', [])
        raw_score = scores[0]['scores']['default'] if scores else 0
        fraud_score = round(raw_score * 10, 2)  # Scale 0-100 → 0-1000
        reasons = [r['ruleId'] for r in response.get('ruleResults', [])]
        risk_level = score_to_risk(fraud_score)
        return fraud_score, risk_level, reasons

    except Exception as e:
        logger.warning(f"AWS Fraud Detector unavailable, using rule-based: {e}")
        return rule_based_fraud_score(app_data)


def rule_based_fraud_score(app_data):
    """Fallback: simple rule-based fraud scoring"""
    score = 100
    reasons = []

    # Rule 1: Debt-to-income ratio
    income = float(app_data.get('monthly_income') or 0)
    loan_amount = float(app_data.get('loan_amount') or 0)
    if income > 0:
        dti = loan_amount / (income * 12)
        if dti > 0.6:
            score += 300
            reasons.append('high_debt_to_income_ratio')
        elif dti > 0.4:
            score += 150
            reasons.append('elevated_debt_to_income_ratio')

    # Rule 2: High loan amount (new customer)
    if loan_amount > 100000:
        score += 200
        reasons.append('high_loan_amount')

    # Rule 3: Duplicate pending apps
    dups = count_duplicate_applications(app_data['customer_id'], app_data['id'])
    if dups > 0:
        score += 400
        reasons.append(f'duplicate_applications_found:{dups}')

    # Rule 4: Age under 18 — hard block (can't sign contracts in Mexico)
    dob = app_data.get('date_of_birth')
    applicant_age = compute_age(dob)
    if applicant_age is not None and applicant_age < 18:
        score += 900  # Guarantees HIGH regardless of other rules
        reasons.append(f'applicant_under_18:age={applicant_age}')

    # Rule 5: CURP vs DOB cross-check (CURP encodes YYMMDD at positions 4-9)
    curp = app_data.get('curp', '')
    if curp and len(curp) >= 10 and dob:
        if not curp_dob_match(curp, dob):
            score += 400
            reasons.append('curp_dob_mismatch')

    # Rule 6: INE expired
    expiry_raw = get_extracted_field(app_data.get('id'), 'expiry_date')
    if expiry_raw and is_document_expired(expiry_raw):
        score += 200
        reasons.append('ine_expired')

    # Rule 7: Address mismatch between INE and proof of address
    ine_address = get_extracted_field(app_data.get('id'), 'address', doc_type='INE')
    poa_address = get_extracted_field(app_data.get('id'), 'address', doc_type='PROOF_OF_ADDRESS')
    if ine_address and poa_address and not names_similar(ine_address, poa_address):
        score += 300
        reasons.append('address_mismatch_ine_vs_proof_of_address')

    # Rule 8: Proof of address older than 90 days (CNBV regulation)
    poa_date_raw = get_extracted_field(app_data.get('id'), 'document_date', doc_type='PROOF_OF_ADDRESS')
    if poa_date_raw and is_document_too_old(poa_date_raw, max_days=90):
        score += 150
        reasons.append('proof_of_address_older_than_90_days')

    # Rule 9: Same CURP rejected in last 30 days
    if curp and was_recently_rejected(curp, app_data.get('id')):
        score += 400
        reasons.append('recent_rejection_same_curp')

    score = min(score, 1000)
    return score, score_to_risk(score), reasons


def score_to_risk(score):
    if score >= 700:
        return 'HIGH'
    elif score >= 300:
        return 'MEDIUM'
    return 'LOW'


def compute_age(dob):
    """Return age in years from a date object or ISO string (YYYY-MM-DD), or None."""
    if not dob:
        return None
    try:
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return None


def curp_dob_match(curp, dob):
    """
    CURP positions 4-9 encode YYMMDD.
    dob is a date object or ISO string (YYYY-MM-DD).
    Returns True if they agree (within century ambiguity).
    """
    try:
        if isinstance(dob, str):
            dob = date.fromisoformat(dob)
        curp_yy = curp[4:6]
        curp_mm = curp[6:8]
        curp_dd = curp[8:10]
        return (
            curp_mm == f"{dob.month:02d}" and
            curp_dd == f"{dob.day:02d}" and
            curp_yy == f"{dob.year % 100:02d}"
        )
    except Exception:
        return True  # Can't verify → don't penalise


def is_document_expired(date_str):
    """Returns True if DD/MM/YYYY date is in the past."""
    try:
        exp = datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
        return exp < date.today()
    except Exception:
        return False


def is_document_too_old(date_str, max_days=90):
    """Returns True if DD/MM/YYYY date is older than max_days ago."""
    try:
        doc_date = datetime.strptime(date_str.strip(), '%d/%m/%Y').date()
        return (date.today() - doc_date).days > max_days
    except Exception:
        return False


def names_similar(name1, name2):
    """True if names share ≥75% characters (ignoring whitespace, case)."""
    n1 = ''.join(name1.lower().split())
    n2 = ''.join(name2.lower().split())
    shorter = min(len(n1), len(n2))
    if shorter == 0:
        return False
    matches = sum(c1 == c2 for c1, c2 in zip(n1, n2))
    return (matches / max(len(n1), len(n2))) >= 0.75


def get_extracted_field(application_id, field_name, doc_type=None):
    """Fetch a single extracted field value for an application, optionally filtered by doc_type."""
    try:
        if doc_type:
            row = execute_query_single("""
                SELECT ed.field_value
                FROM extracted_data ed
                JOIN documents d ON ed.document_id = d.id
                WHERE d.application_id = %s
                  AND d.document_type = %s
                  AND ed.field_name = %s
                LIMIT 1
            """, (application_id, doc_type, field_name))
        else:
            row = execute_query_single("""
                SELECT ed.field_value
                FROM extracted_data ed
                JOIN documents d ON ed.document_id = d.id
                WHERE d.application_id = %s
                  AND ed.field_name = %s
                ORDER BY ed.extracted_at DESC
                LIMIT 1
            """, (application_id, field_name))
        return row['field_value'] if row else None
    except Exception:
        return None


def was_recently_rejected(curp, exclude_application_id, days=30):
    """True if the same CURP had a REJECTED application in the last 30 days."""
    try:
        row = execute_query_single("""
            SELECT COUNT(*) AS count
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE c.curp = %s
              AND a.id != %s
              AND a.status = 'REJECTED'
              AND a.updated_at >= NOW() - INTERVAL '30 days'
        """, (curp, exclude_application_id))
        return (row['count'] if row else 0) > 0
    except Exception:
        return False


def count_duplicate_applications(customer_id, exclude_id):
    result = execute_query_single("""
        SELECT COUNT(*) as count FROM applications
        WHERE customer_id = %s AND id != %s AND status = 'PENDING'
    """, (customer_id, exclude_id))
    return result['count'] if result else 0
