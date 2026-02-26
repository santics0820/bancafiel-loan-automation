"""
Lambda #5: Approval Notifier
Stores Step Functions task token, notifies approver via SNS
Also handles POST /api/loans/{id}/approve and /reject (API Gateway events)
"""
import json
import boto3
import os
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single, create_application_history
    from utils.response import success_response, error_response, not_found_response
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}
    def not_found_response(m='Not found'): return {'statusCode': 404, 'body': json.dumps({'error': m})}

logger = setup_logger(__name__)
sns_client = boto3.client('sns')
stepfunctions_client = boto3.client('stepfunctions')


def handler(event, context):
    """Router: handles both Step Functions payload and API Gateway requests"""

    # API Gateway requests (approve/reject)
    if event.get('httpMethod'):
        path = event.get('path', '')
        if '/approve' in path:
            return handle_approve(event)
        elif '/reject' in path:
            return handle_reject(event)

    # Step Functions invocation (store task token + notify)
    return handle_notify_approver(event)


def handle_notify_approver(event):
    """Store task token and send SNS notification to approver"""
    try:
        application_id = event.get('application_id')
        task_token = event.get('task_token')
        approver_type = event.get('approver_type', 'analyst')

        # Store task token in DB
        execute_insert("""
            INSERT INTO approval_tokens (application_id, task_token, status)
            VALUES (%s, %s, 'PENDING')
            ON CONFLICT (application_id) DO UPDATE
            SET task_token = EXCLUDED.task_token,
                status = 'PENDING',
                created_at = CURRENT_TIMESTAMP
        """, (application_id, task_token))

        # Get application summary for notification
        app = execute_query_single("""
            SELECT a.loan_amount, a.fraud_score, a.fraud_risk_level, c.full_name
            FROM applications a JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        # Send SNS notification
        sns_topic_arn = os.environ.get('APPROVER_SNS_TOPIC_ARN')
        frontend_url = os.environ.get('FRONTEND_URL', 'https://bancafiel.com')

        if sns_topic_arn:
            message = (
                f"New loan application requires your review.\n\n"
                f"Customer: {app['full_name'] if app else 'Unknown'}\n"
                f"Amount: ${app['loan_amount']:,.2f} MXN\n"
                f"Fraud Risk: {app['fraud_risk_level']} (score: {app['fraud_score']})\n\n"
                f"Review: {frontend_url}/dashboard/applications/{application_id}"
            )
            sns_client.publish(
                TopicArn=sns_topic_arn,
                Subject=f'[BancaFiel] Loan Application Pending Approval',
                Message=message
            )

        create_application_history(
            application_id, 'approval_notification_sent', 'system',
            notes=f'Approver type: {approver_type}'
        )

        log_event(logger, 'approval_notification_sent', {
            'application_id': application_id,
            'approver_type': approver_type
        })

        # Lambda waits here — Step Functions waits for task token callback

    except Exception as e:
        log_error(logger, 'notify_approver_error', e)
        raise


def handle_approve(event):
    """POST /api/loans/{id}/approve - Resumes Step Functions with APPROVED"""
    try:
        application_id = event['pathParameters']['id']
        body = json.loads(event.get('body') or '{}')
        approved_by = body.get('approvedBy', 'unknown')
        notes = body.get('notes', '')

        token_row = execute_query_single(
            "SELECT task_token FROM approval_tokens WHERE application_id = %s AND status = 'PENDING'",
            (application_id,)
        )
        if not token_row:
            return not_found_response('Approval token not found or already processed')

        # Resume Step Functions
        stepfunctions_client.send_task_success(
            taskToken=token_row['task_token'],
            output=json.dumps({
                'application_id': application_id,
                'decision': 'APPROVED',
                'approved_by': approved_by,
                'notes': notes
            })
        )

        # Mark token as used
        execute_insert(
            "UPDATE approval_tokens SET status = 'APPROVED' WHERE application_id = %s",
            (application_id,)
        )

        log_event(logger, 'application_approved', {
            'application_id': application_id,
            'approved_by': approved_by
        })

        return success_response({
            'success': True,
            'loanId': application_id,
            'status': 'approved',
            'message': 'Application approved successfully',
            'timestamp': datetime.now(UTC).isoformat()
        })

    except Exception as e:
        log_error(logger, 'approve_error', e)
        return error_response(str(e), 500)


def handle_reject(event):
    """POST /api/loans/{id}/reject - Resumes Step Functions with REJECTED"""
    try:
        application_id = event['pathParameters']['id']
        body = json.loads(event.get('body') or '{}')
        rejected_by = body.get('rejectedBy', 'unknown')
        reason = body.get('reason', 'No reason provided')

        token_row = execute_query_single(
            "SELECT task_token FROM approval_tokens WHERE application_id = %s AND status = 'PENDING'",
            (application_id,)
        )
        if not token_row:
            return not_found_response('Approval token not found or already processed')

        stepfunctions_client.send_task_success(
            taskToken=token_row['task_token'],
            output=json.dumps({
                'application_id': application_id,
                'decision': 'REJECTED',
                'rejected_by': rejected_by,
                'reason': reason
            })
        )

        execute_insert(
            "UPDATE approval_tokens SET status = 'REJECTED' WHERE application_id = %s",
            (application_id,)
        )

        log_event(logger, 'application_rejected', {
            'application_id': application_id,
            'rejected_by': rejected_by
        })

        return success_response({
            'success': True,
            'loanId': application_id,
            'status': 'rejected',
            'message': 'Application rejected',
            'timestamp': datetime.now(UTC).isoformat()
        })

    except Exception as e:
        log_error(logger, 'reject_error', e)
        return error_response(str(e), 500)
