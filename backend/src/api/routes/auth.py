"""
API Routes: Auth
POST /api/auth/register  — create client account
POST /api/auth/login     — verify credentials, return session token
"""
import json
import hashlib
import secrets

try:
    from utils.logger import setup_logger, log_error
    from utils.database import execute_query_single, execute_insert
    from utils.response import success_response, error_response, created_response
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")
    def success_response(d, s=200): return {'statusCode': s, 'body': json.dumps(d, default=str)}
    def error_response(m, s=400, c=None): return {'statusCode': s, 'body': json.dumps({'error': m})}
    def created_response(d, l=None): return {'statusCode': 201, 'body': json.dumps(d, default=str)}

logger = setup_logger(__name__)


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 200_000).hex()


def register(event, context):
    """POST /api/auth/register"""
    try:
        body = json.loads(event.get('body') or '{}')
        email    = (body.get('email')    or '').strip().lower()
        password = (body.get('password') or '').strip()

        if not email or '@' not in email:
            return error_response('Email inválido', 400)
        if len(password) < 6:
            return error_response('La contraseña debe tener al menos 6 caracteres', 400)

        # Check if already registered
        existing = execute_query_single(
            "SELECT id FROM client_accounts WHERE email = %s", (email,)
        )
        if existing:
            return error_response('Este correo ya tiene una cuenta. Inicia sesión.', 409)

        salt          = secrets.token_hex(32)
        password_hash = _hash_password(password, salt)
        session_token = secrets.token_urlsafe(32)

        execute_insert("""
            INSERT INTO client_accounts (email, password_hash, salt, session_token)
            VALUES (%s, %s, %s, %s)
        """, (email, password_hash, salt, session_token))

        # Check if they already have an application with this email
        app = execute_query_single("""
            SELECT UPPER(LEFT(a.id::text, 8)) as folio
            FROM applications a
            LEFT JOIN customers c ON a.customer_id = c.id
            WHERE LOWER(COALESCE(c.email, a.applicant_email)) = %s
            ORDER BY a.created_at DESC LIMIT 1
        """, (email,))

        return created_response({
            'token':          session_token,
            'email':          email,
            'folio':          app['folio'] if app else None,
            'hasApplication': app is not None,
        })

    except Exception as e:
        log_error(logger, 'register_error', e)
        return error_response('Error al crear la cuenta', 500)


def login(event, context):
    """POST /api/auth/login"""
    try:
        body = json.loads(event.get('body') or '{}')
        email    = (body.get('email')    or '').strip().lower()
        password = (body.get('password') or '').strip()

        if not email or not password:
            return error_response('Correo y contraseña requeridos', 400)

        account = execute_query_single(
            "SELECT id, password_hash, salt FROM client_accounts WHERE email = %s", (email,)
        )
        if not account:
            return error_response('Correo o contraseña incorrectos', 401)

        if _hash_password(password, account['salt']) != account['password_hash']:
            return error_response('Correo o contraseña incorrectos', 401)

        # Rotate session token on each login
        session_token = secrets.token_urlsafe(32)
        execute_insert(
            "UPDATE client_accounts SET session_token = %s WHERE id = %s",
            (session_token, str(account['id']))
        )

        # Fetch their latest application folio
        app = execute_query_single("""
            SELECT UPPER(LEFT(a.id::text, 8)) as folio
            FROM applications a
            LEFT JOIN customers c ON a.customer_id = c.id
            WHERE LOWER(COALESCE(c.email, a.applicant_email)) = %s
            ORDER BY a.created_at DESC LIMIT 1
        """, (email,))

        return success_response({
            'token':          session_token,
            'email':          email,
            'folio':          app['folio'] if app else None,
            'hasApplication': app is not None,
        })

    except Exception as e:
        log_error(logger, 'login_error', e)
        return error_response('Error al iniciar sesión', 500)
