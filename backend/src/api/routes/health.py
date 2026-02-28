"""
API Routes: Health Check
GET /health - verifies API and DB connectivity
"""
import json
from datetime import datetime, UTC

try:
    from utils.database import execute_query_single
    from utils.response import success_response, error_response
except ImportError:
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}


def handler(event, context):
    """GET /health"""
    try:
        # DB ping
        result = execute_query_single("SELECT 1 AS ok, NOW() AS server_time")
        db_ok = result and result.get('ok') == 1

        return success_response({
            'status': 'healthy' if db_ok else 'degraded',
            'timestamp': datetime.now(UTC).isoformat(),
            'services': {
                'api': 'ok',
                'database': 'ok' if db_ok else 'error'
            },
            'version': '1.0.0'
        })

    except Exception as e:
        return error_response(f'Health check failed: {str(e)}', 503)
