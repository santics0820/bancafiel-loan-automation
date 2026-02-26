"""
Lambda #4: Detect Fraud
Calls AWS Fraud Detector, scores risk, triggers Step Functions
"""
import json
import boto3
import os
from datetime import datetime, timezone, UTC

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
            SELECT a.*, c.curp, c.email, c.phone, c.full_name
            FROM applications a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        if not app_data:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Application not found'})}

        # Try AWS Fraud Detector, fallback to rule-based
        fraud_score, risk_level, reasons = run_fraud_detection(app_data, application_id)
        dup_count = count_duplicate_applications(app_data['customer_id'], application_id)

        # Save fraud check result
        execute_insert("""
            INSERT INTO fraud_checks
            (application_id, fraud_score, risk_level, fraud_reasons, duplicate_applications_count)
            VALUES (%s, %s, %s, %s, %s)
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

    score = min(score, 1000)
    return score, score_to_risk(score), reasons


def score_to_risk(score):
    if score >= 700:
        return 'HIGH'
    elif score >= 300:
        return 'MEDIUM'
    return 'LOW'


def count_duplicate_applications(customer_id, exclude_id):
    result = execute_query_single("""
        SELECT COUNT(*) as count FROM applications
        WHERE customer_id = %s AND id != %s AND status = 'PENDING'
    """, (customer_id, exclude_id))
    return result['count'] if result else 0
