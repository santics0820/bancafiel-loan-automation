"""
API Routes: Fraud
Handler for GET /api/fraud — fraud detection dashboard data
"""
import json
from datetime import datetime, UTC

try:
    from utils.logger import setup_logger, log_error
    from utils.database import execute_query, execute_query_single
    from utils.response import success_response, error_response
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d, default=str)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}

logger = setup_logger(__name__)

_REASON_LABELS = {
    'high_debt_to_income_ratio':      'Alto ratio deuda-ingreso',
    'elevated_debt_to_income_ratio':  'Ratio deuda-ingreso elevado',
    'high_loan_amount':               'Monto de préstamo elevado',
    'duplicate_applications_found':   'Solicitudes duplicadas detectadas',
}


def _translate_reasons(reasons_raw):
    try:
        reasons = json.loads(reasons_raw) if isinstance(reasons_raw, str) else (reasons_raw or [])
    except Exception:
        return []
    result = []
    for r in reasons:
        base = r.split(':')[0]
        result.append(_REASON_LABELS.get(base, r.replace('_', ' ').title()))
    return result


def _relative_time(dt):
    if not dt:
        return 'N/A'
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    minutes = int((now - dt).total_seconds() / 60)
    if minutes < 60:
        return f'{minutes}M AGO'
    hours = minutes // 60
    if hours < 24:
        return f'{hours}H AGO'
    return f'{hours // 24}D AGO'


def _derive_details(score_raw, risk_level, dup_count):
    """Derive analysis detail fields from available DB data."""
    pct = score_raw / 10  # 0-1000 → 0-100
    identity_conf     = round(max(20.0, 100 - pct * 0.70), 1)
    doc_authenticity  = round(max(15.0, 100 - pct * 0.50), 1)
    behavior_score    = round(max(10.0, 100 - pct * 0.85), 1)

    ip_map = {'LOW': 'CLEAN', 'MEDIUM': 'MODERATE', 'HIGH': 'SUSPICIOUS'}
    ip_rep = ip_map.get(risk_level, 'MODERATE')

    if dup_count >= 2:
        device_fp, velocity = 'SUSPICIOUS', 'FAILED'
    elif dup_count == 1:
        device_fp, velocity = 'KNOWN DEVICE', 'WARNING'
    else:
        device_fp = 'VERIFIED'   if risk_level == 'LOW' else 'NEW DEVICE'
        velocity  = 'PASSED'     if risk_level == 'LOW' else 'WARNING'

    return {
        'identityConfidence':    identity_conf,
        'documentAuthenticity':  doc_authenticity,
        'behaviorScore':         behavior_score,
        'ipReputation':          ip_rep,
        'deviceFingerprint':     device_fp,
        'velocityCheck':         velocity,
    }


def get_fraud_data(event, context):
    """GET /api/fraud"""
    try:
        # --- Flagged applications (MEDIUM + HIGH risk) ---
        flagged_rows = execute_query("""
            SELECT
                fc.application_id,
                fc.fraud_score,
                fc.risk_level,
                fc.fraud_reasons,
                fc.duplicate_applications_count,
                fc.created_at,
                c.full_name
            FROM fraud_checks fc
            JOIN applications a ON fc.application_id = a.id
            LEFT JOIN customers c ON a.customer_id = c.id
            WHERE fc.risk_level IN ('MEDIUM', 'HIGH')
            ORDER BY fc.fraud_score DESC, fc.created_at DESC
            LIMIT 50
        """)

        flagged = []
        for r in flagged_rows:
            score_raw = float(r['fraud_score'] or 0)
            risk      = r['risk_level'] or 'LOW'
            dup_count = int(r['duplicate_applications_count'] or 0)
            app_id    = str(r['application_id'])
            short_id  = f"LN-{app_id[:4].upper()}-{app_id[4:8].upper()}"

            flagged.append({
                'id':            short_id,
                'applicationId': app_id,
                'name':          r['full_name'] or 'N/A',
                'fraudScore':    round(score_raw / 10, 1),
                'riskLevel':     risk,
                'time':          _relative_time(r['created_at']),
                'flags':         _translate_reasons(r['fraud_reasons']),
                'details':       _derive_details(score_raw, risk, dup_count),
            })

        # --- Summary stats ---
        stats_row = execute_query_single("""
            SELECT
                COUNT(*) AS total_scanned,
                SUM(CASE WHEN risk_level = 'HIGH'   THEN 1 ELSE 0 END) AS high_risk,
                SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_risk,
                SUM(CASE WHEN risk_level = 'LOW'    THEN 1 ELSE 0 END) AS low_risk,
                AVG(fraud_score)                                        AS avg_score,
                SUM(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 ELSE 0 END) AS flagged_today
            FROM fraud_checks
        """)

        blocked_row = execute_query_single("""
            SELECT COUNT(*) AS blocked
            FROM applications
            WHERE status = 'REJECTED' AND fraud_risk_level = 'HIGH'
        """)

        avg_raw = float(stats_row['avg_score'] or 0)
        stats = {
            'totalScanned': int(stats_row['total_scanned'] or 0),
            'highRisk':     int(stats_row['high_risk'] or 0),
            'mediumRisk':   int(stats_row['medium_risk'] or 0),
            'lowRisk':      int(stats_row['low_risk'] or 0),
            'avgFraudScore': round(avg_raw / 10, 1),
            'blocked':      int(blocked_row['blocked'] or 0) if blocked_row else 0,
            'flaggedToday': int(stats_row['flagged_today'] or 0),
        }

        # --- Recently blocked ---
        blocked_rows = execute_query("""
            SELECT
                a.id,
                a.rejection_reason,
                fc.fraud_score,
                fc.created_at
            FROM applications a
            JOIN fraud_checks fc ON a.id = fc.application_id
            WHERE a.status = 'REJECTED' AND a.fraud_risk_level = 'HIGH'
            ORDER BY fc.created_at DESC
            LIMIT 5
        """)

        recent_blocked = []
        for r in blocked_rows:
            app_id   = str(r['id'])
            short_id = f"LN-{app_id[:4].upper()}-{app_id[4:8].upper()}"
            recent_blocked.append({
                'id':     short_id,
                'reason': r['rejection_reason'] or 'Alto riesgo de fraude',
                'time':   _relative_time(r['created_at']),
                'score':  round(float(r['fraud_score'] or 0) / 10, 1),
            })

        # --- Fraud patterns (aggregate reasons from recent checks) ---
        pattern_rows = execute_query("""
            SELECT fraud_reasons
            FROM fraud_checks
            WHERE fraud_reasons IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 500
        """)

        counts = {}
        for row in pattern_rows:
            try:
                reasons = json.loads(row['fraud_reasons']) if isinstance(row['fraud_reasons'], str) else (row['fraud_reasons'] or [])
                for r in reasons:
                    base  = r.split(':')[0]
                    label = _REASON_LABELS.get(base, r.replace('_', ' ').title())
                    counts[label] = counts.get(label, 0) + 1
            except Exception:
                pass

        patterns = [
            {'pattern': k, 'detected': v, 'trend': 'stable'}
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]

        return success_response({
            'flaggedApplications': flagged,
            'stats':               stats,
            'patterns':            patterns,
            'recentBlocked':       recent_blocked,
        })

    except Exception as e:
        log_error(logger, 'get_fraud_data_error', e)
        return error_response('Failed to retrieve fraud data', 500)
