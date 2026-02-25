"""
API Routes: Analytics
Handler for GET /api/analytics
"""
import json
from datetime import datetime, timedelta

try:
    from utils.logger import setup_logger, log_error
    from utils.database import execute_query, execute_query_single
    from utils.response import success_response, error_response
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d, default=str)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}

logger = setup_logger(__name__)


def get_analytics(event, context):
    """GET /api/analytics?startDate=2026-02-01&endDate=2026-02-15"""
    try:
        params = event.get('queryStringParameters') or {}
        end_date = params.get('endDate', datetime.utcnow().date().isoformat())
        start_date = params.get('startDate', (datetime.utcnow() - timedelta(days=30)).date().isoformat())

        # Aggregate stats
        stats = execute_query_single("""
            SELECT
                COUNT(*) AS total_applications,
                SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected,
                SUM(CASE WHEN status = 'PENDING'  THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN fraud_risk_level = 'HIGH' THEN 1 ELSE 0 END) AS fraud_alerts,
                AVG(
                    CASE WHEN processed_at IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (processed_at - requested_date)) / 60
                    ELSE NULL END
                ) AS avg_processing_minutes
            FROM applications
            WHERE requested_date::date BETWEEN %s AND %s
        """, (start_date, end_date))

        total = int(stats['total_applications'] or 0)
        approved = int(stats['approved'] or 0)

        # Volume by day
        daily = execute_query("""
            SELECT
                DATE(requested_date) AS date,
                COUNT(*) AS applications
            FROM applications
            WHERE requested_date::date BETWEEN %s AND %s
            GROUP BY DATE(requested_date)
            ORDER BY date
        """, (start_date, end_date))

        return success_response({
            'totalApplications': total,
            'approved': approved,
            'rejected': int(stats['rejected'] or 0),
            'pending': int(stats['pending'] or 0),
            'approvalRate': round(approved / total, 2) if total > 0 else 0,
            'averageProcessingTime': round(float(stats['avg_processing_minutes'] or 0), 1),
            'fraudAlerts': int(stats['fraud_alerts'] or 0),
            'volumeByDay': [
                {'date': str(r['date']), 'applications': int(r['applications'])}
                for r in daily
            ]
        })

    except Exception as e:
        log_error(logger, 'get_analytics_error', e)
        return error_response('Failed to retrieve analytics', 500)
