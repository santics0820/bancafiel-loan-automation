"""
Lambda #7: Notification Sender
Sends SES HTML emails to customers at each stage of the process
"""
import json
import boto3
import os

try:
    from utils.logger import setup_logger, log_event, log_error
    from utils.database import execute_query_single, create_application_history
except ImportError:
    import logging
    def setup_logger(name): return logging.getLogger(name)
    def log_event(l, t, d): l.info(f"{t}: {d}")
    def log_error(l, t, e, c=None): l.error(f"{t}: {e}")

logger = setup_logger(__name__)
ses_client = boto3.client('ses', region_name='us-east-1')

FROM_EMAIL = os.environ.get('SES_FROM_EMAIL', 'bancafiel.noreply@gmail.com')

# ── Shared HTML layout ─────────────────────────────────────────────────────

def _base(content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BancaFiel</title>
</head>
<body style="margin:0;padding:0;background:#05070a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#05070a;padding:40px 16px;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0" border="0" style="max-width:580px;width:100%;">

          <!-- HEADER: orb + wordmark -->
          <tr>
            <td align="center" style="padding-bottom:28px;">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td valign="middle" style="padding-right:10px;">
                    <!-- orb -->
                    <div style="width:32px;height:32px;border-radius:50%;background:radial-gradient(circle at 35% 30%, #f1f5f9 0%, #cbd5e1 35%, #64748b 65%, #334155 100%);box-shadow:0 4px 16px rgba(148,163,184,0.35);"></div>
                  </td>
                  <td valign="middle">
                    <span style="font-size:22px;font-weight:800;letter-spacing:0.06em;color:#ffffff;">BANCAFIEL</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- CARD -->
          <tr>
            <td style="background:#0f1218;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px 40px 36px;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
              {content}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td align="center" style="padding-top:28px;">
              <p style="margin:0;font-size:12px;color:#475569;line-height:1.6;">
                Este correo fue enviado automáticamente por BancaFiel. Por favor no respondas a este mensaje.<br/>
                ¿Necesitas ayuda? <a href="mailto:soporte@bancafiel.com" style="color:#60a5fa;text-decoration:none;">soporte@bancafiel.com</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _divider() -> str:
    return '<tr><td style="padding:20px 0;"><div style="height:1px;background:rgba(255,255,255,0.07);"></div></td></tr>'


def _detail_row(label: str, value: str, value_color: str = '#ffffff') -> str:
    return f"""
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;">{label}</td>
            <td align="right" style="font-size:14px;font-weight:700;color:{value_color};">{value}</td>
          </tr>
        </table>
      </td>
    </tr>"""


# ── Template: received ──────────────────────────────────────────────────────

def _html_received(name: str, amount: float, app_id: str) -> str:
    content = f"""
      <h1 style="margin:0 0 8px;font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">
        Solicitud recibida
      </h1>
      <p style="margin:0 0 28px;font-size:15px;color:#94a3b8;line-height:1.6;">
        Hola <strong style="color:#ffffff;">{name}</strong>, hemos recibido tu solicitud correctamente.
      </p>

      <!-- Amount block -->
      <div style="background:rgba(96,165,250,0.07);border:1px solid rgba(96,165,250,0.18);border-radius:14px;padding:24px;margin-bottom:28px;text-align:center;">
        <p style="margin:0 0 4px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:#60a5fa;">Monto solicitado</p>
        <p style="margin:0;font-size:36px;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">${amount:,.0f} <span style="font-size:18px;font-weight:400;color:#94a3b8;">MXN</span></p>
      </div>

      <!-- Details table -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        {_detail_row('Folio', app_id, '#e2e8f0')}
        {_detail_row('Estado', 'En proceso', '#fbbf24')}
      </table>

      <p style="margin:28px 0 0;font-size:14px;color:#94a3b8;line-height:1.7;">
        Estamos analizando tu información. Te notificaremos por correo en cuanto tengamos una resolución.
      </p>
    """
    return _base(content)


# ── Template: approved ──────────────────────────────────────────────────────

def _html_approved(name: str, amount: float, app_id: str) -> str:
    content = f"""
      <!-- Badge -->
      <div style="display:inline-block;background:rgba(110,231,183,0.1);border:1px solid rgba(110,231,183,0.3);border-radius:100px;padding:6px 16px;margin-bottom:20px;">
        <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#6ee7b7;">✓ &nbsp;Aprobada</span>
      </div>

      <h1 style="margin:0 0 8px;font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">
        ¡Tu crédito fue aprobado!
      </h1>
      <p style="margin:0 0 28px;font-size:15px;color:#94a3b8;line-height:1.6;">
        Hola <strong style="color:#ffffff;">{name}</strong>, tenemos excelentes noticias para ti.
      </p>

      <!-- Amount block -->
      <div style="background:rgba(110,231,183,0.07);border:1px solid rgba(110,231,183,0.2);border-radius:14px;padding:28px;margin-bottom:28px;text-align:center;">
        <p style="margin:0 0 4px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:#6ee7b7;">Línea de crédito aprobada</p>
        <p style="margin:0;font-size:40px;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">${amount:,.0f} <span style="font-size:20px;font-weight:400;color:#94a3b8;">MXN</span></p>
      </div>

      <!-- Details table -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        {_detail_row('Folio', app_id, '#e2e8f0')}
        {_detail_row('Estado', 'Aprobada', '#6ee7b7')}
      </table>

      <!-- CTA -->
      <div style="text-align:center;margin:32px 0 8px;">
        <a href="https://bancafiel.com" style="display:inline-block;background:linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%);color:#0f172a;font-size:14px;font-weight:800;letter-spacing:0.04em;text-decoration:none;padding:16px 40px;border-radius:14px;">
          Activar mi tarjeta →
        </a>
      </div>
    """
    return _base(content)


# ── Template: rejected ──────────────────────────────────────────────────────

def _html_rejected(name: str, app_id: str) -> str:
    content = f"""
      <!-- Badge -->
      <div style="display:inline-block;background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.25);border-radius:100px;padding:6px 16px;margin-bottom:20px;">
        <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#f87171;">Solicitud no aprobada</span>
      </div>

      <h1 style="margin:0 0 8px;font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.02em;">
        Actualización de tu solicitud
      </h1>
      <p style="margin:0 0 28px;font-size:15px;color:#94a3b8;line-height:1.6;">
        Hola <strong style="color:#ffffff;">{name}</strong>, lamentamos informarte que en este momento no fue posible aprobar tu solicitud.
      </p>

      <!-- Details table -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        {_detail_row('Folio', app_id, '#e2e8f0')}
        {_detail_row('Puedes reintentar en', '90 días', '#94a3b8')}
      </table>

      <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:20px;margin-top:28px;">
        <p style="margin:0 0 6px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#64748b;">¿Tienes dudas?</p>
        <p style="margin:0;font-size:14px;color:#94a3b8;line-height:1.6;">
          Escríbenos a <a href="mailto:soporte@bancafiel.com" style="color:#60a5fa;text-decoration:none;">soporte@bancafiel.com</a> y con gusto te orientamos.
        </p>
      </div>
    """
    return _base(content)


# ── Email templates map ─────────────────────────────────────────────────────

EMAIL_SUBJECTS = {
    'received': 'Hemos recibido tu solicitud — BancaFiel',
    'approved': '¡Tu línea de crédito fue aprobada! — BancaFiel',
    'rejected': 'Actualización sobre tu solicitud — BancaFiel',
}


def _build_html(notification_type: str, name: str, amount: float, app_id: str) -> str:
    if notification_type == 'approved':
        return _html_approved(name, amount, app_id)
    elif notification_type == 'rejected':
        return _html_rejected(name, app_id)
    return _html_received(name, amount, app_id)


# ── Handler ─────────────────────────────────────────────────────────────────

def handler(event, context):
    try:
        application_id = event.get('application_id')
        notification_type = event.get('type', 'received')

        log_event(logger, 'notificationSender_invoked', {
            'application_id': application_id,
            'type': notification_type
        })

        app = execute_query_single("""
            SELECT a.loan_amount, a.application_type, c.full_name, c.email
            FROM applications a JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
        """, (application_id,))

        if not app:
            logger.error(f"Application {application_id} not found")
            return {'statusCode': 404}

        customer_email = app['email']
        name = app['full_name'].title()
        amount = float(app['loan_amount'])
        app_id = str(application_id)[:8].upper()

        subject = EMAIL_SUBJECTS.get(notification_type, EMAIL_SUBJECTS['received'])
        html_body = _build_html(notification_type, name, amount, app_id)

        try:
            ses_client.send_email(
                Source=FROM_EMAIL,
                Destination={'ToAddresses': [customer_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}},
                }
            )
            log_event(logger, 'email_sent', {
                'to': customer_email,
                'type': notification_type,
                'application_id': application_id
            })
        except Exception as e:
            logger.warning(f"SES send failed: {e}")

        create_application_history(
            application_id, f'email_sent_{notification_type}', 'system',
            notes=f'HTML notification email sent: {notification_type} to {customer_email}'
        )

        return {'statusCode': 200, 'message': f'Notification sent: {notification_type}'}

    except Exception as e:
        log_error(logger, 'notificationSender_error', e)
        return {'statusCode': 500, 'error': str(e)}
