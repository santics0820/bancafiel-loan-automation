"""
Database utilities for BancaFiel backend
Uses pg8000 (pure-Python PostgreSQL driver — no compilation needed)
"""
import os
import json
import logging
import pg8000.native as pg

logger = logging.getLogger(__name__)

DB_HOST     = os.environ.get('DB_HOST', 'localhost')
DB_NAME     = os.environ.get('DB_NAME', 'bancafiel')
DB_USER     = os.environ.get('DB_USER', 'bancafiel_admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_PORT     = int(os.environ.get('DB_PORT', '5432'))


def _connect():
    """Open a new pg8000 connection."""
    return pg.Connection(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        ssl_context=True          # RDS requires SSL
    )


def _rows_to_dicts(conn, rows):
    """Convert pg8000 row tuples + column names → list of dicts."""
    if not rows:
        return []
    columns = [c['name'] for c in conn.columns]
    return [dict(zip(columns, row)) for row in rows]


def execute_query(query, params=None):
    """Execute a SELECT and return list of dicts."""
    conn = _connect()
    try:
        q, kwargs = _prepare(query, params)
        rows = conn.run(q, **kwargs)
        return _rows_to_dicts(conn, rows)
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise
    finally:
        conn.close()


def execute_query_single(query, params=None):
    """Return first row as dict, or None."""
    results = execute_query(query, params)
    return results[0] if results else None


def execute_insert(query, params=None):
    """Execute INSERT/UPDATE/DELETE — returns RETURNING rows or row count."""
    conn = _connect()
    try:
        q, kwargs = _prepare(query, params)
        rows = conn.run(q, **kwargs)
        if rows is not None and conn.columns:
            return _rows_to_dicts(conn, rows)
        return conn.row_count
    except Exception as e:
        logger.error(f"Insert/update error: {e}")
        raise
    finally:
        conn.close()


def _pg_params(params):
    """Normalise params to a flat list."""
    if params is None:
        return []
    if isinstance(params, (list, tuple)):
        return list(params)
    return [params]


def _prepare(query, params):
    """
    Convert %s or $N placeholders → :p1, :p2 … (pg8000 native named style)
    and build the matching kwargs dict {p1: val1, p2: val2, …}.
    """
    import re
    values = _pg_params(params)

    # Replace %s sequentially → :p1, :p2, …
    counter = [0]
    def next_placeholder(_):
        counter[0] += 1
        return f':p{counter[0]}'
    q = re.sub(r'%s', next_placeholder, query)

    # Also replace any pre-existing $1/$2 style → :p1/:p2
    q = re.sub(r'\$(\d+)', lambda m: f':p{m.group(1)}', q)

    kwargs = {f'p{n+1}': v for n, v in enumerate(values)}
    return q, kwargs


def _convert_placeholders(query):
    """Legacy helper kept for compatibility."""
    count = 0
    out = []
    i = 0
    while i < len(query):
        if query[i:i+2] == '%s':
            count += 1
            out.append(f'${count}')
            i += 2
        else:
            out.append(query[i])
            i += 1
    return ''.join(out)


# ── Convenience helpers ───────────────────────────────────────────────────────

def get_customer_by_curp(curp):
    return execute_query_single("SELECT * FROM customers WHERE curp = $1", (curp,))


def get_application_by_id(application_id):
    return execute_query_single("""
        SELECT a.*, c.full_name, c.email, c.curp, c.phone, c.address
        FROM applications a JOIN customers c ON a.customer_id = c.id
        WHERE a.id = $1
    """, (application_id,))


def create_application_history(application_id, action, actor,
                               notes=None, metadata=None):
    """Append an audit-trail row."""
    metadata_json = json.dumps(metadata) if metadata else None
    execute_insert("""
        INSERT INTO application_history
            (application_id, action, actor, notes, metadata)
        VALUES ($1, $2, $3, $4, $5)
    """, (application_id, action, actor, notes, metadata_json))
