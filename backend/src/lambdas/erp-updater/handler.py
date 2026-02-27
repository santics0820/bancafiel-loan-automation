"""
Lambda #6: ERP Updater
Updates application status in RDS after approval decision
"""
import json
import boto3
import os
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_insert, execute_query_single, create_application_history
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")

logger = setup_logger(__name__)
lambda_client = boto3.client('lambda')


def handler(event, context):
    try:
        application_id = event.get('application_id')
        status = event.get('status')          # 'APPROVED' or 'REJECTED'
        approved_by = event.get('approved_by')
        rejected_by = event.get('rejected_by')
        notes = event.get('notes', '')
        reason = event.get('reason', '')

        log_event(logger, 'updateERP_invoked', {
            'application_id': application_id,
            'status': status
        })

        if status == 'APPROVED':
            now_utc = datetime.now(UTC)
            execute_insert("""
                UPDATE applications
                SET status = 'APPROVED',
                    approved_by = %s,
                    approval_notes = %s,
                    processed_at = %s,
                    updated_at = %s
                WHERE id = %s
            """, (approved_by, notes, now_utc, now_utc, application_id))

            create_application_history(
                application_id, 'approved', approved_by or 'system',
                notes=notes,
                metadata={'status': 'APPROVED'}
            )

        elif status == 'REJECTED':
            now_utc = datetime.now(UTC)
            execute_insert("""
                UPDATE applications
                SET status = 'REJECTED',
                    rejected_by = %s,
                    rejection_reason = %s,
                    processed_at = %s,
                    updated_at = %s
                WHERE id = %s
            """, (rejected_by or 'system', reason, now_utc, now_utc, application_id))

            create_application_history(
                application_id, 'rejected', rejected_by or 'system',
                notes=reason,
                metadata={'status': 'REJECTED', 'reason': reason}
            )

        log_event(logger, 'erp_updated', {
            'application_id': application_id,
            'status': status
        })

        return {
            'statusCode': 200,
            'application_id': application_id,
            'status': status
        }

    except Exception as e:
        log_error(logger, 'updateERP_error', e)
        return {'statusCode': 500, 'error': str(e)}
