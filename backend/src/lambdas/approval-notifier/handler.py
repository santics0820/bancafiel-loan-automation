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
ses_client = boto3.client('ses', region_name='us-east-1')
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

        # Send email directly via SES
        approver_email = os.environ.get('APPROVER_EMAIL')
        sender_email = os.environ.get('SENDER_EMAIL', 'bancafiel.noreply@gmail.com')
        frontend_url = os.environ.get('FRONTEND_URL', 'https://bancafiel.com')

        if approver_email:
            customer_name = app['full_name'].title() if app else 'Unknown'
            loan_amount_fmt = f"${float(app['loan_amount']):,.0f} MXN" if app else 'N/A'
            risk_level = (app['fraud_risk_level'] or 'low').lower() if app else 'low'
            risk_score = app['fraud_score'] if app else 0
            risk_color = '#f87171' if risk_level == 'high' else '#fbbf24' if risk_level in ('medium', 'med') else '#6ee7b7'
            risk_label = 'ALTO' if risk_level == 'high' else 'MEDIO' if risk_level in ('medium', 'med') else 'BAJO'
            review_url = f"{frontend_url}/dashboard/applications/{application_id}"
            short_id = str(application_id)[:8].upper()

            html_body = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#05070a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#05070a;padding:40px 16px;">
    <tr><td align="center">
      <table width="580" cellpadding="0" cellspacing="0" border="0" style="max-width:580px;width:100%;">
        <!-- Logo -->
        <tr><td align="center" style="padding-bottom:28px;">
          <table cellpadding="0" cellspacing="0" border="0"><tr>
            <td valign="middle" style="padding-right:10px;">
              <div style="width:32px;height:32px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#f1f5f9 0%,#cbd5e1 35%,#64748b 65%,#334155 100%);box-shadow:0 4px 16px rgba(148,163,184,0.35);"></div>
            </td>
            <td valign="middle"><span style="font-size:22px;font-weight:800;letter-spacing:0.06em;color:#ffffff;">BANCAFIEL</span></td>
          </tr></table>
        </td></tr>
        <!-- Card -->
        <tr><td style="background:#0f1218;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
          <!-- Badge -->
          <div style="display:inline-block;background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.3);border-radius:100px;padding:6px 16px;margin-bottom:20px;">
            <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#fbbf24;">⚡ &nbsp;Requiere revisión</span>
          </div>
          <h1 style="margin:0 0 8px;font-size:24px;font-weight:800;color:#ffffff;">Nueva solicitud pendiente</h1>
          <p style="margin:0 0 28px;font-size:15px;color:#94a3b8;line-height:1.6;">Se recibió una nueva solicitud de crédito que requiere tu aprobación.</p>
          <!-- Details -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Cliente</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#ffffff;">{customer_name}</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Monto solicitado</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#ffffff;">{loan_amount_fmt}</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Riesgo de fraude</td>
                <td align="right" style="font-size:14px;font-weight:700;color:{risk_color};">{risk_label} ({risk_score})</td>
              </tr></table>
            </td></tr>
            <tr><td style="padding:8px 0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
                <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">Folio</td>
                <td align="right" style="font-size:14px;font-weight:700;color:#e2e8f0;">{short_id}</td>
              </tr></table>
            </td></tr>
          </table>
          <!-- CTA -->
          <div style="text-align:center;margin-top:32px;">
            <a href="{review_url}" style="display:inline-block;background:linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%);color:#0f172a;font-size:14px;font-weight:800;letter-spacing:0.04em;text-decoration:none;padding:16px 40px;border-radius:14px;">
              Revisar solicitud →
            </a>
          </div>
        </td></tr>
        <!-- Footer -->
        <tr><td align="center" style="padding-top:28px;">
          <p style="margin:0;font-size:12px;color:#475569;line-height:1.6;">
            BancaFiel — Sistema interno de crédito.<br/>
            <a href="mailto:soporte@bancafiel.com" style="color:#60a5fa;text-decoration:none;">soporte@bancafiel.com</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

            ses_client.send_email(
                Source=sender_email,
                Destination={'ToAddresses': [approver_email]},
                Message={
                    'Subject': {'Data': f'[BancaFiel] Nueva solicitud — {customer_name}', 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}},
                }
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
